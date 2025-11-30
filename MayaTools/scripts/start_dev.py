import socket
import os
import textwrap  # 用于清理缩进


def run_in_maya(project_path, package_name, entry_module, port=7001):
    # 1. 强制将 Windows 路径的反斜杠 \ 替换为 /，防止转义灾难
    safe_project_path = project_path.replace("\\", "/")

    # 2. 构建代码字符串
    # 注意：我们在代码最前面加了弹窗，用来测试代码是否真的开始执行了
    code_body = f"""
import sys
import importlib
import maya.cmds as cmds

# 【调试信标】如果你能看到这个弹窗，说明 Socket 连接成功，代码没有语法错误
# cmds.confirmDialog(title='Debug', message='Socket 连接成功！\\n准备加载: {package_name}', button=['OK'])

# 1. 确保项目路径在 sys.path
path = "{safe_project_path}"
if path not in sys.path:
    sys.path.insert(0, path)
    print(f"Added path: {{path}}")

# 2. 清理旧模块 (热重载核心)
package_name = "{package_name}"
to_delete = []
for name in sys.modules.keys():
    if name.startswith(package_name):
        to_delete.append(name)

# 按长度倒序删除
to_delete.sort(key=len, reverse=True)

if to_delete:
    print(f"Reloading: Removing {{len(to_delete)}} modules...")
    for name in to_delete:
        try:
            del sys.modules[name]
        except:
            pass
else:
    print("First time load.")

# 3. 运行入口
try:
    print(f"Importing entry: {entry_module}")
    import {entry_module} as entry

    # 再次强制 reload 入口，确保最新
    importlib.reload(entry)

    if hasattr(entry, 'show_ui'):
        print("Executing show_ui()...")
        entry.show_ui()
    else:
        cmds.warning(f"No show_ui found in {{entry}}")

except Exception as e:
    # 捕获运行时的所有错误并打印到 Script Editor
    print(f"\\nError Detail:\\n{{e}}")
    import traceback
    traceback.print_exc()
"""

    # 3. 关键：去除代码块所有的公共缩进，确保发过去的是顶格代码
    cmd = textwrap.dedent(code_body)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', port))
            s.sendall(cmd.encode('utf-8'))
            print(f"✅ 发送成功 (包: {package_name})")
            print(f"项目路径: {safe_project_path}")
    except ConnectionRefusedError:
        print(f"❌ 错误: 无法连接 Maya 端口 {port}")
        print("请检查 Maya 是否已打开端口，且模式为 Python。")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 配置
    MY_PACKAGE = "my_tool"
    MY_ENTRY = "my_tool.ui.window"  # 确保这里是指向 .window 文件

    run_in_maya(current_dir, MY_PACKAGE, MY_ENTRY)