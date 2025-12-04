import maya.cmds as cmds
from .base_check import CheckItem

class HistoryCheck(CheckItem):
    label = "Construction History"
    category = "Geometry"
    is_fixable = True

    def check(self):
        meshes = cmds.ls(type="mesh", long=True)
        transforms = cmds.listRelatives(meshes, parent=True, fullPath=True) or []
        transforms = list(set(transforms))

        failed = []

        for obj in transforms:
            history = cmds.listHistory(obj, pruneDagObjects=True) # 排除本身， 查询对这个节点有影响的DAG
            if history and len(history) > 0:
                failed.append(obj)

        if not failed:
            self.status = "Passed"
            self.info_message = "No history found on meshes."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(failed)} objects with history."
            self.failed_objects = failed

    def fix(self):
        if self.failed_objects:
            cmds.delete(self.failed_objects, constructionHistory=True)
            print(f"Deleted history for {len(self.failed_objects)} objects.")
        self.check()

class UnFrozenTransformCheck(CheckItem):
    label = "Unfrozen Transforms"
    category = "Geometry"
    is_fixable = True

    def check(self):
        meshes = cmds.ls(type="mesh", long=True)
        transforms = cmds.listRelatives(meshes, parent=True, fullPath=True) or []
        transforms = list(set(transforms))

        failed = []
        for obj in transforms:
            # Check translate(x,y,z) = 0
            t = cmds.xform(obj, query=True, translation=True, objectSpace=True)
            # Check rotation(x,y,z) = 0
            r = cmds.xform(obj, query=True, rotation=True, objectSpace=True)
            # Check scale = 1
            s = cmds.xform(obj, query=True, scale=True, objectSpace=True)
            if any(abs(v) > 0.001 for v in t) or any(abs(r) > 0.001 for r in r) or any(abs(s - 1.0) > 0.001 for s in s):
                failed.append(obj)

        if not failed:
            self.status = "Passed"
            self.info_message = "No unfrozen transforms found."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(failed)} unfrozen objects."
            self.failed_objects = failed

    def fix(self):
        if self.failed_objects:
            cmds.makeIdentity(self.failed_objects, apply=True, translate=True, rotate=True, scale=True)
        self.check()

class NgonsCheck(CheckItem):
    label = "N-gons (Faces > 4 edges)"
    category = "Geometry"
    is_fixable = False

    def check(self):
        meshes = cmds.ls(type="mesh", long=True)
        if not meshes:
            self.status = "Passed"
            return

        cmds.select(meshes)
        cmds.selectMode(component=True)
        cmds.selectType(facet=True)

        cmds.polySelectConstraint(mode=3, type=0x0008, size=3)

        ngons = cmds.ls(selection=True)

        cmds.polySelectConstraint(disable=True)
        cmds.selectMode(object=True)

        if not ngons:
            self.status = "Passed"
            self.info_message = "No N-gons found."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(ngons)} faces > 4 edges."
            self.failed_objects = ngons
