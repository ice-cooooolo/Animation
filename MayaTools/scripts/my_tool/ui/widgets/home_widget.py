import random

# --- 1. 完美的兼容性导入 (核心修复) ---
# 不要单独在最上面 import shiboken6，要放在 try 块里
try:
    # Maya 2022/2023 (Python 3.7/3.9)
    from PySide2 import QtCore, QtWidgets, QtGui
    import shiboken2 as shiboken
except ImportError:
    # Maya 2024/2025 (Python 3.10+)
    from PySide6 import QtCore, QtWidgets, QtGui
    import shiboken6 as shiboken

class HomeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        # UI 元素
        self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)
        self.button = QtWidgets.QPushButton("Click me!")
        self.button1 = QtWidgets.QPushButton("Test Button")

        # 布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.button1)
        self.layout.addStretch()  # 把内容顶上去，好看一点

        # 信号
        self.button.clicked.connect(self.magic)

    def magic(self):
        self.text.setText(random.choice(self.hello))