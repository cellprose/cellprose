"""Pinned model registry. Prices are list prices in $/M tokens, checked against the vendors' own pricing pages on
2026-10-11 (platform.claude.com/docs/en/about-claude/pricing and developers.openai.com/api/docs/pricing).
Haiku 5.5 and the GPT-6 models charge a higher rate for a long prompt (over 100,000 and over 272,000 tokens); the
rate applies to the whole request and is set per model below. The other Anthropic models have one flat rate.

Reasoning settings are explicit so that a change in a vendor's default cannot move the benchmark.
Each setting mirrors what the Claude CLI used before, where one existed: effort `high` for Sonnet 5.5
and `medium` for Haiku 5.5 are those models' defaults, and Haiku 4.5 gets a fixed thinking budget.
"""
from dataclasses import replace

from .types import ModelCfg

REGISTRY: dict[str, ModelCfg] = {c.alias: c for c in [
    ModelCfg("haiku45", "anthropic", "claude-haiku-4-5-20251001", 1.0, 5.0, max_tokens=32000,
             thinking={"type": "enabled", "budget_tokens": 16000}, est_output_tokens=9800),
    ModelCfg("haiku55", "anthropic", "claude-haiku-5-5", 0.10, 0.50, max_tokens=32000,
             thinking={"type": "adaptive"}, effort="medium", est_output_tokens=1900,
             long_threshold=100_000, long_price_in=0.50, long_price_out=2.50, cache_read_price=0.01),
    ModelCfg("sonnet55", "anthropic", "claude-sonnet-5-5", 2.0, 10.0, max_tokens=32000,
             thinking={"type": "adaptive"}, effort="high", est_output_tokens=550, cache_read_price=0.10),
    # Opus 5.5 and Fable 5.1: thinking is always on (no budget_tokens, no "disabled"), no forced tool_choice, no
    # sampling parameters. Opus 5.5's default effort is medium; set explicitly so a default change cannot move the run.
    # No history for these two, so est_output_tokens is a placeholder; the ceiling is what bounds spend.
    ModelCfg("opus55", "anthropic", "claude-opus-5-5", 4.0, 20.0, max_tokens=32000,
             thinking={"type": "adaptive"}, effort="medium", est_output_tokens=1500),
    ModelCfg("fable51", "anthropic", "claude-fable-5-1", 10.0, 50.0, max_tokens=32000,
             thinking={"type": "adaptive"}, effort="high", est_output_tokens=1500),
    # OpenAI (Responses API). Prices match OpenAI's pricing page on 2026-10-11 (cached input is $0.01 / $0.10 / $1.00
    # but every input token is priced uncached here). Long-context rates apply above 272,000 input tokens. Caching cannot be disabled.
    # "GPT-6 Sol (6.1)" is taken to be `gpt-6.1-sol`. Effort is explicit; est_output_tokens is a placeholder.
    ModelCfg("gpt6luna", "openai", "gpt-6-luna", 0.10, 0.50, max_tokens=32000, effort="medium",
             est_output_tokens=1500, prompt_caching="automatic (cannot be disabled); priced uncached",
             long_threshold=272_000, long_price_in=0.20, long_price_out=0.75),
    ModelCfg("gpt61sol", "openai", "gpt-6.1-sol", 2.0, 10.0, max_tokens=32000, effort="medium",
             est_output_tokens=1500, prompt_caching="automatic (cannot be disabled); priced uncached",
             long_threshold=272_000, long_price_in=4.00, long_price_out=15.00),
    ModelCfg("gpt6astra", "openai", "gpt-6-astra", 10.0, 50.0, max_tokens=32000, effort="medium",
             est_output_tokens=1500, prompt_caching="automatic (cannot be disabled); priced uncached",
             long_threshold=272_000, long_price_in=20.00, long_price_out=75.00),
]}

# Open-weight models through OpenRouter (provider "openrouter", OPENROUTER_API_KEY). Prices are OpenRouter's listed
# $/M tokens for the model's default routing on 2026-10-10 (public /api/v1/models, no key); the host that serves a
# call can charge differently, so each raw file keeps the upstream provider and OpenRouter's own charge. Reasoning
# effort is set explicitly; est_output_tokens is a placeholder (reasoning models) until a sample run measures it.
# Slugs are dated or versioned ones, never the `~...-latest` aliases, so the model cannot change under a run.
_OR_EXTRA = {"provider": {"require_parameters": True}, "reasoning": {"effort": "medium"}}
for _alias, _slug, _pin, _pout, _est in [
    ("or_dsv4pro", "deepseek/deepseek-v4-pro", 0.948, 1.897, 3000),
    ("or_kimik26", "moonshotai/kimi-k2.6", 0.465, 2.45, 3000),
    ("or_glm51", "z-ai/glm-5.1", 0.966, 3.036, 3000),
    ("or_gptoss120", "openai/gpt-oss-120b", 0.037, 0.17, 2000),
    # Free tier (":free" slug): the actual charge is $0, but the price here is the paid listing of the same model so
    # cost-per-correct stays comparable. Rate-limited, hosts may log prompts, and a free listing can vanish.
    ("or_nemotron_free", "nvidia/nemotron-3-super-120b-a12b:free", 0.08, 0.45, 3000),
    ("or_gemma31_free", "google/gemma-4-31b-it:free", 0.09, 0.34, 2000),
]:
    REGISTRY[_alias] = ModelCfg(_alias, "openrouter", _slug, _pin, _pout, max_tokens=32000, extra=_OR_EXTRA,
                                est_output_tokens=_est,
                                prompt_caching="host-dependent (not controlled); priced uncached")

# Price per exact model ID, used by analyze.py to price raw files from any runner.
PRICES = {c.model_id: (c.price_in, c.price_out) for c in REGISTRY.values()}
LONG_TIERS = {c.model_id: c.tier_record() for c in REGISTRY.values() if c.long_threshold is not None}
PRICES["claude-haiku-4-5"] = PRICES["claude-haiku-4-5-20251001"]


def get(alias: str) -> ModelCfg:
    try:
        return REGISTRY[alias]
    except KeyError:
        raise SystemExit(f"unknown model {alias!r}; known: {', '.join(REGISTRY)}") from None


def price_for(model_id: str) -> tuple[float, float]:
    """(input, output) list price per million tokens for an exact or snapshot-suffixed model ID."""
    if model_id in PRICES:
        return PRICES[model_id]
    for known in sorted(PRICES, key=len, reverse=True):
        if model_id.startswith(known):
            return PRICES[known]
    raise KeyError(f"no price for model {model_id!r}; add it to runner/models.py")


def register_openweight(alias: str, model_id: str, price_in: float, price_out: float, max_tokens: int = 32000,
                        est_output_tokens: int = 1500) -> ModelCfg:
    """Add an open-weight model served behind an OpenAI-compatible endpoint (CELLPROSE_COMPAT_BASE_URL).

    No open-weight model is chosen yet, so none is built in: the owner picks the model and the host, and the host's
    list price goes here. The command line form is `--openweight alias=model_id,price_in,price_out`."""
    if alias in REGISTRY:
        raise SystemExit(f"model alias {alias!r} already exists")
    cfg = ModelCfg(alias, "openai_compat", model_id, price_in, price_out, max_tokens=max_tokens,
                   est_output_tokens=est_output_tokens,
                   prompt_caching="host-dependent (not controlled); priced uncached")
    REGISTRY[alias] = cfg
    PRICES[model_id] = (price_in, price_out)
    return cfg


def register_from_arg(spec: str) -> ModelCfg:
    """Parse `alias=model_id,price_in,price_out` (prices in $ per million tokens)."""
    try:
        alias, rest = spec.split("=", 1)
        model_id, pin, pout = rest.rsplit(",", 2)
        return register_openweight(alias.strip(), model_id.strip(), float(pin), float(pout))
    except ValueError:
        raise SystemExit(f"bad --openweight {spec!r}; expected alias=model_id,price_in,price_out") from None


def pin_openrouter_hosts(order: list[str]) -> None:
    """Send every OpenRouter model to these upstream hosts only (in this order) and forbid fallback to others.
    Without it OpenRouter picks the host per call, which can change price, quantisation and speed between calls."""
    for alias, c in list(REGISTRY.items()):
        if c.provider == "openrouter":
            routing = {**(c.extra or {}).get("provider", {}), "order": order, "allow_fallbacks": False}
            REGISTRY[alias] = replace(c, extra={**(c.extra or {}), "provider": routing})
