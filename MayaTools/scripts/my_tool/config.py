# my_tool/config.py
from .core.checks import scene_checks, naming_checks, geometry_checks

# --- 全局常量配置 ---
TARGET_FPS = "film"  # 可以在这里统一修改 FPS 标准

# --- 检查项清单 (Menu) ---
# 这里定义了不同模式下，具体要运行哪些检查
# 直接存 Class 对象，而不是字符串，这样跳转方便，不易出错

CHECK_LIST = {
    "Model": [
        scene_checks.FPSCheck,
        scene_checks.UnknownNodeCheck,
        naming_checks.DuplicateNameCheck,
        geometry_checks.HistoryCheck,
        geometry_checks.UnFrozenTransformCheck,
        geometry_checks.NgonsCheck,
    ],

    "Rig": [
        scene_checks.FPSCheck,
        scene_checks.UnknownNodeCheck,
        naming_checks.DuplicateNameCheck,
        # rig_checks.UnfrozenCtrlCheck,
    ],

    "Animation": [
        scene_checks.FPSCheck,
        # anim_checks.KeyframeOnGeoCheck,
    ]
}