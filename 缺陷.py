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
            &1.\ 计算阈值电压\ V_{th} = \arg\max\left(\frac{d^2I_d}{dV_g^2}\right) \\
            &2.\ 计算\ I_{do}(V_d) = \frac{I_d(th)}{e^{\beta V_{th} \cdot (\beta V_{th})^{-1/2}}} \\
            &3.\ 计算\ I_{mg} = I_{do}(V_d)e^{\beta \frac{V_{th}}{2} \cdot \left(\beta \frac{V_{th}}{2}\right)^{-1/2}} \\
            &4.\ 确定\ V_{mg}\ 为\ I_{mg}\ 对应的栅压 \\
            &5.\ \Delta N_{ot} = \frac{C_{ox}(V_{mg1} - V_{mg2})}{q}
            \end{aligned}
            """,
            "inputs": [
                {"label": "辐照前数据文件", "key": "pre_file", "type": "file"},
                {"label": "辐照后数据文件", "key": "post_file", "type": "file"},
                {"label": "温度T (K)", "key": "temp", "default": 300},
                {"label": "氧化层电容Cox (F/cm²)", "key": "cox", "default": 6.91e-8}
            ],
            "calc_function": ss_calculate_not,
            "table_key": "ss_table1",
            "result_col": "ΔNot (cm⁻²)",
            "custom_ui": ss_oxide_ui
        },
        # 界面态配置保持不变...
    }
}

# 新增物理常数
q = 1.6e-19  # 电子电荷
k = 1.38e-23  # 玻尔兹曼常数

def ss_oxide_ui(config):
    """氧化物俘获电荷专用界面"""
    st.header("SS测试 - 完整分析流程")
    
    # 文件上传
    pre_file = st.file_uploader("上传辐照前数据", type=["csv","xlsx"], key="ss_pre_upload")
    post_file = st.file_uploader("上传辐照后数据", type=["csv","xlsx"], key="ss_post_upload")
    
    # 温度输入
    temp = st.sidebar.number_input("温度 (K)", min_value=77, max_value=400, value=300)

    if pre_file and post_file:
        # 解析数据
        pre_data = parse_ss_file(pre_file, temp)
        post_data = parse_ss_file(post_file, temp)
        
        # 显示分析结果
        col1, col2 = st.columns(2)
        with col1:
            show_analysis_result("辐照前参数", pre_data)
        with col2:
            show_analysis_result("辐照后参数", post_data)

def parse_ss_file(file, temp):
    """解析SS数据文件"""
    try:
        # 读取数据
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # 计算导数
        vg = df['Vg'].values
        id = np.abs(df['Id'].values)
        
        # 计算一阶导数
        dId_dVg = np.gradient(id, vg)
        
        # 计算二阶导数并平滑
        window_size = min(21, len(vg)//2*2-1)
        d2Id_dVg2 = savgol_filter(dId_dVg, window_size, 3, deriv=1)
        
        # 找到Vth
        peak_idx = np.argmax(d2Id_dVg2)
        vth = vg[peak_idx]
        id_th = id[peak_idx]
        
        # 计算β
        beta = q / (k * temp)
        
        # 计算Ido(Vd)
        exponent = beta*vth * (beta*vth)**(-0.5)
        ido_vd = id_th / np.exp(exponent)
        
        # 计算Img
        half_exponent = (beta*(vth/2)) * (beta*(vth/2))**(-0.5)
        img = ido_vd * np.exp(half_exponent)
        
        # 查找Vmg
        f = interp1d(vg, id, kind='linear')
        v_interp = np.linspace(vg.min(), vg.max(), 1000)
        id_interp = f(v_interp)
        vmg = v_interp[np.argmin(np.abs(id_interp - img))]
        
        return {
            'vth': vth,
            'id_th': id_th,
            'beta': beta,
            'ido_vd': ido_vd,
            'img': img,
            'vmg': vmg
        }
        
    except Exception as e:
        st.error(f"文件解析错误: {str(e)}")
        return None

def show_analysis_result(title, data):
    """显示单次分析结果"""
    st.subheader(title)
    cols = st.columns(2)
    cols[0].metric("阈值电压Vth", f"{data['vth']:.3f} V")
    cols[1].metric("阈值电流Id(th)", f"{data['id_th']:.2e} A")
    
    cols = st.columns(2)
    cols[0].metric("β值", f"{data['beta']:.2e} C/(J·K)")
    cols[1].metric("Ido(Vd)", f"{data['ido_vd']:.2e} A")
    
    cols = st.columns(2)
    cols[0].metric("计算Img", f"{data['img']:.2e} A") 
    cols[1].metric("对应Vmg", f"{data['vmg']:.3f} V")
    
    # 绘制特征曲线
    fig, ax = plt.subplots()
    ax.semilogy(data['vg'], data['id'], 'b-', label='I_d')
    ax.axvline(x=data['vth'], color='r', linestyle='--', label='Vth')
    ax.axhline(y=data['img'], color='g', linestyle=':', label='Img')
    ax.set_xlabel("Gate Voltage (V)")
    ax.set_ylabel("Drain Current (A)")
    ax.legend()
    st.pyplot(fig)
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
