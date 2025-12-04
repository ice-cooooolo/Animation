from .checks import scene_checks
from .. import config

def get_checks(mode = "Model"):
    """
        工厂函数：从配置中读取清单，并实例化检查项。
        """
    # 1. 从配置中获取对应的类列表
    # 如果模式不存在，默认返回空列表，或者 fallback 到 Model
    check_classes = config.CHECK_LIST.get(mode, [])

    instances = []

    # 2. 实例化 (Instantiation)
    for cls in check_classes:
        # 这里发生了魔法：cls 是一个类 (FPSCheck)，cls() 创建了对象
        instance = cls()
        instances.append(instance)

    return instances