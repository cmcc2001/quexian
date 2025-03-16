import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xlrd

def handle_calculation(formula, inputs, calc_function, table_key, result_col):
    # 显示公式
    st.header("栅扫描")
    st.write("求解公式：")
    st.latex(formula)

    # 初始化表格
    if table_key not in st.session_state:
        st.session_state[table_key] = pd.DataFrame(columns=["剂量(krad)", result_col])

    # 侧边栏输入参数
    st.sidebar.subheader("输入参数")
    input_values = {}
    for param in inputs:
        input_values[param['key']] = st.sidebar.number_input(
            param['label'], 
            value=param['default'],
            format=param.get('format', "%f")
        )

    # 计算并更新表格
    if st.button("计算"):
        try:
            result = calc_function(**input_values)
            new_row = {"剂量(krad)": "", result_col: result}
            st.session_state[table_key] = pd.concat(
                [st.session_state[table_key], pd.DataFrame([new_row])],
                ignore_index=True
            )
        except Exception as e:
            st.error(f"计算出错：{e}")

    # 表格编辑功能
    st.write("编辑表格内容：")
    updated_data = []
    df = st.session_state[table_key]
    
    for index, row in df.iterrows():
        cols = st.columns(2)
        with cols[0]:
            dose = st.text_input(f"剂量(krad) [行{index+1}]", 
                               value=row["剂量(krad)"], 
                               key=f"dose_{table_key}_{index}")
        with cols[1]:
            val = st.number_input(f"{result_col} [行{index+1}]", 
                                value=row[result_col],
                                key=f"val_{table_key}_{index}")
        updated_data.append({"剂量(krad)": dose, result_col: val})
    
    st.session_state[table_key] = pd.DataFrame(updated_data)
    
    # 显示表格
    st.write("更新后的表格：")
    st.dataframe(st.session_state[table_key])

    # 绘图功能
    if st.button("绘制图形", key=f"plot_{table_key}"):
        if not st.session_state[table_key].empty:
            fig, ax = plt.subplots()
            df = st.session_state[table_key]
            ax.plot(df["剂量(krad)"], df[result_col], 'bo-')
            ax.set_xlabel("剂量(krad)")
            ax.set_ylabel(result_col)
            st.pyplot(fig)
        else:
            st.warning("表格为空，无法绘制图形！")

# ΔNot 计算逻辑
def calc_delta_not(ΔVmg):
    q = 1.6e-19
    Cox = 1
    return Cox * ΔVmg / q

# ΔNit 计算逻辑
def calc_delta_nit(ΔIpeak):
    q = 1.6e-19
    ni = 1
    VBE = 1
    k = 1.38e-23
    T = 1
    Speak = 1
    σ = 1
    Vth = 1
    
    # 注意保持原计算逻辑
    exp_term = math.exp((q * VBE) / 2 * (k * T))  # 保留原始计算顺序
    denominator = q * Speak * ni * σ * Vth * exp_term
    return (2 * ΔIpeak) / denominator

# 根据选择调用不同计算
if formula_type == "GS":
    if type == "氧化物俘获电荷缺陷浓度ΔNot":
        handle_calculation(
            formula=r"\mathrm{\Delta}N_{ot}=\frac{Cox\cdot\mathrm{\Delta}V_{mg}}{q}",
            inputs=[{
                'label': "输入 ΔVmg（单位：V）",
                'key': "ΔVmg",
                'default': 1.0
            }],
            calc_function=calc_delta_not,
            table_key="table_data1",
            result_col="ΔNot"
        )
    elif type == "界面态陷阱浓度ΔNit":
        handle_calculation(
            formula=r"\Delta N_{it}=\frac{2\Delta I_{peak}}{q\cdot S_{peak}\cdot n_i\cdot\sigma\cdot\nu_{th}exp{\left(\frac{qV_{BE}}{2kT}\right)}}",
            inputs=[{
                'label': "输入 ΔIpeak（单位：A）",
                'key': "ΔIpeak",
                'default': 1.0,
                'format': "%e"
            }],
            calc_function=calc_delta_nit,
            table_key="table_data2",
            result_col="ΔNit"
        )
if formula_type == "SS":
    st.header("亚阈值扫描")
    st.write("求解公式：")
