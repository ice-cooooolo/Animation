try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

import os
import glob
from ...core import version_manager
from ...core.exporters import model_exporter, anim_exporter


class ExporterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 实例化版本管理器 (用于 Pipeline 模式)
        self.vm = version_manager.VersionManager()

        self._init_ui()
        self._connect_signals()

        # 默认刷新一次 Pipeline 列表
        self.refresh_pipeline_list()

    def _init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # --- A. 顶部：模式选择 (Tabs) ---
        self.tabs = QtWidgets.QTabWidget()

        # Tab 1: Pipeline Mode (自动流)
        self.tab_pipeline = QtWidgets.QWidget()
        layout_pipe = QtWidgets.QVBoxLayout(self.tab_pipeline)
        self.list_pipeline = QtWidgets.QListWidget()
        self.list_pipeline.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # 允许多选
        self.btn_refresh_pipe = QtWidgets.QPushButton("Refresh Published Versions")
        layout_pipe.addWidget(self.list_pipeline)
        layout_pipe.addWidget(self.btn_refresh_pipe)

        # Tab 2: File Mode (手动流)
        self.tab_files = QtWidgets.QWidget()
        layout_files = QtWidgets.QVBoxLayout(self.tab_files)

        # 文件夹选择器
        dir_layout = QtWidgets.QHBoxLayout()
        self.input_folder = QtWidgets.QLineEdit()
        self.input_folder.setPlaceholderText("Paste folder path here...")
        self.btn_browse = QtWidgets.QPushButton("Browse...")
        dir_layout.addWidget(self.input_folder)
        dir_layout.addWidget(self.btn_browse)

        self.list_files = QtWidgets.QListWidget()
        self.list_files.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        layout_files.addLayout(dir_layout)
        layout_files.addWidget(self.list_files)

        self.tabs.addTab(self.tab_pipeline, "Pipeline Mode (Published)")
        self.tabs.addTab(self.tab_files, "File Batch Mode")

        # --- B. 中部：导出设置 ---
        grp_settings = QtWidgets.QGroupBox("Export Settings")
        layout_settings = QtWidgets.QGridLayout(grp_settings)

        self.combo_type = QtWidgets.QComboBox()
        self.combo_type.addItems(["Model", "Animation"])

        self.input_output = QtWidgets.QLineEdit()
        self.input_output.setPlaceholderText("Leave empty to use default '_exports' folder")
        self.btn_browse_out = QtWidgets.QPushButton("Set Output...")

        layout_settings.addWidget(QtWidgets.QLabel("Export Type:"), 0, 0)
        layout_settings.addWidget(self.combo_type, 0, 1)
        layout_settings.addWidget(QtWidgets.QLabel("Output Dir:"), 1, 0)
        layout_settings.addWidget(self.input_output, 1, 1)
        layout_settings.addWidget(self.btn_browse_out, 1, 2)

        # --- C. 底部：执行与日志 ---
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.text_log = QtWidgets.QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumHeight(150)
        self.text_log.setStyleSheet("background-color: #222; color: #AAA; font-family: Consolas;")

        self.btn_export = QtWidgets.QPushButton("🚀 BATCH EXPORT")
        self.btn_export.setMinimumHeight(50)
        self.btn_export.setStyleSheet("background-color: #D35400; color: white; font-weight: bold; font-size: 14px;")

        # --- 组装 ---
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(grp_settings)
        main_layout.addWidget(self.btn_export)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.text_log)

    def _connect_signals(self):
        self.btn_refresh_pipe.clicked.connect(self.refresh_pipeline_list)
        self.btn_browse.clicked.connect(self.browse_source_folder)
        self.btn_browse_out.clicked.connect(self.browse_output_folder)
        self.btn_export.clicked.connect(self.run_batch_export)
        self.input_folder.textChanged.connect(self.refresh_file_list)  # 路径变了自动刷新列表

    # ----------------------------------------------------------------
    # 逻辑部分
    # ----------------------------------------------------------------

    def log(self, msg):
        """往 UI 日志框里写字，并强制刷新界面"""
        self.text_log.append(msg)
        # 强制滚动到底部
        cursor = self.text_log.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.text_log.setTextCursor(cursor)
        # 【关键】让 UI 立即重绘，否则循环时界面是死的
        QtWidgets.QApplication.processEvents()

    def refresh_pipeline_list(self):
        """Tab 1: 读取 meta.json 里的 Published 版本"""
        self.list_pipeline.clear()
        self.vm.refresh_context()  # 刷新后端路径

        versions = self.vm.data.get("versions", {})
        count = 0

        # 倒序遍历
        for v_code in sorted(versions.keys(), reverse=True):
            info = versions[v_code]

            # 【关键】只显示 is_published = True 的
            if info.get("is_published"):
                # 构造完整路径
                rel_path = info.get("path")
                full_path = os.path.join(self.vm.workspace_path, rel_path).replace("\\", "/")

                # 列表显示
                item = QtWidgets.QListWidgetItem(f"{v_code} | {info.get('comment')} ({info.get('author')})")
                item.setToolTip(full_path)
                item.setData(QtCore.Qt.UserRole, full_path)  # 存路径
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))

                self.list_pipeline.addItem(item)
                count += 1

        self.log(f"Pipeline: Found {count} published versions.")

    def browse_source_folder(self):
        """Tab 2: 选择源文件夹"""
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder with .ma files")
        if path:
            self.input_folder.setText(path)
            # textChanged 信号会自动触发 refresh_file_list

    def refresh_file_list(self):
        """Tab 2: 扫描文件夹里的 Maya 文件"""
        self.list_files.clear()
        folder = self.input_folder.text()
        if not folder or not os.path.exists(folder):
            return

        # 查找 .ma 和 .mb
        files = glob.glob(os.path.join(folder, "*.m*"))

        for f in files:
            f = f.replace("\\", "/")
            name = os.path.basename(f)
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, f)  # 存全路径
            self.list_files.addItem(item)

        self.log(f"File Mode: Found {len(files)} files.")

    def browse_output_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.input_output.setText(path)

    # ----------------------------------------------------------------
    # 【核心】批量导出逻辑
    # ----------------------------------------------------------------
    def run_batch_export(self):
        # 1. 收集要导出的文件
        tasks = []

        # 判断当前在哪个 Tab
        if self.tabs.currentIndex() == 0:  # Pipeline Mode
            # 获取所有被选中的 (如果没选，默认导全部？大厂通常只导选中的，防止误操作)
            # 这里我们逻辑：如果有选中，导选中的；如果没选中，导全部列表里的。
            selected_items = self.list_pipeline.selectedItems()
            if not selected_items:
                # 没选就全导
                for i in range(self.list_pipeline.count()):
                    tasks.append(self.list_pipeline.item(i).data(QtCore.Qt.UserRole))
            else:
                for item in selected_items:
                    tasks.append(item.data(QtCore.Qt.UserRole))
        else:  # File Mode
            selected_items = self.list_files.selectedItems()
            if not selected_items:
                for i in range(self.list_files.count()):
                    tasks.append(self.list_files.item(i).data(QtCore.Qt.UserRole))
            else:
                for item in selected_items:
                    tasks.append(item.data(QtCore.Qt.UserRole))

        if not tasks:
            self.log("No files to export!")
            return

        # 2. 准备导出器
        export_type = self.combo_type.currentText()
        if export_type == "Model":
            worker = model_exporter.ModelExporter()
        else:
            worker = anim_exporter.AnimExporter()

        # 3. 准备输出路径
        out_dir = self.input_output.text()
        if not out_dir:
            # 默认路径：在第一个文件的同级建立 _exports 文件夹
            # 或者使用 Pipeline 的 workspace/_exports
            first_file_dir = os.path.dirname(tasks[0])
            out_dir = os.path.join(first_file_dir, "_exports")

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # 4. 开始循环 (Batch Loop)
        self.text_log.clear()
        self.log(f"=== Starting Batch Export ({len(tasks)} files) ===")
        self.log(f"Mode: {export_type}")
        self.log(f"Output: {out_dir}")

        self.progress_bar.setRange(0, len(tasks))
        self.progress_bar.setValue(0)

        success_count = 0

        for i, file_path in enumerate(tasks):
            file_name = os.path.basename(file_path)
            self.log(f"\n[{i + 1}/{len(tasks)}] Processing: {file_name}...")

            # --- 核心调用 ---
            # run() 方法里包含了 Open -> Check -> Fix -> Bake -> Export
            result = worker.run(file_path, out_dir)

            # --- 收集后端日志 ---
            # 把 worker 里的 log 搬运到 UI 上
            for msg in worker.log:
                self.text_log.append(f"  | {msg}")

            if result:
                self.log(f"  ✅ Success!")
                success_count += 1
            else:
                self.log(f"  ❌ Failed!")

            # 更新进度
            self.progress_bar.setValue(i + 1)

            # 【防卡死关键】
            QtWidgets.QApplication.processEvents()

        self.log(f"\n=== Batch Complete. Success: {success_count}/{len(tasks)} ===")
        QtWidgets.QMessageBox.information(self, "Done", f"Exported {success_count} files.\nCheck logs for details.")