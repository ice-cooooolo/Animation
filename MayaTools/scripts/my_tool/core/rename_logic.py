# my_tool/core/renamer_logic.py
import maya.cmds as cmds
from ..utils.decorators import undoable

def get_safe_selection(include_hierarchy = False):
    sel = cmds.ls(selection=True, long=True)

    if include_hierarchy:
        sel = cmds.ls(sel, dagObjects=True, long=True)

    if not sel:
        return []

    sel = list(set(sel))
    sel.sort(key=len, reverse=True)
    return sel

@undoable
def batch_replace(search_str, replace_str, mode, include_hierarchy = False):
    if search_str is None:
        return

    sel = get_safe_selection(include_hierarchy)
    count = 0

    for full_path in sel:
        short_name = full_path.split("|")[-1]
        new_name = short_name

        if mode == 0:
            new_name = short_name.replace(search_str, replace_str)
        elif mode == 1:
            # prefix
            if short_name.startswith(search_str):
                new_name = replace_str + short_name[len(search_str):]
        elif mode == 2:
            # end
            if short_name.endswith(replace_str):
                new_name = short_name[:-len(search_str)] + replace_str
        if new_name != short_name:
            try:
                cmds.rename(full_path, new_name)
                count += 1
            except Exception as e:
                print(f"Skipped {short_name}: {e}")

    print(f"Renamed {count} objects.")

def batch_renumber(base_name, start_num, padding, include_hierarchy = False):
    if base_name is None:
        return

    objects = get_safe_selection(include_hierarchy)

    if not objects:
        return

    temp_names = []
    for obj in objects:
        try:
            temp_name = cmds.rename(obj, "TEMP_RENAME_Process_#")
            temp_names.append(temp_name)
        except Exception as e:
            print(f"Skipped {obj}: {e}")
    temp_names.reverse()
    count = 0
    current_num = start_num

    for tmp_name in temp_names:
        # 构造数字部分: f"{5:03d}" -> "005"
        num_str = f"{current_num:0{padding}d}"

        if "#" in base_name:
            final_name = base_name.replace("#", num_str)
        else:
            final_name = f"{base_name}_{num_str}"

        try:
            cmds.rename(tmp_name, final_name)
            current_num += 1
            count += 1
        except Exception as e:
            print(f"Error renaming {tmp_name}: {e}")

    print(f"Renumbered {count} objects.")

def batch_prefix_suffix(prefix, suffix, include_hierarchy = False):
    objects = get_safe_selection(include_hierarchy)
    count = 0

    for full_path in objects:
        short_name = full_path.split("|")[-1]

        # 拼接
        new_name = f"{prefix}{short_name}{suffix}"

        if new_name != short_name:
            try:
                cmds.rename(full_path, new_name)
                count += 1
            except:
                pass

    print(f"Modified {count} objects.")