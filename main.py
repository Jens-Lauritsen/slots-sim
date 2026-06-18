from __future__ import annotations

import os
from pathlib import Path

from src.slot_machine import SlotMachine
from src.simulator import SimulationConfig, Simulator
from src.analysis import (
    build_player_dataframe,
    convergence_table,
    format_report,
    quantile_summary,
    summary_table,
)
from src.visualizations import (
    plot_balance_distribution,
    plot_cumulative_profit,
    plot_player_trajectories,
    plot_rtp_convergence,
)


OUTPUT_DIR = Path("visualizations")
SEED = 42  # deterministic seed so results are reproducible

NUM_PLAYERS = 10_000
STARTING_BALANCE = 1000.0
BET_SIZE = 10.0  # kr
NUM_SPINS = 10_000

SPIN_COUNTS = [100, 1_000, 5_000, 10_000, 50_000, 100_000]
CONVERGENCE_PLAYERS = 1_000

def main() -> None:
    """Run the full demonstration."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  THE MATHEMATICS OF GAMBLING: Why the House Always Wins")
    print("=" * 60)
    print()

    machine = SlotMachine.create_classic(seed=SEED)

    print("Slot Machine Configuration")
    print("-" * 40)
    print(f"  {'Outcome':<12} {'Probability':>10}  {'Payout':>8}")
    print(f"  {'─' * 12} {'─' * 10}  {'─' * 8}")
    for o in machine.outcomes:
        print(f"  {o.name:<12} {o.probability:>9.1%}  {o.payout:>5.0f}x")

    print()
    print("Theoretical Properties")
    print("-" * 40)
    print(f"  RTP (Return to Player):  {machine.theoretical_rtp():>6.2f}%")
    print(f"  House Edge:              {machine.house_edge():>6.2f}%")
    print(f"  Expected value (10 kr bet): {machine.expected_value(10.0):>+.2f} kr")
    print()
    print(
        "  Every 10 kr spin costs the player "
        f"{-machine.expected_value(10.0):.2f} kr on average."
    )
    print()
    print("Running Monte Carlo Simulation...")
    print(f"     {NUM_PLAYERS:,} players × {NUM_SPINS:,} spins")
    print()

    sim = Simulator(machine)
    config = SimulationConfig(
        num_players=NUM_PLAYERS,
        starting_balance=STARTING_BALANCE,
        bet_size=BET_SIZE,
        num_spins=NUM_SPINS,
    )
    aggregate = sim.run(config)

    print(format_report(aggregate))
    print()

    print("Percentile Breakdown of Final Balances")
    print("-" * 40)
    quantiles = quantile_summary(aggregate["player_results"])
    print(quantiles.to_string(index=False))
    print()


    print("Convergence Study — RTP vs. Spin Count")
    print("-" * 40)
    convergence = sim.convergence_study(
        num_players=CONVERGENCE_PLAYERS,
        starting_balance=STARTING_BALANCE * 10, 
        bet_size=BET_SIZE,
        spin_counts=SPIN_COUNTS,
    )
    print(convergence_table(convergence).to_string(index=False))
    print()
    print("Generating visualisations...")
    print()

    plot_rtp_convergence(
        convergence, save_path=OUTPUT_DIR / "01_rtp_convergence.png"
    )

    plot_player_trajectories(
        aggregate["player_results"],
        num_trajectories=25,
        save_path=OUTPUT_DIR / "02_player_trajectories.png",
    )

    plot_balance_distribution(
        aggregate["player_results"],
        save_path=OUTPUT_DIR / "03_balance_distribution.png",
    )

    plot_cumulative_profit(
        aggregate["player_results"],
        sample_size=50,
        save_path=OUTPUT_DIR / "04_cumulative_profit.png",
    )

    print("Key takeaways:")
    print(f"      • The theoretical house edge is {machine.house_edge():.2f}%.")
    print(f"      • {aggregate['pct_lost_money']:.1f}% of simulated players lost money.")
    print( "      • A few players won, but the *average* player lost.")
    print( "      • Over millions of spins, results converge to the math.")
    print( "      • Casinos don't need to cheat — probability does the work.")
    print()


if __name__ == "__main__":
    main()
