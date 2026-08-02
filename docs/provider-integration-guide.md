# Adding a New LLM Provider

Per PROJECT_SPEC_1 §27, adding a provider requires only a new adapter class and one registry
entry -- nothing else in the codebase changes.

## Steps

1. Create `backend/app/providers/<name>_provider.py`.
   - If the vendor exposes an OpenAI-Chat-Completions-compatible API (as Groq and DeepSeek do),
     subclass `OpenAICompatibleProvider` (`app/providers/openai_compatible.py`) and only set
     `default_base_url`, `requires_api_key`, and `pricing_per_1k_tokens`.
   - Otherwise, subclass `HttpJsonProviderBase` (`app/providers/http_provider_base.py`) directly
     and implement `generate()`, `stream()`, `health_check()`, and `list_models()`, mapping the
     vendor's wire format to/from `app.providers.schemas.ProviderRequest`/`ProviderResponse`.
2. Register it in `backend/app/providers/factory.py`'s `_REGISTRY` dict.
3. Add a unit test under `backend/tests/unit/providers/` mirroring the existing adapters' tests
   (mock the HTTP layer with `respx`; never call the real API in tests).
4. Add the provider's name to this repository's docs and to `.env.example` if it needs any
   provider-specific defaults.

No other file needs to change: `ProviderFactory.create_aut()`/`create_judge()`, the execution
engine, and the evaluation engine all depend only on `BaseProvider`.
