from abc import ABC, abstractmethod
from models.chat import ChatMessage
from typing import List, Tuple


class ServiceRag(ABC):
    """
    Service for validating (and optionally diffing) OpenAPI Specification content.
    - Performs YAML parsing fallback
    - Runs JSON Schema validation
    - If "oas_llm" is in settings.FEATURE_FLAGS, calls Azure OpenAI to produce an HTML diff.
    """

    @abstractmethod
    def retrieve_and_answer(
        self,
        history: List[ChatMessage],
        user_input: str,
    ) -> Tuple[str, List[dict]]:
        pass
