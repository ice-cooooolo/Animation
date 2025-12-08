import maya.cmds as cmds

import os
import json
import shutil
import datetime
import getpass # 获取当前用户名
import io

# 定义版本库的隐藏文件夹名
VERSION_DIR_NAME = "_versions"
META_FILE_NAME = "meta.json"

class VersionManager:

    def __init__(self):
        self.version_root = ""
        self.workspace_path = ""
        self.meta_path = ""
        self.data = {}

        self.refresh_context()

    def refresh_context(self):
        scene_name = cmds.file(query=True, sceneName=True)
        if not scene_name:
            # not saved
            self.workspace_path = None
            return

        # 获取当前文件所在的文件夹
        current_dir = os.path.dirname(scene_name)

        normalized_dir = current_dir.replace("\\", "/")

        # 判断：如果我们身处 _versions 文件夹内部
        # Z:/Shots/Shot_010/Work.ma -> Z:/Shots/Shot_010
        if f"/{VERSION_DIR_NAME}" in normalized_dir:
            # 比如: Z:/Shot/_versions/v001
            # 截取 _versions 之前的部分 -> Z:/Shot
            self.workspace_path = normalized_dir.split(f"/{VERSION_DIR_NAME}")[0]
            print(f"Context Adjusted: Found root at {self.workspace_path}")
        else:
            # 正常在根目录下
            self.workspace_path = normalized_dir

        # Z:/Shots/Shot_010/_versions
        self.version_root = os.path.join(self.workspace_path, VERSION_DIR_NAME)
        # Z:/Shots/Shot_010/meta.json
        self.meta_path = os.path.join(self.workspace_path, META_FILE_NAME)

        self.load_data()

    def load_data(self):
        old_meta_path = os.path.join(self.version_root, META_FILE_NAME)

        # 情况 A: 新路径不存在，但旧路径存在 -> 执行自动搬家
        if not os.path.exists(self.meta_path) and os.path.exists(old_meta_path):
            print("🔧 Migrating meta.json to root directory...")
            try:
                shutil.move(old_meta_path, self.meta_path)
            except Exception as e:
                print(f"Migration failed: {e}")

        if not self.meta_path or not os.path.exists(self.meta_path):
            self.data = {
                "asset_name": self._get_asset_name_from_scene(),
                "versions": {}
            }
        else:
            try:
                with io.open(self.meta_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading meta.json: {e}")
                self.data = {"versions": {}}

    def save_data(self):
        if not self.workspace_path:
            return

        try:
            with io.open(self.meta_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving meta.json: {e}")

    def create_version(self, comment = "", make_thumbnail = True):
        """
            核心功能：发布新版本
            1. 计算版本号
            2. 创建子文件夹
            3. 截图
            4. 保存/拷贝文件
            5. 更新 JSON
        """
        if not self.workspace_path:
            return False

        # 1.CAL VERSIONS
        current_count = len(self.data.get("versions", {}))
        next_version_num = current_count + 1
        version_code = f"v{next_version_num:03d}"

        # .../_versions/v001/
        version_dir = os.path.join(self.version_root, version_code)
        if not os.path.exists(version_dir):
            os.makedirs(version_dir)

        current_scene = cmds.file(query=True, sceneName=True)
        base_name = os.path.basename(current_scene) # Work.ma
        name_no_ext, ext = os.path.splitext(base_name) # Work, .ma

        # new file: shot_v001.ma
        asset_name = self.data.get("asset_name", "Asset")
        new_file_name = f"{asset_name}_{version_code}{ext}"
        new_file_path = os.path.join(version_dir, new_file_name)

        # save file
        cmds.file(save=True, force=True)
        # copy
        shutil.copy2(current_scene, new_file_path)

        # screenshot
        thumb_path = ""
        if make_thumbnail:
            thumb_name = f"{asset_name}_{version_code}.jpg"
            thumb_full_path = os.path.join(version_dir, thumb_name)
            self._capture_thumbnail(thumb_full_path)
            thumb_path = os.path.join(VERSION_DIR_NAME, version_code, thumb_name) #relative path

        # update data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = getpass.getuser()

        version_info = {
            "version": version_code,
            "filename": new_file_name,
            "path": os.path.join(VERSION_DIR_NAME, version_code, new_file_name).replace("\\", "/"),
            "author": user,
            "time": timestamp,
            "comment": comment,
            "thumbnail": thumb_path,
            "is_published": False  # 默认为 False
        }

        self.data["versions"][version_code] = version_info

        self.save_data()

        print(f"Version {version_code} created successfully!")
        return version_info

    def open_version_file(self, version_code):
        if  version_code in self.data["versions"]:
            rel_path = self.data["versions"][version_code]["path"]
            full_path = os.path.join(self.workspace_path, rel_path)

            if os.path.exists(full_path):
                if cmds.file(query=True, modified=True):
                    res = cmds.confirmDialog(t="Unsaved Changes", m="Save changes?", b=["Yes", "No", "Cancel"])
                    if res == "Yes":
                        cmds.file(save=True)
                    elif res == "Cancel":
                        return

                cmds.file(full_path, open=True, force=True)
                print(f"Opened version: {version_code}")

                # 打开旧版本后，记得刷新一下 context，否则路径可能对不上
                self.refresh_context()
            else:
                print(f"Path {full_path} not found.")

    def _get_asset_name_from_scene(self):
        scene = cmds.file(query=True, sceneName=True)
        if not scene: return "UnknownAsset"
        base = os.path.basename(scene)
        name, _ = os.path.splitext(base)
        return name.replace("_Work", "").replace("_v", "")

    def _capture_thumbnail(self, output_path):
        try:
            cmds.playblast(
                completeFilename=output_path,
                forceOverwrite=True,
                format="image",
                compression="jpg",
                width=320,
                height=240,
                showOrnaments=False,  # 不显示坐标轴、相机名
                viewer=False,  # 不弹窗
                frame=[cmds.currentTime(q=True)],  # 只截当前帧
                percent=100
            )
        except Exception as e:
            print(f"Error capturing thumbnail: {e}")