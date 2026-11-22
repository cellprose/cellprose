"""Provider adapters. Each turns a (model config, system, user) triple into a CallResult.

Anthropic, OpenAI and OpenAI-compatible endpoints (open-weight models) share one `complete()` /
`count_tokens()` interface. A call that does not end in a usable answer raises a `CallError` that carries the
provider's result, so the runner can record the tokens it billed.
"""
import os

from .types import ApiFailure, CacheLeak, CallResult, ModelCfg, Refused, Truncated, Usage


ANTHROPIC_BASE_URL = "https://api.anthropic.com"  # explicit: ignore any ANTHROPIC_BASE_URL in the environment


def anthropic_credentials(env=None) -> tuple[str | None, dict]:
    """(api key, extra headers). Key: ANTHROPIC_API_KEY, else CELLPROSE_ANTHROPIC_KEY, else the
    pre-rename SHEETMARK_ANTHROPIC_KEY.
    The workspace header comes from CELLPROSE_ANTHROPIC_WORKSPACE_ID (or ANTHROPIC_WORKSPACE_ID). Values are never printed."""
    env = os.environ if env is None else env
    key = env.get("ANTHROPIC_API_KEY") or env.get("CELLPROSE_ANTHROPIC_KEY") or env.get("SHEETMARK_ANTHROPIC_KEY") or None
    ws = env.get("CELLPROSE_ANTHROPIC_WORKSPACE_ID") or env.get("ANTHROPIC_WORKSPACE_ID")
    return key, ({"anthropic-workspace-id": ws} if ws else {})


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client=None):
        if client is None:
            import anthropic
            key, headers = anthropic_credentials()
            client = anthropic.Anthropic(api_key=key, base_url=ANTHROPIC_BASE_URL, max_retries=3,
                                         default_headers=headers)
            print(f"anthropic host: {ANTHROPIC_BASE_URL.split('//', 1)[1]} "
                  f"(workspace header: {'yes' if headers else 'no'})", flush=True)
        self.client = client

    @staticmethod
    def request(cfg: ModelCfg, system: str, user: str) -> dict:
        """The exact request body. No cache_control anywhere, so nothing is written to or read from the cache."""
        kw = {"model": cfg.model_id, "max_tokens": cfg.max_tokens, "system": system,
              "messages": [{"role": "user", "content": user}]}
        if cfg.thinking is not None:
            kw["thinking"] = cfg.thinking
        if cfg.effort is not None:
            kw["output_config"] = {"effort": cfg.effort}
        return kw

    def complete(self, cfg: ModelCfg, system: str, user: str) -> CallResult:
        # Streaming avoids the SDK's non-streaming guard on large max_tokens; the final message is identical.
        with self.client.messages.stream(**self.request(cfg, system, user)) as stream:
            msg = stream.get_final_message()
        res = self.to_result(msg)
        res.raw_usage.update(self.tokenizer_usage(cfg, system, user))
        # Every raise below carries the result, so the runner can record the billed tokens of a failed call.
        if res.usage.cache_read_tokens or res.usage.cache_write_tokens:
            raise CacheLeak(f"cache activity with caching off: read={res.usage.cache_read_tokens} "
                            f"write={res.usage.cache_write_tokens} (request {res.request_id})", res)
        if msg.stop_reason == "max_tokens":
            raise Truncated(f"hit max_tokens={cfg.max_tokens}", res)
        if msg.stop_reason == "refusal":
            raise Refused("model refused the request", res)
        return res

    @staticmethod
    def to_result(msg) -> CallResult:
        u = msg.usage
        details = getattr(u, "output_tokens_details", None)
        usage = Usage(
            input_tokens=u.input_tokens or 0,
            output_tokens=u.output_tokens or 0,
            reasoning_tokens=getattr(details, "thinking_tokens", None),
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        raw = u.model_dump() if hasattr(u, "model_dump") else {}
        return CallResult(text=text, model_returned=msg.model, request_id=getattr(msg, "_request_id", None),
                          usage=usage, stop_reason=msg.stop_reason, raw_usage=raw)

    def tokenizer_usage(self, cfg: ModelCfg, system: str, user: str) -> dict:
        """Anthropic's own count of system+user (the free count_tokens endpoint), stored beside billed usage.
        It never fails the call: an error leaves the count out."""
        try:
            n = self.count_tokens(cfg, system, user)
        except Exception:
            return {"tokenizer": "anthropic count_tokens", "tokenizer_input_tokens": None}
        return {"tokenizer": "anthropic count_tokens", "tokenizer_input_tokens": n}

    def count_tokens(self, cfg: ModelCfg, system: str, user: str) -> int:
        r = self.client.messages.count_tokens(model=cfg.model_id, system=system,
                                              messages=[{"role": "user", "content": user}])
        return r.input_tokens


OPENAI_BASE_URL = "https://api.openai.com/v1"  # explicit: ignore any OPENAI_BASE_URL in the environment


def _tokenizer_count(text: str):
    """OpenAI tokenizer (o200k_base) count of `text`, or None when tiktoken or its vocabulary is unavailable."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding("o200k_base").encode(text))
    except Exception:
        return None


class OpenAIProvider:
    """OpenAI Responses API. Reasoning effort is sent explicitly; temperature is left at the provider default.

    OpenAI caches long prompts automatically and the API has no switch to turn that off, so cached input is
    recorded as cache_read_tokens (billed input is split the way Anthropic's is) and costs are still priced
    at the full, uncached input rate. The tokenizer count of system+user is stored beside billed usage.
    """
    name = "openai"

    def __init__(self, client=None):
        if client is None:
            import openai
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=OPENAI_BASE_URL, max_retries=3)
            print(f"openai host: {OPENAI_BASE_URL.split('//', 1)[1].split('/')[0]}", flush=True)
        self.client = client

    @staticmethod
    def request(cfg: ModelCfg, system: str, user: str) -> dict:
        kw = {"model": cfg.model_id, "instructions": system, "input": user,
              "max_output_tokens": cfg.max_tokens, "store": False}
        if cfg.effort is not None:
            kw["reasoning"] = {"effort": cfg.effort}
        return kw

    def complete(self, cfg: ModelCfg, system: str, user: str) -> CallResult:
        r = self.client.responses.create(**self.request(cfg, system, user))
        u = r.usage
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        usage = Usage(
            input_tokens=(u.input_tokens or 0) - cached,
            output_tokens=u.output_tokens or 0,
            reasoning_tokens=getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None),
            cache_read_tokens=cached,
        )
        if getattr(r, "status", "completed") == "incomplete":
            reason = getattr(getattr(r, "incomplete_details", None), "reason", None)
            res = self.to_result(r, usage, system, user)
            raise Truncated(f"response incomplete ({reason}) at max_output_tokens={cfg.max_tokens}", res)
        res = self.to_result(r, usage, system, user)
        for item in r.output:
            for part in getattr(item, "content", None) or []:
                if getattr(part, "type", None) == "refusal":
                    raise Refused("model refused the request", res)
        return res

    @staticmethod
    def to_result(r, usage: Usage, system: str, user: str) -> CallResult:
        raw = r.usage.model_dump() if hasattr(r.usage, "model_dump") else {}
        raw["billed_input_tokens"] = usage.total_input
        n = _tokenizer_count(system + user)
        raw["tokenizer_input_tokens_o200k"] = n
        raw["tokenizer"] = "o200k_base (tiktoken)"
        raw["tokenizer_input_tokens"] = n
        return CallResult(text=getattr(r, "output_text", "") or "", model_returned=r.model,
                          request_id=getattr(r, "_request_id", None), usage=usage,
                          stop_reason=getattr(r, "status", None), raw_usage=raw)

    def count_tokens(self, cfg: ModelCfg, system: str, user: str) -> int:
        """Local tokenizer count (OpenAI has no free counting endpoint); a few tokens short of billed input."""
        n = _tokenizer_count(system + user)
        if n is None:
            raise RuntimeError("tiktoken vocabulary unavailable")
        return n


class OpenAICompatProvider:
    """Chat Completions against any OpenAI-compatible endpoint (vLLM, Together, Fireworks, a local server...), for
    open-weight models. The endpoint comes from CELLPROSE_COMPAT_BASE_URL and the key from CELLPROSE_COMPAT_API_KEY;
    neither is ever printed beyond the host name. Sampling and reasoning parameters are left at the server's
    defaults and recorded as such, because compatible servers do not agree on them.

    Prompt caching is whatever the host does and cannot be inspected here; cached prompt tokens are recorded when
    the server reports them and, as with OpenAI, every input token is priced as uncached. There is no tokenizer
    count: the model's tokenizer is not the endpoint's to expose, so only billed usage is stored.
    """
    name = "openai_compat"

    def __init__(self, client=None, env=None):
        if client is None:
            env = os.environ if env is None else env
            base = env.get("CELLPROSE_COMPAT_BASE_URL")
            if not base:
                raise SystemExit("provider openai_compat needs CELLPROSE_COMPAT_BASE_URL "
                                 "(and CELLPROSE_COMPAT_API_KEY if the endpoint wants one)")
            import openai
            client = openai.OpenAI(api_key=env.get("CELLPROSE_COMPAT_API_KEY") or "none", base_url=base, max_retries=3)
            print(f"openai-compatible host: {base.split('//', 1)[-1].split('/')[0]}", flush=True)
        self.client = client

    @staticmethod
    def request(cfg: ModelCfg, system: str, user: str) -> dict:
        return {"model": cfg.model_id, "max_tokens": cfg.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}

    def complete(self, cfg: ModelCfg, system: str, user: str) -> CallResult:
        r = self.client.chat.completions.create(**self.request(cfg, system, user))
        self._check(r)
        u = r.usage
        cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
        usage = Usage(
            input_tokens=(u.prompt_tokens or 0) - cached,
            output_tokens=u.completion_tokens or 0,
            reasoning_tokens=getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
            cache_read_tokens=cached,
        )
        choice = r.choices[0]
        raw = u.model_dump() if hasattr(u, "model_dump") else {}
        raw["billed_input_tokens"] = usage.total_input
        raw["tokenizer"] = None
        raw["tokenizer_input_tokens"] = None
        self._annotate(r, raw)
        res = CallResult(text=choice.message.content or "", model_returned=r.model,
                         request_id=getattr(r, "id", None), usage=usage, stop_reason=choice.finish_reason,
                         raw_usage=raw)
        if choice.finish_reason == "length":
            raise Truncated(f"hit max_tokens={cfg.max_tokens}", res)
        if choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
            raise Refused("model refused the request", res)
        return res

    @staticmethod
    def _check(r) -> None:
        """Hook for subclasses to reject a response that has no usable body."""

    @staticmethod
    def _annotate(r, raw: dict) -> None:
        """Hook for subclasses to add host-specific facts to the stored usage."""

    def count_tokens(self, cfg: ModelCfg, system: str, user: str) -> int:
        raise RuntimeError("an OpenAI-compatible endpoint has no token-counting call")


OPENROUTER_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(OpenAICompatProvider):
    """OpenRouter's OpenAI-compatible Chat Completions API, for open-weight models.

    The key comes from OPENROUTER_API_KEY (never printed). Differences from a plain compatible endpoint:
    the request carries `extra` from the model config (provider routing, reasoning effort), `usage.include` so the
    response reports what OpenRouter charged, and the raw file keeps the upstream provider that served the call
    and that charge. With `allow_fallbacks` off a call fails rather than silently moving to another host. Token
    counts are whatever OpenRouter reports; no tokenizer count exists, so only billed usage is stored."""
    name = "openrouter"

    def __init__(self, client=None, env=None):
        if client is None:
            env = os.environ if env is None else env
            key = env.get("OPENROUTER_API_KEY")
            if not key:
                raise SystemExit("provider openrouter needs OPENROUTER_API_KEY")
            import openai
            client = openai.OpenAI(api_key=key, base_url=env.get("OPENROUTER_BASE_URL", OPENROUTER_URL), max_retries=3,
                                   default_headers={"X-Title": "sheetmark-benchmark"})
            print("openrouter: key present", flush=True)
        self.client = client

    @staticmethod
    def request(cfg: ModelCfg, system: str, user: str) -> dict:
        body = OpenAICompatProvider.request(cfg, system, user)
        body["extra_body"] = {**(cfg.extra or {}), "usage": {"include": True}}
        return body

    @staticmethod
    def _check(r) -> None:
        if not getattr(r, "choices", None):      # OpenRouter reports upstream failures as a 200 with an error body
            raise ApiFailure(f"OpenRouter returned no choices: {getattr(r, 'error', None) or 'no error given'}")

    @staticmethod
    def _annotate(r, raw: dict) -> None:
        extra = getattr(r, "model_extra", None) or {}
        raw["upstream_provider"] = extra.get("provider") or getattr(r, "provider", None)
        raw["openrouter_cost_usd"] = raw.get("cost")      # what OpenRouter charged; the runner still prices at list

    def count_tokens(self, cfg: ModelCfg, system: str, user: str) -> int:
        raise RuntimeError("OpenRouter has no token-counting call")


def get_provider(cfg: ModelCfg):
    if cfg.provider == "anthropic":
        return AnthropicProvider()
    if cfg.provider == "openai":
        return OpenAIProvider()
    if cfg.provider == "openai_compat":
        return OpenAICompatProvider()
    if cfg.provider == "openrouter":
        return OpenRouterProvider()
    raise ValueError(f"unknown provider {cfg.provider!r}")
