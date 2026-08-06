"""
Genereert een chart-afbeelding bij een golden pocket-signaal: candles met de
swing-high/low, de golden pocket-zone, en de entry-candle gemarkeerd.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def generate_chart(df: pd.DataFrame, result: dict, symbol: str, timeframe: str, direction: str,
                    out_path: str, lookback: int = 60):
    n = len(df)
    start = max(0, n - lookback)
    plot_df = df.iloc[start:n].reset_index(drop=True)
    dates = pd.to_datetime(plot_df["timestamp"], unit="ms")

    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="#c9d1d9", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#30363d")
    ax.grid(True, color="#21262d", linewidth=0.5)

    for i, row in plot_df.iterrows():
        color = "#26a69a" if row["close"] >= row["open"] else "#ef5350"
        ax.plot([i, i], [row["low"], row["high"]], color=color, linewidth=1)
        ax.plot([i, i], [row["open"], row["close"]], color=color, linewidth=5)

    marker_color = "#26a69a" if direction == "LONG" else "#ef5350"

    if result.get("zone_low") is not None:
        ax.axhspan(result["zone_low"], result["zone_high"], color="#f0a500", alpha=0.15)
        ax.text(0, result["zone_high"], f"  Golden Pocket ({result['zone_low']:.2f} - {result['zone_high']:.2f})",
                color="#f0a500", fontsize=8, va="bottom")

    for label_key, price_key, color in [("swing_high_index", "swing_high_price", "#8b949e"),
                                          ("swing_low_index", "swing_low_price", "#8b949e")]:
        idx = result.get(label_key)
        price = result.get(price_key)
        if idx is not None and price is not None:
            idx_in_plot = idx - start
            if 0 <= idx_in_plot < len(plot_df):
                ax.scatter([idx_in_plot], [price], color=color, s=40, zorder=5, marker="D")

    last_x = len(plot_df) - 1
    entry_y = plot_df["close"].iloc[-1]
    ax.annotate(
        f"GOLDEN POCKET\n({direction})",
        xy=(last_x, entry_y),
        xytext=(last_x - 12, entry_y + (3 if direction == "SHORT" else -3)),
        color="#ffffff", fontsize=9, fontweight="bold", ha="center",
        arrowprops=dict(arrowstyle="->", color=marker_color, lw=1.8)
    )

    ax.set_title(f"{symbol}  ·  {timeframe}  ·  Kraken", color="#c9d1d9", fontsize=11, loc="left")
    fig.suptitle(f"{symbol}  {timeframe}  —  Golden Pocket {direction}",
                 color=marker_color, fontsize=13, y=0.99, fontweight="bold")
    ax.set_ylabel("Prijs", color="#c9d1d9", fontsize=9)

    n_ticks = 6
    tick_positions = list(range(0, len(plot_df), max(1, len(plot_df) // n_ticks)))
    tick_labels = [dates.iloc[i].strftime("%m-%d %H:%M") for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=30, ha="right")

    plt.tight_layout()
    plt.savefig(out_path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
