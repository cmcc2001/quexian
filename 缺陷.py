import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xlrd


with st.sidebar:
    st.title("缺陷提取")
    
 
    
    formula_type = st.selectbox("测试方法", ("GS", "SS", "CP"))
    defect_type = st.selectbox(
        "提取类型",
        ("氧化物俘获电荷缺陷浓度ΔNot", "界面态陷阱浓度ΔNit")
    )

if "results" not in st.session_state:
    st.session_state["results"] = {"GS": [], "SS": [], "CP": []}
#氧
if formula_type == "GS" and type == "氧化物俘获电荷缺陷浓度ΔNot":
    st.header("栅扫描")
    st.write("求解公式：")
    st.latex(r"""
\mathrm{\Delta}N_{ot}=\frac{Cox\cdot\mathrm{\Delta}V_{mg}}{q}
""")

    # 常量值（可设为默认值，也可以允许用户调整）
    q = 1.6e-19  # 电子电荷 (C)
    Cox = 1#
    if "table_data1" not in st.session_state:
        # 初始化一个空表格
        st.session_state["table_data1"] = pd.DataFrame(columns=["剂量(krad)", "ΔNot"])

    # 输入变量
    st.sidebar.subheader("输入参数")
    ΔVmg = st.sidebar.number_input("输入 ΔVmg（单位：V）", value=1.0)


    # 计算结果
    if st.button("计算"):
        try:

            # 完整公式
            tau = (Cox * ΔVmg / q )
            # 将计算结果追加到表格
            new_row = {"剂量(krad)": "", "ΔNot": tau}
            st.session_state["table_data1"] = pd.concat(
                [st.session_state["table_data1"], pd.DataFrame([new_row])],
                ignore_index=True
            )


        except Exception as e:
            st.write(f"计算出错：{e}")
    st.write("编辑表格内容：")
    updated_data = []
    for index, row in st.session_state["table_data1"].iterrows():
        col1, col2 = st.columns(2)
        with col1:
            remark = st.text_input(f"剂量(krad) [行 {index + 1}]", value=row["剂量(krad)"], key=f"remark_{index}")

        with col2:
            tau_value = st.number_input(f"ΔNot [行 {index + 1}]", value=row["ΔNot"], key=f"tau_{index}")
        updated_data.append({"剂量(krad)": remark, "ΔNot": tau_value})

    # 将更新后的数据存回 session_state
    st.session_state["table_data1"] = pd.DataFrame(updated_data)

    # 显示更新后的表格
    st.write("更新后的表格：")
    st.dataframe(st.session_state["table_data1"])
    # 绘制备注为 X 轴，τ (秒) 为 Y 轴的图形
    if st.button("绘制图形"):
        fig, ax = plt.subplots()
        if not st.session_state["table_data1"].empty:
            # 获取备注和 τ 数据
            x_data = st.session_state["table_data1"]["剂量(krad)"]
            y_data = st.session_state["table_data1"]["ΔNot"]
            # 绘制散点图
            ax.plot(x_data, y_data, color='blue', label='ΔNot')
            ax.set_xlabel("Dose(krad)")  # 设置 X 轴标签
            ax.set_ylabel("ΔNot")  # 设置 Y 轴标签

            ax.legend()

            st.pyplot(fig)  # 显示图表
        else:
            st.write("表格为空，无法绘制图形！")
            # 界
if formula_type == "GS" and type == "界面态陷阱浓度ΔNit":
    st.header("栅扫描")
    st.write("求解公式：")
    st.latex(r"""
\Delta N_{it}=\frac{2\Delta I_{peak}}{q\cdot S_{peak}\cdot n_i\cdot\sigma\cdot\nu_{th}exp{\left(\frac{qV_{BE}}{2kT}\right)}}
""")

    # 常量值（可设为默认值，也可以允许用户调整）
    q = 1.6e-19  # 电子电荷 (C)
    ni = 1
    VBE = 1
    k = 1.38e-23  # 玻尔兹曼常数 (J/K)
    T = 1
    if "table_data2" not in st.session_state:
        # 初始化一个空表格
        st.session_state["table_data2"] = pd.DataFrame(columns=["剂量(krad)", "ΔNit"])

    # 输入变量
    st.sidebar.subheader("输入参数")
    ΔIpeak = st.sidebar.number_input("输入 ΔIpeak（单位：A）", value=1.0)
    Speak = st.sidebar.number_input("输入 Speak（单位：A）", value=1.0)
    σ = st.sidebar.number_input("输入 σ（单位：A）", value=1.0)
    Vth = st.sidebar.number_input("输入 Vth（单位：A）", value=1.0)
    # 计算结果
    if st.button("计算"):
        try:
            # 指数部分
            exp_term = math.exp((q * VBE) / 2*(k * T))

            # fenmu
            term1 = (q * Speak * ni * σ * Vth)


            # 完整公式
            tau = (2*ΔIpeak/(term1*exp_term))
            # 将计算结果追加到表格
            new_row = {"剂量(krad)": "", "ΔNit": tau}
            st.session_state["table_data2"] = pd.concat(
                [st.session_state["table_data2"], pd.DataFrame([new_row])],
                ignore_index=True
            )


        except Exception as e:
            st.write(f"计算出错：{e}")
    st.write("编辑表格内容：")
    updated_data = []
    for index, row in st.session_state["table_data2"].iterrows():
        col1, col2 = st.columns(2)
        with col1:
            remark = st.text_input(f"剂量(krad) [行 {index + 1}]", value=row["剂量(krad)"], key=f"remark_{index}")

        with col2:
            tau_value = st.number_input(f"ΔNit [行 {index + 1}]", value=row["ΔNit"], key=f"tau_{index}")
        updated_data.append({"剂量(krad)": remark, "ΔNit": tau_value})

    # 将更新后的数据存回 session_state
    st.session_state["table_data2"] = pd.DataFrame(updated_data)

    # 显示更新后的表格
    st.write("更新后的表格：")
    st.dataframe(st.session_state["table_data2"])
    # 绘制备注为 X 轴，τ (秒) 为 Y 轴的图形
    if st.button("绘制图形"):
        fig, ax = plt.subplots()
        if not st.session_state["table_data2"].empty:
            # 获取备注和 τ 数据
            x_data = st.session_state["table_data2"]["剂量(krad)"]
            y_data = st.session_state["table_data2"]["ΔNit"]
            # 绘制散点图
            ax.plot(x_data, y_data, color='blue', label='ΔNit')
            ax.set_xlabel("Dose(krad)")  # 设置 X 轴标签
            ax.set_ylabel("ΔNit")  # 设置 Y 轴标签

            ax.legend()

            st.pyplot(fig)  # 显示图表
        else:
            st.write("表格为空，无法绘制图形！")

if formula_type == "SS":
    st.header("亚阈值扫描")
    st.write("求解公式：")
