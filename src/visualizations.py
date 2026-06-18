"""
Visualizations
==============
Matplotlib-based charts that illustrate the key mathematical insights:
    1. House edge convergence (law of large numbers)
    2. Individual player balance trajectories
    3. Final balance distribution histogram
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

from .simulator import PlayerResult


# ---------------------------------------------------------------------------
# Global style settings — applied once to give the project a consistent look
# ---------------------------------------------------------------------------

_STYLE_APPLIED = False


def _apply_style() -> None:
    """Apply a clean, publication-ready matplotlib style."""
    global _STYLE_APPLIED
    if _STYLE_APPLIED:
        return
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
        }
    )
    _STYLE_APPLIED = True


# ---------------------------------------------------------------------------
# Chart 1: House edge convergence
# ---------------------------------------------------------------------------


def plot_rtp_convergence(
    convergence_results: List[Dict[str, Any]],
    save_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Plot how simulated RTP approaches theoretical RTP as spins increase.

    This is the visual embodiment of the law of large numbers: the more spins
    we observe, the closer the actual return gets to the mathematical
    expectation.

    Parameters
    ----------
    convergence_results : list of dict
        Output of ``Simulator.convergence_study()``.
    save_path : str or Path, optional
        If provided, save the figure to this path.

    Returns
    -------
    plt.Figure
    """
    _apply_style()

    spin_counts = np.array([r["config"].num_spins for r in convergence_results])
    simulated_rtps = np.array([r["simulated_rtp"] for r in convergence_results])
    theoretical_rtp = convergence_results[0]["theoretical_rtp"]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Simulated RTP as points + line
    ax.plot(spin_counts, simulated_rtps, "o-", color="#2196F3", linewidth=2,
            markersize=7, label="Simulated RTP", zorder=3)

    # Theoretical RTP as a horizontal reference line
    ax.axhline(y=theoretical_rtp, color="#D32F2F", linewidth=2, linestyle="--",
               label=f"Theoretical RTP = {theoretical_rtp:.2f}%", zorder=2)

    ax.set_xscale("log")
    ax.set_xlabel("Spins per player (log scale)")
    ax.set_ylabel("Return to Player (%)")
    ax.set_title("House Edge Convergence — Simulated RTP Approaches Theory")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    # Add a text annotation explaining the insight
    ax.annotate(
        "With few spins, luck dominates.\n"
        "With many spins, math dominates.",
        xy=(spin_counts[0], simulated_rtps[0]),
        xytext=(0.35, 0.15),
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->", color="gray",
                        connectionstyle="arc3,rad=-0.2"),
        fontsize=10,
        color="gray",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
        print(f"  ✓ Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Chart 2: Player balance trajectories
# ---------------------------------------------------------------------------


def plot_player_trajectories(
    results: List[PlayerResult],
    num_trajectories: int = 20,
    save_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Plot balance-over-time for a sample of players.

    This chart shows that while *some* players are temporarily profitable,
    the overall trend is downward — the house edge grinds away at every bet.

    Parameters
    ----------
    results : list of PlayerResult
    num_trajectories : int
        How many individual player lines to draw.
    save_path : str or Path, optional
        If provided, save the figure to this path.

    Returns
    -------
    plt.Figure

    Notes
    -----
    Because we don't store per-spin balances (only final results), we
    simulate fresh trajectories here.  For large num_trajectories this is
    fast enough to run interactively.
    """
    _apply_style()

    # Grab config from the first result's data
    if not results:
        raise ValueError("No results provided")

    ref = results[0]
    starting_balance = ref.starting_balance
    bet_size = ref.bet_size
    max_spins = ref.spins_completed  # rough upper bound

    # We'll simulate fresh trajectories so we have per-spin data
    from .slot_machine import SlotMachine

    # Pick a deterministic seed so the chart is reproducible
    machine = SlotMachine.create_classic(seed=12345)

    fig, ax = plt.subplots(figsize=(12, 6))

    balances_over_time: List[np.ndarray] = []
    max_observed_spins = 0

    for i in range(num_trajectories):
        balance = starting_balance
        history = [balance]

        for _ in range(max_spins):
            if balance < bet_size:
                break
            outcome = machine.spin()
            balance -= bet_size
            balance += bet_size * outcome.payout
            history.append(balance)

        # Extend to a common length with NaN padding so we can plot
        balances = np.array(history)
        max_observed_spins = max(max_observed_spins, len(history))
        balances_over_time.append(balances)

    # Plot each trajectory
    for i, balances in enumerate(balances_over_time):
        spins = np.arange(len(balances))
        # Use a colour gradient based on final profit
        profit = balances[-1] - starting_balance
        color = "#4CAF50" if profit > 0 else "#F44336"
        alpha = 0.6
        ax.plot(spins, balances, color=color, alpha=alpha, linewidth=0.8)

    # Add the starting balance reference line
    ax.axhline(y=starting_balance, color="gray", linestyle="--", linewidth=1,
               label=f"Starting balance = {starting_balance:,.0f} kr")

    ax.set_xlabel("Spin number")
    ax.set_ylabel("Balance (kr)")
    ax.set_title(
        f"Balance Trajectories for {num_trajectories} Simulated Players\n"
        f"(Green = profitable, Red = losing at end)"
    )
    ax.legend(loc="upper right")

    # Add an annotation
    ax.annotate(
        f"House edge: {machine.house_edge():.1f}% per spin",
        xy=(0.98, 0.05),
        xycoords="axes fraction",
        ha="right",
        fontsize=10,
        color="gray",
    )

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
        print(f"  ✓ Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Chart 3: Final balance distribution histogram
# ---------------------------------------------------------------------------


def plot_balance_distribution(
    results: List[PlayerResult],
    save_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Plot a histogram of final player balances.

    The distribution is typically right-skewed: most players cluster below
    the starting balance (losers), with a long thin tail of winners.

    Parameters
    ----------
    results : list of PlayerResult
    save_path : str or Path, optional

    Returns
    -------
    plt.Figure
    """
    _apply_style()

    final_balances = np.array([r.final_balance for r in results])
    profits = np.array([r.profit for r in results])
    starting_balance = results[0].starting_balance

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # ---------- Left: histogram of final balances ----------
    bins = 60
    ax1.hist(final_balances, bins=bins, color="#607D8B", edgecolor="white",
             alpha=0.85)

    # Mark starting balance
    ax1.axvline(x=starting_balance, color="#D32F2F", linewidth=2, linestyle="--",
                label=f"Starting balance ({starting_balance:,.0f} kr)")

    # Mark mean final balance
    mean_bal = np.mean(final_balances)
    ax1.axvline(x=mean_bal, color="#2196F3", linewidth=2, linestyle="-.",
                label=f"Mean final ({mean_bal:,.0f} kr)")

    ax1.set_xlabel("Final balance (kr)")
    ax1.set_ylabel("Number of players")
    ax1.set_title("Distribution of Final Player Balances")
    ax1.legend(fontsize=9)

    # ---------- Right: histogram of profits ----------
    ax2.hist(profits, bins=bins, color="#FF9800", edgecolor="white",
             alpha=0.85)

    # Mark zero-profit line
    ax2.axvline(x=0, color="#4CAF50", linewidth=2, linestyle="--",
                label="Break-even")
    ax2.axvline(x=np.mean(profits), color="#D32F2F", linewidth=2,
                linestyle="-.", label=f"Mean profit ({np.mean(profits):,.0f} kr)")

    ax2.set_xlabel("Profit (kr)")
    ax2.set_ylabel("Number of players")
    ax2.set_title("Distribution of Player Profits")
    ax2.legend(fontsize=9)

    # Summary stats text box
    pct_lost = np.sum(profits < 0) / len(profits) * 100
    pct_won = np.sum(profits > 0) / len(profits) * 100
    text = (
        f"Players: {len(results):,}\n"
        f"Lost money: {pct_lost:.1f}%\n"
        f"Made money: {pct_won:.1f}%\n"
        f"Avg loss: {-np.mean(profits):,.0f} kr"
    )
    ax2.text(
        0.98, 0.97, text, transform=ax2.transAxes,
        fontsize=10, verticalalignment="top", horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85),
    )

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
        print(f"  ✓ Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Chart 4: Cumulative profit over time (optional bonus chart)
# ---------------------------------------------------------------------------


def plot_cumulative_profit(
    results: List[PlayerResult],
    sample_size: int = 50,
    save_path: Optional[str | Path] = None,
) -> plt.Figure:
    """Plot cumulative profit for a sample of players over their entire session.

    Unlike the trajectory chart, this shows the accumulated profit (net of
    starting balance) so you can directly see who is up and who is down.

    Parameters
    ----------
    results : list of PlayerResult
    sample_size : int
        Number of players to plot.
    save_path : str or Path, optional

    Returns
    -------
    plt.Figure
    """
    _apply_style()

    from .slot_machine import SlotMachine

    ref = results[0]
    machine = SlotMachine.create_classic(seed=42)

    fig, ax = plt.subplots(figsize=(12, 5))

    for i in range(min(sample_size, len(results))):
        balance = ref.starting_balance
        cumulative: List[float] = [0.0]  # profit from start

        for _ in range(ref.spins_completed):
            if balance < ref.bet_size:
                break
            outcome = machine.spin()
            balance -= ref.bet_size
            winnings = ref.bet_size * outcome.payout
            balance += winnings
            cumulative.append(balance - ref.starting_balance)

        spins = np.arange(len(cumulative))
        profit = cumulative[-1]
        color = "#4CAF50" if profit > 0 else "#F44336"
        ax.plot(spins, cumulative, color=color, alpha=0.5, linewidth=0.6)

    # Mean trajectory (thick black line)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=1,
               label="Break-even")
    ax.set_xlabel("Spin number")
    ax.set_ylabel("Cumulative profit (kr)")
    ax.set_title(
        f"Cumulative Profit Trajectories ({sample_size} players)\n"
        f"Theoretical expected profit per spin: {machine.expected_value(ref.bet_size):.2f} kr"
    )
    ax.legend()

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
        print(f"  ✓ Saved: {save_path}")

    return fig
