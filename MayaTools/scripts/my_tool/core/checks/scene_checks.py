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
        from ... import config
        cmds.currentUnit(time=config.TARGET_FPS)
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

class AnimationRangeCheck(CheckItem):
    label = "Animation Range Check"
    category = "Animation"
    is_fixable = True

    def __init__(self):
        super().__init__()
        # 用来临时存储计算出的正确时间，传给 fix() 用
        self._calculated_start = 0
        self._calculated_end = 0

    def check(self):
        # 1. 获取当前 Timeline 设置
        current_min = cmds.playbackOptions(q=True, min=True)
        current_max = cmds.playbackOptions(q=True, max=True)

        # 2. 获取场景里所有的“时间驱动”动画曲线
        # TL=Translate, TA=Angle(Rotate), TU=Unknown(Scale/Visibility)
        # 排除 UL, UA, UU (这些是 Driven Keys)
        anim_curves = cmds.ls(type=['animCurveTL', 'animCurveTA', 'animCurveTU'])

        if not anim_curves:
            self.status = "Passed"
            self.info_message = "No animation curves found."
            return

        # 3. 获取这些曲线上的所有关键帧时间点
        # result 会是一个长列表 [1.0, 2.0, 5.0, ...]
        try:
            keys = cmds.keyframe(anim_curves, query=True, timeChange=True)
        except:
            keys = []

        if not keys:
            self.status = "Passed"
            self.info_message = "No keys found."
            return

        # 4. 找到最小和最大帧
        real_start = min(keys)
        real_end = max(keys)

        # 存储计算结果
        self._calculated_start = real_start
        self._calculated_end = real_end

        # 5. 比较 (允许 1 帧的误差)
        # 很多时候动画师会从 0 帧还是 1 帧开始会有争议，这里严格一点检查
        if abs(current_min - real_start) > 0.01 or abs(current_max - real_end) > 0.01:
            self.status = "Failed"
            self.info_message = f"Timeline: {int(current_min)}-{int(current_max)} | Actual: {int(real_start)}-{int(real_end)}"
            # 这里的 failed_objects 没法具体指向某个物体，因为是全局设置
            self.failed_objects = ["Timeline Settings"]
        else:
            self.status = "Passed"
            self.info_message = "Timeline matches animation keys."

    def fix(self):
        # 自动将时间轴对齐到真实动画长度
        if self._calculated_start == 0 and self._calculated_end == 0:
            self.check()  # 如果还没运行过 check，先跑一遍计算

        print(f"Fixing Timeline to: {self._calculated_start} - {self._calculated_end}")

        # 设置播放范围 (Range Slider)
        cmds.playbackOptions(minTime=self._calculated_start, maxTime=self._calculated_end)

        # 设置动画总范围 (Animation Start/End)
        cmds.playbackOptions(animationStartTime=self._calculated_start, animationEndTime=self._calculated_end)

        self.check()