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

