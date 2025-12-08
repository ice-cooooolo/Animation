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



### 方法一：手动制造“病态”物体 (理解原理)



请按照以下步骤在 Maya 里操作，分别制造三种错误：



#### 1. 制造“未冻结变换” (Unfrozen Transforms)



- **原理**：物体的位置、旋转不是 0，缩放不是 1。
- **操作**：
  1. 创建一个 **Cube** (`pCube1`)。
  2. 随便把它移到旁边，旋转一下，放大两倍。
  3. **不要**点 Modify -> Freeze Transformations。
- **预期**：工具应该报错，因为它的 Translate/Rotate/Scale 有数值。



#### 2. 制造“历史记录” (Construction History)



- **原理**：模型保留了建模过程的操作节点（输入流）。
- **操作**：
  1. 创建一个 **Sphere** (`pSphere1`)。
  2. 右键选 Face，随便选几个面。
  3. 按 `Ctrl + E` (Extrude) 挤出一下。
  4. **不要**点 Edit -> Delete by Type -> History。
  5. 你可以在 Channel Box 的 Inputs 栏里看到 `polyExtrudeFace1`，这就是历史。
- **预期**：工具应该报错，因为检测到了 Inputs。



#### 3. 制造“N-gons” (多边面 > 4条边)



- **原理**：N-gon 是指有 5 条或更多边的面。
- **操作**：
  1. 创建一个 **Plane** (平面)。在属性里把 `Subdivisions Width` 设为 **2**，`Height` 设为 **1**。
     - 此时它是两个并排的正方形面。
  2. 右键选 **Edge**。
  3. 选中**中间**那条把两个面隔开的线。
  4. 按 `Delete` (或 `Backspace`) 删掉它。
  5. **结果**：现在这就变成了一个大长方形面。数一数它的边：上面 2 条 + 下面 2 条 + 左边 1 条 + 右边 1 条 = **6 条边**。
  6. 这就是一个标准的 N-gon。
- **预期**：工具应该报错，并选中这个面。



#### ❓ Q1 (架构篇): "我看了你的代码，你为什么要把检查项写成一个个 Class (类)，而不是直接写一堆函数？"



- **🕵️‍♂️ 面试官在想什么**：他在考察你的 **OOP (面向对象)** 意识和 **可扩展性 (Scalability)**。初学者才写一堆函数，高手都用类。

- **❌ 错误回答**：因为类看起来更高级 / 因为教程是这么教的。

- **✅ 满分回答**：

  > “主要是为了**可扩展性**和**多态性**。
  >
  > 如果用函数写，UI 代码里会有大量的 `if type == 'FPS': do_fps()` 这种硬编码判断。
  >
  > 我定义了一个 `CheckItem` 基类，规定了所有检查项都要有 `check()` 和 `fix()` 方法。这样在 UI 层，我只需要遍历检查项列表，统一调用 `.check()` 即可，完全不需要关心具体是查 FPS 还是查命名。
  >
  > 以后如果还要加 50 个检查项，我只需要写新的类并注册到 Config 里，**UI 代码一行都不用改**。这符合‘**开闭原则**’。”



#### ❓ Q2 (Qt 技术篇): "我看你的 UI 和逻辑是分离的，那点击修复按钮时，UI 怎么知道要去修复哪个物体？"



- **🕵️‍♂️ 面试官在想什么**：考察你对 **Qt 数据绑定 (Data Binding)** 的理解。这是开发复杂工具的核心技能。

- **✅ 满分回答**：

  > “我利用了 Qt 的 `setData(Qt.UserRole)` 功能。
  >
  > 在生成 UI 列表时，我把后端的 `CheckItem` **实例对象**直接存储在了 `QTreeWidgetItem` 里。 当用户点击按钮时，我从当前选中的 UI Item 里把这个对象取出来 (`data()`)，直接调用它身上的 `.fix()` 方法。
  >
  > 这样做实现了 UI 和 数据的**强绑定但低耦合**，不需要维护额外的字典或索引来查找对应关系。”



#### ❓ Q3 (Maya 性能篇): "关于 N-gons (多边面) 检查，如果场景里有一百万个面，遍历检查会不会卡死？你是怎么优化的？"



- **🕵️‍♂️ 面试官在想什么**：考察你对 **Maya API 效率** 的认知。死循环遍历是新手的通病。

- **✅ 满分回答**：

  > “确实，如果用 Python `for` 循环去遍历 `cmds.polyInfo` 查边数，在大场景下绝对会卡死。
  >
  > 所以我没有用遍历，而是利用了 Maya 的 **选择约束 (Selection Constraints)** 功能 (`cmds.polySelectConstraint`)。 我将约束模式设为‘边数 > 4’，Maya 底层（C++层）会瞬间帮我选出所有的 N-gons，然后我只需要获取 `cmds.ls(sl=1)`。 这种方法的效率比 Python 遍历快成百上千倍。”



#### ❓ Q4 (流程篇): "对于‘重名检查’，为什么你把它设为不可自动修复 (is_fixable=False)？"



- **🕵️‍♂️ 面试官在想什么**：考察你的 **流程安全意识 (Pipeline Safety)**。敢于说“不”的 TA 才是好 TA。

- **✅ 满分回答**：

  > “因为自动修复重名是非常危险的。
  >
  > 在绑定或动画文件中，很多逻辑是依赖路径引用的。如果我自动把 `hand_L` 改成了 `hand_L_1`，可能会导致 Referenced 的文件断连，或者脚本报错。
  >
  > 作为一个资产检查工具，我的职责是**‘发现问题’**和**‘拦截垃圾’**。对于这种破坏性风险极高的操作，我认为应该把决定权交给美术人员，而不是由工具擅自做主。”

#### ❓ Q1 (数据安全): "如果有两个美术同时打开了这个工具，同时点了 Save Version，你的 meta.json 会怎么样？"



- **考察点**：并发冲突 (Concurrency) / 竞态条件 (Race Condition)。

- **你的现状**：目前的 `json.dump` 是直接覆盖写入。如果 A 读了数据，B 读了数据；A 写入 v003，B 写入 v003（覆盖了 A）。这会导致数据丢失。

- **✅ 满分回答**：

  > “目前的版本是为单人本地管理设计的。如果是多人协作项目，我会采取以下升级方案：
  >
  > 1. **文件锁 (File Lock)**：在写入 json 前生成一个 `.lock` 文件，写完删除。如果别人想写，发现有锁就等待。
  > 2. **数据库化**：大厂通常会把 `meta.json` 升级为 MySQL 或 MongoDB，利用数据库的事务（Transaction）机制来处理并发。
  > 3. **原子写入 (Atomic Write)**：先写到 `meta_tmp.json`，写完确认无误后，再 rename 覆盖原文件，防止写入中断导致文件损坏。”



#### ❓ Q2 (性能优化): "如果一个镜头做了 500 个版本，你的 meta.json 变得很大，列表加载变慢，你会怎么优化？"



- **考察点**：Qt 性能优化 / 大数据处理。

- **✅ 满分回答**：

  > “我会做两步优化：
  >
  > 1. **分页加载 (Pagination)**：UI 列表默认只显示最近的 20 个版本。只有当用户滚轮滑到底部时，再加载更多。
  > 2. **增量读取**：不把所有数据都塞在一个 `meta.json` 里。可以按月归档（`meta_2023_10.json`），或者把缩略图等大信息分离出去，主 JSON 只存关键索引。
  > 3. **多线程 (Threading)**：把截图加载和 JSON 读取放在后台线程 (`QThread`) 处理，不阻塞主 UI 线程，保持界面流畅。"



#### ❓ Q3 (管线逻辑): "你现在的工具是存 JSON 的，那如果有美术手动去文件夹里删了一个 .ma 文件，你的工具会报错吗？怎么处理？"



- **考察点**：数据一致性 (Data Consistency) / 鲁棒性。

- **✅ 满分回答**：

  > “这是‘文件系统’与‘数据库’不同步的问题。 我的工具在 `open_version` 时加了 `os.path.exists` 判断。如果 JSON 里有记录，但物理文件没了，工具会弹窗提示‘文件丢失’。 进阶的话，我可以写一个 **Validate Database** 的功能，启动时扫描一遍硬盘，把那些文件已经丢失的版本从 JSON 里自动标记为‘已损坏’或清洗掉。”



#### ❓ Q4 (用户体验): "你的缩略图是存在本地的。如果我想把这个工具做成联网的，让总监在网页上也能看版本预览，你会怎么改？"



- **考察点**：Web 端思维 / 路径处理。

- **✅ 满分回答**：

  > “核心在于**路径解耦**。 目前我的 JSON 里存的是相对路径 `_versions/v001/xxx.jpg`。 如果要上 Web，我只需要写一个简单的 Python 后端（比如 Flask/Django），读取这个 JSON。 前端网页请求图片时，后端根据 JSON 里的相对路径，去服务器的文件存储（NAS/S3）里找到图片返回即可。因为我存的是相对路径，所以数据结构天然支持这种扩展。”