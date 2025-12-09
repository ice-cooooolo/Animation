class CheckItem:
    label = "Unknown Check"
    category = "General"
    is_fixable = False
    is_critical = True

    def __init__(self):
        self.status = "Idle" # Idle, Passed, Failed, Warning
        self.failed_objects = [] # 具体的错误物体列表 (存全路径)
        self.info_message = "" # 检查结果的文字描述 (UI 显示用)

    def check(self):
        """
        核心检查逻辑。
        子类必须重写此方法。
        逻辑：
        1. 执行检查
        2. 更新 self.status
        3. 更新 self.failed_objects
        4. 更新 self.info_message
        """
        raise NotImplementedError("Subclasses must implement check()")

    def fix(self):
        """
        一键修复逻辑。
        只有 is_fixable = True 时才会被调用。
        """
        print(f"No fix implementation for {self.label}")

    def reset(self):
        """重置状态"""
        self.status = "Idle"
        self.failed_objects = []
        self.info_message = ""