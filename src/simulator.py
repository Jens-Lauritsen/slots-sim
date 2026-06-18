from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .slot_machine import Outcome, SlotMachine


@dataclass
class PlayerResult:
    player_id: int
    starting_balance: float
    final_balance: float
    bet_size: float
    spins_completed: int
    total_wagered: float
    total_winnings: float
    profit: float
    went_broke: bool


@dataclass
class SimulationConfig:
    num_players: int
    starting_balance: float
    bet_size: float
    num_spins: int


class Simulator:

    def __init__(self, machine: SlotMachine) -> None:
        self._machine = machine



    def run(self, config: SimulationConfig) -> dict:
        player_results = self._simulate_players(config)
        aggregate = self._compute_aggregates(player_results)
        aggregate["config"] = config
        aggregate["player_results"] = player_results
        return aggregate


    def _simulate_players(self, config: SimulationConfig) -> List[PlayerResult]:
        results: List[PlayerResult] = []

        for player_id in range(config.num_players):
            result = self._simulate_one_player(config, player_id)
            results.append(result)

        return results

    def _simulate_one_player(
        self, config: SimulationConfig, player_id: int
    ) -> PlayerResult:
        balance = config.starting_balance
        total_winnings = 0.0
        spins_completed = 0
        went_broke = False

        for _ in range(config.num_spins):
            if balance < config.bet_size:
                went_broke = True
                break

            outcome: Outcome = self._machine.spin()
            balance -= config.bet_size
            winnings = config.bet_size * outcome.payout
            balance += winnings
            total_winnings += winnings
            spins_completed += 1

        total_wagered = spins_completed * config.bet_size

        return PlayerResult(
            player_id=player_id,
            starting_balance=config.starting_balance,
            final_balance=balance,
            bet_size=config.bet_size,
            spins_completed=spins_completed,
            total_wagered=total_wagered,
            total_winnings=total_winnings,
            profit=balance - config.starting_balance,
            went_broke=went_broke,
        )

    def _compute_aggregates(self, results: List[PlayerResult]) -> dict:
        final_balances = np.array([r.final_balance for r in results])
        profits = np.array([r.profit for r in results])
        total_wagered_all = sum(r.total_wagered for r in results)
        total_winnings_all = sum(r.total_winnings for r in results)

        simulated_rtp = (
            (total_winnings_all / total_wagered_all * 100.0)
            if total_wagered_all > 0
            else 0.0
        )

        num_lost = int(np.sum(profits < 0))
        num_made = int(np.sum(profits > 0))
        num_broke_even = int(np.sum(profits == 0))

        return {
            "avg_final_balance": float(np.mean(final_balances)),
            "median_final_balance": float(np.median(final_balances)),
            "std_final_balance": float(np.std(final_balances)),
            "avg_profit": float(np.mean(profits)),
            "median_profit": float(np.median(profits)),
            "total_wagered_all": float(total_wagered_all),
            "total_winnings_all": float(total_winnings_all),
            "simulated_rtp": float(simulated_rtp),
            "theoretical_rtp": float(self._machine.theoretical_rtp()),
            "house_edge": float(self._machine.house_edge()),
            "pct_lost_money": num_lost / len(results) * 100.0,
            "pct_made_money": num_made / len(results) * 100.0,
            "pct_broke_even": num_broke_even / len(results) * 100.0,
            "biggest_winner": max(results, key=lambda r: r.profit),
            "biggest_loser": min(results, key=lambda r: r.profit),
            "num_players": len(results),
        }

    def convergence_study(
        self,
        num_players: int,
        starting_balance: float,
        bet_size: float,
        spin_counts: List[int],
    ) -> List[dict]:
        results = []
        for spins in spin_counts:
            config = SimulationConfig(
                num_players=num_players,
                starting_balance=starting_balance,
                bet_size=bet_size,
                num_spins=spins,
            )
            result = self.run(config)
            results.append(result)
        return results
