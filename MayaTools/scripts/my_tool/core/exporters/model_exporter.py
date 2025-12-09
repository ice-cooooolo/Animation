from .base_exporter import ExporterBase
from ..checks import geometry_checks
from ..checks import naming_checks

class ModelExporter(ExporterBase):
    """
    模型导出策略。
    特点：强力检查几何体质量，自动修复历史和变换，但不烘焙动画。
    """
    def _process_logic(self):
        self.add_log("Running Model Sanity Checks...")
        # --- 1. 历史记录检查 & 自动修复 ---
        check_hist = geometry_checks.HistoryCheck()
        check_hist.check()
        if check_hist.status == "Failed":
            self.add_log(f"Found history on {len(check_hist.failed_objects)} objects. Fixing...")
            check_hist.fix()
            if check_hist.status == "Failed":
                self.add_log("Error: Failed to delete history.")
                return False
        # --- 2. 冻结变换检查 & 自动修复 ---
        check_xform = geometry_checks.UnFrozenTransformCheck()
        check_xform.check()
        if check_xform.status == "Failed":
            self.add_log(f"Found unfrozen transforms. Fixing...")
            check_xform.fix()
            if check_xform.status == "Failed":
                self.add_log("Error: Failed to delete unfrozen transforms.")
                return False
        # --- 3. 重名检查 (硬性指标) ---
        check_name = naming_checks.DuplicateNameCheck()
        check_name.check()
        if check_name.status == "Failed":
            self.add_log("CRITICAL ERROR: Duplicate names found!")
            self.add_log(f"Duplicates: {check_name.failed_objects}")
            self.add_log("Auto-fix disabled for safety. Please fix manually.")
            return False  # 这里的 False 会中断整个导出流程
        # --- 4. 准备导出 ---

        self.add_log("Model ready for export.")
        return True