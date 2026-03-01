# 🎮 鸣潮剧情RAG助手

基于Streamlit的鸣潮游戏剧情问答系统，支持角色信息查询、剧情事件检索、章节内容分析等功能。

## ✨ 功能特点

- 🤖 智能问答：基于RAG技术的剧情问答
- 🎯 精准检索：混合向量检索+BM25关键词检索
- 📊 结构化提取：自动识别角色、地点、章节等实体
- 💬 对话历史：保存和查看对话记录
- 🚀 实时响应：支持Enter键快速提问

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

4. **准备数据**
将剧情数据文件放入`md_output/`目录

6. **启动应用**
```bash
streamlit run streamlit_app.py
```

7. **访问应用**
打开浏览器访问：http://localhost:8501

## 🔧 配置说明

### API密钥
- 在应用界面中输入Moonshot API密钥
- 密钥仅在当前会话有效，刷新页面后需要重新输入
- 如何获取API密钥：
  1. 访问 https://platform.moonshot.cn
  2. 注册/登录账号
  3. 进入API密钥页面
  4. 创建新密钥
  5. 复制密钥到应用中

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