# 🎮 鸣潮剧情RAG助手

基于Streamlit的鸣潮游戏剧情问答系统，支持角色信息查询、剧情事件检索、章节内容分析等功能。

## ✨ 功能特点

- 🤖 智能问答：基于RAG技术的剧情问答
- 🎯 精准检索：混合向量检索+BM25关键词检索
- 📊 结构化提取：自动识别角色、地点、章节等实体
- 💬 对话历史：保存和查看对话记录
- 🚀 实时响应：支持Enter键快速提问

## 🚀 在线体验

### Streamlit Cloud部署
访问：[https://your-app.streamlit.app](https://your-app.streamlit.app)

### Hugging Face Spaces
访问：[https://huggingface.co/spaces/your-username/your-app](https://huggingface.co/spaces/your-username/your-app)

## 📦 本地部署

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-username/mc_rag.git
cd mc_rag
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入你的MOONSHOT_API_KEY
```

5. **准备数据**
将剧情数据文件放入`md_output/`目录

6. **启动应用**
```bash
streamlit run streamlit_app.py
```

7. **访问应用**
打开浏览器访问：http://localhost:8501

## 🔧 配置说明

### 环境变量
- `MOONSHOT_API_KEY`: Moonshot AI API密钥（必需）

### 数据目录
- `md_output/`: 剧情数据文件目录
- `index/`: 向量索引缓存目录

## 📖 使用说明

### 基本使用
1. 在输入框中输入问题
2. 按Enter键或点击发送
3. 等待系统分析并返回答案

### 示例问题
- "炽霞第一次出现"
- "秧秧和谁是一对？"
- "第一章发生了什么？"
- "漂泊者最恨谁？"

### 功能说明
- **角色查询**：查询角色信息、关系、出现位置
- **剧情检索**：检索特定章节的事件和对话
- **推理分析**：分析角色关系和情感倾向

## 🌐 部署到云端

### Streamlit Cloud（推荐）
1. 将代码上传到GitHub
2. 访问 https://share.streamlit.io
3. 连接GitHub账号并选择仓库
4. 配置环境变量`MOONSHOT_API_KEY`
5. 点击部署

### Hugging Face Spaces
1. 创建Hugging Face账号
2. 新建Space，选择Streamlit
3. 上传代码文件
4. 在Settings中配置Secrets
5. 自动部署

## 📝 技术栈

- **前端**: Streamlit
- **后端**: Python
- **LLM**: Moonshot AI
- **向量检索**: FAISS
- **关键词检索**: BM25
- **框架**: LangChain

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

如有问题，请提交Issue或联系作者。

---

⭐ 如果觉得有用，请给个Star！