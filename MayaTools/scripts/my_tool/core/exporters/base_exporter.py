import os
import maya.cmds as cmds
import maya.mel as mel
from ... import config
from .. import checker_logic

class ExporterBase:
    """
    导出策略基类。
    规定了所有导出器必须遵守的流程：
    Open -> Process (Check/Fix/Bake) -> Export
    """
    def __init__(self):
        self.status = "Idle"
        self.log = []

        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya")
            except:
                self.add_log("Error: Failed to load fbxmaya plugin!")

    def add_log(self, message):
        print(f"[{self.__class__.__name__}] {message}")
        self.log.append(message)

    def run_preflight_checks(self, mode):
        """
        通用功能：读取 Config，运行所有检查，尝试自动修复。
        如果遇到无法修复的致命错误，返回 False。
        """
        self.add_log(f"--- Running Pre-flight Checks for [{mode}] ---")
        check_instances = checker_logic.get_checks(mode)

        all_passed = True

        for check_item in check_instances:
            check_item.check()

            if check_item.status == "Failed":
                self.add_log(f"xx Failed: {check_item.label}")
                self.add_log(f"   Reason: {check_item.info_message}")

                # 尝试修复
                if check_item.is_fixable:
                    self.add_log(f"   >> Attempting Auto-fix...")
                    check_item.fix()

                    # 修复后复查
                    if check_item.status == "Passed":
                        self.add_log(f"   >> Fixed successfully!")
                        continue  # 继续下一个检查
                    else:
                        self.add_log(f"   >> Fix Failed!")

                # 如果没修好，或者是不可修的
                if check_item.is_critical:
                    self.add_log("CRITICAL ERROR. Stopping Export.")
                    all_passed = False
                    break  # 致命错误，直接跳出循环
                else:
                    self.add_log("Warning: Ignoring non-critical error.")
        return all_passed

    def run(self, file_path, output_dir):
        """
        模板方法模式 (Template Method): 定义了导出的标准骨架。
        子类只需要重写 _process_logic 即可。
        """
        self.log = []
        self.add_log(f"Starting process for: {file_path}")

        if not os.path.exists(file_path):
            self.status = "Failed"
            self.add_log(f"File Not Found: {file_path}")
            return False

        # 1. 打开文件 (Force open)
        try:
            cmds.file(file_path, open=True, force=True)
        except Exception as e:
            self.status = "Failed"
            self.add_log(f"Failed to open file: {file_path}")
            return False
        # 2. 执行核心逻辑 (由子类实现：检查、烘焙、清理)
        try:
            success = self._process_logic()
            if not success:
                self.status = "Failed"
                self.add_log(f"Process Failed: {file_path}")
                return False
        except Exception as e:
            self.status = "Failed"
            self.add_log(f"Error during processing: {e}")
            import traceback
            traceback.print_exc()
            return False
        # 3. 导出 FBX
        # 构造输出路径: OutputDir/FileName.fbx
        file_name = os.path.basename(file_path)
        name_no_ext = os.path.splitext(file_name)[0]
        fbx_path = os.path.join(output_dir, f"{name_no_ext}.fbx").replace("\\", "/")

        try:
            self._export_fbx_command(fbx_path)
            self.status = "Success"
            self.add_log(f"Exported file: {fbx_path}")
            return True
        except Exception as e:
            self.status = "Failed"
            self.add_log(f"Error during export: {e}")
            return False

    def _process_logic(self):
        raise NotImplementedError()

    def _export_fbx_command(self, path):
        """
        执行 FBX 导出命令。
        这里配置通用的 FBX 选项。
        """
        # FBX 设置 (使用 MEL，因为 cmds.file 的 options 字符串太难拼)
        # 1. 几何体
        mel.eval("FBXExportSmoothingGroups -v true")
        mel.eval("FBXExportSmoothMesh -v true")
        mel.eval("FBXExportTriangulate -v false")  # 引擎通常自己会三角化，Maya这边保持四边面更干净

        # 2. 动画 (子类可以在 process_logic 里覆盖这个设置)
        mel.eval("FBXExportBakeComplexAnimation -v false")

        # 3. 杂项
        mel.eval("FBXExportUpAxis y")  # 引擎通常是 Y-Up (Unity) 或 Z-Up (Unreal)，需根据项目配置
        mel.eval("FBXExportScaleFactor 1.0")

        # 4. 执行导出 (Export All)
        # 如果只想导出选中的，改为 es=True (Export Selected)
        # 为了通用性，我们这里用 Export All，或者由子类先选中需要的东西再调 Export Selected
        cmds.file(path, force=True, options="v=0;", type="FBX export", pr=True, ea=True)