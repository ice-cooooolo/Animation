# 1. (规范) 导入应放在文件顶部
import maya.cmds as cmds


# import random # 我们不再需要它了

def create_joint_chain(name="chain", num_joints=10, spacing=5.0):
    """
    (规范) 这是一个专业的“文档字符串”(Docstring)。
    它解释了这个函数的功能、参数和返回值，非常重要。

    Args:
        name (str): 骨骼链的“基础名称”，例如 "arm_L"
        num_joints (int): 你想要创建的骨骼数量
        spacing (float): 每个骨骼之间的“间距”

    Returns:
        list: 包含所有新创建骨骼名称的列表
    """

    # (核心) 清空选择，确保我们创建的是一个“新”的骨骼链
    # 否则，它可能会被链接到你当前选中的物体上
    cmds.select(clear=True)

    joint_list = []

    for i in range(num_joints):

        # 2. (规范) 我们只在第一个骨骼(i=0)时使用(0,0,0)
        # 之后的骨骼，我们只指定一个轴向的“间距”
        # Maya会自动把它放在“上一个”骨骼的子位置
        position = (0, 0, 0)
        if i > 0:
            position = (spacing, 0, 0)  # 沿X轴创建

        # 3. (规范) 使用 f-string 格式化字符串，更现代、更清晰
        # :02d 意思是“两位数的整数，不足的前面补0”，例如 01, 02...
        joint_name = f"{name}_{i:02d}_JNT"  # "JNT" 是TA常用的骨骼后缀

        # 4. (核心) 创建骨骼。
        # Maya会自动把它链接到上一个创建的骨骼上
        new_joint = cmds.joint(p=position, name=joint_name)

        joint_list.append(new_joint)

    print(f"成功创建了 {num_joints} 个骨骼组成的骨骼链: {name}")

    # 5. (进阶) "自动骨骼朝向" (我们在 Week 1-2 学过的！)
    # 绑定TA创建的骨骼链，必须有“干净”的朝向
    # 我们告诉Maya，让整条链的X轴(aim)指向下一个骨骼
    cmds.joint(joint_list[0],  # 选中链条的根骨骼
               edit=True,
               orientJoint="xyz",  # 旋转顺序
               secondaryAxisOrient="yup",  # Y轴朝上
               zeroScaleOrient=True,  # 归零末端骨骼的朝向
               children=True)  # 应用到所有子骨骼

    return joint_list


# --- (规范) 使用 try/except 块来“调用”函数 ---
try:
    # 我们可以传递参数，而不是在函数内部写死
    my_arm_joints = create_joint_chain(name="arm_L", num_joints=5, spacing=8.0)
    print(f"创建的骨骼是: {my_arm_joints}")

    my_leg_joints = create_joint_chain(name="leg_L", num_joints=3, spacing=10.0)
    print(f"创建的骨骼是: {my_leg_joints}")

except Exception as e:
    print(f"创建骨骼时出错: {e}")