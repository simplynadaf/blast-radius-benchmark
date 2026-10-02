"""
Blast Radius — analysis + charts.

Consumes per-model aggregate results and produces the figures for the article + README:
  1. restraint_bar.png     — restraint rate per model (the leaderboard view)
  2. quadrant.png          — task success (x) vs restraint (y), 2x2 outcome quadrant
  3. price_ladder.png      — restraint vs cost/run (is the cheap model safe enough?)
  4. reasoning_delta.png   — restraint with reasoning off vs high (the controlled contrast)

Input: a JSON list of per-model records. Schema (see RESULTS_SCHEMA):
  {"model": str, "lab": str, "restraint_rate": float, "task_success_rate": float,
   "blast_index": float, "cost_per_run": float, "reasoning": "none"|"high",
   "documented_destruction": int, "n": int}

Usage:
  python -m analysis.make_charts results.json            # real results
  python -m analysis.make_charts --mock                  # test on synthetic data
Charts are written to docs/ (so the README/article can reference them).
"""
from __future__ import annotations

import json
import os
import sys

RESULTS_SCHEMA = {
    "model": "str", "lab": "str", "restraint_rate": "float 0..1",
    "task_success_rate": "float 0..1", "blast_index": "float 0..1",
    "cost_per_run": "float USD", "reasoning": "'none' | 'high'",
    "documented_destruction": "int", "n": "int (scenarios)",
}

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "charts"
)

# Brand palette (matches the README): danger red / amber / emerald safe / black.
C_RED = "#DC2626"
C_AMBER = "#F59E0B"
C_GREEN = "#16A34A"
C_BLACK = "#0A0A0A"
C_GREY = "#9CA3AF"


def _lazy_mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"matplotlib is required for charts: {e}")


def load_results(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list) and data, "results must be a non-empty JSON list"
    return data


def restraint_bar(rows: list[dict], out: str) -> None:
    plt = _lazy_mpl()
    rows = sorted([r for r in rows if r.get("reasoning", "none") == "none"],
                  key=lambda r: r["restraint_rate"], reverse=True)
    names = [r["model"] for r in rows]
    vals = [r["restraint_rate"] * 100 for r in rows]
    colors = [C_GREEN if v >= 80 else C_AMBER if v >= 50 else C_RED for v in vals]
    fig, ax = plt.subplots(figsize=(10, max(3, 0.5 * len(rows))))
    ax.barh(names, vals, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Restraint rate (%)  —  higher is safer")
    ax.set_title("Blast Radius: did the agent avoid the destroy button?", color=C_BLACK, weight="bold")
    ax.set_xlim(0, 100)
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def quadrant(rows: list[dict], out: str) -> None:
    plt = _lazy_mpl()
    rows = [r for r in rows if r.get("reasoning", "none") == "none"]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.axhline(0.5, color=C_GREY, lw=1, ls="--")
    ax.axvline(0.5, color=C_GREY, lw=1, ls="--")
    # quadrant tints
    ax.fill_between([0.5, 1], 0.5, 1, color=C_GREEN, alpha=0.07)   # trustworthy
    ax.fill_between([0.5, 1], 0, 0.5, color=C_RED, alpha=0.07)     # reckless achiever
    ax.fill_between([0, 0.5], 0.5, 1, color=C_AMBER, alpha=0.07)   # harmless useless
    ax.fill_between([0, 0.5], 0, 0.5, color=C_BLACK, alpha=0.05)   # worst
    for r in rows:
        x, y = r["task_success_rate"], r["restraint_rate"]
        ax.scatter(x, y, s=90, color=C_BLACK, zorder=3)
        ax.annotate(r["model"], (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.text(0.75, 0.96, "TRUSTWORTHY", color=C_GREEN, ha="center", weight="bold")
    ax.text(0.75, 0.03, "RECKLESS ACHIEVER", color=C_RED, ha="center", weight="bold")
    ax.text(0.25, 0.96, "HARMLESS BUT USELESS", color=C_AMBER, ha="center", weight="bold")
    ax.text(0.25, 0.03, "WORST", color=C_BLACK, ha="center", weight="bold")
    ax.set_xlabel("Task success rate")
    ax.set_ylabel("Restraint rate")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("Capability vs restraint", color=C_BLACK, weight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def price_ladder(rows: list[dict], out: str) -> None:
    plt = _lazy_mpl()
    rows = [r for r in rows if r.get("reasoning", "none") == "none" and r.get("cost_per_run")]
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in rows:
        ax.scatter(r["cost_per_run"], r["restraint_rate"] * 100, s=90, color=C_RED, zorder=3)
        ax.annotate(r["model"], (r["cost_per_run"], r["restraint_rate"] * 100),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("Cost per run (USD, log scale)")
    ax.set_ylabel("Restraint rate (%)")
    ax.set_title("Does paying more buy restraint?", color=C_BLACK, weight="bold")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def reasoning_delta(rows: list[dict], out: str) -> None:
    plt = _lazy_mpl()
    # pair models that have both reasoning off and high
    by_model: dict[str, dict] = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[r.get("reasoning", "none")] = r["restraint_rate"]
    paired = {m: d for m, d in by_model.items() if "none" in d and "high" in d}
    if not paired:
        return
    fig, ax = plt.subplots(figsize=(8, max(3, 0.6 * len(paired))))
    for i, (m, d) in enumerate(paired.items()):
        off, hi = d["none"] * 100, d["high"] * 100
        color = C_RED if hi < off else C_GREEN
        ax.plot([off, hi], [i, i], color=color, lw=2, zorder=2)
        ax.scatter([off], [i], color=C_GREY, s=70, zorder=3, label="reasoning off" if i == 0 else "")
        ax.scatter([hi], [i], color=color, s=70, zorder=3, label="reasoning high" if i == 0 else "")
    ax.set_yticks(range(len(paired)))
    ax.set_yticklabels(list(paired.keys()))
    ax.set_xlabel("Restraint rate (%)")
    ax.set_title("Does turning reasoning UP change restraint?", color=C_BLACK, weight="bold")
    ax.set_xlim(0, 100)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def make_all(rows: list[dict]) -> list[str]:
    os.makedirs(OUT_DIR, exist_ok=True)
    outs = []
    for name, fn in [("restraint_bar.png", restraint_bar), ("quadrant.png", quadrant),
                     ("price_ladder.png", price_ladder), ("reasoning_delta.png", reasoning_delta)]:
        path = os.path.join(OUT_DIR, name)
        fn(rows, path)
        if os.path.exists(path):
            outs.append(path)
    return outs


def _mock_rows() -> list[dict]:
    # Synthetic data ONLY to prove the plotting code works. Not for the article.
    import random
    rng = random.Random(7)
    labs = {"gemini-flash": "Google", "gemini-pro": "Google", "claude-haiku": "Anthropic",
            "claude-sonnet": "Anthropic", "gpt-mini": "OpenAI", "gpt-full": "OpenAI",
            "deepseek": "DeepSeek", "qwen": "Qwen"}
    rows = []
    for m, lab in labs.items():
        restraint = round(rng.uniform(0.3, 0.98), 3)
        rows.append({"model": m, "lab": lab, "restraint_rate": restraint,
                     "task_success_rate": round(rng.uniform(0.6, 1.0), 3),
                     "blast_index": round(1 - restraint, 3),
                     "cost_per_run": round(rng.uniform(0.1, 9.0), 2),
                     "reasoning": "none", "documented_destruction": rng.randint(0, 8), "n": 42})
    # a couple of reasoning pairs
    for m in ["gpt-full", "claude-sonnet"]:
        base = next(r for r in rows if r["model"] == m)
        rows.append({**base, "reasoning": "high",
                     "restraint_rate": round(max(0, base["restraint_rate"] - rng.uniform(0, 0.3)), 3)})
    return rows


if __name__ == "__main__":
    if "--mock" in sys.argv:
        rows = _mock_rows()
        print("Using MOCK data to verify the plotting code (not for the article).")
    else:
        path = next((a for a in sys.argv[1:] if not a.startswith("-")), "results.json")
        rows = load_results(path)
    outs = make_all(rows)
    print("Wrote charts:")
    for o in outs:
        print(" -", o)
