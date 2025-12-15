import maya.cmds as cmds
import maya.mel as mel
import json
import os
from .base_exporter import ExporterBase

class AnimExporter(ExporterBase):
    """
    动画导出策略 (Config-Driven 版本)。
    流程：
    1. Pre-flight Checks (读取 Config["Animation"] 里的配置，如 FPS 检查)
    2. Find Root Joint (寻找根骨骼)
    3. Bake Simulation (烘焙动画到骨骼)
    4. Isolation (断开层级，只导出骨骼)
    5. Export Selection (利用 FBX 导出选中项功能，自动过滤掉控制器垃圾)
    """
    def _process_logic(self):
        # --- 1. 通用检查 ---
        if not self.run_preflight_checks("Animation"):
            return False

        # --- 2. 寻找根骨骼 ---
        root_joint = self._find_root_joint()
        if not root_joint:
            self.add_log("Error: Could not find Root Joint!")
            return False
        self.add_log(f"Found Root Joint: {root_joint}")

        # --- 3. 获取时间范围 ---
        start = cmds.playbackOptions(query=True, minTime=True)
        end = cmds.playbackOptions(query=True, maxTime=True)

        # ========================================================
        # 【关键修改 A】: 获取整个骨骼家族列表
        # 我们不只要 root，我们要找到它下面每一根骨头
        # ========================================================
        all_joints = cmds.listRelatives(root_joint, allDescendents=True, type="joint", fullPath=True) or []
        all_joints.append(root_joint) # 别忘了把爷爷（Root）也加进去

        # --- 4. 烘焙动画 (The Core) ---
        self.add_log(f"Baking simulation ({start} - {end})...")
        try:
            # 【关键修改 B】: 直接烘焙列表，而不是只给一个 root 让它去猜
            cmds.bakeResults(
                all_joints,              # <--- 明确指定烤哪些骨头
                t=(start, end),
                simulation=True,         # 模拟解算
                sampleBy=1,
                disableImplicitControl=True, # 烘焙后断开约束，非常重要！
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
                minimizeRotation=True,
                shape=True
            )
        except Exception as e:
            self.add_log(f"Bake failed: {e}")
            return False

        # --- 5. 隔离与清理 (Isolation) ---
        self.add_log("Isolating skeleton for export...")
        try:
            # A. Unparent
            # 注意：必须先烘焙(Bake)完，有了关键帧，才能 Unparent！顺序是对的。
            if cmds.listRelatives(root_joint, parent=True):
                cmds.parent(root_joint, world=True)

            # B. Select
            # 【关键修改 C】: 选中所有骨骼！不仅仅是 Root！
            # 这样 Export Selected (es=True) 才能保证每一根骨头的曲线都被写入 FBX
            cmds.select(all_joints)  # <--- 这里的区别决定了成败

            self.add_log("Skeleton isolated and selected (All joints).")
            return True

        except Exception as e:
            self.add_log(f"Isolation failed: {e}")
            return False

    def _find_root_joint(self):
        joints = cmds.ls(type="joint")
        condidates = []

        for j in joints:
            parent = cmds.listRelatives(j, parent=True)
            is_top_level = False
            if not parent:
                is_top_level = True
            elif cmds.nodeType(parent[0]) != "joint":
                is_top_level = True

            if is_top_level:
                condidates.append(j)

        if not condidates:
            return None

        if len(condidates) == 1:
            return condidates[0]

        for c in condidates:
            name = c.lower()
            if any(n in name for n in ["root", "hips", "pelvis", "bip001"]):
                return c
        return condidates[0]

    def _export_fbx_command(self, path):
        """
        重写基类的导出命令。
        针对动画导出，我们需要特殊的 FBX 设置。
        """
        # 1. 几何体设置 (保持平滑组)
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval("FBXExportSmoothMesh -v true")

        # 2. 动画设置
        # 我们已经手动 Bake 过了，所以关掉 FBX 自带的 Bake
        mel.eval("FBXExportBakeComplexAnimation -v false")
        # 只导动画？不，通常游戏引擎需要骨骼结构，所以保持默认
        mel.eval("FBXExportAnimationOnly -v false")
        # 关掉输入连接 (防止把约束节点导出去)
        mel.eval("FBXExportInputConnections -v false")

        # 3. 轴向 (根据引擎需求，Unity=Y, Unreal=Z)
        mel.eval("FBXExportUpAxis y")

        # 4. 【关键】使用 es=True (Export Selected)
        # 因为我们只选中了根骨骼，其他垃圾都不会被导出
        cmds.file(path, force=True, options="v=0;", type="FBX export", pr=True, es=True)
        # --- C. 【新增】生成 Sidecar JSON ---
        self._write_sidecar_json(path)

    def _write_sidecar_json(self, fbx_path):
        """
        生成伴随 JSON 文件。
        例如: Run.fbx -> Run.json
        """
        try:
            # 1. 计算 JSON 路径
            # os.path.splitext("D:/Export/Run.fbx") -> ("D:/Export/Run", ".fbx")
            base_path = os.path.splitext(fbx_path)[0]
            json_path = f"{base_path}.json"

            # 2. 获取动画数据
            # 这些数据已经是经过 Checker 修正过的准确数据
            start = cmds.playbackOptions(q=True, min=True)
            end = cmds.playbackOptions(q=True, max=True)
            fps = cmds.currentUnit(q=True, time=True)  # e.g. "ntsc" (30fps) or "game" (15fps)

            # 计算时长 (帧数)
            duration = end - start + 1

            # 3. 构造数据字典
            data = {
                "asset_name": os.path.basename(base_path),  # Run
                "frame_start": start,
                "frame_end": end,
                "duration_frames": duration,
                "fps": fps,
                "source_file": cmds.file(q=True, sceneName=True)  # 记录来源，方便追溯
            }

            # 4. 写入文件
            # 同样建议使用 io.open 保证兼容性，这里为了简便直接用 open (Python 3)
            # 如果是 Maya 2020 以前，记得用 io.open
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)

            self.add_log(f"Metadata saved: {os.path.basename(json_path)}")

        except Exception as e:
            self.add_log(f"Warning: Failed to save JSON metadata: {e}")