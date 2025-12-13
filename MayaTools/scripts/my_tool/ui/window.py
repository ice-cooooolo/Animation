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

        # 导航按钮
        # self.btn_home = QtWidgets.QPushButton("主页 / Home")
        self.btn_rig = QtWidgets.QPushButton("绑定 / Rig")
        self.btn_check = QtWidgets.QPushButton("检查 / Check")
        self.btn_rename = QtWidgets.QPushButton("重命名 / Rename")
        self.btn_version = QtWidgets.QPushButton("版本控制 / Version")
        self.btn_export = QtWidgets.QPushButton("导出 / Export")

        # 按钮样式优化 (高度设大一点)
        for btn in [ self.btn_rig, self.btn_check, self.btn_rename, self.btn_version, self.btn_export]:
            btn.setMinimumHeight(30)
            menu_layout.addWidget(btn)

        # === B. 右侧：内容堆叠区 ===
        self.stack = QtWidgets.QStackedWidget()

        # 1. 实例化子页面
        # self.page_home = home_widget.HomeWidget()
        # (以后这里可以加 self.page_rig, self.page_check 等)
        self.page_rig_placeholder = controller_box_widget.ControlBoxWidget()
        self.page_check_placeholder = checker_widget.CheckerWidget()
        self.page_rename_placeholder = renamer_widget.RenamerWidget()
        self.page_version_placeholder = version_widget.VersionWidget()
        self.page_exporter_placeholder = exporter_widget.ExporterWidget()

        # 2. 加入堆叠
        # self.stack.addWidget(self.page_home)  # Index 0
        self.stack.addWidget(self.page_rig_placeholder)  # Index 1
        self.stack.addWidget(self.page_check_placeholder)  # Index 2
        self.stack.addWidget(self.page_rename_placeholder)
        self.stack.addWidget(self.page_version_placeholder)
        self.stack.addWidget(self.page_exporter_placeholder)

        # === C. 组装 ===
        main_layout.addWidget(self.side_menu)
        main_layout.addWidget(self.stack)

        # === D. 信号连接 ===
        # self.btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_rig.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_check.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_rename.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_version.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.btn_export.clicked.connect(lambda: self.stack.setCurrentIndex(4))

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