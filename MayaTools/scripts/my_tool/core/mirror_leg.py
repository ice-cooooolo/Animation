import maya.cmds as cmds


def mirror_leg_clean_setup_v10():
    # ================= 配置 =================
    # 只需要选中左边第一条腿的总组 (L_Leg_01_Grp)
    # =======================================

    selection = cmds.ls(selection=True)
    if not selection:
        cmds.error("请选中【L_Leg_01_Grp】！")
        return

    source_grp = selection[0]
    print("=== 🛠️ V10: 启动‘干净镜像’重建程序 ===")

    # 1. 解析源结构 (找到左边的骨骼和控制器)
    all_nodes = cmds.listRelatives(source_grp, allDescendents=True, fullPath=True)

    l_root_jnt = ""
    l_ctrl_grp = ""

    for node in all_nodes:
        short = node.split("|")[-1]
        # 找骨骼根 (通常是 L_Leg_01_Jnt)
        if "01_Jnt" in short and "L_" in short:
            l_root_jnt = node
        # 找控制器组 (通常是 L_Leg_Ctrl_Grp)
        elif "Ctrl_Grp" in short and "L_" in short and "PV" not in short and "IK" not in short:
            l_ctrl_grp = node

    if not l_root_jnt or not l_ctrl_grp:
        cmds.error("找不到 L_Leg_01_Jnt 或 L_Leg_Ctrl_Grp，请检查命名！")
        return

    # ==========================================
    # 2. 镜像骨骼 (使用 Maya 原生 Mirror，保证 Scale 为正)
    # ==========================================
    # MirrorJoint 命令返回的是列表
    r_root_jnt = cmds.mirrorJoint(l_root_jnt, mirrorYZ=True, mirrorBehavior=True, searchReplace=("L_", "R_"))[0]
    print(f"   ✅ 骨骼镜像完成: {r_root_jnt}")

    # ==========================================
    # 3. 镜像控制器 (Scale -1 但不带 IK)
    # ==========================================
    # 复制控制器组
    r_ctrl_grp_list = cmds.duplicate(l_ctrl_grp)
    r_ctrl_grp = r_ctrl_grp_list[0]

    # 创建镜像台
    mirror_stage = cmds.group(empty=True)
    cmds.parent(r_ctrl_grp, mirror_stage)
    cmds.setAttr(f"{mirror_stage}.scaleX", -1)

    # 拿出控制器 (Bake Scale)
    cmds.parent(r_ctrl_grp, world=True)
    cmds.delete(mirror_stage)

    # 改名 (L_ -> R_)
    # 递归改名所有子物体
    r_ctrls = cmds.listRelatives(r_ctrl_grp, allDescendents=True, fullPath=True)
    if r_ctrls:
        r_ctrls.sort(key=len, reverse=True)
        for ctrl in r_ctrls:
            short = ctrl.split("|")[-1]
            if "L_" in short:
                new_name = short.replace("L_", "R_")
                cmds.rename(ctrl, new_name)

    # 改总组名
    r_ctrl_grp = cmds.rename(r_ctrl_grp, l_ctrl_grp.split("|")[-1].replace("L_", "R_"))
    print(f"   ✅ 控制器镜像完成: {r_ctrl_grp}")

    # ==========================================
    # 4. 重建 IK (原生创建，拒绝复制)
    # ==========================================
    # 找到右边的骨骼链头尾
    r_jnt_chain = cmds.listRelatives(r_root_jnt, allDescendents=True, fullPath=True)
    r_end_jnt = ""
    # 简单的逻辑：链条里名字带 End 的就是末端
    for jnt in r_jnt_chain:
        if "End" in jnt.split("|")[-1]:
            r_end_jnt = jnt
            break

    if r_root_jnt and r_end_jnt:
        ik_name = "R_Leg_IK"
        # 创建 RP Solver IK
        r_ik_handle = cmds.ikHandle(n=ik_name, sj=r_root_jnt, ee=r_end_jnt, sol="ikRPsolver")[0]

        # 创建 Rig 组存放它
        r_rig_grp = cmds.group(empty=True, n="R_Leg_Rig_Grp")
        cmds.parent(r_ik_handle, r_rig_grp)

        # ==========================================
        # 5. 连接约束 (Constraints)
        # ==========================================
        # 在新的控制器组里找 R_PV 和 R_IK_Ctrl
        r_ctrl_children = cmds.listRelatives(r_ctrl_grp, allDescendents=True)
        r_pv_ctrl = ""
        r_main_ctrl = ""

        for node in r_ctrl_children:
            if "PV_Ctrl" in node and "Grp" not in node:
                r_pv_ctrl = node
            elif "IK_Ctrl" in node and "Grp" not in node:
                r_main_ctrl = node

        if r_pv_ctrl:
            try:
                cmds.poleVectorConstraint(r_pv_ctrl, r_ik_handle)
            except:
                pass

        if r_main_ctrl:
            try:
                cmds.pointConstraint(r_main_ctrl, r_ik_handle, maintainOffset=True)
                # 如果你也做了旋转约束，解开下面这行注释
                # cmds.orientConstraint(r_main_ctrl, r_end_jnt, maintainOffset=True)
            except:
                pass

        print("   ✅ IK 重建与约束完成")

        # ==========================================
        # 6. 最终打包
        # ==========================================
        final_grp = cmds.group(empty=True, n="R_Leg_01_Grp")

        # 创建结构组
        r_jnt_grp = cmds.group(empty=True, n="R_Leg_Jnt_Grp")
        cmds.parent(r_root_jnt, r_jnt_grp)

        # 把所有东西扔进总组
        cmds.parent(r_rig_grp, final_grp)
        cmds.parent(r_jnt_grp, final_grp)
        cmds.parent(r_ctrl_grp, final_grp)

        print(f"=== 🎉 成功生成完美右腿: {final_grp} ===")
        print("💡 下一步：选中这个新生成的 R_Leg_01_Grp，再次运行 V8 脚本生成右边的其他腿！")


# 运行
mirror_leg_clean_setup_v10()