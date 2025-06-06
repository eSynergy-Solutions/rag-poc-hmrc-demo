# app/tests/unit/test_oas_service.py

import pytest
import yaml
import importlib
from services.oas_service import OASService, ValidationReport
from errors import OASValidationError
from openapi_schema_validator import OAS30Validator


@pytest.fixture(autouse=True)
def clear_feature_flags(monkeypatch):
    """
    Ensure that FEATURE_FLAGS does not inadvertently include 'oas_llm'
    unless explicitly set in the test.
    """
    # Reload config so we have a fresh Settings instance
    import core.config as config_mod

    importlib.reload(config_mod)
    from core.config import settings

    # Backup existing flags (though after reload, this is a new Settings)
    orig_flags = settings.FEATURE_FLAGS.copy()
    settings.FEATURE_FLAGS.clear()
    yield
    settings.FEATURE_FLAGS[:] = orig_flags


def test_validate_spec_valid_minimal():
    """
    A minimal valid OpenAPI spec should pass without exception,
    returning ValidationReport(valid=True).
    """
    service = OASService()
    spec = """
openapi: 3.0.0
info:
  title: My API
  version: '1.0'
paths: {}
"""
    report: ValidationReport = service.validate_spec(spec)
    assert report.valid is True
    assert report.errors == []
    assert report.diff_html is None


def test_validate_spec_missing_openapi_raises_error():
    """
    Missing the top-level 'openapi' field should raise OASValidationError
    with the appropriate error message.
    """
    service = OASService()
    spec = """
info:
  title: My API
  version: '1.0'
paths: {}
"""
    with pytest.raises(OASValidationError) as exc_info:
        _ = service.validate_spec(spec)
    err = exc_info.value
    assert isinstance(err.errors, list)
    assert "Missing required 'openapi' field" in err.errors[0]


def test_validate_spec_bad_yaml_raises_error():
    """
    Unparsable YAML should raise OASValidationError indicating parse failure.
    """
    service = OASService()
    bad = "::: not a spec :::"
    with pytest.raises(OASValidationError) as exc_info:
        _ = service.validate_spec(bad)
    err = exc_info.value
    # Expect error message containing 'Failed to parse spec'
    assert any("Failed to parse spec" in e for e in err.errors)


def test_validate_spec_schema_errors_raise_with_paths_info():
    """
    Valid YAML but invalid OpenAPI schema (e.g., paths not being an object)
    should raise OASValidationError, and errors list should mention 'paths'.
    """
    service = OASService()
    spec = """
openapi: 3.0.0
info:
  title: Test
  version: '1.0'
paths:
  /ping: 123
"""
    with pytest.raises(OASValidationError) as exc_info:
        _ = service.validate_spec(spec)
    err = exc_info.value
    # At least one error should mention 'paths'
    assert any("paths" in e for e in err.errors)


def test_llm_based_diff_applies_when_flag_set(monkeypatch):
    """
    If FEATURE_FLAGS includes 'oas_llm', then on schema errors, OASService
    should attempt an LLM-based diff and set ValidationReport.diff_html
    to the returned HTML. We simulate AzureOpenAI returning dummy content.
    """
    # 1) Reload config and oas_service so settings inside oas_service is fresh
    import core.config as config_mod

    importlib.reload(config_mod)
    from core.config import settings

    import services.oas_service as oas_mod

    importlib.reload(oas_mod)
    from services.oas_service import OASService

    # Enable the feature flag on the fresh settings
    settings.FEATURE_FLAGS.clear()
    settings.FEATURE_FLAGS.append("oas_llm")

    # 2) Monkeypatch AzureOpenAI in the freshly reloaded oas_service module
    class FakeLLMResponse:
        class Choice:
            def __init__(self, content):
                self.message = type("M", (), {"content": content})

        def __init__(self, html_text: str):
            self.choices = [self.Choice(html_text)]

    class FakeAzureOpenAI:
        def __init__(self, azure_endpoint, api_key, api_version):
            pass

        def chat(self):
            return self

        def completions(self):
            return self

        def create(self, **kwargs):
            return FakeLLMResponse("<h2>Diff: missing field 'info.description'</h2>")

    monkeypatch.setattr(oas_mod, "AzureOpenAI", FakeAzureOpenAI)

    # 3) Call validate_spec with a spec missing 'paths' to trigger errors
    service = OASService()
    invalid_spec = """
openapi: 3.0.0
info:
  title: Test
  version: '1.0'
# Note: 'paths' is omitted to trigger validation error
"""
    with pytest.raises(OASValidationError) as exc_info:
        _ = service.validate_spec(invalid_spec)

    err = exc_info.value
    # diff_html should reflect our FakeLLMResponse
    assert err.diff_html == "<h2>Diff: missing field 'info.description'</h2>"
