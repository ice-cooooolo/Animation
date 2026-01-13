import maya.cmds as cmds

class BaseModule:
    """
    绑定基类
    传入guides数据创建locator
    guides -> 用户摆放locator位置 -> 创建骨骼 -> 蒙皮
    """
    def __init__(self, name, side, idx = 0):
        self.name = name
        self.side = side
        self.idx = idx

    def get_name(self, suffix):
        return f"{self.side}_{self.name}_{self.idx}_{suffix}"

    def create_main_group(self):
        name = self.get_name("Grp")
        cmds.select()