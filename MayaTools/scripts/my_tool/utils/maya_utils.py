from maya import cmds
from functools import wraps

def undoable(func):
    """
    装饰器：将函数内的所有 Maya 操作打包成一个 Undo 块。
    如果报错，自动关闭 Undo 块，防止 Maya 撤销队列损坏。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 开启 Undo 记录块
        cmds.undoInfo(openChunk=True, chunkName=func.__name__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            raise  # 继续抛出错误让控制台看到
        finally:
            # 无论成功还是报错，都必须关闭 Undo 块
            cmds.undoInfo(closeChunk=True)
    return wrapper