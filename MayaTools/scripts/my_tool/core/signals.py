# my_tool/core/signals.py
from PySide6.QtCore import QObject, Signal

class GlobalSignals(QObject):
    """全局信号中心"""
    asset_renamed = Signal(str, str)  # 发送 (旧名字, 新名字)

# 单例实例
signals = GlobalSignals()