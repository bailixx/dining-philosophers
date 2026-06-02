import streamlit as st
import threading
import time

# 页面配置
st.set_page_config(page_title="哲学家进餐可视化演示", layout="wide")
st.title("🍝 哲学家进餐并发调度系统 (非对称防死锁版)")

# 常量定义
N = 5

# --- 1. 初始化 Session State (保证每次刷新页面状态不丢失) ---
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.running = False
    st.session_state.states = ['思考中 🧠'] * N
    st.session_state.forks = ['闲置 🍴'] * N
    st.session_state.locks = [threading.Lock() for _ in range(N)]
    st.session_state.threads = []
    st.session_state.logs = []

# --- 2. 核心算法：哲学家的多线程逻辑 ---
def philosopher_logic(id):
    left = id
    right = (id + 1) % N
    
    while st.session_state.running:
        # 思考阶段
        st.session_state.states[id] = '思考中 🧠'
        time.sleep(2) # 模拟思考
        
        if not st.session_state.running:
            break
            
        # 饥饿阶段
        st.session_state.states[id] = '饥饿，等待餐具 🤤'
        
        # 【核心】非对称破除死锁算法
        if id % 2 == 0:
            # 偶数先锁左（刀），再锁右（叉）
            with st.session_state.locks[left]:
                st.session_state.forks[left] = f'🔴 被 P{id} 拿作刀'
                add_log(f"偶数哲学家 P{id} 拿起了左手的刀 (资源 {left})")
                time.sleep(0.5) # 刻意制造延迟，暴露并发冲突
                
                with st.session_state.locks[right]:
                    st.session_state.forks[right] = f'🔴 被 P{id} 拿作叉'
                    add_log(f"偶数哲学家 P{id} 拿起了右手的叉 (资源 {right})")
                    
                    # 进餐阶段
                    st.session_state.states[id] = '进餐中 🍝'
                    time.sleep(3) # 模拟进餐
                    
                    st.session_state.forks[right] = '闲置 🍴'
            st.session_state.forks[left] = '闲置 🍴'
        else:
            # 奇数先锁右（叉），再锁左（刀）
            with st.session_state.locks[right]:
                st.session_state.forks[right] = f'🔴 被 P{id} 拿作叉'
                add_log(f"奇数哲学家 P{id} 拿起了右手的叉 (资源 {right})")
                time.sleep(0.5)
                
                with st.session_state.locks[left]:
                    st.session_state.forks[left] = f'🔴 被 P{id} 拿作刀'
                    add_log(f"奇数哲学家 P{id} 拿起了左手的刀 (资源 {left})")
                    
                    # 进餐阶段
                    st.session_state.states[id] = '进餐中 🍝'
                    time.sleep(3) # 模拟进餐
                    
                    st.session_state.forks[left] = '闲置 🍴'
            st.session_state.forks[right] = '闲置 🍴'
            
        add_log(f"哲学家 P{id} 吃饱了，放下所有餐具。")

def add_log(msg):
    st.session_state.logs.insert(0, time.strftime("%H:%M:%S") + " - " + msg)
    if len(st.session_state.logs) > 15:
        st.session_state.logs.pop()

# --- 3. 侧边栏控制面板 ---
with st.sidebar:
    st.header("控制面板 ⚙️")
    if st.button("▶️ 启动并发模拟", use_container_width=True) and not st.session_state.running:
        st.session_state.running = True
        st.session_state.logs.clear()
        add_log("系统启动：开启 5 个并发线程...")
        for i in range(N):
            t = threading.Thread(target=philosopher_logic, args=(i,), daemon=True)
            st.session_state.threads.append(t)
            t.start()
        st.rerun()

    if st.button("⏹️ 停止模拟", use_container_width=True) and st.session_state.running:
        st.session_state.running = False
        add_log("系统停止：向所有线程发送终止信号...")
        st.session_state.threads.clear()
        # 强制重置界面状态
        time.sleep(1)
        st.session_state.states = ['思考中 🧠'] * N
        st.session_state.forks = ['闲置 🍴'] * N
        st.rerun()

# --- 4. 前端可视化渲染 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("餐桌实时监控看板 📊")
    
    # 渲染哲学家状态卡片
    cols = st.columns(N)
    for i in range(N):
        with cols[i]:
            state = st.session_state.states[i]
            if "进餐中" in state:
                st.success(f"**P{i}**\n\n{state}")
            elif "等待" in state:
                st.warning(f"**P{i}**\n\n{state}")
            else:
                st.info(f"**P{i}**\n\n{state}")

    st.markdown("---")
    st.subheader("公用资源池 (刀叉) 状态 🔧")
    
    # 渲染资源（刀叉）状态卡片
    fork_cols = st.columns(N)
    for i in range(N):
        with fork_cols[i]:
            fork_state = st.session_state.forks[i]
            if "闲置" in fork_state:
                st.info(f"**资源 {i}**\n\n{fork_state}")
            else:
                st.error(f"**资源 {i}**\n\n{fork_state}")

with col2:
    st.subheader("系统调度日志 📝")
    log_container = st.container(height=400)
    for log in st.session_state.logs:
        log_container.text(log)

# --- 5. 自动刷新机制 (让网页动起来) ---
if st.session_state.running:
    time.sleep(0.5) # 每 0.5 秒刷新一次前端界面
    st.rerun()