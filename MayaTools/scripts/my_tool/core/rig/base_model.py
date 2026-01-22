import maya.cmds as cmds

class BaseModule:
    """
    绑定基类
    传入guides数据创建locator
    guides -> 用户摆放locator位置 -> 创建骨骼 -> 蒙皮
    """
    def __init__(self, name: str, side: str, idx: int = 0):
        """
        Init BaseModule
        Args:
            name(str): function name (e.g. 'Arm', 'Leg')
            side(str): side ('L', 'R')
            idx(int): index
        """
        self.name = name
        self.side = side
        self.idx = idx

        # 存储生成的 Guide 列表，方便后续访问
        self.guides = []

    def get_name(self, suffix: str, sub_idx: int = None) -> str:
        """Returns a formatted name string (e.g., L_Arm_0_Grp)."""
        index_to_use = sub_idx if sub_idx is not None else self.idx
        return f"{self.side}_{self.name}_{index_to_use}_{suffix}"

    def create_main_group(self)-> str:
        """
        Creates the main hierarchy group for this module.
        Returns:
            str: The name of the created group.
        """
        grp_name = f"{self.side}_{self.name}_{self.idx}_Grp"
        if not cmds.objExists(grp_name):
            cmds.group(empty=True, name=grp_name)
        return grp_name

    def create_guides(self):
        raise NotImplementedError

    def create_locator(self, name, pos = (0, 0, 0)):
        loc = cmds.spaceLocator(name=name)[0]
        cmds.xform(loc, worldSpace=True, translation=pos)
        cmds.setAttr(loc + ".localScale", 0.5, 0.5, 0.5, type="double3")
        return loc

    def add_guide_attributes(self, guide_locator, **kwargs):
        """
        Adds metadata attributes to a guide locator
        Args:
            guide_locator (str): The name of the locator.
            **kwargs: Key-value pairs of attributes to add.
                      Example: module_type="limb", guide_index=1
        """
        if not cmds.objExists(guide_locator):
            cmds.warning(f"{guide_locator} does not exist. Skipping attributes.")
            return

        for attr_name, value in kwargs.items():
            # 1. 检查属性是否已存在，不存在则创建
            if not cmds.attributeQuery(attr_name, node=guide_locator, exists=True):
                if isinstance(value, str):
                    cmds.addAttr(guide_locator, longName=attr_name, dataType="string")
                elif isinstance(value, bool):
                    cmds.addAttr(guide_locator, longName=attr_name, attributeType="boolean")
                elif isinstance(value, int):
                    cmds.addAttr(guide_locator, longName=attr_name, attributeType="long")
                else:
                    # default is float
                    cmds.addAttr(guide_locator, longName=attr_name, attributeType="double")

            # 2. 赋值 (Set Value)
            if isinstance(value, str):
                cmds.setAttr(f"{guide_locator}.{attr_name}", value, type="string")
            else:
                cmds.setAttr(f"{guide_locator}.{attr_name}", value, keyable= True)