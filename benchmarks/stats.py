"""Paired bootstrap intervals and the win / loss / no-difference verdict of docs/PROTOCOL.md section 7.

Pure functions over a frame with one row per call: model, workbook, encoding, rep, cost, acc. The unit that is
resampled is the workbook: repeats are averaged within a workbook first, so the interval reflects workbook-to-workbook
spread (the thing a reader generalises over) and not just repeat noise, and calls for the same workbook and repeat
stay paired across encodings.
"""
import numpy as np

RESAMPLES = 10_000
SEED = 20261009
ACC_TOLERANCE = 0.01        # a win allows accuracy up to 1 point below the baseline


def _per_workbook(df, model, enc):
    g = df[(df.model == model) & (df.encoding == enc)].groupby("workbook")[["cost", "acc"]].mean()
    return g


def _cpc(cost, acc):
    """cost per correct answer, inf when nothing was answered correctly."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = cost / acc
    return np.where(acc > 0, out, np.inf)


def _interval(x, level=0.95):
    """Percentile interval by order statistics, so infinite resamples (nothing answered) cannot make the ends NaN."""
    x = np.sort(np.asarray(x, dtype=float))
    tail = (1 - level) / 2
    return x[int(np.floor(tail * (len(x) - 1)))], x[int(np.ceil((1 - tail) * (len(x) - 1)))]


def paired_comparison(df, model, a, b, resamples=RESAMPLES, seed=SEED):
    """Encoding `a` against baseline `b` for one model. Ratios are a / b, so below 1 means `a` is cheaper per correct
    answer. Returns None when the two share no workbook."""
    ga, gb = _per_workbook(df, model, a), _per_workbook(df, model, b)
    wbs = sorted(set(ga.index) & set(gb.index))
    if not wbs:
        return None
    ca, aa = ga.loc[wbs, "cost"].to_numpy(), ga.loc[wbs, "acc"].to_numpy()
    cb, ab = gb.loc[wbs, "cost"].to_numpy(), gb.loc[wbs, "acc"].to_numpy()
    n = len(wbs)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    ratio = _cpc(ca[idx].mean(1), aa[idx].mean(1)) / _cpc(cb[idx].mean(1), ab[idx].mean(1))
    ratio = np.where(np.isnan(ratio), np.inf, ratio)         # inf / inf: neither side answered anything
    diff = aa[idx].mean(1) - ab[idx].mean(1)
    point_cost = ca.mean() / aa.mean() if aa.mean() > 0 else np.inf
    point_base = cb.mean() / ab.mean() if ab.mean() > 0 else np.inf
    point = point_cost / point_base if np.isfinite(point_base) else np.nan
    lo, hi = _interval(ratio)
    dlo, dhi = _interval(diff)
    acc_diff = float(aa.mean() - ab.mean())
    return {"model": model, "encoding": a, "baseline": b, "n_workbooks": n,
            "acc": float(aa.mean()), "acc_baseline": float(ab.mean()), "acc_diff_points": 100 * acc_diff,
            "acc_diff_lo": 100 * float(dlo), "acc_diff_hi": 100 * float(dhi),
            "cost_per_correct": float(point_cost), "cost_per_correct_baseline": float(point_base),
            "ratio": float(point), "ratio_lo": float(lo), "ratio_hi": float(hi),
            "verdict": verdict(lo, hi, acc_diff)}


def verdict(ratio_lo, ratio_hi, acc_diff):
    """win: the whole interval is below 1 and accuracy is no more than 1 point below the baseline.
    loss: the whole interval is above 1. Anything else: no difference."""
    if ratio_hi < 1 and acc_diff >= -ACC_TOLERANCE:
        return "win"
    if ratio_lo > 1:
        return "loss"
    return "no difference"


def comparisons(df, a, baselines, models=None, **kw):
    """One row per model and baseline that both have data for `a`."""
    rows = []
    for m in sorted(models or df.model.unique()):
        for b in baselines:
            r = paired_comparison(df, m, a, b, **kw)
            if r:
                rows.append(r)
    return rows
