# app/api/v1/oas.py

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import HTMLResponse
from services.oas_service import OASService, ValidationReport
from core.deps import get_settings
from errors import OASValidationError, ChatServiceError
import yaml
from core.logging import logger
from core.deps import get_chat_service
from models.chat import QueryRequest, QueryResponseValidation

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
        return QueryResponseValidation(content=llm_response)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during LLM-based validation",
        )
