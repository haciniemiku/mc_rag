import logging
from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RetrievalOptimizationModule:
    """检索优化模块 - 负责混合检索和过滤"""

    def __init__(self, vectorstore: FAISS, chunks: List[Document]):
        self.vectorstore = vectorstore
        self.chunks = chunks
        self.vector_retriever = None
        self.bm25_retriever = None
        self.setup_retrievers()

    def setup_retrievers(self):
        """设置向量检索器和BM25检索器"""
        try:
            # 向量检索器
            self.vector_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )

            # BM25检索器
            self.bm25_retriever = BM25Retriever.from_documents(
                self.chunks,
                k=5
            )
            logger.info("✅ 检索器初始化成功")
        except Exception as e:
            logger.error(f"❌ 检索器初始化失败: {e}")
            raise

    def hybrid_search(self, query: str, top_k: int = 3) -> List[Document]:
        """混合检索 - 结合向量检索和BM25检索，使用RRF重排"""
        try:
            # 分别获取向量检索和BM25检索结果
            vector_docs = self.vector_retriever.invoke(query)
            bm25_docs = self.bm25_retriever.invoke(query)

            # 使用RRF重排
            reranked_docs = self._rrf_rerank(vector_docs, bm25_docs)
            logger.info(f"✅ 混合检索完成，返回 {min(top_k, len(reranked_docs))} 个结果")
            return reranked_docs[:top_k]
        except Exception as e:
            logger.error(f"❌ 混合检索失败: {e}")
            return []

    def _rrf_rerank(self, vector_results: List[Document], bm25_results: List[Document]) -> List[Document]:
        """RRF (Reciprocal Rank Fusion) 重排"""
        # RRF融合算法
        rrf_scores = {}
        k = 60  # RRF参数

        # 计算向量检索的RRF分数
        for rank, doc in enumerate(vector_results):
            doc_id = id(doc)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        # 计算BM25检索的RRF分数
        for rank, doc in enumerate(bm25_results):
            doc_id = id(doc)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        # 合并所有文档并按RRF分数排序
        all_docs = {id(doc): doc for doc in vector_results + bm25_results}
        sorted_docs = sorted(all_docs.items(),
                             key=lambda x: rrf_scores.get(x[0], 0),
                             reverse=True)

        return [doc for _, doc in sorted_docs]

    def metadata_filtered_search(self, query: str, filters: Dict[str, Any],
                                 top_k: int = 5) -> List[Document]:
        """基于元数据过滤的检索"""
        try:
            # 先进行向量检索
            vector_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k * 3, "filter": filters}  # 扩大检索范围
            )

            results = vector_retriever.invoke(query)
            logger.info(f"✅ 元数据过滤检索完成，返回 {min(top_k, len(results))} 个结果")
            return results[:top_k]
        except Exception as e:
            logger.error(f"❌ 元数据过滤检索失败: {e}")
            return []

    def character_occurrence_search(self, character_name: str, occurrence_type: str = "first") -> List[Document]:
        """查找角色的首次或最后出现
        
        Args:
            character_name: 角色名称
            occurrence_type: "first" 或 "last"
            
        Returns:
            包含角色首次或最后出现的文档列表
        """
        try:
            # 过滤包含该角色的所有片段
            character_chunks = []
            for chunk in self.chunks:
                local_chars = chunk.metadata.get('local_characters', [])
                global_chars = chunk.metadata.get('characters', [])
                # 检查元数据中的角色列表或文本内容中是否包含角色名称
                if character_name in local_chars or character_name in global_chars or character_name in chunk.page_content:
                    character_chunks.append(chunk)
            
            if not character_chunks:
                logger.info(f"❌ 未找到角色 {character_name} 的出现")
                return []
            
            # 按章节编号、幕编号和片段索引排序
            sorted_chunks = sorted(
                character_chunks,
                key=lambda x: (
                    x.metadata.get('chapter_number', 999),
                    x.metadata.get('act_number', 999),
                    x.metadata.get('chunk_index', 999)
                )
            )
            
            # 返回首次或最后出现
            result = [sorted_chunks[0]] if occurrence_type == "first" else [sorted_chunks[-1]]
            logger.info(f"✅ 角色 {character_name} 的{'首次' if occurrence_type == 'first' else '最后'}出现检索完成")
            return result
        except Exception as e:
            logger.error(f"❌ 角色出现检索失败: {e}")
            return []
