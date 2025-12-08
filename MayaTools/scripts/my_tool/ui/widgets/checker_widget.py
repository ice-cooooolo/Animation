try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

import maya.cmds as cmds
from ...core import checker_logic  # 导入逻辑层

class CheckerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(8)

        # --- A. 顶部：模式选择与运行 ---
        top_layout = QtWidgets.QHBoxLayout()

        self.combo_mode = QtWidgets.QComboBox()
        self.combo_mode.addItems(["Model", "Rig", "Animation"])  # 对应 config 里的 Key
        self.combo_mode.setMinimumWidth(100)

        self.btn_run = QtWidgets.QPushButton("Run Sanity Check")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #555; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #666; }
            QPushButton:pressed { background-color: #444; }
        """)

        top_layout.addWidget(QtWidgets.QLabel("Mode:"))
        top_layout.addWidget(self.combo_mode)
        top_layout.addWidget(self.btn_run)

        # --- B. 核心展示区 ---
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Check Item", "Status", "Message"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 80)
        self.tree.setAlternatingRowColors(True)

        # --- C. 底部功能区 ---
        bot_layout = QtWidgets.QHBoxLayout()
        self.btn_select_fail = QtWidgets.QPushButton("Select Failed Objects")
        # 这是一个动态按钮：如果你选中的检查项可以修，它就亮起来
        self.btn_fix = QtWidgets.QPushButton("Fix Selected Item")
        self.btn_fix.setEnabled(False)  # 默认禁用
        self.btn_export = QtWidgets.QPushButton("📄 Export JSON")

        bot_layout.addWidget(self.btn_select_fail)
        bot_layout.addWidget(self.btn_fix)
        bot_layout.addWidget(self.btn_export)

        # --- 组装 ---
        self.main_layout.addLayout(top_layout)
        self.main_layout.addWidget(self.tree)
        self.main_layout.addLayout(bot_layout)

    def _connect_signals(self):
        self.btn_run.clicked.connect(self.run_checks)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemClicked.connect(self.on_item_clicked)  # 单击用于更新“修复按钮”状态
        self.btn_select_fail.clicked.connect(self.select_all_failed_in_ui)
        self.btn_fix.clicked.connect(self.fix_selected_item)
        self.btn_export.clicked.connect(self.export_report)

    # ----------------------------------------------------------------
    # 核心逻辑：运行检查并填充 UI
    # ----------------------------------------------------------------
    def run_checks(self):
        self.tree.clear()

        # 1. 获取当前模式
        mode = self.combo_mode.currentText()

        # 2. 从 Core 获取检查项实例列表
        # 这里实际上去调用了 checker_logic -> config -> 实例化
        checks = checker_logic.get_checks(mode)

        print(f"UI: Running {len(checks)} checks for {mode}...")

        # 3. 遍历运行并生成 UI
        for item in checks:
            # --- 运行核心检查代码 ---
            item.check()

            # --- 创建父节点 ---
            root = QtWidgets.QTreeWidgetItem(self.tree)
            root.setText(0, item.label)
            root.setText(1, item.status)
            root.setText(2, item.info_message)

            # 【黑科技】把整个 item 对象存入 UI 控件中
            # UserRole 是 Qt 预留给我们存私货的地方
            root.setData(0, QtCore.Qt.UserRole, item)

            # --- 设置样式 ---
            if item.status == "Passed":
                root.setForeground(1, QtGui.QBrush(QtGui.QColor("#66FF66")))  # 绿字
                root.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
            elif item.status == "Failed":
                root.setForeground(1, QtGui.QBrush(QtGui.QColor("#FF5555")))  # 红字
                root.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical))

                # --- 如果失败，添加子节点显示具体物体 ---
                if item.failed_objects:
                    for obj in item.failed_objects:
                        child = QtWidgets.QTreeWidgetItem(root)
                        child.setText(0, obj)
                        # 把具体的物体名字也存起来
                        child.setData(0, QtCore.Qt.UserRole, obj)

                        # 展开所有项方便查看
        self.tree.expandAll()

    # ----------------------------------------------------------------
    # 交互逻辑
    # ----------------------------------------------------------------
    def on_item_double_clicked(self, item, col):
        """双击逻辑：如果是物体则选中，如果是检查项则无视"""
        data = item.data(0, QtCore.Qt.UserRole)

        # 如果存的是字符串，说明是具体的物体
        if isinstance(data, str):
            if cmds.objExists(data):
                cmds.select(data)
                print(f"Selected: {data}")
            else:
                print(f"Object not found: {data}")

        # 如果存的是 CheckItem 对象，说明点了父节点，这里不做操作
        # (或者你可以设计成双击父节点就是一键修复)

    def on_item_clicked(self, item, col):
        """单击逻辑：判断修复按钮是否可用"""
        data = item.data(0, QtCore.Qt.UserRole)

        # 检查 data 是否是 CheckItem 实例，并且是否支持 fix
        # hasattr 检查是为了防止拿到的是字符串(子节点)
        if hasattr(data, "is_fixable") and data.is_fixable and data.status == "Failed":
            self.btn_fix.setEnabled(True)
            self.btn_fix.setText(f"Fix: {data.label}")
        else:
            self.btn_fix.setEnabled(False)
            self.btn_fix.setText("Fix Selected Item")

    def fix_selected_item(self):
        """点击修复按钮"""
        item = self.tree.currentItem()
        if not item: return

        # 取出藏好的对象 checkItem
        check_obj = item.data(0, QtCore.Qt.UserRole)

        if hasattr(check_obj, "fix"):
            print(f"UI: Fixing {check_obj.label}...")
            # 1. 调用 Core 的修复
            check_obj.fix()

            # 2. 修复完后，Core 会自动 re-check
            # 我们只需要更新 UI 这一行的文字和颜色即可
            item.setText(1, check_obj.status)
            item.setText(2, check_obj.info_message)

            # 简单粗暴的方法：修复完直接变成绿色
            if check_obj.status == "Passed":
                item.setForeground(1, QtGui.QBrush(QtGui.QColor("#66FF66")))
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
                # 删除所有子节点 (错误列表)
                item.takeChildren()

    def select_all_failed_in_ui(self):
        """把 Tree 里所有展开的、红色的子节点对应的物体都选中"""
        all_failed_objs = []

        # 遍历根节点
        iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, QtCore.Qt.UserRole)

            # 如果是字符串 (代表是子物体)
            if isinstance(data, str) and cmds.objExists(data):
                all_failed_objs.append(data)

            iterator += 1

        if all_failed_objs:
            cmds.select(all_failed_objs)
            print(f"Selected {len(all_failed_objs)} failed objects.")



    def export_report(self):
        import json
        import os
        """将当前检查结果导出为 JSON 文件"""
        report_data = {}

        # 1. 遍历 TreeWidget 收集数据
        iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            check_obj = item.data(0, QtCore.Qt.UserRole)

            # 只要是 CheckItem 对象 (排除子节点物体)
            if hasattr(check_obj, "label"):
                report_data[check_obj.label] = {
                    "status": check_obj.status,
                    "message": check_obj.info_message,
                    "failed_count": len(check_obj.failed_objects)
                }
            iterator += 1

        # 2. 保存文件 (保存到当前用户的桌面)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop, "Asset_Check_Report.json")

        with open(file_path, "w") as f:
            json.dump(report_data, f, indent=4)

        print(f"Report saved to: {file_path}")
        # 弹个窗告诉用户
        QtWidgets.QMessageBox.information(self, "Export Success", f"Report saved to:\n{file_path}")