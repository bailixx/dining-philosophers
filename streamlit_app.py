import streamlit as st
import threading
import time
import math
from streamlit.runtime.scriptrunner import add_script_run_ctx # 🔴 修复核心1：引入上下文管理器

# --- 页面配置 ---
st.set_page_config(page_title="哲学家进餐可视化 (圆桌版)", layout="wide")
st.title("🍝 哲学家进餐并发调度系统 - 沉浸式圆桌版")

N = 5

# --- 初始化 Session State ---
if 'init' not in st.session_state:
    st.session_state.running = False
    st.session_state.states = ['思考中'] * N
    st.session_state.forks = ['闲置'] * N
    st.session_state.locks = [threading.Lock() for _ in range(N)]
    st.session_state.threads = []

# --- 核心算法：多线程逻辑 ---
def philosopher_logic(id):
    left = id
    right = (id + 1) % N
    
    while st.session_state.running:
        st.session_state.states[id] = '思考中'
        time.sleep(0.3)
        
        if not st.session_state.running: break
            
        st.session_state.states[id] = '等待餐具'
        
        # 核心：非对称破除死锁算法
        if id % 2 == 0:
            with st.session_state.locks[left]:
                st.session_state.forks[left] = f'P{id}占用'
                time.sleep(0.1) 
                with st.session_state.locks[right]:
                    st.session_state.forks[right] = f'P{id}占用'
                    st.session_state.states[id] = '进餐中'
                    time.sleep(0.6) 
                    st.session_state.forks[right] = '闲置'
            st.session_state.forks[left] = '闲置'
        else:
            with st.session_state.locks[right]:
                st.session_state.forks[right] = f'P{id}占用'
                time.sleep(0.1)
                with st.session_state.locks[left]:
                    st.session_state.forks[left] = f'P{id}占用'
                    st.session_state.states[id] = '进餐中'
                    time.sleep(0.6)
                    st.session_state.forks[left] = '闲置'
            st.session_state.forks[right] = '闲置'

# --- 实时 SVG 圆桌渲染引擎 ---
def render_round_table():
    svg = '<svg width="600" height="500" xmlns="http://www.w3.org/2000/svg">'
    cx, cy = 300, 250
    
    svg += f'<circle cx="{cx}" cy="{cy}" r="120" fill="#EAEAEA" stroke="#CCCCCC" stroke-width="5"/>'
    svg += f'<text x="{cx-35}" y="{cy+5}" font-size="18" fill="#888" font-weight="bold">🍝 餐桌</text>'

    for i in range(N):
        angle = math.radians(i * 72 - 90 + 36)
        x = cx + 85 * math.cos(angle)
        y = cy + 85 * math.sin(angle)
        
        fork_color = "#FF4B4B" if "占用" in st.session_state.forks[i] else "#A0AEC0"
        svg += f'<circle cx="{x}" cy="{y}" r="14" fill="{fork_color}" />'
        svg += f'<text x="{x-7}" y="{y+4}" font-size="12" fill="white" font-weight="bold">F{i}</text>'

    for i in range(N):
        angle = math.radians(i * 72 - 90)
        x = cx + 180 * math.cos(angle)
        y = cy + 180 * math.sin(angle)
        
        state = st.session_state.states[i]
        if "进餐" in state:
            color = "#00CC66"  
        elif "等待" in state:
            color = "#FFA500"  
        else:
            color = "#4B8BBE"  
            
        svg += f'<circle cx="{x}" cy="{y}" r="35" fill="{color}" />'
        svg += f'<text x="{x-11}" y="{y-2}" font-size="16" fill="white" font-weight="bold">P{i}</text>'
        svg += f'<text x="{x-18}" y="{y+15}" font-size="12" fill="white">{state}</text>'
        
    svg += '</svg>'
    return svg

# --- 侧边栏与控制 ---
with st.sidebar:
    st.header("控制面板 ⚙️")
    st.markdown("**图例说明：**\n* 🟢 **绿色**：正在进餐\n* 🟠 **橙色**：饥饿等待\n* 🔵 **蓝色**：正在思考\n* 🔴 **红色小圆点**：餐具被占用")
    
    if st.button("▶️ 极速启动", use_container_width=True) and not st.session_state.running:
        st.session_state.running = True
        for i in range(N):
            t = threading.Thread(target=philosopher_logic, args=(i,), daemon=True)
            add_script_run_ctx(t) # 🔴 修复核心2：把主线程的访问权限赋予给各个子线程
            st.session_state.threads.append(t)
            t.start()
        st.rerun()

    if st.button("⏹️ 停止运行", use_container_width=True) and st.session_state.running:
        st.session_state.running = False
        st.session_state.threads.clear()
        time.sleep(0.5)
        st.session_state.states = ['思考中'] * N
        st.session_state.forks = ['闲置'] * N
        st.rerun()

# --- 主界面渲染 ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.components.v1.html(render_round_table(), height=550)
st.markdown("</div>", unsafe_allow_html=True)

# --- 极致的自动刷新 (约20FPS) ---
if st.session_state.running:
    time.sleep(0.05) 
    st.rerun()