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
            &\text{1. 计算阈值电压 } V_{th} = \arg\max\left(\frac{d^2I_d}{dV_g^2}\right) \\
            &\text{2. 计算 } I_{do}(V_d) = \frac{I_d(th)}{e^{\beta V_{th} \cdot (\beta V_{th})^{-1/2}}} \\
            &\text{3. 计算 } I_{mg} = I_{do}(V_d)e^{\beta \frac{V_{th}}{2} \cdot \left(\beta \frac{V_{th}}{2}\right)^{-1/2} \\
            &\text{4. 确定 } V_{mg} \text{ 为 } I_{mg} \text{对应的栅压} \\
            &\Delta N_{ot} = \frac{C_{ox}(V_{mg1} - V_{mg2})}{q}
            \end{aligned}
            """,
            "inputs": [
                {"label": "辐照前数据文件", "key": "pre_file", "type": "file"},
                {"label": "辐照后数据文件", "key": "post_file", "type": "file"},
                {"label": "氧化层电容Cox (F/cm²)", "key": "cox", "default": 6.91e-8}
            ],
            "calc_function": ss_calculate_not,
            "table_key": "ss_table1",
            "result_col": "ΔNot (cm⁻²)",
            "custom_ui": ss_oxide_ui  # 专用界面组件
        },
        "界面态陷阱浓度ΔNit": {
            "formula": r"""
            \begin{aligned}
            &\Delta V_{th} = V_{th2} - V_{th1} \\
            &\Delta V_{ot} = V_{mg2} - V_{mg1} \\
            &\Delta N_{it} = \frac{C_{ox}(\Delta V_{th} - \Delta V_{ot})}{q}
            \end{aligned}
            """,
            "inputs": [
                {"label": "阈值电压变化ΔVth (V)", "key": "dvth", "type": "auto"},
                {"label": "ΔVot (V)", "key": "dvot", "type": "auto"},
                {"label": "氧化层电容Cox (F/cm²)", "key": "cox", "default": 6.91e-8}
            ],
            "calc_function": ss_calculate_nit,
            "table_key": "ss_table2",
            "result_col": "ΔNit (cm⁻²)",
            "custom_ui": ss_interface_ui
        }
    }
}

# 新增SS专用函数
def ss_oxide_ui(config):
    """氧化物俘获电荷专用界面"""
    st.header("SS测试 - 氧化物俘获电荷分析")
    
    # 文件上传
    pre_file = st.file_uploader("上传辐照前数据", type=["csv","xlsx"], 
                              key="ss_pre_upload")
    post_file = st.file_uploader("上传辐照后数据", type=["csv","xlsx"],
                               key="ss_post_upload")
    
    if pre_file and post_file:
        # 解析数据
        pre_data = parse_ss_file(pre_file)
        post_data = parse_ss_file(post_file)
        
        # 显示分析结果
        with st.expander("辐照前参数"):
            show_ss_analysis(pre_data)
            
        with st.expander("辐照后参数"):
            show_ss_analysis(post_data)
        
        # 自动计算ΔVmg
        dvmg = post_data['vmg'] - pre_data['vmg']
        st.session_state['auto_dvmg'] = dvmg
        
        # 保存到参数系统
        st.session_state['ss_params'] = {
            'pre': pre_data,
            'post': post_data,
            'cox': config['inputs'][2]['default']
        }

def ss_calculate_not(cox):
    """氧化物俘获电荷计算"""
    params = st.session_state.get('ss_params')
    if not params:
        raise ValueError("请先上传并分析数据")
    
    dvmg = params['post']['vmg'] - params['pre']['vmg']
    return (cox * dvmg) / 1.6e-19

def parse_ss_file(file):
    """解析SS数据文件"""
    # 与之前实现的文件解析逻辑一致
    # 返回包含vth, vmg, ido_vd等参数的字典
    return analysis_results

def show_ss_analysis(data):
    """显示单次分析结果"""
    cols = st.columns(3)
    cols[0].metric("Vth", f"{data['vth']:.3f} V")
    cols[1].metric("Vmg", f"{data['vmg']:.3f} V")
    cols[2].metric("Ido(Vd)", f"{data['ido_vd']:.2e} A")
    
    # 绘制特征曲线
    fig = plot_ss_curves(data)
    st.pyplot(fig)

# 主逻辑调整
if formula_type in method_configs:
    config = method_configs[formula_type][defect_type]
    
    if "custom_ui" in config:  # SS专用处理
        config["custom_ui"](config)
        if st.button("计算", key="ss_calc"):
            try:
                result = config["calc_function"](**get_ss_params(config))
                update_table(config, result)
            except Exception as e:
                st.error(str(e))
        show_data_table(config)
    else:  # 其他方法原有逻辑
        handle_calculation(config)
      
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
