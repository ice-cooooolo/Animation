# my_tool/core/controller_logic.py
import maya.cmds as cmds
from ..utils.decorators import undoable

def get_current_selection_name():
    """获取当前选中物体名"""
    sel = cmds.ls(selection=True)
    return sel[0] if sel else None


import maya.cmds as cmds

@undoable
def create_controller(name, shape, size, color_data, match_pos, match_rot, use_offset, constrain_mode, target_node):
    """
    V6.0: 终极形态 - 自动构建 FK 层级 (Auto-Hierarchy)
    """

    # --- 1. 名字处理 ---
    # 为了让自动层级能工作，我们需要更严格的命名逻辑
    # 假设骨骼叫 "Spine_02"，控制器必须叫 "CTRL_Spine_02"
    if target_node:
        short_name = target_node.split("|")[-1]
        # 强制命名规范，以便后续查找父级
        expected_name = f"CTRL_{short_name}"
        if not name:
            ctrl_name = expected_name
        else:
            ctrl_name = name
    else:
        ctrl_name = name if name else "CTRL_new"

    # --- 2. 原点创建 (保持 X 轴朝向) ---
    if shape == "Square":
        ctrl = cmds.circle(n=ctrl_name, nr=(0, 1, 0), r=size, d=1, s=4)[0]
        cmds.xform(ctrl, ro=(45, 0, 0), relative=True)
        cmds.makeIdentity(ctrl, apply=True, t=1, r=1, s=1)
    elif shape == "Cube":
        ctrl = cmds.circle(n=ctrl_name, nr=(1, 0, 0), r=size)[0]
    else:
        ctrl = cmds.circle(n=ctrl_name, nr=(0, 1, 0), r=size)[0]

    # --- 3. 上色 ---
    _apply_color(ctrl, color_data)

    # 同步旋转顺序
    # if target_node:
    #     try:
    #         ro_idx = cmds.getAttr(f"{target_node}.rotateOrder")
    #         cmds.setAttr(f"{ctrl}.rotateOrder", ro_idx)
    #     except:
    #         pass

    # --- 4. 打组 ---
    node_to_move = ctrl
    # 强制 FK 系统必须有组，否则无法做层级
    # 哪怕用户没勾选，为了层级安全，建议还是得有个组，或者直接操作控制器
    # 这里我们假设用户为了做绑定，肯定勾选了 use_offset
    if use_offset:
        grp_name = f"GRP_{ctrl_name}"
        grp = cmds.group(ctrl, n=grp_name)
        node_to_move = grp

    # --- 5. 对齐 ---
    if target_node:
        try:
            kwargs = {}
            if match_pos:
                kwargs['pos'] = True
            if match_rot:
                kwargs['rot'] = True

            if kwargs:  # 至少有一个参数才调用
                cmds.matchTransform(node_to_move, target_node, **kwargs)

        except Exception as e:
            print(e)

    # --- 6. 约束 ---
    if target_node and constrain_mode != "None":
        try:
            if constrain_mode == "Parent":
                cmds.parentConstraint(ctrl, target_node, mo=True)
            elif constrain_mode == "Point":
                cmds.pointConstraint(ctrl, target_node, mo=True)
            elif constrain_mode == "Orient":
                cmds.orientConstraint(ctrl, target_node, mo=True)
        except Exception as e:
            print(f"Constraint error: {e}")

    # -------------------------------------------------------------------------
    # 🆕 V6.0 核心功能：自动寻找父级控制器 (Auto Hierarchy)
    # -------------------------------------------------------------------------
    if target_node and use_offset:
        # 1. 找骨骼的爸爸
        parent_jnt_list = cmds.listRelatives(target_node, parent=True)

        if parent_jnt_list:
            parent_jnt = parent_jnt_list[0]
            # 2. 推测爸爸的控制器应该叫什么名字
            # 假设命名规则是: BoneName -> CTRL_BoneName
            # 这里需要处理一下 namespace 或者路径，取短名
            parent_jnt_short = parent_jnt.split("|")[-1]
            search_ctrl_name = f"CTRL_{parent_jnt_short}"

            # 3. 检查场景里有没有这个控制器
            if cmds.objExists(search_ctrl_name):
                print(f"🤖 Auto-Hierarchy: Found parent controller [{search_ctrl_name}], parenting...")
                try:
                    # 4. 【关键】把当前的组 (GRP)，P 给爸爸的控制器 (CTRL)
                    cmds.parent(node_to_move, search_ctrl_name)
                except Exception as e:
                    print(f"Auto-parent failed: {e}")
            else:
                print(f"ℹ️ Parent controller [{search_ctrl_name}] not found. Skipping hierarchy.")

    # --- 7. 收尾 ---
    cmds.select(ctrl)
    return ctrl


def _apply_color(node, color_data):
    # (保持不变)
    shapes = cmds.listRelatives(node, shapes=True)
    if not shapes: return
    shape = shapes[0]
    cmds.setAttr(f"{shape}.overrideEnabled", 1)
    if color_data['type'] == 'index':
        cmds.setAttr(f"{shape}.overrideRGBColors", 0)
        cmds.setAttr(f"{shape}.overrideColor", int(color_data['value']))
    elif color_data['type'] == 'rgb':
        cmds.setAttr(f"{shape}.overrideRGBColors", 1)
        cmds.setAttr(f"{shape}.overrideColorRGB", *color_data['value'])