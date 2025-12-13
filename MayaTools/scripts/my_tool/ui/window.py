# my_tool/ui/window.py
import maya.OpenMayaUI as omui
import os

from .widgets.renamer_widget import RenamerWidget

# --- 1. 兼容性导入 ---
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    import shiboken2 as shiboken
except ImportError:
    from PySide6 import QtCore, QtWidgets, QtGui
    import shiboken6 as shiboken

# --- 2. 导入子页面 ---
# 注意：这里引用了刚才新建的 home_widget
from .widgets import home_widget
from .widgets import controller_box_widget, renamer_widget, checker_widget, version_widget, exporter_widget

WINDOW_OBJECT_NAME = "My_TATool_Unique_ID_v1"

class MainWindow(QtWidgets.QWidget):
    # 定义单例变量
    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("My TA Tool (Architecture Ver.)")
        self.resize(1000, 800)
        self.setWindowFlags(QtCore.Qt.Window)

        # 初始化 UI
        self._init_ui()

    def _init_ui(self):
        # 主布局：水平 (左边菜单，右边内容)
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        main_layout.setSpacing(0)

        # === A. 左侧：侧边栏 ===
        self.side_menu = QtWidgets.QFrame()
        self.side_menu.setFixedWidth(150)
        # 简单美化一下背景，一眼看出分区
        self.side_menu.setStyleSheet("background-color: #2b2b2b; border-right: 1px solid #111;")

        menu_layout = QtWidgets.QVBoxLayout(self.side_menu)
        menu_layout.setContentsMargins(5, 10, 5, 10)
        menu_layout.setAlignment(QtCore.Qt.AlignTop)

        # === 1. 定义页面配置 (Registry) ===
        # 这是一个列表，每一项是一个元组/字典：(按钮显示文字, 对应的页面类)
        # 这种数据结构让顺序和内容一目了然，想调整顺序只需要在这里换行
        page_config = [
            ("绑定 / Rig", controller_box_widget.ControlBoxWidget),
            ("检查 / Check", checker_widget.CheckerWidget),
            ("重命名 / Rename", renamer_widget.RenamerWidget),
            ("版本控制 / Version", version_widget.VersionWidget),
            ("导出 / Export", exporter_widget.ExporterWidget)
        ]

        # === 2. 循环生成 (Factory Loop) ===
        self.stack = QtWidgets.QStackedWidget()

        # 我们用 enumerate 获取索引 i，用于后面的信号连接
        for i, (btn_text, widget_class) in enumerate(page_config):
            # --- A. 创建并配置按钮 ---
            btn = QtWidgets.QPushButton(btn_text)
            btn.setMinimumHeight(30)

            # 添加到侧边栏布局
            menu_layout.addWidget(btn)

            # --- B. 实例化并添加页面 ---
            # 动态实例化类：widget_class() 等同于 exporter_widget.ExporterWidget()
            page_widget = widget_class()
            self.stack.addWidget(page_widget)

            # --- C. 信号连接 ---
            btn.clicked.connect(lambda checked=False, index=i: self.switch_page(index))

        # 加弹簧，把按钮顶上去
        menu_layout.addStretch()

        # === 3. 组装 ===
        main_layout.addWidget(self.side_menu)
        main_layout.addWidget(self.stack)

        # === 辅助函数 ===

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

    # --- 单例启动方法 ---
    @classmethod
    def show_ui(cls):
        """
        健壮的单例启动方法：
        通过 objectName 在 Qt 全局层面查找旧窗口，无视 Python Reload 的影响。
        """
        # 1. 获取 Maya 主窗口
        maya_win_ptr = omui.MQtUtil.mainWindow()
        maya_win = None
        if maya_win_ptr:
            maya_win = shiboken.wrapInstance(int(maya_win_ptr), QtWidgets.QWidget)

        # 2. 【核心修复】关闭旧窗口
        # 不再依赖 cls._instance，而是直接问 Qt 应用程序
        # topLevelWidgets() 会返回当前内存里所有独立的窗口
        for widget in QtWidgets.QApplication.topLevelWidgets():
            try:
                if widget.objectName() == WINDOW_OBJECT_NAME:
                    print(f"--- Found old instance: {widget}, closing it... ---")
                    widget.close()
                    widget.deleteLater()
            except RuntimeError:
                # 这种错误通常发生在窗口已经被 C++ 销毁但 Python 还有引用的情况
                pass

        # 3. 创建新窗口
        cls._instance = cls(parent=maya_win)
        cls._instance.show()

        print(f"--- Standard Window Launched: {cls._instance} ---")

def show_ui():
    """
    这是 start_dev.py 寻找的入口函数。
    它负责调用 MainWindow 类里面的 show_ui 方法。
    """
    MainWindow.show_ui()