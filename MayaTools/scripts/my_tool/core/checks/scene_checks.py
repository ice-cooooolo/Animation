import maya.cmds as cmds
from .base_check import CheckItem


class FPSCheck(CheckItem):
    label = "FPS Setting Check"
    category = "Scene"
    is_fixable = True

    def check(self):
        from ... import config
        current_time_unit = cmds.currentUnit(query=True, time=True)
        target_time_unit = config.TARGET_FPS

        if current_time_unit == target_time_unit:
            self.status = "Passed"
            self.info_message = f"Current FPS is correct ({current_time_unit})"
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Current FPS is incorrect ({current_time_unit})"
            self.failed_objects = ["Time Settings Node"]

    def fix(self):
        cmds.currentUnit(time="film")
        print("Fixed: FPS set to 24fps (film)")
        self.check()

class UnknownNodeCheck(CheckItem):
    label = "Unknown Nodes Check"
    category = "Scene"
    is_fixable = True
    
    def check(self):
        unknows = cmds.ls(type="unknown")
        if not unknows:
            self.status = "Passed"
            self.info_message = "Clean scene."
            self.failed_objects = []
        else:
            self.status = "Failed"
            count = len(unknows)
            self.info_message = f"Found ({count} unknown nodes)"
            self.failed_objects = unknows

    def fix(self):
        for unknown in self.failed_objects:
            if cmds.objExists(unknown):
                try:
                    cmds.lockNode(unknown, lock=False)
                    cmds.delete(unknown)
                except Exception as e:
                    print(f"Could not delete {unknown}: {e}")
        self.check()