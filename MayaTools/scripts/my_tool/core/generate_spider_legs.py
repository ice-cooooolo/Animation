import maya.cmds as cmds


def generate_spider_legs_v8_rebirth():
    # ================= 配置区 =================
    legs_per_side = 4
    angle_gap = 26.0
    # =========================================

    selection = cmds.ls(selection=True)
    if not selection:
        cmds.error("请选中【左边第一条腿】(L_Leg_01_Grp)！")
        return
    source_leg_grp = selection[0]

    print(f"=== 🕷️ 启动 V8：IK 重生系统 (Rebirth) ===")

    for i in range(1, legs_per_side):

        # --- 1. 复制与旋转 ---
        new_leg_list = cmds.duplicate(source_leg_grp)
        new_leg_root = new_leg_list[0]

        temp_pivot = cmds.group(empty=True, name="Temp_Pivot_Grp")
        cmds.parent(new_leg_root, temp_pivot)
        current_angle = i * angle_gap
        cmds.setAttr(f"{temp_pivot}.rotateY", current_angle)
        cmds.parent(new_leg_root, world=True)
        cmds.delete(temp_pivot)

        # --- 2. 改名逻辑 ---
        index_str = str(i + 1).zfill(2)  # "02"
        new_prefix = f"Leg_{index_str}"  # "Leg_02"

        children = cmds.listRelatives(new_leg_root, allDescendents=True, fullPath=True)
        if children:
            children.sort(key=len, reverse=True)
            for child in children:
                if not cmds.objExists(child): continue
                short_name = child.split("|")[-1]
                if "L_Leg" in short_name:
                    new_child_name = short_name.replace("L_Leg", new_prefix)
                    if "01" in new_child_name:
                        # 这里只替换第一次出现的 01，防止要把 Jnt_01 里的 01 换掉
                        # 你的骨骼叫 Leg_02_01_Jnt 是正常的，不要误伤
                        if "_01_" in new_child_name:
                            pass  # 骨骼层级名字保留
                        else:
                            new_child_name = new_child_name.replace("01", index_str, 1)
                    cmds.rename(child, new_child_name)

        final_root_name = f"{new_prefix}_Grp"
        try:
            new_leg_root = cmds.rename(new_leg_root, final_root_name)
        except:
            pass

        # ========================================================
        # 🔧 3. 核心手术：切除坏死 IK，植入新 IK
        # ========================================================

        # 3.1 搜寻关键部件 (在新组里找)
        all_new_nodes = cmds.listRelatives(new_leg_root, allDescendents=True, fullPath=True)

        bad_ik = ""
        target_pv_ctrl = ""
        target_main_ctrl = ""
        start_joint = ""
        end_joint = ""
        rig_grp = ""  # 用来存放新 IK

        for node in all_new_nodes:
            short = node.split("|")[-1]

            # 找坏掉的 IK
            if "IK" in short and "Ctrl" not in short and "Grp" not in short:
                bad_ik = node
            # 找 PV 控制器
            elif "PV_Ctrl" in short and "Grp" not in short:
                target_pv_ctrl = node
            # 找脚部主控制器
            elif "IK_Ctrl" in short and "Grp" not in short:
                target_main_ctrl = node
            # 找存放 IK 的组 (Rig_Grp)
            elif "Rig_Grp" in short:
                rig_grp = node
            # 找起始骨骼 (通常名字里带 01_Jnt)
            elif "01_Jnt" in short:
                start_joint = node
            # 找末端骨骼 (通常名字里带 End_Jnt)
            elif "End_Jnt" in short:
                end_joint = node

        # 3.2 手术开始
        if bad_ik:
            print(f"   🔪 切除坏死 IK: {bad_ik.split('|')[-1]}")
            cmds.delete(bad_ik)  # 删掉坏的

        if start_joint and end_joint:
            print(f"   🧬 创建新 IK: {start_joint.split('|')[-1]} -> {end_joint.split('|')[-1]}")

            # 生成新 IK 名字
            new_ik_name = f"{new_prefix}_IK"

            # 创建全新的 Rotate-Plane Solver IK
            # sj=startJoint, ee=endEffector, sol=solver
            new_ik_handle = \
            cmds.ikHandle(name=new_ik_name, startJoint=start_joint, endEffector=end_joint, solver="ikRPsolver")[0]

            # 把新 IK 扔进 Rig_Grp 保持整洁
            if rig_grp:
                cmds.parent(new_ik_handle, rig_grp)

            # 3.3 重新建立神经连接 (约束)

            # PV 约束
            if target_pv_ctrl:
                try:
                    cmds.poleVectorConstraint(target_pv_ctrl, new_ik_handle)
                    print("      ✅ PV 约束连接成功")
                except Exception as e:
                    print(f"      ❌ PV 失败: {e}")

            # Point 约束
            if target_main_ctrl:
                try:
                    cmds.pointConstraint(target_main_ctrl, new_ik_handle, maintainOffset=True)
                    print("      ✅ 主控制器连接成功")
                except:
                    pass
        else:
            print("   ❌ 严重错误：找不到骨骼(Start/End Jnt)，无法创建 IK！请检查骨骼命名是否包含 '01_Jnt' 和 'End_Jnt'")

    print("=== 🕷️ V8 手术完成：所有腿部已获得新生！ ===")


# 运行
generate_spider_legs_v8_rebirth()