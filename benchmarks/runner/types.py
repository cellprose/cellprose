"""Plain data types shared by every provider."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelCfg:
    """One benchmarked model: the exact ID, list prices and every setting sent with each call."""
    alias: str                 # directory name under results/raw and the "model" field score.py groups by
    provider: str              # "anthropic" | "openai" | "openai_compat" | "openrouter"
    model_id: str              # exact ID sent to the API
    price_in: float            # list $ per million input tokens
    price_out: float           # list $ per million output tokens (reasoning tokens are billed as output)
    max_tokens: int
    thinking: dict | None = None
    effort: str | None = None
    est_output_tokens: int = 4000   # fallback when no history exists for this model
    prompt_caching: str = "off"     # "off", or a note when the vendor cannot switch caching off
    extra: dict | None = None       # provider-specific request fields (OpenRouter routing and reasoning), recorded
    # Some models charge more for a request whose prompt is long (Haiku 5.5 over 100,000 tokens; the GPT-6 models over
    # 272,000). The rate applies to the whole request, its input and its output, so it is chosen per request.
    long_threshold: int | None = None
    long_price_in: float | None = None
    long_price_out: float | None = None
    # Anthropic prompt-cache prices, used only for the billed amount (`billed_cost`); the benchmark's cost metric prices
    # every token uncached. A cache write is 1.25x the input price (5-minute TTL); a read is cache_read_price.
    cache_read_price: float | None = None

    def prices(self, prompt_tokens: int) -> tuple[float, float]:
        """(input, output) $ per million tokens for one request whose prompt has `prompt_tokens` tokens."""
        if self.long_threshold is not None and prompt_tokens > self.long_threshold:
            return self.long_price_in, self.long_price_out
        return self.price_in, self.price_out

    def tier_record(self) -> dict | None:
        """The long-prompt tier as stored in each raw file, so a file can be re-priced without the registry."""
        if self.long_threshold is None:
            return None
        return {"threshold": self.long_threshold, "price_in": self.long_price_in, "price_out": self.long_price_out}

    def settings(self) -> dict:
        """Every setting sent with the request, recorded in each raw file."""
        s = {"max_tokens": self.max_tokens, "temperature": "provider default", "prompt_caching": self.prompt_caching}
        if self.thinking is not None:
            s["thinking"] = self.thinking
        if self.effort is not None:
            s["effort"] = self.effort
        if self.extra is not None:
            s["extra"] = self.extra
        return s


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0          # includes reasoning tokens
    reasoning_tokens: int | None = None
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_input(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens


@dataclass
class CallResult:
    text: str
    model_returned: str             # the model ID the server says it used
    request_id: str | None
    usage: Usage
    stop_reason: str | None = None
    raw_usage: dict = field(default_factory=dict)
    cost: float | None = None       # set when the cost is not a function of the summed usage (agent turns are priced one by one)


class InfraFailure(RuntimeError):
    """A call that failed for a reason outside the model (credit, key, rate limit, overload, network). Not recorded:
    the call stays to do and a resume makes it. `cost` is what the attempt spent before it failed (agent turns that
    completed); it counts toward the vendor cap and is logged, but is not in the metric."""

    def __init__(self, message: str, cost: float = 0.0):
        super().__init__(message)
        self.cost = cost


class CallError(RuntimeError):
    """A call that finished without a usable answer. `result` holds what the provider returned, when it returned
    anything, so the runner can record the tokens that were billed and score the call as 0."""

    kind = "error"

    def __init__(self, message: str, result: "CallResult | None" = None):
        super().__init__(message)
        self.result = result


class CacheLeak(CallError):
    """A response reported prompt-cache activity although caching is meant to be off."""
    kind = "cache_leak"


class Truncated(CallError):
    """The model hit max_tokens before finishing, so the answer cannot be trusted."""
    kind = "truncated"


class Refused(CallError):
    """The model declined to answer."""
    kind = "refused"


class TurnLimit(CallError):
    """Agent mode: the model used every allowed turn without giving a final answer."""
    kind = "turn_limit"


class BudgetExceeded(CallError):
    """Agent mode: the call's list-price cost reached the per-call cap before a final answer."""
    kind = "budget_exceeded"


class ApiFailure(CallError):
    """The provider's API failed (after the SDK's own retries) part-way through a call."""
    kind = "api_error"
