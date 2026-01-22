from .base_model import BaseModule
import maya.cmds as cmds

class LimbModule(BaseModule):
    def create_guides(self):
        position = [(0,5,0), (0,3,1), (0,0,0)]
        main_grp = self.create_main_group()
        for index, pos in enumerate(position):
            name = self.get_name("Guide", sub_idx=index)
            locator = self.create_locator(name, pos)
            self.add_guide_attributes(locator, module_type = "limb", guide_index = index)
            self.guides.append(locator)
            if index > 0:
                cmds.parent(locator, self.guides[index-1])

        if self.guides:
            cmds.parent(self.guides[0], main_grp)

        print(f"Limb Module '{self.name}' Created!")