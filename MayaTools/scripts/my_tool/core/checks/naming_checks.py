import maya.cmds as cmds

from collections import Counter
from .base_check import CheckItem

class DuplicateNameCheck(CheckItem):
    label = "Duplicate Names Check"
    category = "Naming"
    is_fixable = False

    def check(self):
        # 比如 ['|Group1|pCube1', '|Group2|pCube1', '|pSphere1']
        all_dag_nodes = cmds.ls(type="transform", long=True)

        short_names = [path.split("|")[-1] for path in all_dag_nodes]

        #{'pCube1': 2, 'pSphere1': 1}
        counts = Counter(short_names)

        duplicates_short = [name for name, count in counts.items() if count > 1]

        if not duplicates_short:
            self.status = "Passed"
            self.info_message = "No duplicate names found."
            self.failed_objects = []
        else:
            self.status = "Failed"
            self.info_message = f"Found {len(duplicates_short)} duplicated names."
            failed_list = []
            for path in all_dag_nodes:
                short = path.split("|")[-1]
                if short in duplicates_short:
                    failed_list.append(path)
            self.failed_objects = failed_list

        print("All failed objects:", self.failed_objects)