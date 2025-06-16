from abc import ABC, abstractmethod
from models.oas import ValidationReport


class ServiceOAS(ABC):
    """
    Service for validating (and optionally diffing) OpenAPI Specification content.
    - Performs YAML parsing fallback
    - Runs JSON Schema validation
    - If "oas_llm" is in settings.FEATURE_FLAGS, calls Azure OpenAI to produce an HTML diff.
    """

    @abstractmethod
    def validate_spec(self, spec_str: str) -> ValidationReport:
        # 1. Attempt full ResolvingParser; if that fails, fallback to yaml.safe_load
        pass
