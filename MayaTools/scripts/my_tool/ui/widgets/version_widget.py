try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

import os
from ...core import version_manager  # 导入我们刚写好的后端


class VersionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 实例化后端逻辑
        self.manager = version_manager.VersionManager()

        self._init_ui()
        self._connect_signals()

        # 初始化时刷新一次列表
        self.refresh_list()

    def _init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- A. 顶部信息栏 ---
        info_layout = QtWidgets.QHBoxLayout()
        self.lbl_project = QtWidgets.QLabel("Asset: Unknown")
        self.lbl_project.setStyleSheet("font-size: 14px; font-weight: bold; color: #EEE;")

        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.setFixedWidth(80)

        info_layout.addWidget(self.lbl_project)
        info_layout.addStretch()
        info_layout.addWidget(self.btn_refresh)

        # --- B. 中间核心区 (左右分栏) ---
        # 使用 QSplitter 让用户可以拖拽调整左右宽度
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # --- B1. 左侧：版本列表 ---
        self.list_widget = QtWidgets.QListWidget()
        # 开启交替行颜色
        self.list_widget.setAlternatingRowColors(True)
        # 允许右键菜单
        self.list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # --- B2. 右侧：详情面板 ---
        self.details_panel = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(10, 0, 0, 0)

        # 1. 缩略图区域 (固定大小 320x240 保持比例)
        self.lbl_thumbnail = QtWidgets.QLabel()
        self.lbl_thumbnail.setFixedSize(320, 240)
        self.lbl_thumbnail.setStyleSheet("background-color: #222; border: 1px solid #444;")
        self.lbl_thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_thumbnail.setText("No Preview")

        # 2. 版本详细信息
        self.lbl_version_info = QtWidgets.QLabel("Select a version...")
        self.lbl_version_info.setWordWrap(True)
        self.lbl_version_info.setStyleSheet("color: #AAA; line-height: 1.5;")

        # 3. Publish 标记
        self.chk_publish = QtWidgets.QCheckBox("Is Published (Release)")
        self.chk_publish.setEnabled(False)  # 只有选中列表时才启用

        # 4. 打开按钮
        self.btn_open = QtWidgets.QPushButton("Open This Version")
        self.btn_open.setMinimumHeight(40)
        self.btn_open.setEnabled(False)
        self.btn_open.setStyleSheet("background-color: #444;")

        details_layout.addWidget(self.lbl_thumbnail)
        details_layout.addWidget(self.lbl_version_info)
        details_layout.addWidget(self.chk_publish)
        details_layout.addStretch()  # 顶上去
        details_layout.addWidget(self.btn_open)

        # 将左右加入 Splitter
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(self.details_panel)
        # 设置初始比例 (左 4 : 右 6)
        self.splitter.setSizes([300, 400])

        # --- C. 底部：存新版本区域 ---
        save_group = QtWidgets.QGroupBox("Save New Version")
        save_layout = QtWidgets.QVBoxLayout(save_group)

        # 备注输入框
        self.input_comment = QtWidgets.QTextEdit()
        self.input_comment.setPlaceholderText("Enter comment here (e.g. Fixed knee popping)...")
        self.input_comment.setMaximumHeight(60)

        # 截图选项
        self.chk_make_thumb = QtWidgets.QCheckBox("Capture Thumbnail (Playblast)")
        self.chk_make_thumb.setChecked(True)

        # 保存按钮
        self.btn_save = QtWidgets.QPushButton("Save New Version")
        self.btn_save.setMinimumHeight(45)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #2A82DA; color: white; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #3A92EA; }
        """)

        save_layout.addWidget(self.input_comment)
        save_layout.addWidget(self.chk_make_thumb)
        save_layout.addWidget(self.btn_save)

        # --- 组装总布局 ---
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(save_group)

    def _connect_signals(self):
        # 按钮事件
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_refresh.clicked.connect(self.refresh_list)
        self.btn_open.clicked.connect(self.on_open_clicked)

        # 列表交互
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 标记交互
        self.chk_publish.clicked.connect(self.on_publish_toggled)

    # -----------------------------------------------------------
    # 逻辑实现 (先写个框架)
    # -----------------------------------------------------------

    def refresh_list(self):
        """调用 Core 读取数据并刷新列表"""
        self.list_widget.clear()
        self.manager.refresh_context()  # 确保路径是对的

        # 1. 更新顶部资产名
        asset_name = self.manager.data.get("asset_name", "Unknown Asset")
        self.lbl_project.setText(f"Asset: {asset_name}")

        # 2. 遍历版本
        # data["versions"] 是个字典，我们需要按版本号排序 (v001, v002...)
        versions_dict = self.manager.data.get("versions", {})
        # 排序：按 Key 排序 (默认就是 v001, v002 字母序)
        sorted_keys = sorted(versions_dict.keys(), reverse=True)  # 倒序，最新的在上面

        for v_code in sorted_keys:
            info = versions_dict[v_code]

            # 创建列表项
            # 显示格式： v003 | Polito | Fix knee...
            display_text = f"{v_code} | {info.get('author')} | {info.get('comment')}"
            item = QtWidgets.QListWidgetItem(display_text)

            # 发布标记
            if info.get("is_published"):
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))  # 打个勾
                item.setForeground(QtGui.QBrush(QtGui.QColor("#44FF44")))  # 变绿

            # 数据绑定：把整条 info 字典存进去，方便后面取图片路径
            item.setData(QtCore.Qt.UserRole, info)

            self.list_widget.addItem(item)

    def on_save_clicked(self):
        comment = self.input_comment.toPlainText()
        make_thumb = self.chk_make_thumb.isChecked()

        # 调用 Core
        result = self.manager.create_version(comment, make_thumbnail=make_thumb)

        if result:
            self.input_comment.clear()
            self.refresh_list()  # 刷新列表显示新版本

    def on_item_clicked(self, item):
        """单击：显示详情和图片"""
        info = item.data(QtCore.Qt.UserRole)

        # 1. 更新文字
        details_text = (
            f"<b>Version:</b> {info['version']}<br>"
            f"<b>User:</b> {info['author']}<br>"
            f"<b>Date:</b> {info['time']}<br>"
            f"<b>File:</b> {info['filename']}<br><br>"
            f"<b>Comment:</b><br>{info['comment']}"
        )
        self.lbl_version_info.setText(details_text)

        # 2. 更新 Publish 勾选框
        self.chk_publish.setEnabled(True)
        # 必须先 block signals，否则 setChecked 会触发 toggled 信号导致死循环逻辑
        self.chk_publish.blockSignals(True)
        self.chk_publish.setChecked(info.get("is_published", False))
        self.chk_publish.blockSignals(False)

        # 3. 启用打开按钮
        self.btn_open.setEnabled(True)

        # 4. 【核心】显示图片
        thumb_rel_path = info.get("thumbnail")
        if thumb_rel_path:
            # 拼出绝对路径
            full_thumb_path = os.path.join(self.manager.workspace_path, thumb_rel_path)

            if os.path.exists(full_thumb_path):
                pixmap = QtGui.QPixmap(full_thumb_path)
                # 缩放以适应标签 (KeepAspectRatio)
                scaled_pix = pixmap.scaled(self.lbl_thumbnail.size(), QtCore.Qt.KeepAspectRatio,
                                           QtCore.Qt.SmoothTransformation)
                self.lbl_thumbnail.setPixmap(scaled_pix)
            else:
                self.lbl_thumbnail.setText("Image Missing")
        else:
            self.lbl_thumbnail.setText("No Preview")

    def on_open_clicked(self):
        # 获取当前选中的
        item = self.list_widget.currentItem()
        if not item: return

        info = item.data(QtCore.Qt.UserRole)
        v_code = info['version']

        self.manager.open_version_file(v_code)

        # 打开后刷新一下，因为可能换了文件
        self.refresh_list()

    def on_item_double_clicked(self, item):
        """双击直接打开"""
        self.on_open_clicked()

    def on_publish_toggled(self):
        """修改发布状态"""
        item = self.list_widget.currentItem()
        if not item: return

        info = item.data(QtCore.Qt.UserRole)
        new_state = self.chk_publish.isChecked()

        # 修改内存数据
        v_code = info['version']
        self.manager.data['versions'][v_code]['is_published'] = new_state

        # 保存到磁盘
        self.manager.save_data()

        # 刷新列表 UI (更新图标颜色)
        self.refresh_list()