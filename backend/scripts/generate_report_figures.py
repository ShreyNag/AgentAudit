"""Turn a results.csv produced by run_benchmark_suite.py into paper-ready figures + tables.

Reads only ``results.csv`` from ``--results-dir`` (never touches the database or any app/
module) and writes into ``<results-dir>/figures/``:

    01_cts_overview.png       mean CTS per model + trust-level distribution
    02_evaluator_heatmap.png  mean score per model x evaluator (10 evaluators)
    03_behaviour_distribution.png   behavioural classification mix per model
    04_failure_attribution.png      which evaluator is most often the primary failure cause
    06_radar_profiles.png     overlaid per-evaluator radar profile, one polygon per model
    summary_table.csv / .tex  headline numbers, ready to paste into the paper
    summary.txt               plain-English headline comparisons

Usage (needs pandas + matplotlib -- see scripts/research_requirements.txt):

    python scripts/generate_report_figures.py --results-dir research/results/<batch_id>

Colors follow the validated categorical/sequential/status palette from the project's
dataviz skill (references/palette.md) so figures stay colorblind-safe and consistent with
the rest of the project's visual language.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

EVALUATOR_NAMES: tuple[str, ...] = (
    "instruction_integrity",
    "planner",
    "memory",
    "tool_selection",
    "tool_invocation",
    "tool_correctness",
    "alignment",
    "tool_faithfulness",
    "security",
    "integrity",
)

# -- Validated palette (dataviz skill, references/palette.md) -- fixed categorical order,
# never cycled/reassigned per chart, so a given model keeps the same color everywhere.
CATEGORICAL = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
]
# One line style + marker per model as secondary encoding, since the radar chart shows every
# model at once (the "all series visible simultaneously" case the palette doc calls out).
LINESTYLES = ["-", "--", ":", "-.", (0, (3, 1, 1, 1))]
MARKERS = ["o", "s", "^", "D", "v"]

STATUS = {
    "SAFE_CORRECT": "#0ca30c",
    "PARTIAL_SUCCESS": "#ec835a",
    "SAFE_BY_INCOMPETENCE": "#fab219",
    "UNSAFE_COMPLIANCE": "#d03b3b",
}
BEHAVIOUR_ORDER = ["SAFE_CORRECT", "PARTIAL_SUCCESS", "SAFE_BY_INCOMPETENCE", "UNSAFE_COMPLIANCE"]

TRUST_ORDER = [
    "Untrusted",
    "Low Trust",
    "Limited Trust",
    "Moderate Trust",
    "High Trust",
    "Very High Trust",
]
TRUST_SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#0d366b"]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)


def _style_axes(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BASELINE)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def model_order(df: pd.DataFrame) -> list[str]:
    """Models ordered by mean CTS, descending -- the order every figure uses.

    Ordered by ``cts_raw`` (the uncapped weighted sum), never ``cts_reported``: the reported
    value is clamped to 30 on a critical failure, so a mean over it is a mean over clamped
    numbers and not a meaningful ranking (docs/adr/0008-cts-cap-is-policy-not-metric.md).
    """
    return list(df.groupby("model_label")["cts_raw"].mean().sort_values(ascending=False).index)


def model_colors(models: list[str]) -> dict[str, str]:
    return {label: CATEGORICAL[i % len(CATEGORICAL)] for i, label in enumerate(models)}


def fig_cts_overview(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    colors = model_colors(models)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor=SURFACE)

    means = df.groupby("model_label")["cts_raw"].mean().reindex(models)
    stds = df.groupby("model_label")["cts_raw"].std().reindex(models).fillna(0)
    ax1.set_facecolor(SURFACE)
    bars = ax1.bar(
        models,
        means.values,
        yerr=stds.values,
        capsize=4,
        color=[colors[m] for m in models],
        edgecolor=SURFACE,
        linewidth=2,
        zorder=3,
    )
    for bar, value in zip(bars, means.values, strict=True):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK_PRIMARY,
        )
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("Composite Trust Score, raw/uncapped (mean ± std)", color=INK_SECONDARY)
    ax1.set_title(
        "Overall CTS by model (raw, uncapped)", color=INK_PRIMARY, fontsize=11, loc="left"
    )
    ax1.set_xticks(range(len(models)))
    ax1.set_xticklabels(models, rotation=20, ha="right")
    _style_axes(ax1)

    ax2.set_facecolor(SURFACE)
    counts = (
        df.groupby(["model_label", "trust_level"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=models, columns=TRUST_ORDER, fill_value=0)
    )
    proportions = counts.div(counts.sum(axis=1), axis=0) * 100
    bottom = np.zeros(len(models))
    for level, color in zip(TRUST_ORDER, TRUST_SEQUENTIAL, strict=True):
        values = proportions[level].values
        ax2.bar(
            models,
            values,
            bottom=bottom,
            color=color,
            edgecolor=SURFACE,
            linewidth=1,
            label=level,
            zorder=3,
        )
        bottom += values
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Share of runs (%)", color=INK_SECONDARY)
    ax2.set_title("Trust-level distribution by model", color=INK_PRIMARY, fontsize=11, loc="left")
    ax2.set_xticks(range(len(models)))
    ax2.set_xticklabels(models, rotation=20, ha="right")
    ax2.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8)
    _style_axes(ax2)

    fig.tight_layout()
    fig.savefig(out_dir / "01_cts_overview.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def fig_evaluator_heatmap(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    score_cols = [f"score_{name}" for name in EVALUATOR_NAMES]
    pivot = df.groupby("model_label")[score_cols].mean().reindex(models)
    pivot.columns = list(EVALUATOR_NAMES)

    fig, ax = plt.subplots(figsize=(11, 0.6 * len(models) + 2), facecolor=SURFACE)
    im = ax.imshow(pivot.values, cmap=SEQUENTIAL_CMAP, vmin=0, vmax=100, aspect="auto")

    ax.set_xticks(range(len(EVALUATOR_NAMES)))
    ax.set_xticklabels(EVALUATOR_NAMES, rotation=35, ha="right", fontsize=9, color=INK_SECONDARY)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=9, color=INK_SECONDARY)
    ax.set_title("Mean evaluator score by model", color=INK_PRIMARY, fontsize=11, loc="left")

    for i in range(len(models)):
        for j in range(len(EVALUATOR_NAMES)):
            value = pivot.values[i, j]
            text_color = "white" if value < 55 else INK_PRIMARY
            ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=8, color=text_color)

    ax.set_xticks(np.arange(-0.5, len(EVALUATOR_NAMES), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(models), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Score (0-100)", color=INK_SECONDARY, fontsize=9)
    cbar.ax.tick_params(colors=INK_SECONDARY, labelsize=8)

    fig.tight_layout()
    fig.savefig(out_dir / "02_evaluator_heatmap.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def fig_behaviour_distribution(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    counts = (
        df.groupby(["model_label", "behaviour_classification"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=models, columns=BEHAVIOUR_ORDER, fill_value=0)
    )
    proportions = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    bottom = np.zeros(len(models))
    for label in BEHAVIOUR_ORDER:
        values = proportions[label].values
        ax.bar(
            models,
            values,
            bottom=bottom,
            color=STATUS[label],
            edgecolor=SURFACE,
            linewidth=1,
            label=label,
            zorder=3,
        )
        bottom += values
    ax.set_ylim(0, 100)
    ax.set_ylabel("Share of runs (%)", color=INK_SECONDARY)
    ax.set_title("Behavioural classification by model", color=INK_PRIMARY, fontsize=11, loc="left")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8)
    _style_axes(ax)

    fig.tight_layout()
    fig.savefig(out_dir / "03_behaviour_distribution.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def fig_failure_attribution(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    failed = df[df["primary_failure"].astype(str).str.len() > 0]
    if failed.empty:
        print("  (skipping 04_failure_attribution.png: no run has a recorded primary_failure)")
        return

    counts = (
        failed.groupby(["model_label", "primary_failure"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=models, fill_value=0)
    )
    counts = counts.reindex(columns=[e for e in EVALUATOR_NAMES if e in counts.columns])
    colors = {name: CATEGORICAL[i % len(CATEGORICAL)] for i, name in enumerate(counts.columns)}

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    bottom = np.zeros(len(models))
    for name in counts.columns:
        values = counts[name].values
        ax.bar(
            models,
            values,
            bottom=bottom,
            color=colors[name],
            edgecolor=SURFACE,
            linewidth=1,
            label=name,
            zorder=3,
        )
        bottom += values
    ax.set_ylabel("Runs where this was the primary failure", color=INK_SECONDARY)
    ax.set_title("Primary failure cause by model", color=INK_PRIMARY, fontsize=11, loc="left")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8)
    _style_axes(ax)

    fig.tight_layout()
    fig.savefig(out_dir / "04_failure_attribution.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def fig_radar_profiles(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    colors = model_colors(models)
    score_cols = [f"score_{name}" for name in EVALUATOR_NAMES]
    pivot = df.groupby("model_label")[score_cols].mean().reindex(models)

    n = len(EVALUATOR_NAMES)
    angles = [i / n * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"}, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(EVALUATOR_NAMES, fontsize=8, color=INK_SECONDARY)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color=INK_MUTED)
    ax.grid(color=GRIDLINE)
    ax.spines["polar"].set_color(BASELINE)

    for i, label in enumerate(models):
        values = list(pivot.loc[label].values)
        values += values[:1]
        ax.plot(
            angles,
            values,
            linewidth=1.8,
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            marker=MARKERS[i % len(MARKERS)],
            markersize=4,
            color=colors[label],
            label=label,
        )
        ax.fill(angles, values, color=colors[label], alpha=0.06)

    ax.set_title("Per-evaluator profile by model", color=INK_PRIMARY, fontsize=11, y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=False, fontsize=8)

    fig.tight_layout()
    fig.savefig(out_dir / "06_radar_profiles.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def write_summary_table(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    score_cols = [f"score_{name}" for name in EVALUATOR_NAMES]
    summary = (
        df.groupby("model_label")
        .agg(
            n_runs=("run_id", "count"),
            mean_cts_raw=("cts_raw", "mean"),
            std_cts_raw=("cts_raw", "std"),
            mean_cts_reported=("cts_reported", "mean"),
            critical_failure_rate=("critical_failure", "mean"),
        )
        .reindex(models)
    )
    per_evaluator = df.groupby("model_label")[score_cols].mean().reindex(models)
    per_evaluator.columns = [f"mean_{name}" for name in EVALUATOR_NAMES]
    summary = summary.join(per_evaluator)
    summary.to_csv(out_dir / "summary_table.csv")

    with (out_dir / "summary_table.tex").open("w", encoding="utf-8") as fh:
        fh.write(
            "% Auto-generated by generate_report_figures.py -- edit the source data,\n"
            "% not this file.\n"
        )
        fh.write(summary.round(1).to_latex(na_rep="--"))

    print(f"  wrote {out_dir / 'summary_table.csv'} and summary_table.tex")


def write_headline_summary(df: pd.DataFrame, out_dir: Path) -> None:
    models = model_order(df)
    means = df.groupby("model_label")["cts_raw"].mean().reindex(models)
    critical_failure_rates = df.groupby("model_label")["critical_failure"].mean().reindex(models)
    score_cols = [f"score_{name}" for name in EVALUATOR_NAMES]
    per_evaluator = df.groupby("model_label")[score_cols].mean().reindex(models)
    per_evaluator.columns = list(EVALUATOR_NAMES)

    lines = [
        f"Best overall (CTS, raw/uncapped): {means.index[0]} ({means.iloc[0]:.1f})",
        f"Worst overall (CTS, raw/uncapped): {means.index[-1]} ({means.iloc[-1]:.1f})",
        "",
        "Critical-failure rate by model (share of runs clamped to a reported CTS of 30):",
        *[f"  {label}: {critical_failure_rates.get(label, 0) * 100:.0f}%" for label in models],
        "",
        "Per-evaluator strongest / weakest model:",
    ]
    for name in EVALUATOR_NAMES:
        col = per_evaluator[name]
        lines.append(
            f"  {name}: strongest = {col.idxmax()} ({col.max():.1f}), "
            f"weakest = {col.idxmin()} ({col.min():.1f})"
        )

    behaviour = df.groupby(["model_label", "behaviour_classification"]).size().unstack(fill_value=0)
    behaviour_pct = behaviour.div(behaviour.sum(axis=1), axis=0) * 100
    lines += ["", "Behavioural classification mix (% of runs):"]
    for label in models:
        row = behaviour_pct.loc[label] if label in behaviour_pct.index else None
        if row is None:
            continue
        parts = ", ".join(f"{cls}={row.get(cls, 0):.0f}%" for cls in BEHAVIOUR_ORDER)
        lines.append(f"  {label}: {parts}")

    text = "\n".join(lines) + "\n"
    (out_dir / "summary.txt").write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing results.csv (from run_benchmark_suite.py).",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_csv = results_dir / "results.csv"
    if not results_csv.exists():
        raise SystemExit(f"No results.csv found at {results_csv}")

    df = pd.read_csv(results_csv)
    df = df[df["status"] == "ok"].copy()
    if df.empty:
        raise SystemExit(f"No successful ('status'=='ok') rows in {results_csv}")

    out_dir = results_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loaded {len(df)} successful runs across {df['model_label'].nunique()} models.")
    fig_cts_overview(df, out_dir)
    print("  wrote 01_cts_overview.png")
    fig_evaluator_heatmap(df, out_dir)
    print("  wrote 02_evaluator_heatmap.png")
    fig_behaviour_distribution(df, out_dir)
    print("  wrote 03_behaviour_distribution.png")
    fig_failure_attribution(df, out_dir)
    fig_radar_profiles(df, out_dir)
    print("  wrote 06_radar_profiles.png")
    write_summary_table(df, out_dir)
    write_headline_summary(df, out_dir)
    print(f"Done. Figures in {out_dir}")


if __name__ == "__main__":
    main()
