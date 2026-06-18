
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Outcome:
    name: str
    probability: float
    payout: float

    def __post_init__(self) -> None:
        if not (0 <= self.probability <= 1):
            raise ValueError(f"Probability must be in [0, 1], got {self.probability}")
        if self.payout < 0:
            raise ValueError(f"Payout cannot be negative, got {self.payout}")


class SlotMachine:

    def __init__(self, outcomes: Sequence[Outcome], seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._outcomes: List[Outcome] = list(outcomes)
        total = sum(o.probability for o in self._outcomes)
        if total <= 0:
            raise ValueError("At least one outcome must have probability > 0")

        self._outcomes = [
            Outcome(o.name, o.probability / total, o.payout) for o in self._outcomes
        ]

        self._cumulative: List[Tuple[float, Outcome]] = []
        cum = 0.0
        for outcome in self._outcomes:
            cum += outcome.probability
            self._cumulative.append((cum, outcome))
        self._cumulative[-1] = (1.0, self._outcomes[-1])

    @property
    def outcomes(self) -> List[Outcome]:
        return list(self._outcomes)

    def spin(self) -> Outcome:
        r = self._rng.random()  # uniform in [0.0, 1.0)
        for threshold, outcome in self._cumulative:
            if r < threshold:
                return outcome
        return self._cumulative[-1][1]

    def theoretical_rtp(self) -> float:
        rtp = sum(o.probability * o.payout for o in self._outcomes)
        return rtp * 100.0

    def house_edge(self) -> float:
        return 100.0 - self.theoretical_rtp()

    def expected_value(self, bet_size: float = 1.0) -> float:
        rtp_decimal = self.theoretical_rtp() / 100.0
        return (rtp_decimal - 1.0) * bet_size

    @classmethod
    def create_classic(cls, seed: int | None = None) -> "SlotMachine":
        outcomes = [
            Outcome("Loss",    0.45,  0),
            Outcome("Cherry",  0.35,  1),
            Outcome("Lemon",   0.12,  2),
            Outcome("Diamond", 0.06,  3),
            Outcome("Seven",   0.015, 10),
            Outcome("Jackpot", 0.005, 10),
        ]
        return cls(outcomes, seed=seed)

    @classmethod
    def create_high_rtp(cls, seed: int | None = None) -> "SlotMachine":
        outcomes = [
            Outcome("Loss",    0.53,  0),
            Outcome("Cherry",  0.28,  1),
            Outcome("Lemon",   0.11,  2),
            Outcome("Diamond", 0.05,  4),
            Outcome("Seven",   0.025, 8),
            Outcome("Jackpot", 0.005, 10),
        ]
        return cls(outcomes, seed=seed)

    def __repr__(self) -> str:
        return (
            f"SlotMachine(rtp={self.theoretical_rtp():.2f}%, "
            f"house_edge={self.house_edge():.2f}%)"
        )
