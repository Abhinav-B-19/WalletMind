from __future__ import annotations

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.models import AIResponse


class StubPromptBuilder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def build_system_prompt(self, *, base_instruction, context=None):
        self.calls.append(("system", base_instruction))
        return "SYSTEM_PROMPT"

    def build_user_prompt(self, *, user_input, context=None):
        self.calls.append(("user", user_input))
        return "USER_PROMPT"


class StubGeminiClient:
    def __init__(self) -> None:
        self.request_args = None

    def build_request(self, **kwargs):
        self.request_args = kwargs
        return "REQUEST_OBJECT"

    def generate(self, request):
        assert request == "REQUEST_OBJECT"
        return AIResponse(
            text="AI output",
            model="gemini-1.5-flash",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            finish_reason="stop",
        )

    def get_configuration_status(self):
        return True, "gemini-1.5-flash", "session"


def test_ai_service_orchestration() -> None:
    prompt_builder = StubPromptBuilder()
    client = StubGeminiClient()
    service = AIService(gemini_client=client, prompt_builder=prompt_builder)

    response = service.generate(
        system_instruction="System instruction",
        user_input="User input",
        system_context={"policy": "strict"},
        user_context={"language": "en"},
        temperature=0.5,
        max_output_tokens=300,
    )

    assert response.text == "AI output"
    assert prompt_builder.calls == [
        ("system", "System instruction"),
        ("user", "User input"),
    ]
    assert client.request_args == {
        "system_prompt": "SYSTEM_PROMPT",
        "user_prompt": "USER_PROMPT",
        "temperature": 0.5,
        "max_output_tokens": 300,
    }


def test_ai_service_forwards_schema_without_mutation() -> None:
    prompt_builder = StubPromptBuilder()
    client = StubGeminiClient()
    service = AIService(gemini_client=client, prompt_builder=prompt_builder)

    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
        },
    }

    service.generate(
        system_instruction="System instruction",
        user_input="User input",
        response_schema=schema,
    )

    assert client.request_args["response_schema"] == schema
    assert client.request_args["response_schema"] is not schema


def test_ai_service_health() -> None:
    service = AIService(
        gemini_client=StubGeminiClient(),
        prompt_builder=StubPromptBuilder(),
    )

    health = service.health()

    assert health.configured is True
    assert health.model == "gemini-1.5-flash"
    assert health.status == "healthy"
    assert health.source == "session"
