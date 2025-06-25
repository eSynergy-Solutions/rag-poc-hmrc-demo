# app/api/v1/validate.py

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from services.validation_service import OASService
from core.deps import get_settings
from core.custom_logging import logger
from schemas.requests import QueryRequest
from schemas.responses import QueryResponse

# from llm.chat_chain import build_chat_chain  # for future LLM-based path
from fastapi import status

router = APIRouter()

response_examples = {
    200: {
        "description": "Successful validation response",
        "content": {
            "application/json": {
                "examples": {
                    "BasicSuccess": {
                        "summary": "Valid OpenAPI spec with suggestions",
                        "value": {
                            "messages": [
                                {
                                    "role": "assistant",
                                    "content": "The OpenAPI spec is valid, but consider removing extra line breaks in the info.description.",
                                }
                            ]
                        },
                    }
                }
            }
        },
    },
    422: {
        "description": "Validation error",
        "content": {
            "application/json": {
                "examples": {
                    "MissingContent": {
                        "summary": "Missing 'content' field",
                        "value": {
                            "detail": [
                                {
                                    "loc": ["body", "content"],
                                    "msg": "field required",
                                    "type": "value_error.missing",
                                }
                            ]
                        },
                    }
                }
            }
        },
    },
}


@router.post(
    "/validate",
    response_model=QueryResponse,
    responses=response_examples,
)
def validate(
    request: Request,
    payload: QueryRequest = Body(
        ...,
        examples=[
            {
                "content": "openapi: 3.0.3\ninfo:\n  title: Hello World API\n  version: '1.0'\npaths:....",
                "streaming": False,
            },
        ],
    ),
    settings=Depends(get_settings),
):
    """
    Endpoint to validate an OpenAPI spec and return YAML formatted suggestions.
    Run static validation first, then LLM-based suggestions.
    This endpoint does not maintain state or conversation history.
    It expects a valid OpenAPI spec in YAML format as input.
    The response will be a YAML formatted string with suggestions or errors.
    If the input is not a valid OpenAPI spec, it will return an error.
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
