try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

from ...core import rename_logic

class RenamerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        # 主布局
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.tabs = QtWidgets.QTabWidget()
        self.tab_replace = self._create_replace_tab()
        self.tab_renumber = self._create_renumber_tab()
        self.tab_modify = self._create_modify_tab()

        self.tabs.addTab(self.tab_replace, "Search && Replace")
        self.tabs.addTab(self.tab_renumber, "Renumber")
        self.tabs.addTab(self.tab_modify, "Prefix / Suffix")

        self.main_layout.addWidget(self.tabs)
        self.main_layout.addStretch()

    def _create_replace_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # A. 输入区
        form = QtWidgets.QFormLayout()
        self.input_search = QtWidgets.QLineEdit()
        self.input_search.setPlaceholderText("Find what... (e.g. _L)")

        self.input_replace = QtWidgets.QLineEdit()
        self.input_replace.setPlaceholderText("Replace with... (e.g. _R)")

        form.addRow("Search:", self.input_search)
        form.addRow("Replace:", self.input_replace)

        # B. 模式选择 (核心功能：防止误伤)
        grp_mode = QtWidgets.QGroupBox("Search Mode")
        layout_mode = QtWidgets.QHBoxLayout(grp_mode)

        self.radio_all = QtWidgets.QRadioButton("Anywhere")
        self.radio_start = QtWidgets.QRadioButton("Start Only")
        self.radio_end = QtWidgets.QRadioButton("End Only")

        self.radio_all.setChecked(True)  # 默认选中

        # 给这些按钮加点 Tooltip (鼠标悬停提示)，方便实习生理解
        self.radio_all.setToolTip("Example: 'arm' -> 'leg' (arm_armor -> leg_legor)")
        self.radio_start.setToolTip("Only replace if it starts with the text.")
        self.radio_end.setToolTip("Only replace if it ends with the text (Safest for sides).")

        layout_mode.addWidget(self.radio_all)
        layout_mode.addWidget(self.radio_start)
        layout_mode.addWidget(self.radio_end)

        # C. 选中范围
        self.chk_hierarchy = QtWidgets.QCheckBox("Include Hierarchy")
        self.chk_hierarchy.setToolTip("If checked, renames children of selected objects too.")

        # D. 执行按钮
        self.btn_apply_replace = QtWidgets.QPushButton("Replace Selected")
        self.btn_apply_replace.setMinimumHeight(40)

        layout.addLayout(form)
        layout.addWidget(grp_mode)
        layout.addWidget(self.chk_hierarchy)
        layout.addSpacing(10)
        layout.addWidget(self.btn_apply_replace)
        layout.addStretch()

        return widget

    def _create_renumber_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        form = QtWidgets.QFormLayout()

        self.input_base_name = QtWidgets.QLineEdit()
        self.input_base_name.setPlaceholderText("e.g. Spine_#_Jnt")
        self.input_base_name.setToolTip("Use # to indicate where numbers go.")

        self.spin_start = QtWidgets.QSpinBox()
        self.spin_start.setValue(1)
        self.spin_start.setRange(0, 9999)

        self.spin_padding = QtWidgets.QSpinBox()
        self.spin_padding.setValue(2)  # 默认 01, 02
        self.spin_padding.setSuffix(" digits")

        form.addRow("Format:", self.input_base_name)
        form.addRow("Start #:", self.spin_start)
        form.addRow("Padding:", self.spin_padding) #补零 eg. spine_01

        self.chk_renumber_hi = QtWidgets.QCheckBox("Include Hierarchy")
        self.chk_renumber_hi.setToolTip("Renumber children objects as well.")

        self.btn_apply_number = QtWidgets.QPushButton("Rename Sequence")
        self.btn_apply_number.setMinimumHeight(40)

        layout.addLayout(form)
        layout.addSpacing(10)
        layout.addWidget(self.chk_renumber_hi)
        layout.addWidget(self.btn_apply_number)
        layout.addStretch()

        return widget

    def _create_modify_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Prefix
        grp_pre = QtWidgets.QGroupBox("Add Prefix")
        l_pre = QtWidgets.QHBoxLayout(grp_pre)
        self.input_prefix = QtWidgets.QLineEdit()
        self.input_prefix.setPlaceholderText("e.g. SM_")
        self.btn_add_prefix = QtWidgets.QPushButton("Add")
        l_pre.addWidget(self.input_prefix)
        l_pre.addWidget(self.btn_add_prefix)

        # Suffix
        grp_suf = QtWidgets.QGroupBox("Add Suffix")
        l_suf = QtWidgets.QHBoxLayout(grp_suf)
        self.input_suffix = QtWidgets.QLineEdit()
        self.input_suffix.setPlaceholderText("e.g. _GEO")
        self.btn_add_suffix = QtWidgets.QPushButton("Add")
        l_suf.addWidget(self.input_suffix)
        l_suf.addWidget(self.btn_add_suffix)

        self.chk_modify_hi = QtWidgets.QCheckBox("Include Hierarchy")

        layout.addWidget(grp_pre)
        layout.addWidget(grp_suf)
        layout.addWidget(self.chk_modify_hi)
        layout.addStretch()

        return widget

    def _connect_signals(self):
        # 1. Replace Tab
        self.btn_apply_replace.clicked.connect(self.on_replace_clicked)

        # 2. Renumber Tab
        self.btn_apply_number.clicked.connect(self.on_renumber_clicked)

        # 3. Modify Tab (Prefix/Suffix)
        self.btn_add_prefix.clicked.connect(self.on_prefix_suffix_clicked)
        self.btn_add_suffix.clicked.connect(self.on_prefix_suffix_clicked)

    # --- Slots ---

    def on_replace_clicked(self):
        search = self.input_search.text()
        replace = self.input_replace.text()
        # 获取模式索引 (0, 1, 2)
        # 这里用个小技巧：检查哪个 radio 被选中
        mode = 0
        if self.radio_start.isChecked(): mode = 1
        if self.radio_end.isChecked(): mode = 2
        include_hi = self.chk_hierarchy.isChecked()
        rename_logic.batch_replace(search, replace, mode, include_hi)

    def on_renumber_clicked(self):
        base = self.input_base_name.text()
        start = self.spin_start.value()
        pad = self.spin_padding.value()

        include_hi = self.chk_renumber_hi.isChecked()

        # 简单的校验：如果用户没填名字，就不跑
        if not base:
            print("Please enter a base name format (e.g. Item_#)")
            return
        rename_logic.batch_renumber(base, start, pad, include_hierarchy=include_hi)

    def on_prefix_suffix_clicked(self):
        # 这里比较简单，直接读两个框
        # 如果是点 "Add Prefix" 按钮，就只加前缀吗？
        # 为了简单，我们可以让两个按钮都触发同一个逻辑，读两个框的值
        # 或者你可以区分对待。这里演示读所有值：
        pre = self.input_prefix.text()
        suf = self.input_suffix.text()
        include_hi = self.chk_modify_hi.isChecked()
        rename_logic.batch_prefix_suffix(pre, suf, include_hierarchy=include_hi)