import requests
from typing import List, Union, Dict, Any
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
import json


class GailzLLM(Runnable):
    """
    A class to interact with the Gailz LLM API for generating chat responses.
    Supports both LangChain prompt chains and manual message lists.
    """

    def __init__(
        self,
        base_url,
        deployment,
        misc_string,
        deployment_version,
        deployment_model,
        logger,
    ):
        self._logger = logger
        self._llm_api_string = (
            f"{base_url}/{deployment}/{misc_string}/{deployment}/{deployment_version}"
        )
        self._model = deployment_model

        self._logger.info(f"Built url:\n{self._llm_api_string}")

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        Converts LangChain SystemMessage/HumanMessage to dict format.
        """
        return [
            {
                "role": getattr(
                    m, "role", m.__class__.__name__.replace("Message", "").lower()
                ),
                "content": m.content,
            }
            for m in messages
        ]

    def chat(self, messages: List[BaseMessage], streaming: bool = False) -> dict:
        """
        Manually send messages (SystemMessage, HumanMessage, etc.).
        """
        url = self._llm_api_string

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self._model,
            "messages": self._convert_messages(messages),
            "temperature": 0.7,
            "stream": streaming,
        }

        self._logger.info(
            f"Payload:\n{json.dumps(payload)}"
        )
        self._logger.info(
            f"Headers:\n{json.dumps(headers)}"
        )

        response = requests.post(
            url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def invoke(
        self, input_data: Union[Dict[str, Any], List[BaseMessage]], config: Dict = None
    ) -> str:
        if isinstance(input_data, list):
            # Treat as direct message list
            response = self.chat(input_data)
        elif isinstance(input_data, dict):
            # Treat as LangChain-style input
            messages = [
                SystemMessage(content=input_data.get("system", "")),
                HumanMessage(content=input_data.get("user", "")),
            ]
            response = self.chat(messages)
        else:
            raise ValueError("Unsupported input type for invoke().")

        return response["choices"][0]["message"]["content"]
