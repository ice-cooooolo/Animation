import maya.cmds as cmds

from .base_check import CheckItem

class HistoryCheck(CheckItem):
    label = "Construction History"
    category = "Geometry"
    is_fixable = True

    def __init__(self):
        super().__init__()

        self.whitelist = [
            'skinCluster',  # 蒙皮
            'blendShape',  # 表情/变形器
            'tweak',  # 节点微调
            'groupParts',  # 组部件
            'groupId',  # 组ID
            'dagPose',  # 绑定姿态
            'shadingEngine',  # 材质组
            'materialInfo'  # 材质信息
        ]

    def check(self):
        # 1. 优先检查选中的物体
        selected = cmds.ls(selection=True, long=True) or []

        # 如果没选中东西，为了保险起见，还是检查场景所有 Mesh 的父级
        if not selected:
            meshes = cmds.ls(type="mesh", long=True)
            transforms = cmds.listRelatives(meshes, parent=True, fullPath=True) or []
            selected = list(set(transforms))
        else:
            # 过滤：只保留 Transform 类型的节点，且要有 Shape (排除空组)
            # 同时排除 骨骼 (Joints)，因为骨骼通常没有历史问题
            filtered_selection = []
            for obj in selected:
                if cmds.objectType(obj) == 'transform':
                    shapes = cmds.listRelatives(obj, shapes=True)
                    if shapes and cmds.objectType(shapes[0]) == 'mesh':
                        filtered_selection.append(obj)
            selected = filtered_selection

        failed = []

        for obj in selected:
            # 获取历史，pruneDagObjects=True 排除自身 Transform 和 Shape
            history = cmds.listHistory(obj, pruneDagObjects=True) or []

            has_bad_history = False
            for node in history:
                node_type = cmds.objectType(node)
                # 【关键逻辑】如果节点类型不在白名单里，才算“垃圾历史”
                if node_type not in self.whitelist:
                    # 可以在这里 print 调试，看看到底是什么节点导致的
                    print(f"DEBUG: Found bad history '{node}' ({node_type}) on {obj}")
                    has_bad_history = True
                    break

            if has_bad_history:
                failed.append(obj)

        if not failed:
            self.status = "Passed"
            self.info_message = "No modeling history found (Skinning ignored)."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(failed)} objects with unbaked modeling history."
            self.failed_objects = failed

    def fix(self):
        if self.failed_objects:
            for obj in self.failed_objects:
                try:
                    # 【关键修改】使用 bakePartialHistory
                    # prePostDeformers=True 意思是在变形器(蒙皮)之前清理历史
                    # 这样可以保留蒙皮，只删除建模记录
                    cmds.bakePartialHistory(obj, prePostDeformers=True)
                    print(f"Fixed history for: {obj}")
                except Exception as e:
                    print(f"Failed to fix {obj}: {e}")

        # 修复完重新检查一遍状态
        self.check()


class UnFrozenTransformCheck(CheckItem):
    label = "Unfrozen Transforms"
    category = "Geometry"
    is_fixable = True

    def check(self):
        # 1. 优先获取选中物体
        selected = cmds.ls(selection=True, long=True) or []

        # 2. 如果没选中，回退到检查所有 Mesh
        if not selected:
            meshes = cmds.ls(type="mesh", long=True)
            transforms = cmds.listRelatives(meshes, parent=True, fullPath=True) or []
            selected = list(set(transforms))

        failed = []
        for obj in selected:
            # 【关键保护】绝对跳过骨骼 (Joints)
            # 骨骼必须有位移数据，不能 Freeze
            if cmds.objectType(obj) == 'joint':
                continue

            # 确保是 Transform 节点
            if cmds.objectType(obj) != 'transform':
                continue

            # Check translate(x,y,z) < 0.001 (允许极小浮点误差)
            t = cmds.xform(obj, query=True, translation=True, objectSpace=True)
            r = cmds.xform(obj, query=True, rotation=True, objectSpace=True)
            s = cmds.xform(obj, query=True, scale=True, objectSpace=True)

            # 只要有一个数值超标，就加入错误列表
            if any(abs(v) > 0.001 for v in t) or \
                    any(abs(v) > 0.001 for v in r) or \
                    any(abs(v - 1.0) > 0.001 for v in s):
                failed.append(obj)

        if not failed:
            self.status = "Passed"
            self.info_message = "All meshes are frozen."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(failed)} meshes with non-zero transforms."
            self.failed_objects = failed

    def fix(self):
        if self.failed_objects:
            # 注意：如果模型已经蒙皮，Freeze Transform 可能会报错或被锁定
            # 这是 Maya 的保护机制，这种情况下需要用户手动解绑修复
            try:
                cmds.makeIdentity(self.failed_objects, apply=True, translate=True, rotate=True, scale=True)
                print(f"Frozen transforms for {len(self.failed_objects)} objects.")
            except Exception as e:
                print(f"Error fixing transforms (Mesh might be skinned?): {e}")

        self.check()


class NgonsCheck(CheckItem):
    label = "N-gons (Faces > 4 edges)"
    category = "Geometry"
    is_fixable = False

    def check(self):
        # 优先检查选中的，没选中则检查所有
        meshes = cmds.ls(selection=True, type="transform", long=True)
        if not meshes:
            # 如果选中的不是transform或者没选中，尝试找所有mesh
            all_meshes = cmds.ls(type="mesh", long=True)
            if not all_meshes:
                self.status = "Passed"
                return
            meshes = cmds.listRelatives(all_meshes, parent=True, fullPath=True)
            meshes = list(set(meshes))

        # 过滤掉非 Mesh 物体 (比如误选了骨骼)
        target_meshes = []
        for obj in meshes:
            shapes = cmds.listRelatives(obj, shapes=True)
            if shapes and cmds.objectType(shapes[0]) == 'mesh':
                target_meshes.append(obj)

        if not target_meshes:
            self.status = "Passed"
            return

        cmds.select(target_meshes)
        cmds.selectMode(component=True)
        cmds.selectType(facet=True)

        # Maya 查找 N-gon 的约束命令
        cmds.polySelectConstraint(mode=3, type=0x0008, size=3)

        ngons = cmds.ls(selection=True)

        # 还原选择模式
        cmds.polySelectConstraint(disable=True)
        cmds.selectMode(object=True)
        # 还原选中状态 (可选)
        cmds.select(target_meshes)

        if not ngons:
            self.status = "Passed"
            self.info_message = "No N-gons found."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(ngons)} faces > 4 edges."
            self.failed_objects = ngons