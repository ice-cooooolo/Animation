**基础模块划分：**

```
my_tool/                  <-- 【你的产品】
 ├── core/                <-- 【大脑】纯逻辑
 │    ├── rigger.py       <-- 干活的 (Maya Cmds/API)
 │    └── utils.py        <-- 各种装饰器 (@undoable)
 ├── ui/                  <-- 【脸面】纯界面
 │    ├── window.py       <-- 【骨架】容器、单例、侧边栏
 │    └── widgets/        <-- 【器官】具体的页面 (Home, Rig)
 ├── utils/               <-- 【辅助】纯工具
 │    ├── maya_utils      <-- 【辅助】撤回等工具
 └── start_dev.py         <-- 【起搏器】负责清洗环境、启动
```

**UI模块：**

window.py

作为其他所有UI的容器，负责装载其他UI

```
# my_tool/ui/window.py

def show_ui():
    """
    这是 start_dev.py 寻找的入口函数。
    它负责调用 MainWindow 类里面的 show_ui 方法。
    """
    MainWindow.show_ui()
```

这里会调用MainWindow的show_ui方法，因为show_ui是类方法 (`def func(cls)`)

```
        # 1. 获取 Maya 主窗口
        maya_win_ptr = omui.MQtUtil.mainWindow()
        maya_win = None
        if maya_win_ptr:
            maya_win = shiboken.wrapInstance(int(maya_win_ptr), QtWidgets.QWidget)
        
        # 2.如果有旧窗口就关闭
        for ... in QtWidgets.QApplication.topLevelWidgets():
        	if widget.objectName() == WINDOW_OBJECT_NAME:
        		widget.close()
        		
        # 3. 创建新窗口
        cls._instance = cls(parent=maya_win)
        cls._instance.show()
```

UI整体布局采用水平格式

```
MainWindow (self) 
│  [Layout: QHBoxLayout]  <-- 主布局 (水平：左侧+右侧)
│
├── 1. 左侧容器 (self.side_menu) [类型: QFrame]
│   │  [Layout: QVBoxLayout]  <-- 菜单布局 (垂直：上到下排按钮)
│   │
│   ├── self.btn_home   (QPushButton: "主页")
│   ├── self.btn_rig    (QPushButton: "绑定")
│   ├── self.btn_check  (QPushButton: "检查")
│   └── self.btn_rename (QPushButton: "重命名")
│
└── 2. 右侧容器 (self.stack) [类型: QStackedWidget]
    │  (没有 Layout，只有 Index 索引，一次只显示一层)
    │
    ├── Index 0: self.page_home   [类型: HomeWidget]
    ├── Index 1: self.page_rig    [类型: ControlBoxWidget]
    ├── Index 2: self.page_check  [类型: QLabel] (占位符)
    └── Index 3: self.page_rename [类型: RenamerWidget]
```

第一个装载的UI - ControlBoxWidget：
![image-20251130101206592](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251130101206592.png)

Target Selection:

```
sel = cmds.ls(selection=True)
return sel[0] if sel else None
```

```
create_controller核心逻辑
1.设置名字，如果传入名字就用name，否则严格按照f"CTRL_{short_name}"格式
2.根据shape创建不同形状的控制器再原点
3.获取传入的颜色并且上色
4.打组，为了让控制器不脏
5.根据Options看是否要对齐位置或者旋转
6.根据下拉框看是否创建约束，然后寻找父控制器节点进行父子连接
```

```
1.
		short_name = target_node.split("|")[-1]
        # 强制命名规范，以便后续查找父级
        expected_name = f"CTRL_{short_name}"
2.
        ctrl = cmds.circle(n=ctrl_name, nr=(1, 0, 0), r=size)[0]
3.
		cmds.setAttr(f"{shape}.overrideRGBColors", 0)
        cmds.setAttr(f"{shape}.overrideColor", int(color_data['value']))
# --- 4. 打组 ---
    node_to_move = ctrl
    # 强制 FK 系统必须有组，否则无法做层级
    # 哪怕用户没勾选，为了层级安全，建议还是得有个组，或者直接操作控制器
    # 这里我们假设用户为了做绑定，肯定勾选了 use_offset
    if use_offset:
        grp_name = f"GRP_{ctrl_name}"
        grp = cmds.group(ctrl, n=grp_name)
        node_to_move = grp
5.
            kwargs = {}
            if match_pos:
                kwargs['pos'] = True
            if match_rot:
                kwargs['rot'] = True

            if kwargs:  # 至少有一个参数才调用
                cmds.matchTransform(node_to_move, target_node, **kwargs)
6.
		cmds.parentConstraint(ctrl, target_node, mo=True)
		parent_jnt_list = cmds.listRelatives(target_node, parent=True)
		parent_jnt_short = parent_jnt.split("|")[-1]
        search_ctrl_name = f"CTRL_{parent_jnt_short}"
        cmds.parent(node_to_move, search_ctrl_name)
```

**Rename Widget**

![image-20251130144523200](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251130144523200.png)

```
首先导航栏self.tabs = QtWidgets.QTabWidget()组成

1.第一个页面由一个QFormLayout里面两个LineEdit
2.Search Mode是QGroupBox，单选QRadioButton，默认是Anywhere
3.self.chk_hierarchy = QtWidgets.QCheckBox("Include Hierarchy")这是勾选是否选择层级，将子级也全选
4.self.btn_apply_replace = QtWidgets.QPushButton("Replace Selected")连接core发送请求
```

```
core代码：
batch_replace(search_str, replace_str, mode, include_hierarchy = False)

1.根据include_hierarchy判断是获取一个还是层级所有的，然后字符串截取下得到名字
2.根据mode决定是只替换开头结尾或者全部替换
```

**Renumber - 让重复的骨骼可以快速命名**

![image-20251130145318950](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251130145318950.png)

```
1.form = QtWidgets.QFormLayout()表单是输入格式，#是要被替换的部分
2.两个QSpinBox分别是起始数字和补多少0
3.同样的Include Hierarchy
```

```
core：
def batch_renumber(base_name, start_num, padding, include_hierarchy = False):
1.获取节点集合（根据include_hierarchy）
2.因为直接修改名字可能会有重名，比如Spine_01 -> Spine_02, 可是Spine_02已经存在了，maya会把它改成Spine_021。所以我们引入中间名
    temp_names = []
    for obj in objects:
        try:
            temp_name = cmds.rename(obj, "TEMP_RENAME_Process_#")
            temp_names.append(temp_name)
        except Exception as e:
            print(f"Skipped {obj}: {e}")
    temp_names.reverse()
3.遍历集合，把名字替换：
        if "#" in base_name:
            final_name = base_name.replace("#", num_str)
        else:
            final_name = f"{base_name}_{num_str}"
```

**Add prefix, suffix**

![image-20251130150935405](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251130150935405.png)

```
这个ui和core都很简单，同样的获取line_edit，然后遍历集合，加在开头或者结尾
```



Checker.widget

![image-20251204203258123](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251204203258123.png)

```
ui中比较重要的代码就是
Run_check()时候，我们首先获取当前mode,然后从config里面得到需要检查的类，通过cls()实例化

# 【黑科技】把整个 item 对象存入 UI 控件中
# UserRole 是 Qt 预留给我们存私货的地方
root.setData(0, QtCore.Qt.UserRole, item)

之后不管单机还是选择节点，都可以通过QtCore.Qt.UserRole获取

双击：选取有问题的节点data = item.data(0, QtCore.Qt.UserRole) if isinstance(data, str):cmds.select(data)

单机：判断是否可以修复data = item.data(0, QtCore.Qt.UserRole) if hasattr(data, "is_fixable") and data.is_fixable and data.status == "Failed":

修复：item = self.tree.currentItem()， check_obj = item.data(0, QtCore.Qt.UserRole) 然后修复

选取所有有问题的节点： iterator = QtWidgets.QTreeWidgetItemIterator(self.tree) item = iterator.value()
```



```
core的代码：

config作为配置文件，checker_logic.py是获取当前模式所有要检查的类，展示了工厂模式和面向对象编程。有利于后续开发的扩展，无需更改ui层的代码，也没有繁琐的if代码，因为都是同个基类，直接调用check和fix函数即可

HistoryCheck: 
history = cmds.listHistory(obj, pruneDagObjects=True) # 排除本身， 查询对这个节点有影响的DAG - check
cmds.delete(self.failed_objects, constructionHistory=True) # fix方法核心

UnFrozenTransformCheck：
检查translate≈0， rotation≈0， scale ≈ 1 - check
cmds.makeIdentity(self.failed_objects, apply=True, translate=True, rotate=True, scale=True) - fix冻结变换

NgonsCheck：
cmds.polySelectConstraint(mode=3, type=0x0008, size=3)  - 筛选出来所有边数大于3的

FPSCheck:
current_time_unit = cmds.currentUnit(query=True, time=True) # - 判断帧数
cmds.currentUnit(time="film") # - fix

UnknownNodeCheck：
unknows = cmds.ls(type="unknown") # - 判断有没有unknown节点
cmds.lockNode(unknown, lock=False) cmds.delete(unknown) # -解锁然后删除
```



```
Run_Cycle/                  <-- 【资产根目录】
│
├── meta.json               <-- 【大脑】版本数据库
│
├── workspace.ma            <-- 【工作文件】(可选) 永远是当前最新状态，方便引用
│
└── _versions/              <-- 【版本库】(隐藏细节)
    ├── v001/
    │   ├── Run_Cycle_v001.ma
    │   └── Run_Cycle_v001.jpg  <-- 缩略图
    ├── v002/
    │   ├── Run_Cycle_v002.ma
    │   └── Run_Cycle_v002.jpg
    └── ...
```

![image-20251208215905754](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251208215905754.png)

```
core:
scene_name = cmds.file(query=True, sceneName=True)
 - refresh_context： 通过scene_name找到当前工作目录，并且判断是否再子文件夹中
 - load_data： 如果是再根目录并且meta.json存在就加载，否则创建并且输入默认数据
 - save_data： 保存传入的json数据
 - create_version: 计算版本号 -> 创建子文件夹 -> 截图 -> 拷贝文件 -> 更新json
 - open_version_file： cmds.file(full_path, open=True, force=True)打开这个文件，并且refresh_context刷新context
```

```
UI：
UI被拆成上中下三个布局，分别是：
1.info_layout = QtWidgets.QHBoxLayout() # --- A. 顶部信息栏 --- 资产名字 + refresh按钮
2. self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal) # --- B. 中间核心区 (左右分栏) --- QListWidget列表 + 一个布局（QLabel/缩略图 + QLabel/version信息 + QCheckBox/publish勾选框 + QPushButton/open this version按钮）
3. save_group = QtWidgets.QGroupBox("Save New Version") # --- C. 底部：存新版本区域 ---

初始化时候refresh_list
refresh_list: 调用refresh_context, 拿到meta.json数据，根据倒叙写入列表（版本+用户+备注），写入UserRole方便其他方法调用item.setData(QtCore.Qt.UserRole, info)

on_save_clicked: 调用create_version然后refresh_list，刷新一下最新的版本

on_item_clicked： 通过info = item.data(QtCore.Qt.UserRole)拿到当前对象，设置右侧版本+用户+时间+资源名字+备注,然后设置图片

pixmap = QtGui.QPixmap(full_thumb_path)
scaled_pix = pixmap.scaled(self.lbl_thumbnail.size(), QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)
self.lbl_thumbnail.setPixmap(scaled_pix)

on_open_clicked： 拿到当前item，获取当前item的userrole，拿到版本号调用open_version_file，调用refresh_list

on_publish_toggled： 修改json数据，然后调用save_data，调用refresh_list
```

