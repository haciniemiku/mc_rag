
import logging
from typing import List, Optional
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IndexConstructionModule:
    """索引构建模块 - 负责向量化和索引构建"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5",
                 index_save_path: str = "./vector_index"):
        self.model_name = model_name
        self.index_save_path = index_save_path
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.vectorstore: Optional[FAISS] = None
        self.setup_embeddings()

    def setup_embeddings(self):
        """初始化嵌入模型"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"✅ 嵌入模型初始化成功: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ 嵌入模型初始化失败: {e}")
            raise

    def build_vector_index(self, chunks: List[Document]) -> FAISS:
        """构建向量索引"""
        if not chunks:
            raise ValueError("文档块列表不能为空")

        try:
            # 提取文本内容
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            # 构建FAISS向量索引
            self.vectorstore = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            logger.info(f"✅ 向量索引构建成功，包含 {len(chunks)} 个文档块")
            return self.vectorstore
        except Exception as e:
            logger.error(f"❌ 构建向量索引失败: {e}")
            raise

    def save_index(self):
        """保存向量索引到配置的路径"""
        if not self.vectorstore:
            raise ValueError("请先构建向量索引")

        try:
            # 确保保存目录存在
            Path(self.index_save_path).mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(self.index_save_path)
            logger.info(f"✅ 向量索引保存成功: {self.index_save_path}")
        except Exception as e:
            logger.error(f"❌ 保存向量索引失败: {e}")
            raise

    def load_index(self) -> Optional[FAISS]:
        """从配置的路径加载向量索引"""
        if not self.embeddings:
            self.setup_embeddings()

        if not Path(self.index_save_path).exists():
            logger.info(f"⚠️ 索引路径不存在: {self.index_save_path}")
            return None

        try:
            self.vectorstore = FAISS.load_local(
                self.index_save_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"✅ 向量索引加载成功: {self.index_save_path}")
            return self.vectorstore
        except Exception as e:
            logger.error(f"❌ 加载向量索引失败: {e}")
            return None
