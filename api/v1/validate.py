# app/api/v1/validate.py

from fastapi import APIRouter, Depends, HTTPException, Request
from services.oas_service import OASService
from core.deps import get_settings
from core.logging import logger
from schemas.requests import QueryRequest
from schemas.responses import QueryResponse
from models.chat import ChatMessage

# from llm.chat_chain import build_chat_chain  # for future LLM-based path
from fastapi import status

router = APIRouter()


@router.post("/validate")
def validate(
    request: Request,
    payload: QueryRequest,
    settings=Depends(get_settings),
):
    """
    Endpoint to validate an OpenAPI spec and return HTML-formatted suggestions.
    If FEATURE_FLAGS includes "oas_llm", use an LLM-based check (placeholder).
    Otherwise, run static JSON-Schema validation via OASService.
    """

    spec_content = payload.content
    spec_content = spec_content.strip().replace("\t", "")

    # 1) Static validation path
    try:
        service = OASService()
        load_data = service.yaml_to_json(spec_content)

        if isinstance(load_data, str):
            # If YAML parsing failed, return error
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"YAML parsing error: Please provide a valid YAML string. Error: {load_data}",
            )
    except Exception as e:
        logger.error("Failed to parse YAML", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"YAML parsing error: {str(e)}",
        )

    logger.info(f"Loaded data: {load_data}")

    try:
        service.validate_spec(load_data)
    except Exception as e:
        logger.error("OpenAPI Specification validation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OpenAPI Specification validation error: {str(e)}",
        )

    llm_response = service.run_oas_check_llm(load_data)
    if llm_response:
        return QueryResponse(messages=[llm_response])
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during LLM-based validation",
        )
