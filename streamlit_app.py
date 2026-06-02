import streamlit as st
import time
import math
import random

# --- 页面配置 ---
st.set_page_config(page_title="哲学家进餐可视化", layout="wide")
st.title("🍝 哲学家进餐并发调度系统")

N = 5

# --- 初始化 Session State (状态机核心) ---
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.running = False
    # 状态码: 0=思考, 1=饿了试图拿第一把, 2=拿到一把试图拿第二把, 3=进餐中
    st.session_state.states = [0] * N 
    # 记录叉子被谁占用: -1代表闲置，0~4代表被对应哲学家占用
    st.session_state.forks = [-1] * N 
    # 每个哲学家的计时器，模拟执行时间
    st.session_state.ticks = [0] * N

# --- 核心算法：状态机步进 (模拟并发逻辑) ---
def update_logic():
    for i in range(N):
        left = i
        right = (i + 1) % N
        
        # 非对称防死锁分配：偶数先左后右，奇数先右后左
        first_fork = left if i % 2 == 0 else right
        second_fork = right if i % 2 == 0 else left

        state = st.session_state.states[i]

        # [状态 0] 思考中
        if state == 0:
            st.session_state.ticks[i] += 1
            if st.session_state.ticks[i] > random.randint(5, 10):
                st.session_state.states[i] = 1 # 饿了
                st.session_state.ticks[i] = 0

        # [状态 1] 试图拿第一把餐具
        elif state == 1:
            if st.session_state.forks[first_fork] == -1: # 如果第一把餐具闲置
                st.session_state.forks[first_fork] = i   # 抢占资源
                st.session_state.states[i] = 2           # 状态升级

        # [状态 2] 试图拿第二把餐具
        elif state == 2:
            if st.session_state.forks[second_fork] == -1: # 如果第二把餐具也闲置
                st.session_state.forks[second_fork] = i   # 抢占资源
                st.session_state.states[i] = 3            # 开始进餐！
                st.session_state.ticks[i] = 0

        # [状态 3] 进餐中
        elif state == 3:
            st.session_state.ticks[i] += 1
            if st.session_state.ticks[i] > 8: # 吃饱了
                st.session_state.forks[first_fork] = -1   # 放下第一把
                st.session_state.forks[second_fork] = -1  # 放下第二把
                st.session_state.states[i] = 0            # 回去思考
                st.session_state.ticks[i] = 0

# --- 实时 SVG 圆桌渲染引擎 ---
def render_round_table():
    svg = '<svg width="600" height="500" xmlns="http://www.w3.org/2000/svg">'
    cx, cy = 300, 250
    
    svg += f'<circle cx="{cx}" cy="{cy}" r="120" fill="#EAEAEA" stroke="#CCCCCC" stroke-width="5"/>'
    svg += f'<text x="{cx-35}" y="{cy+5}" font-size="18" fill="#888" font-weight="bold">🍝 餐桌</text>'

    # 画餐具
    for i in range(N):
        angle = math.radians(i * 72 - 90 + 36)
        x = cx + 85 * math.cos(angle)
        y = cy + 85 * math.sin(angle)
        
        is_occupied = st.session_state.forks[i] != -1
        fork_color = "#FF4B4B" if is_occupied else "#A0AEC0"
        svg += f'<circle cx="{x}" cy="{y}" r="14" fill="{fork_color}" />'
        svg += f'<text x="{x-7}" y="{y+4}" font-size="12" fill="white" font-weight="bold">F{i}</text>'

    # 画哲学家
    state_texts = {0: "思考中", 1: "等第1把", 2: "等第2把", 3: "进餐中!"}
    for i in range(N):
        angle = math.radians(i * 72 - 90)
        x = cx + 180 * math.cos(angle)
        y = cy + 180 * math.sin(angle)
        
        state_code = st.session_state.states[i]
        
        if state_code == 3: color = "#00CC66"      # 绿
        elif state_code in [1, 2]: color = "#FFA500" # 橙
        else: color = "#4B8BBE"                      # 蓝
            
        svg += f'<circle cx="{x}" cy="{y}" r="35" fill="{color}" />'
        svg += f'<text x="{x-11}" y="{y-2}" font-size="16" fill="white" font-weight="bold">P{i}</text>'
        svg += f'<text x="{x-22}" y="{y+18}" font-size="14" fill="white" font-weight="bold">{state_texts[state_code]}</text>'
        
    svg += '</svg>'
    return svg

# --- 侧边栏与控制 ---
with st.sidebar:
    st.header("控制面板 ⚙️")
    st.markdown("**图例说明：**\n* 🟢 **绿色**：正在进餐\n* 🟠 **橙色**：饥饿等待\n* 🔵 **蓝色**：正在思考\n* 🔴 **红色小圆点**：餐具被占用")
    
    if st.button("▶️ 极速启动", use_container_width=True) and not st.session_state.running:
        st.session_state.running = True
        st.rerun()

    if st.button("⏹️ 停止运行", use_container_width=True) and st.session_state.running:
        st.session_state.running = False
        st.session_state.states = [0] * N
        st.session_state.forks = [-1] * N
        st.rerun()

# --- 主界面渲染 ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.components.v1.html(render_round_table(), height=550)
st.markdown("</div>", unsafe_allow_html=True)

# --- 稳定的状态机时钟引擎 ---
if st.session_state.running:
    update_logic()  # 步进一次状态
    time.sleep(2) # 稳定帧率
    st.rerun()      # 刷新页面