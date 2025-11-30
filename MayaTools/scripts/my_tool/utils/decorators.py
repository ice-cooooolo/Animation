# my_tool/utils/decorators.py
from functools import wraps
from maya import cmds

def undoable(func):
    """
    将函数包裹在一个 Undo Chunk 中，保证用户按 Ctrl+Z 能一步撤销。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True, chunkName=func.__name__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 可以在这里加通用的错误弹窗，或者记录日志
            cmds.warning(f"工具运行出错: {e}")
            raise # 继续抛出异常，方便调试
        finally:
            cmds.undoInfo(closeChunk=True)
    return wrapper