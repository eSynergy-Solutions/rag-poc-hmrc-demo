"""a class that implements SimpleRAG but uses a different prompt and handles the weird HMRC vector database chunking stuff"""

from src.loaders import hmrcLoader1
from src.chat.HistoryRAG import HistoryRAG
from src.prompts import DiscoveryPrompt_v2

# Chat -> SimpleRAG -> HistoryRAG -> HMRCRag
# Chat -> SimpleRAG -> HistoryRAG -> Discovery


class DiscoveryRAGChat(HistoryRAG):
    systemprompt = {
        "role": "system",
        "content": DiscoveryPrompt_v2,
    }

    def retrieve(self, input: str, chunk_limit: int = 1):
        """
        This retriever will return a description of one api plus at most `chunk_limit` YAML specifications of endpoints"""
        return hmrcLoader1.retrieve(input, endpoint_limit=chunk_limit)
