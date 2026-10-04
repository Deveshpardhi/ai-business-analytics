
import json
import os


class LLMConfigurationError(RuntimeError):
    """Raised when a configured explanation provider cannot be created."""


class AzureOpenAIExplanationProvider:
    """Azure OpenAI adapter for verified explanation evidence."""

    def __init__(self, api_key, endpoint, model, client_factory=None):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self._client_factory = client_factory

    def _get_client(self):
        if self._client_factory is not None:
            return self._client_factory(
                self.api_key,
                self.endpoint,
            )

        from openai import OpenAI

        return OpenAI(
            api_key=self.api_key,
            base_url=f"{self.endpoint.rstrip('/')}/openai/v1/",
        )

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

    if not model:
        raise LLMConfigurationError("LLM_MODEL is required.")

    if provider_name == "azure_openai":
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

        if not api_key:
            raise LLMConfigurationError("AZURE_OPENAI_API_KEY is required.")

        if not endpoint:
            raise LLMConfigurationError("AZURE_OPENAI_ENDPOINT is required.")

        return AzureOpenAIExplanationProvider(
            api_key=api_key,
            endpoint=endpoint,
            model=model,
            client_factory=client_factory,
        )

    raise LLMConfigurationError(
        "LLM_PROVIDER must be set to 'azure_openai'."
    )


def generate_explanation(prompt, llm_function=None):
    """Generate an explanation through an injected fake or configured provider."""
    if llm_function is not None:
        return llm_function(prompt)

    return get_configured_provider().generate(prompt)
