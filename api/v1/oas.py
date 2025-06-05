# app/api/v1/oas.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.models.chat import QueryRequest
from app.services.oas_service import OASService, ValidationReport
from app.core.deps import get_settings
from app.errors import OASValidationError, ChatServiceError
from app.llm.chat_chain import build_chat_chain  # for future LLM-based path
from fastapi import status

router = APIRouter()


@router.post("/oas-check", response_class=HTMLResponse)
def oas_check(
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

    # If LLM-based OAS checking is turned on, route through a LangChain chain
    if "oas_llm" in settings.FEATURE_FLAGS:
        # Placeholder: in the future, replace with actual LLM-based validation
        # e.g. llm_chain = build_chat_chain(...)
        #       return HTMLResponse(content=llm_chain.run_oas_check(spec_content))
        # For now, fall back to static validation
        pass

    # 1) Static validation path
    try:
        service = OASService()
        report: ValidationReport = service.validate_spec(spec_content)

        if not report.valid:
            # Raise an exception carrying the list of errors
            raise OASValidationError(report.errors)

        # If valid but diff_html is provided, return it
        if report.diff_html:
            return HTMLResponse(content=report.diff_html, status_code=status.HTTP_200_OK)

        # Otherwise, success message
        return HTMLResponse(
            content="<h2>Specification is valid. No changes required.</h2>",
            status_code=status.HTTP_200_OK,
        )

    except OASValidationError as ov:
        # Render errors as HTML list and return 400
        errors_html = "<ul>" + "".join(f"<li>{e}</li>" for e in ov.errors) + "</ul>"
        return HTMLResponse(
            content=("<h2>Specification Validation Failed</h2>" + errors_html),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ChatServiceError as cse:
        # If LLM path threw a ChatServiceError
        raise HTTPException(status_code=502, detail=str(cse))
    except Exception as e:
        # Unexpected error in validation
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
