"""Regras e cálculos do caça-níquel."""

from __future__ import annotations

from dataclasses import dataclass
import random

Symbol = tuple[str, int, float]

SYMBOLS: tuple[Symbol, ...] = (
    ("CHERRY", 22, 5.0),
    ("LEMON", 20, 3.0),
    ("ORANGE", 18, 3.5),
    ("PLUM", 16, 4.5),
    ("BELL", 12, 7.0),
    ("STAR", 10, 9.0),
    ("BAR", 8, 12.0),
    ("SEVEN", 4, 20.0),
)

SYMBOL_NAMES = [s[0] for s in SYMBOLS]
SYMBOL_WEIGHTS = [s[1] for s in SYMBOLS]
SYMBOL_MULTIPLIERS = {s[0]: s[2] for s in SYMBOLS}


@dataclass
class SpinResult:
    symbols: tuple[str, str, str]
    aposta: float
    ganho: float

    @property
    def venceu(self) -> bool:
        return self.ganho > 0

    @property
    def lucro(self) -> float:
        return self.ganho - self.aposta


class SlotMachine:
    """Gerencia o saldo e resolve resultados de giros."""

    def __init__(self, saldo_inicial: float) -> None:
        if saldo_inicial <= 0:
            raise ValueError("O saldo inicial precisa ser maior que zero.")
        self._saldo = float(saldo_inicial)

    @property
    def saldo(self) -> float:
        return round(self._saldo, 2)

    def pode_apostar(self, valor: float) -> bool:
        return 0 < valor <= self._saldo

    def girar(self, aposta: float) -> SpinResult:
        if not self.pode_apostar(aposta):
            raise ValueError("A aposta precisa ser positiva e menor ou igual ao saldo.")

        simbolos = tuple(random.choices(SYMBOL_NAMES, weights=SYMBOL_WEIGHTS, k=3))
        ganho = self._calcular_premio(simbolos, aposta)

        self._saldo -= aposta
        if ganho > 0:
            self._saldo += ganho

        return SpinResult(symbols=simbolos, aposta=float(aposta), ganho=ganho)

    @staticmethod
    def _calcular_premio(simbolos: tuple[str, str, str], aposta: float) -> float:
        c1, c2, c3 = simbolos

        if c1 == c2 == c3:
            multiplicador = SYMBOL_MULTIPLIERS.get(c1, 0)
            return aposta * multiplicador

        if c1 == c2 or c2 == c3 or c1 == c3:
            return aposta * 0.5

        if {c1, c2, c3} == {"BAR", "STAR", "SEVEN"}:
            return aposta * 5

        return 0.0
