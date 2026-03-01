import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import RAGSystem

st.set_page_config(
    page_title="鸣潮剧情RAG助手",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🎮 鸣潮剧情RAG助手")
st.markdown("---")

# API密钥输入
with st.expander("🔑 设置API密钥", expanded=False):
    api_key = st.text_input(
        "Moonshot API密钥",
        type="password",
        placeholder="sk-...",
        help="输入你的Moonshot API密钥，不会被保存"
    )
    
    if api_key:
        os.environ["MOONSHOT_API_KEY"] = api_key
        st.success("✅ API密钥已设置")
        st.info("⚠️ 密钥仅在当前会话有效，刷新页面后需要重新输入")
    else:
        st.warning("⚠️ 请设置API密钥以使用本应用")
        st.markdown("""
        **如何获取API密钥：**
        1. 访问 https://platform.moonshot.cn
        2. 注册/登录账号
        3. 进入API密钥页面
        4. 创建新密钥
        5. 复制密钥到此处
        """)

@st.cache_resource
def initialize_rag_system():
    try:
        rag_system = RAGSystem()
        rag_system.initialize_system()
        rag_system.build_knowledge_base()
        return rag_system
    except Exception as e:
        st.error(f"❌ RAG系统初始化失败: {e}")
        return None

# 检查是否有API密钥
has_api_key = bool(os.getenv("MOONSHOT_API_KEY"))

if not has_api_key:
    st.warning("⚠️ 请先设置API密钥才能使用问答功能")
    st.stop()

if 'rag_system' not in st.session_state or not st.session_state.rag_system:
    with st.spinner("🔄 正在初始化RAG系统，请稍候..."):
        st.session_state.rag_system = initialize_rag_system()
        if st.session_state.rag_system:
            st.success("✅ RAG系统初始化成功！")
        else:
            st.error("❌ RAG系统初始化失败，请检查API密钥")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.markdown("### 💡 使用说明")
st.markdown("""
- 输入关于鸣潮游戏剧情的问题
- 支持查询角色信息、剧情事件、章节内容等
- 可以询问角色首次/最后出现的位置
- 示例问题：
  - "炽霞第一次出现"
  - "秧秧和谁是一对？"
  - "第一章发生了什么？"
""")

st.markdown("---")

user_input = st.chat_input(
    "🙋 请输入你的问题：",
    key="user_input"
)

if user_input and user_input.strip():
    if st.session_state.rag_system:
        with st.spinner("🤖 正在思考..."):
            try:
                answer = st.session_state.rag_system.ask_question(user_input.strip(), stream=False)
                st.session_state.chat_history.append({
                    'question': user_input.strip(),
                    'answer': answer
                })
                st.rerun()
            except Exception as e:
                st.error(f"❌ 处理问题时出错: {e}")
    else:
        st.error("❌ RAG系统未初始化")

st.markdown("---")

if st.session_state.chat_history:
    st.markdown("### 💬 对话历史")
    
    for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
        with st.chat_message("user"):
            st.write(f"🙋 {chat['question']}")
        
        with st.chat_message("assistant"):
            st.write(f"🤖 {chat['answer']}")
        
        if i < len(st.session_state.chat_history):
            st.markdown("---")

if st.button("🗑️ 清空对话历史"):
    st.session_state.chat_history = []
    st.rerun()

st.markdown("---")
st.markdown("### 📊 系统信息")
if st.session_state.rag_system:
    st.info("✅ RAG系统运行正常")
else:
    st.error("❌ RAG系统未运行")