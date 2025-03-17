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

    # 初始化表格（修改列初始化）
    if config["table_key"] not in st.session_state:
        st.session_state[config["table_key"]] = pd.DataFrame(
            columns=["剂量(krad)"] + config["result_cols"]
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

   if st.button("计算"):
        try:
            results = config["calc_function"](**input_values)
            new_row = {"剂量(krad)": ""}
            for col, value in zip(config["result_cols"], results):
                new_row[col] = value
            # ... [保持表格更新逻辑]

    # 表格编辑（动态生成列）
    st.write("编辑表格内容：")
    updated_data = []
    df = st.session_state[config["table_key"]]
    
    for index, row in df.iterrows():
        cols = st.columns(len(config["result_cols"]) + 1)
        
        # 剂量输入
        with cols[0]:
            dose = st.text_input(
                f"剂量(krad) [行{index+1}]",
                value=row["剂量(krad)"],
                key=f"dose_{config['table_key']}_{index}"
            )
        
        # 动态生成结果列
        row_data = {"剂量(krad)": dose}
        for i, col in enumerate(config["result_cols"]):
            with cols[i+1]:
                val = st.number_input(
                    f"{col} [行{index+1}]",
                    value=row[col],
                    key=f"{col}_{config['table_key']}_{index}"
                )
                row_data[col] = val
        updated_data.append(row_data)
    
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
    I_d\left(th\right)=I_{do}\left(V_d\right)e^{\left(\beta V_{th}\right)\bullet\left(\beta V_{th}\right)^{-1/2}} \\
    I_{mg}=I_{do}\left(V_d\right)e^{\left(\beta\frac{V_{th}}{2}\right)\bullet\left(\beta\frac{V_{th}}{2}\right)^{-1/2}}\\
     \Delta V_{ot}=\frac{-q\Delta N_{ot}}{C_{ox}}
    \end{aligned}
    """,
    "inputs": [
        {"label": "输入Vth（单位：V）", "key": "Vth", "default": 1.0},
        {"label": "输入Id_th（单位：A）", "key": "Id_th", "default": 1e-6},
        {"label": "电压变化ΔV_ot (V)", "key": "ΔV_ot", "default": 0.1}
    ],
     "calc_function": lambda Vth, Id_th, Cox, ΔV_ot: [
            # 计算Img
            Id_th * math.exp((1.95e-7*Vth) * (1.95e-7*Vth)**-0.5) / math.exp((3.89e-7*Vth) * (3.89e-7*Vth)**-0.5),
            # 计算ΔNot
            (-Cox * ΔV_ot) / 1.6e-19
        ],
        "table_key": "ss_table1",
        "result_cols": "Img", "ΔNot"
},
   
       
        "界面态陷阱浓度ΔNit": {  # 示例配置，根据实际需求修改
            "formula": r"\Delta Y = \sqrt{D \cdot E}",
            "inputs": [
                {"label": "参数D", "key": "D", "default": 9.0},
                {"label": "参数E", "key": "E", "default": 4.0}
            ],
            "calc_function": lambda D, E: math.sqrt(D * E),
            "table_key": "ss_table2",
            "result_col": "ΔY"
        }
    }
}

# 主程序逻辑
if formula_type in method_configs:
    config = method_configs[formula_type][defect_type]
    handle_calculation(config)
else:
    st.info("暂未实现该方法的计算")

