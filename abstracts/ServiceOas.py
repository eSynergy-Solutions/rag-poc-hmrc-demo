from abc import ABC, abstractmethod
from models.chat import ChatMessage


class ServiceOAS(ABC):
    """
    Service for validating (and optionally diffing) OpenAPI Specification content.
    - Performs YAML parsing fallback
    - Runs JSON Schema validation
    - If "oas_llm" is in settings.FEATURE_FLAGS, calls Azure OpenAI to produce an HTML diff.
    """

    @abstractmethod
    def yaml_to_json(self, yaml_string: str) -> dict:
        """
        Convert a YAML string to JSON string

        Parameters:
        yaml_string (str): The YAML content as a string

        Returns:
        dict: The converted JSON string
        """
        pass

    @abstractmethod
    def validate_spec(self, oas_spec: dict) -> bool:
        """
        Validate an OpenAPI Specification (OAS) string.

        Args:
            oas_spec (dict): The OAS content as a dict.

        Returns:
            bool: True if the OAS is valid, False otherwise.
        """
        pass

    @abstractmethod
    def enforce_specific_fields(self, field: str, spec: dict) -> bool:
        pass

    @abstractmethod
    def run_oas_check_llm(self, oas_spec: dict) -> ChatMessage:
        pass
