import json
import os


class LLMConfigurationError(RuntimeError):
    """Raised when a configured explanation provider cannot be created."""


class OpenAIExplanationProvider:
    """OpenAI Responses API adapter for verified explanation evidence."""

    def __init__(self, api_key, model, client_factory=None):
        self.api_key = api_key
        self.model = model
        self._client_factory = client_factory

    def _get_client(self):
        if self._client_factory is not None:
            return self._client_factory(self.api_key)

        from openai import OpenAI

        return OpenAI(api_key=self.api_key)

    def generate(self, prompt):
        response = self._get_client().responses.create(
            model=self.model,
            instructions=prompt["instruction"],
            input=json.dumps(prompt["verified_evidence"]),
            store=False,
        )

        return {"text": response.output_text}


def get_configured_provider(client_factory=None):
    provider_name = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("OPENAI_API_KEY")

    if provider_name != "openai":
        raise LLMConfigurationError("LLM_PROVIDER must be set to 'openai'.")

    if not model:
        raise LLMConfigurationError("LLM_MODEL is required.")

    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is required.")

    return OpenAIExplanationProvider(
        api_key=api_key,
        model=model,
        client_factory=client_factory,
    )


def generate_explanation(prompt, llm_function=None):
    """Generate an explanation through an injected fake or configured provider."""
    if llm_function is not None:
        return llm_function(prompt)

    return get_configured_provider().generate(prompt)
