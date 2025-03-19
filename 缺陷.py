import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xlrd


# 参数选择部分
st.sidebar.header("参数选择")

# 测试方法选择
formula_type = st.sidebar.selectbox(
    "选择测试方法",
    ["GS", "SS","CP","1/f"],  
    key="formula_type"
)

# 缺陷类型选择
defect_types = {
    "GS": ["氧化物俘获电荷缺陷浓度ΔNot", "界面态陷阱浓度ΔNit"],
    "SS": ["氧化物俘获电荷缺陷浓度ΔNot", "界面态陷阱浓度ΔNit"],
    "CP": ["氧化物俘获电荷缺陷浓度ΔNot", "界面态陷阱浓度ΔNit"],
    "1/f": ["氧化物俘获电荷缺陷浓度ΔNot", "界面态陷阱浓度ΔNit"]
}

defect_type = st.sidebar.selectbox(
    "选择缺陷类型",
    defect_types[formula_type],
    key="defect_type"
)

def handle_calculation(config):
    """通用计算处理函数"""
    st.header(f"{formula_type}测试")
    st.write("求解公式：")
    st.latex(config["formula"])

    # 初始化表格
    if config["table_key"] not in st.session_state:
        st.session_state[config["table_key"]] = pd.DataFrame(
            columns=["剂量(krad)", config["result_col"]]
        )

    # 参数输入
    st.sidebar.subheader("输入参数")
    input_values = {}
    for param in config["inputs"]:
        input_values[param['key']] = st.sidebar.number_input(
            param['label'],
            value=param['default'],
            format=param.get('format', "%f")
        )

    # 计算功能
    if st.button("计算"):
        try:
            result = config["calc_function"](**input_values)
            new_row = {
                "剂量(krad)": "",
                config["result_col"]: result
            }
            st.session_state[config["table_key"]] = pd.concat([
                st.session_state[config["table_key"]],
                pd.DataFrame([new_row])
            ], ignore_index=True)
        except Exception as e:
            st.error(f"计算出错：{e}")

    # 表格编辑
    st.write("编辑表格内容：")
    updated_data = []
    df = st.session_state[config["table_key"]]
    
    for index, row in df.iterrows():
        cols = st.columns(2)
        with cols[0]:
            dose = st.text_input(
                f"剂量(krad) [行{index+1}]",
                value=row["剂量(krad)"],
                key=f"dose_{config['table_key']}_{index}"
            )
        with cols[1]:
            val = st.number_input(
                f"{config['result_col']} [行{index+1}]",
                value=row[config['result_col']],
                key=f"val_{config['table_key']}_{index}"
            )
        updated_data.append({
            "剂量(krad)": dose,
            config['result_col']: val
        })
    
    st.session_state[config["table_key"]] = pd.DataFrame(updated_data)
    
    # 显示表格
    st.write("更新后的表格：")
    st.dataframe(st.session_state[config["table_key"]])
  
    # 绘图功能
    if st.button("绘制图形", key=f"plot_{config['table_key']}"):
        if not st.session_state[config["table_key"]].empty:
            fig, ax = plt.subplots()
            df = st.session_state[config["table_key"]]
            ax.plot(df["剂量(krad)"], df[config['result_col']], 'bo-')
            ax.set_xlabel("剂量(krad)")
            ax.set_ylabel(config['result_col'])
            st.pyplot(fig)
        else:
            st.warning("表格为空，无法绘制图形！")

# 不同测试方法的配置
method_configs = {
    "GS": {
        "氧化物俘获电荷缺陷浓度ΔNot": {
            "formula": r"\mathrm{\Delta}N_{ot}=\frac{Cox\cdot\mathrm{\Delta}V_{mg}}{q}",
            "inputs": [{
                "label": "输入 ΔVmg（单位：V）",
                "key": "ΔVmg",
                "default": 1.0
            }],
            "calc_function": lambda ΔVmg: (6.91E-10* ΔVmg) / 1.6e-19, 
            "table_key": "gs_table1",
            "result_col": "ΔNot"
        },
        "界面态陷阱浓度ΔNit": {
            "formula": r"\Delta N_{it}=\frac{2\Delta I_{peak}}{q\cdot S_{peak}\cdot n_i\cdot\sigma\cdot\nu_{th}exp{\left(\frac{qV_{BE}}{2kT}\right)}}",
            "inputs": [{
                "label": "输入 ΔIpeak（单位：A）",
                "key": "ΔIpeak",
                "default": 1.0        
            }],
            "calc_function": lambda ΔIpeak: (2 * ΔIpeak) / (1.6E-19 * 6.16E-6 * 1.5E10 * 1E-16 * 1E-7 * math.exp((1.6e-19*0.5)/(2*1.38e-23*298))),
            "table_key": "gs_table2",
            "result_col": "ΔNit"
        }
    },

    
  "SS": {
        "氧化物俘获电荷缺陷浓度ΔNot": {
            "formula": r"""
            \begin{aligned}
            \Delta V_{ot} &= V_{mg1} - V_{mg2} \\
            \Delta N_{ot} &= \frac{C_{ox} \cdot \Delta V_{ot}}{q}
            \end{aligned}
            """,
            "inputs": [
                {"label": "辐照前Vmg1 (V)", "key": "vmg1", "default": 0.5},
                {"label": "辐照后Vmg2 (V)", "key": "vmg2", "default": 0.4},
                {"label": "氧化层电容Cox (F/cm²)", "key": "cox", "default": 6.91e-8}
            ],
            "calc_function": lambda vmg1, vmg2, cox: (cox * (vmg1 - vmg2)) / 1.6e-19,
            "table_key": "ss_table1",
            "result_col": "ΔNot (cm⁻²)"
        },
        "界面态陷阱浓度ΔNit": {
            "formula": r"""
            \begin{aligned}
            \Delta V_{it} &= \Delta V_{th} - \Delta V_{ot} \\
            \Delta N_{it} &= \frac{C_{ox} \cdot \Delta V_{it}}{q}
            \end{aligned}
            """,
            "inputs": [
                {"label": "阈值电压变化ΔVth (V)", "key": "dvth", "default": 0.15},
                {"label": "ΔVot (V)", "key": "dvot", "default": 0.1},
                {"label": "氧化层电容Cox (F/cm²)", "key": "cox", "default": 6.91e-8}
            ],
            "calc_function": lambda dvth, dvot, cox: (cox * (dvth - dvot)) / 1.6e-19,
            "table_key": "ss_table2",
            "result_col": "ΔNit (cm⁻²)"
        }
    },
    "CP": {
        "氧化物俘获电荷缺陷浓度ΔNot": {
            "formula": r"\Delta V_{ot}=\frac{q\Delta N_{ot}}{C_{ox}}",
            "inputs": [
        {"label": "输入ΔVth（单位：V）", "key": "ΔVth", "default": 1.0},
        {"label": "输入ΔNit（单位：cm-2）", "key": "ΔNit", "default": 1e-6, }
    ],
            "calc_function": lambda ΔVth,ΔNit: (((6.91E-10* ΔVth) / 1.6e-19)-ΔNit), 
            "table_key": "gs_table1",
            "result_col": "ΔNot"
        },
        "界面态陷阱浓度ΔNit": {
            "formula": r"{\mathrm{\Delta N}}_{it}=\frac{\mathrm{\Delta}I_{cpmax}}{q\times f\times A_g}",
            "inputs": [{
                "label": "输入ΔIcpmax（单位：A）",
                "key": "ΔIcpmax",
                "default": 1.0        
            }],
            "calc_function": lambda ΔIcpmax: (ΔIcpmax) / (1.6E-19 *1E6*3.3912E-6),
            "table_key": "gs_table2",
            "result_col": "ΔNit"
        }
    },
}

# 主程序逻辑
if formula_type in method_configs:
    config = method_configs[formula_type][defect_type]
    handle_calculation(config)
else:
    st.info("暂未实现该方法的计算")
