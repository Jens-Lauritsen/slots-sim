"""
Statistical Analysis
====================
Functions that operate on simulation results to produce summary reports,
tables, and formatted text output suitable for inclusion in a README or
Jupyter notebook.

These helpers abstract away the raw data structures so that the main
script (main.py) stays clean and declarative.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .simulator import PlayerResult


def build_player_dataframe(results: List[PlayerResult]) -> pd.DataFrame:
    """Convert a list of PlayerResult into a pandas DataFrame.

    Parameters
    ----------
    results : List[PlayerResult]
        Output of one simulation run.

    Returns
    -------
    pd.DataFrame
        Columns: player_id, starting_balance, final_balance, bet_size,
        spins_completed, total_wagered, total_winnings, profit, went_broke.
    """
    records = [
        {
            "player_id": r.player_id,
            "starting_balance": r.starting_balance,
            "final_balance": r.final_balance,
            "bet_size": r.bet_size,
            "spins_completed": r.spins_completed,
            "total_wagered": r.total_wagered,
            "total_winnings": r.total_winnings,
            "profit": r.profit,
            "went_broke": r.went_broke,
        }
        for r in results
    ]
    return pd.DataFrame(records)


def summary_table(aggregate: Dict[str, Any]) -> pd.DataFrame:
    """Produce a one-row summary DataFrame from an aggregate dictionary.

    Parameters
    ----------
    aggregate : dict
        The dictionary returned by ``Simulator.run()`` (minus the raw
        player_results list — which is too large for a table).

    Returns
    -------
    pd.DataFrame
    """
    rows = {}
    # Copy all scalar values, skip config dicts and raw lists
    for key, value in aggregate.items():
        if isinstance(value, (dict, list)):
            continue
        rows[key] = value

    # Add a few derived columns
    if "avg_profit" in aggregate:
        rows["avg_loss_per_player"] = -aggregate["avg_profit"]
    if "biggest_winner" in aggregate:
        winner: PlayerResult = aggregate["biggest_winner"]
        rows["biggest_winner_id"] = winner.player_id
        rows["biggest_winner_profit"] = winner.profit
        rows["biggest_winner_final"] = winner.final_balance
    if "biggest_loser" in aggregate:
        loser: PlayerResult = aggregate["biggest_loser"]
        rows["biggest_loser_id"] = loser.player_id
        rows["biggest_loser_profit"] = loser.profit
        rows["biggest_loser_final"] = loser.final_balance

    return pd.DataFrame([rows])


def convergence_table(convergence_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build a DataFrame showing how RTP converges with spin count.

    Parameters
    ----------
    convergence_results : list of dict
        Output of ``Simulator.convergence_study()``.

    Returns
    -------
    pd.DataFrame
    """
    rows = []
    for r in convergence_results:
        config = r["config"]
        rows.append(
            {
                "spins_per_player": config.num_spins,
                "num_players": config.num_players,
                "total_spins": config.num_spins * config.num_players,
                "theoretical_rtp": f"{r['theoretical_rtp']:.2f}%",
                "simulated_rtp": f"{r['simulated_rtp']:.2f}%",
                "deviation": f"{abs(r['simulated_rtp'] - r['theoretical_rtp']):.3f} pp",
                "avg_profit": f"{r['avg_profit']:.2f}",
                "pct_lost_money": f"{r['pct_lost_money']:.1f}%",
            }
        )
    return pd.DataFrame(rows)


def quantile_summary(results: List[PlayerResult]) -> pd.DataFrame:
    """Percentile breakdown of final balances.

    Parameters
    ----------
    results : List[PlayerResult]

    Returns
    -------
    pd.DataFrame
    """
    balances = np.array([r.final_balance for r in results])
    percentiles = [0, 5, 10, 25, 50, 75, 90, 95, 100]
    values = np.percentile(balances, percentiles)

    return pd.DataFrame(
        {"percentile": [f"{p}%" for p in percentiles], "balance": values}
    )


def format_report(aggregate: Dict[str, Any]) -> str:
    """Produce a human-readable text report from simulation aggregates.

    Parameters
    ----------
    aggregate : dict
        Output of ``Simulator.run()``.

    Returns
    -------
    str
    """
    config = aggregate["config"]
    lines = [
        "=" * 60,
        "           MONTE CARLO SLOT SIMULATION REPORT",
        "=" * 60,
        "",
        "─ Configuration ─",
        f"  Players:              {config.num_players:>12,}",
        f"  Starting balance:     {config.starting_balance:>12.0f} kr",
        f"  Bet size:             {config.bet_size:>12.0f} kr",
        f"  Max spins per player: {config.num_spins:>12,}",
        "",
        "─ Theoretical Properties ─",
        f"  RTP (Return to Player): {aggregate['theoretical_rtp']:>7.2f}%",
        f"  House Edge:             {aggregate['house_edge']:>7.2f}%",
        "",
        "─ Simulation Results ─",
        f"  Total wagered (all players):     {aggregate['total_wagered_all']:>12,.0f} kr",
        f"  Total winnings (all players):    {aggregate['total_winnings_all']:>12,.0f} kr",
        f"  Simulated RTP:                   {aggregate['simulated_rtp']:>12.4f}%",
        f"  Deviation from theoretical:      "
        f"{abs(aggregate['simulated_rtp'] - aggregate['theoretical_rtp']):>10.4f} pp",
        "",
        "─ Player Outcomes ─",
        f"  Average final balance:   {aggregate['avg_final_balance']:>10.2f} kr",
        f"  Median final balance:    {aggregate['median_final_balance']:>10.2f} kr",
        f"  Std dev of balances:     {aggregate['std_final_balance']:>10.2f} kr",
        f"  Average profit:          {aggregate['avg_profit']:>10.2f} kr",
        f"  Median profit:           {aggregate['median_profit']:>10.2f} kr",
        f"  Average loss per player: {-aggregate['avg_profit']:>10.2f} kr",
        "",
        "─ Win / Loss Breakdown ─",
        f"  Players who lost money:  {aggregate['pct_lost_money']:>7.1f}%",
        f"  Players who made money:  {aggregate['pct_made_money']:>7.1f}%",
        f"  Players who broke even:  {aggregate['pct_broke_even']:>7.1f}%",
        "",
        "─ Extremes ─",
    ]

    winner: PlayerResult = aggregate["biggest_winner"]
    loser: PlayerResult = aggregate["biggest_loser"]
    lines.append(
        f"  Biggest winner:  Player #{winner.player_id:>6,}  "
        f"Profit: {winner.profit:>10,.0f} kr  "
        f"Final: {winner.final_balance:>10,.0f} kr"
    )
    lines.append(
        f"  Biggest loser:   Player #{loser.player_id:>6,}  "
        f"Profit: {loser.profit:>10,.0f} kr  "
        f"Final: {loser.final_balance:>10,.0f} kr"
    )
    lines.append("")
    lines.append("=" * 60)
    lines.append("  CONCLUSION: The house always wins in the long run.")
    lines.append("=" * 60)

    return "\n".join(lines)
