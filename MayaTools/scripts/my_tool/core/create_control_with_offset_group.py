import maya.cmds as cmds


def create_control_with_offset_group(name, radius=1.0, position=(0, 0, 0)):
    """
    V3.0 最终版：采用“先成组，后移动组”的逻辑。
    这是最符合 Maya 底层逻辑的方案，保证控制器全程“不沾灰”。
    """

    ctrl_name = f"ctrl_{name}"
    grp_name = f"grp_{name}"

    # 1. 在原点 (0,0,0) 创建控制器
    # 此时 Pivot 在中心，Translate 为 0
    ctrl = cmds.circle(name=ctrl_name, radius=radius, normal=(0, 1, 0), center=(0, 0, 0))[0]

    # 2. 创建组 (Offset Group)
    # 此时我们不使用 empty=True，而是直接把 ctrl 传进去
    # 这相当于你在 Outliner 里选中 ctrl 然后按 Ctrl+G
    # 结果：grp 在 (0,0,0)，ctrl 是它的子物体
    grp = cmds.group(ctrl, name=grp_name)

    # 3. 【核心逻辑】只移动组 (Group)
    # 我们把“爸爸”搬到目标位置，“儿子”会自动跟着走
    # 此时：
    # Grp 的 World Position = 目标位置
    # Ctrl 的 World Position = 目标位置 (被带过去的)
    # Ctrl 的 Local Translate = (0,0,0) (相对于爸爸没动过)
    cmds.xform(grp, worldSpace=True, translation=position)

    # 4. 清理选择
    cmds.select(ctrl)

    print(f"✅ [TA Tool] Created Perfect Control: {ctrl} (Grp moved to {position})")
    return grp, ctrl

try:
    # 模拟：在 (10, 5, 5) 创建
    target_pos = (10, 5, 5)

    grp, ctrl = create_control_with_offset_group(name="Final_Test", radius=2.0, position=target_pos)

    # 验证 1: 检查控制器的轴心是否在目标位置 (应该是)
    pivot = cmds.xform(ctrl, q=True, worldSpace=True, rotatePivot=True)[0]
    print(f"Pivot 位置: {pivot} (应为 10, 5, 5)")

    # 验证 2: 检查控制器的局部 Translate 是否为 0 (必须是)
    tx = cmds.getAttr(f"{ctrl}.tx")
    print(f"局部 Translate X: {tx} (绝对是 0.0)")

    # 验证 3: 检查 Group 是否“脏”了 (应该是)
    grp_tx = cmds.getAttr(f"{grp}.tx")
    print(f"组 Translate X: {grp_tx} (应为 10.0)")

except Exception as e:
    cmds.error(f"❌ 出错: {e}")