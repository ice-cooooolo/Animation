try:
    # Maya 2022/2023 (Python 3.7/3.9)
    from PySide2 import QtCore, QtWidgets, QtGui
    import shiboken2 as shiboken
except ImportError:
    # Maya 2024/2025 (Python 3.10+)
    from PySide6 import QtCore, QtWidgets, QtGui
    import shiboken6 as shiboken

from ...core import controller_logic

class ControlBoxWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # --- 1. 数据状态缓存 ---
        # 我们用这个变量记录当前选中的颜色
        # 默认是黄色(17)，类型是索引(index)
        self.current_color_data = {"type": "index", "value": 17}
        self.current_target = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        #主布局
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # --- Section A: Target ---
        self.grp_target = QtWidgets.QGroupBox("Target Selection")
        layout_target = QtWidgets.QHBoxLayout(self.grp_target)

        self.lbl_target = QtWidgets.QLabel("Selected: Nothing Selected")
        self.lbl_target.setStyleSheet("color: gray; font-style: italic;")
        self.btn_load = QtWidgets.QPushButton("Load Selection")

        layout_target.addWidget(self.lbl_target)
        layout_target.addWidget(self.btn_load)

        # --- Section B: Settings ---
        self.grp_settings = QtWidgets.QGroupBox("Settings")
        layout_settings = QtWidgets.QFormLayout(self.grp_settings)

        self.input_name = QtWidgets.QLineEdit()
        self.input_name.setPlaceholderText("Auto-generated name")
        self.combo_shape = QtWidgets.QComboBox()
        self.combo_shape.addItems(["circle", "Square", "Cube"])
        self.spin_size = QtWidgets.QDoubleSpinBox()
        self.spin_size.setValue(1.0)
        self.spin_size.setRange(0.1, 100.0)

        layout_settings.addRow("Name", self.input_name)
        layout_settings.addRow("Shape", self.combo_shape)
        layout_settings.addRow("Size", self.spin_size)

        # --- Section C: Color ---
        self.grp_color = QtWidgets.QGroupBox("Color")
        layout_color = QtWidgets.QHBoxLayout(self.grp_color)
        self.btn_red = self._create_color_btn("#FF5555", 13)
        self.btn_blue = self._create_color_btn("#5555FF", 6)
        self.btn_yellow = self._create_color_btn("#FFFF55", 17)
        self.btn_custom_color = QtWidgets.QPushButton("Custom...")

        layout_color.addWidget(self.btn_red)
        layout_color.addWidget(self.btn_blue)
        layout_color.addWidget(self.btn_yellow)
        layout_color.addWidget(self.btn_custom_color)

        # --- Section D: Options ---
        self.grp_options = QtWidgets.QGroupBox("Options")
        layout_opts = QtWidgets.QVBoxLayout(self.grp_options)

        self.chk_match_pos = QtWidgets.QCheckBox("Match Position")
        self.chk_match_rot = QtWidgets.QCheckBox("Match Rotation")
        self.chk_offset = QtWidgets.QCheckBox("Create Offset Group")
        self.combo_constrain = QtWidgets.QComboBox()
        self.combo_constrain.addItems(["None", "Parent", "Point", "Orient"])
        self.chk_match_pos.setChecked(True)
        self.chk_match_rot.setChecked(True)
        self.chk_offset.setChecked(True)
        layout_opts.addWidget(self.chk_match_pos)
        layout_opts.addWidget(self.chk_match_rot)
        layout_opts.addWidget(self.chk_offset)
        layout_opts.addWidget(self.combo_constrain)

        # --- Section E: Action ---
        self.btn_create = QtWidgets.QPushButton("Create Controller")
        self.btn_create.setMinimumHeight(40)
        self.btn_create.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #444;")

        # --- add to main ---
        self.main_layout.addWidget(self.grp_target)
        self.main_layout.addWidget(self.grp_settings)
        self.main_layout.addWidget(self.grp_color)
        self.main_layout.addWidget(self.grp_options)
        self.main_layout.addWidget(self.btn_create)
        self.main_layout.addStretch() # 底部顶上去

    def _create_color_btn(self, css_color, maya_idx):
        """辅助函数：创建带颜色的按钮"""
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(30, 30)
        btn.setStyleSheet(f"background-color: {css_color}; border: 1px solid #000;")
        # 我们可以把 maya_idx 存到按钮的属性里，方便后面取用
        btn.setProperty("maya_color_index", maya_idx)
        return btn

    def _connect_signals(self):
        """连接所有信号与槽"""
        # 1. 加载选择
        self.btn_load.clicked.connect(self.on_load_selection)

        # 2. 预设颜色 (三个按钮连同一个函数)
        self.btn_red.clicked.connect(self.on_preset_color_clicked)
        self.btn_blue.clicked.connect(self.on_preset_color_clicked)
        self.btn_yellow.clicked.connect(self.on_preset_color_clicked)

        # 3. 自定义颜色
        self.btn_custom_color.clicked.connect(self.on_custom_color_clicked)

        # 4. 创建按钮
        self.btn_create.clicked.connect(self.on_create_clicked)

    def on_load_selection(self):
        sel_name = controller_logic.get_current_selection_name()
        if sel_name:
            self.current_target = sel_name
            self.lbl_target.setText(f"Selected: {sel_name}")
            self.lbl_target.setStyleSheet("color: #44FF44; font-weight: bold;")  # 变绿

            base_name = sel_name.split("|")[-1]
            self.input_name.setText(f"CTRL_{base_name}")
        else:
            self.current_target = None
            self.lbl_target.setText("Nothing Selected (World Center)")
            self.lbl_target.setStyleSheet("color: gray; font-style: italic;")
            self.input_name.clear()

    def on_preset_color_clicked(self):
        """点击红黄蓝按钮时触发"""
        # 获取发送信号的按钮
        btn = self.sender()
        if btn:
            # 读取我们在 _create_color_btn 里藏进去的属性
            idx = btn.property("maya_color_index")
            print(f"UI: 用户选了预设颜色索引 {idx}")

            # 更新数据状态
            self.current_color_data = {"type": "index", "value": idx}

            # (可选) 给个视觉反馈，比如让按钮边框变白，这里先略过

    def on_custom_color_clicked(self):
        """点击 Custom 时触发"""
        # 弹出颜色选择框
        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():
            # 获取 RGB (0.0 - 1.0)
            r, g, b = color.redF(), color.greenF(), color.blueF()
            print(f"UI: 用户选了自定义颜色 {r},{g},{b}")

            # 更新数据状态
            self.current_color_data = {"type": "rgb", "value": (r, g, b)}

            # 更新按钮颜色展示用户选的色
            self.btn_custom_color.setStyleSheet(f"background-color: {color.name()};")

    def on_create_clicked(self):
        """点击 Create 时触发 - 收集所有数据并发射"""
        # 1. 收集 UI 数据
        name_txt = self.input_name.text()
        shape_txt = self.combo_shape.currentText()
        size_val = self.spin_size.value()

        match_p = self.chk_match_pos.isChecked()
        match_r = self.chk_match_rot.isChecked()
        do_offset = self.chk_offset.isChecked()
        constrain_mode = self.combo_constrain.currentText()
        print("current constrain_mode : ", constrain_mode)
        # 2. 调用 Core 逻辑
        # 注意：我们把收集到的所有零散数据传给 Core
        result = controller_logic.create_controller(
            name=name_txt,
            shape=shape_txt,
            size=size_val,
            color_data=self.current_color_data,  # 传入刚才存的颜色字典
            match_pos=match_p,
            match_rot=match_r,
            use_offset=do_offset,
            constrain_mode=constrain_mode,
            target_node=self.current_target
        )

        # 3. 简单的反馈
        print(f"UI: Core 返回结果 -> {result}")