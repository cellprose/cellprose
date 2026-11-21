"""Cost estimates and uncached list-price cost of a finished call."""
from dataclasses import dataclass

from .types import ModelCfg, Usage

CHARS_PER_TOKEN = 3.5   # fallback when exact counting is unavailable; spreadsheet text tokenises densely


def call_cost(cfg: ModelCfg, usage: Usage) -> float:
    """One request: every input token at the uncached input price, output (incl. reasoning) at the output price. The rate
    is the long-prompt rate when the prompt is over the model's threshold. Not for usage summed over several requests."""
    price_in, price_out = cfg.prices(usage.total_input)
    return (usage.total_input * price_in + usage.output_tokens * price_out) / 1e6


CACHE_WRITE_MULT = 1.25     # 5-minute TTL


def billed_cost(cfg: ModelCfg, usage: Usage) -> float:
    """One request as billed: cache writes at 1.25x input and cache reads at the cache-read price. Reported beside the
    benchmark's metric (`call_cost`, everything uncached), never in place of it."""
    price_in, price_out = cfg.prices(usage.total_input)
    read = cfg.cache_read_price if cfg.cache_read_price is not None else price_in * 0.1
    if cfg.long_threshold is not None and usage.total_input > cfg.long_threshold:
        read *= price_in / cfg.price_in
    return (usage.input_tokens * price_in + usage.cache_write_tokens * price_in * CACHE_WRITE_MULT
            + usage.cache_read_tokens * read + usage.output_tokens * price_out) / 1e6


@dataclass
class Estimate:
    calls: int
    input_tokens: int
    expected_output_tokens: int
    expected_usd: float
    ceiling_usd: float          # every call spends its whole max_tokens
    exact_input: bool

    def lines(self) -> list[str]:
        src = "counted by the API" if self.exact_input else f"estimated from characters at {CHARS_PER_TOKEN} per token"
        return [f"calls: {self.calls}",
                f"input tokens: {self.input_tokens:,} ({src})",
                f"expected output tokens: {self.expected_output_tokens:,} (per model and arm from the API pilot, E32, "
                f"where it ran them; otherwise the model's est_output_tokens)",
                f"expected cost: ${self.expected_usd:.2f}",
                f"worst case (every call uses max_tokens): ${self.ceiling_usd:.2f}"]


def estimate(jobs, count_tokens=None) -> Estimate:
    """jobs: iterable of (cfg, system, user) or (cfg, system, user, expected output tokens); without the fourth, the
    model's est_output_tokens is used. count_tokens(cfg, system, user) -> int, or None for a char estimate."""
    n = tin = tout = 0
    usd = ceiling = 0.0
    exact = count_tokens is not None
    for job in jobs:
        cfg, system, user = job[:3]
        o = job[3] if len(job) > 3 and job[3] is not None else cfg.est_output_tokens
        t = count_tokens(cfg, system, user) if exact else int((len(system) + len(user)) / CHARS_PER_TOKEN)
        n += 1
        tin += t
        tout += round(o)
        price_in, price_out = cfg.prices(t)
        usd += (t * price_in + o * price_out) / 1e6
        ceiling += (t * price_in + cfg.max_tokens * price_out) / 1e6
    return Estimate(n, tin, tout, usd, ceiling, exact)
