# app/llm/single_call.py

# import os
from fastapi import HTTPException
from llm.gailz_llm import GailzLLM
# from langchain_openai import AzureChatOpenAI

# from llm.prompts import standard_rag_system_prompt


# def build_chat_instance(
#     endpoint: str,
#     api_key: str,
#     deployment: str,
# ) -> AzureChatOpenAI:
def build_chat_instance(
    base_url, deployment, misc_string, deployment_version, deployment_model, logger
):
    """
    Provides a chat service that does not require a vector store.
    This is useful for scenarios where chat capabilities are needed
    without retrieval from a vector store.
    """

    # api_version = os.getenv("OPENAI_API_VERSION", None)
    # if api_version is None:
    #     raise ValueError(
    #         "OPENAI_API_VERSION environment variable must be set for AzureChatOpenAI"
    #     )

    try:
        llm = GailzLLM(
            base_url,
            deployment,
            misc_string,
            deployment_version,
            deployment_model,
            logger,
        )

        # llm = AzureChatOpenAI(
        #     azure_deployment=deployment,
        #     azure_endpoint=str(endpoint),
        #     openai_api_key=api_key,
        #     api_version=api_version,
        #     temperature=0.2,
        #     verbose=False,
        # )

        return llm
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to initialise Azure client")
