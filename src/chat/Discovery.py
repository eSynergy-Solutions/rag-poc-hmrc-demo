"""a class that implements SimpleRAG but uses a different prompt and handles the weird HMRC vector database chunking stuff"""

from src.loaders import hmrcLoader1
from src.chat.HistoryRAG import HistoryRAG
from src.prompts import DiscoveryPrompt_v2
import yaml
from openapi_spec_validator import validate

# Chat -> SimpleRAG -> HistoryRAG -> HMRCRag
# Chat -> SimpleRAG -> HistoryRAG -> Discovery


class DiscoveryRAGChat(HistoryRAG):
    systemprompt = {
        "role": "system",
        "content": DiscoveryPrompt_v2,
    }

    def yaml_to_json(self, yaml_string):
        """
        Convert a YAML string to JSON string

        Parameters:
        yaml_string (str): The YAML content as a string

        Returns:
        str: The converted JSON string
        """
        try:
            # Parse YAML string to Python dictionary
            yaml_dict: dict = yaml.safe_load(yaml_string)
            return yaml_dict
        except Exception as e:
            return f"Error converting YAML to JSON: {str(e)}"

    def validate_oas_spec(self, oas_spec: dict) -> bool:
        """
        Validate an OpenAPI Specification (OAS) string.

        Args:
            oas_spec (dict): The OAS content as a dict.

        Returns:
            bool: True if the OAS is valid, False otherwise.
        """
        try:
            # Parse the OAS spec
            # Validate the OAS spec
            validate(oas_spec)
            return True
        except Exception:
            return False

    def retrieve(self, input: str, chunk_limit: int = 1):
        """
        This retriever will return a description of one api plus at most `chunk_limit` YAML specifications of endpoints"""
        return hmrcLoader1.retrieve(input, endpoint_limit=chunk_limit)
