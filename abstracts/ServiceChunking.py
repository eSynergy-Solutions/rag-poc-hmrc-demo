from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseChunker(ABC):
    """
    Abstract base class for any spec/document chunker
    """

    @abstractmethod
    def chunk(self, input_data: str, spec_id: str) -> List[Dict[str, Any]]:
        """
        Takes raw input (usually a string), returns list of chunks.
        Each chunk is a dictionary with at least:
        - id
        - type
        - name
        - spec_id
        - content
        """
        pass
