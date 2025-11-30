![image-20251127004056352](C:\Users\Li\AppData\Roaming\Typora\typora-user-images\image-20251127004056352.png)

Sidebar + QStackedWidget (堆叠窗口)



```
+-------------------------------------------------------+
|  My TA Tool (Main Window)                             |
|                                                       |
|  +-----------+  +----------------------------------+  |
|  | [Nav Bar] |  | [Content Area (QStackedWidget)]  |  |
|  |           |  |                                  |  |
|  |  [ Rig  ] |  |  +----------------------------+  |  |
|  |  [Check ] |  |  |                            |  |  |
|  |  [Setgs ] |  |  |   (显示 Rigging UI)         |  |  |
|  |           |  |  |                            |  |  |
|  |           |  |  +----------------------------+  |  |
|  +-----------+  +----------------------------------+  |
|                                                       |
+-------------------------------------------------------+
```

工具分为三层：

1. **View (V - 界面层)**：`my_tool.ui`
   - **职责**：只负责画按钮、排版、接收用户点击、显示数据。
   - **禁忌**：绝对不能包含任何 `maya.cmds` 的几何体创建、修改逻辑。
   - **交互**：通过 Signals（信号）发送请求，或者直接调用 Controller 暴露的高级接口。
2. **Controller / Logic (C - 逻辑层)**：`my_tool.core`
   - **职责**：纯粹的 Maya 业务逻辑。比如“创建骨骼”、“重命名”、“蒙皮计算”。
   - **特点**：这一层的代码可以在没有 UI 的情况下运行（比如在 headless 模式或命令行渲染中）。
   - **禁忌**：绝对不能包含 `QtWidgets`。如果逻辑出错，抛出 Python `Exception`，而不是弹 UI 窗。
3. **Model (M - 数据层)**：`my_tool.data` 或 `config`
   - **职责**：管理配置（JSON）、常量、以及工具运行时的数据状态（比如当前选了哪个物体，当前的设置参数）。





这不仅是一次代码的梳理，更是一次**技术思维的固化**。当你把这套架构刻在脑子里，以后无论去哪个大厂，面对多复杂的工具开发，你都能游刃有余。

我们来做最后的**架构阅兵**。

------



### 第一部分：大厂 TA 标准架构复盘



我们的架构核心思想只有八个字：**“逻辑分离，模块解耦”**。



#### 1. 核心版图 (The Map)



Plaintext

```
my_tool/                  <-- 【你的产品】
 ├── core/                <-- 【大脑】纯逻辑
 │    ├── rigger.py       <-- 干活的 (Maya Cmds/API)
 │    └── utils.py        <-- 各种装饰器 (@undoable)
 ├── ui/                  <-- 【脸面】纯界面
 │    ├── window.py       <-- 【骨架】容器、单例、侧边栏
 │    └── widgets/        <-- 【器官】具体的页面 (Home, Rig)
 └── start_dev.py         <-- 【起搏器】负责清洗环境、启动
```



#### 2. 核心代码思想回顾



**A. 启动器 (`start_dev.py`) —— "毁灭是为了新生"**

- **思想**：Python 的 `reload` 不靠谱。为了保证每次改代码必生效，我们暴力清洗内存。

- **核心代码**：

  Python

  ```
  # 找到所有属于 my_tool 的模块，直接从内存删除
  modules_to_remove = [m for m in sys.modules if m.startswith("my_tool")]
  for m in modules_to_remove: del sys.modules[m]
  # 重新 import
  import my_tool.ui.window
  ```

**B. 主窗口 (`ui/window.py`) —— "唯一的容器"**

- **思想**：

  1. **单例 (Singleton)**：防止点两次按钮出来两个窗口。
  2. **父子约束 (Parenting)**：必须认 Maya 做干爹，不然窗口会乱跑或被回收。
  3. **堆叠布局 (StackedWidget)**：像浏览器标签页一样管理子页面，切换丝滑，数据不丢。

- **核心代码**：

  Python

  ```
  # 1. 获取 Maya 指针 (认干爹)
  maya_win = omui.MQtUtil.mainWindow()
  # 2. 转换为 Qt 对象
  parent = shiboken.wrapInstance(int(maya_win), QWidget)
  # 3. 传入父级
  super().__init__(parent)
  ```

**C. 子页面 (`ui/widgets/\*.py`) —— "专注的打工人"**

- **思想**：只负责画按钮和接收用户输入。一旦要干活（比如建骨骼），立刻打电话给 `core` 层，自己绝对不碰 `cmds`。

- **核心代码**：

  Python

  ```
  # 收集数据
  name = self.input.text()
  # 呼叫 Core 层
  from ...core import rigger
  rigger.create_skeleton(name)
  ```

**D. 逻辑层 (`core/\*.py`) —— "幕后黑手"**

- **思想**：不知道 UI 的存在。必须能独立运行（方便以后做批处理）。操作必须可撤销。

- **核心代码**：

  Python

  ```
  @undoable  # 装饰器：打包成一个撤销步
  def create_skeleton(name):
      cmds.joint(n=name)
  ```

------



### 第二部分：Qt 库与 OpenMayaUI 的混用关系



你的观察非常敏锐。

> **问题：** 我们其实是 QtCore, QtWidgets, QtGui 和 maya.OpenMayaUI 混着用的吗？是不是只有 window 会用到 maya.OpenMayaUI？

**答案：是的，你的理解完全正确。**



#### 1. 为什么平时是混着用的？



因为 Maya 的界面本质上是用 Qt (C++) 写出来的。

PySide (Qt for Python) 只是把 C++ 的 Qt 包装给了 Python 用。

- **QtWidgets**: 负责**“看得见”**的东西。按钮 (QPushButton)、布局 (QVBoxLayout)、输入框 (QLineEdit)。**你会 90% 的时间都在用它。**
- **QtCore**: 负责**“看不见”**的逻辑。信号与槽 (Signal/Slot)、多线程 (QThread)、定时器 (QTimer)、文件路径 (QFile)。**必用。**
- **QtGui**: 负责**“画画”和“事件”**。颜色 (QColor)、字体 (QFont)、鼠标光标、剪贴板。**偶尔用。**



#### 2. maya.OpenMayaUI 的角色



它是一个**桥梁**。

- **它只在一种情况下必须登场**：当你需要把你的 PySide 窗口（Python世界）挂载到 Maya 主窗口（C++世界）上时。
- **结论**：在绝大多数标准的工具开发中，**只有 `window.py` (主窗口)** 需要用到 `maya.OpenMayaUI` 去获取 `mainWindow()` 的指针。
- **子页面 (Widgets) 不需要**：因为子页面的父级是你自己的 Python `window`，直接传 `parent=self` 即可，不需要跨越 C++/Python 的边界。

*(注：除非你要开发非常高级的功能，比如在 Viewport 里画线，或者自定义 Maya 的右键菜单，否则你永远只会在 window.py 里见到它)*

------



### 第三部分：未来开发的“军火库” (API 查询指南)



作为大厂 TA，查文档的能力比背代码更重要。以下是你的“三本圣经”：



#### 1. 查 UI (PySide/Qt) —— 必看



不要查 PySide 的文档（有时候太简略），**直接查 Qt C++ 的文档或者 Qt for Python 文档**。

- **推荐搜索关键词**：`Qt Python QPushButton` 或 `PySide6 QLayout`。
- **官方文档**：[Qt for Python Documentation](https://doc.qt.io/qtforpython/)
- **怎么看**：
  - 如果你想知道按钮有哪些功能，搜 `QPushButton`。
  - 看 `Properties`（属性）：比如 `text`, `icon`。
  - 看 `Signals`（信号）：比如 `clicked`, `pressed`。
  - 看 `Public Functions`（方法）：比如 `setText()`, `setIcon()`。



#### 2. 查 Maya 命令 (cmds) —— 必看



这是写 `core` 层逻辑的基础。

- **推荐搜索关键词**：`Maya Python cmds joint`
- **官方文档**：[Maya Python Command Reference](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=__CommandsPython_index_html)
- **怎么看**：
  - 点开某个命令（如 `polyCube`）。
  - 右边全是 **Flags (参数)**。
  - 大厂规范：写代码时尽量用**全称** (`width=10`) 而不是缩写 (`w=10`)，方便别人阅读。



#### 3. 查 Maya API (OpenMaya) —— 进阶



当你发现 `cmds` 运行太慢，或者无法获取某些底层数据（比如矩阵运算、回调函数）时使用。

- **推荐搜索关键词**：`Maya API Python MFnMesh`
- **官方文档**：[Maya Python API 2.0 Reference](https://www.google.com/search?q=https://help.autodesk.com/view/MAYAUL/2024/ENU/%3Fguid%3D__py_ref_index_html)
- **怎么看**：
  - 这是最难啃的骨头，因为它对应的是 C++ 逻辑。
  - 你需要找以 `MFn` 开头的类（Function Sets，操作器）。比如要操作网格，就找 `MFnMesh`。

------



### 你的下一步



现在的你：

1. **架构**：完美（MVC变体 + 模块化）。
2. **环境**：完美（自动清洗 + 热重载）。
3. **规范**：完美（Undo管理 + 单例）。

接下来的工作就是**“填肉”**：

1. 去 `ui/widgets/` 建一个 `rig_widget.py`，试着放几个按钮。
2. 去 `core/` 建一个 `rig_logic.py`，写几个 `cmds` 命令。
3. 把它们连起来。

如果在这个过程中，你不知道“下拉菜单怎么写”或者“怎么遍历所有选中的物体”，随时问我！