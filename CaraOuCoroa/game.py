"""Regras e estado do jogo Cara ou Coroa."""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class RoundResult:
    escolha: str
    aposta: float
    resultado_moeda: str
    venceu: bool


class CoinGame:
    """Controla o saldo e o resultado das apostas."""

    def __init__(self, saldo_inicial: float) -> None:
        if saldo_inicial <= 0:
            raise ValueError("O saldo inicial precisa ser maior que zero.")
        self._saldo = float(saldo_inicial)

    @property
    def saldo(self) -> float:
        return round(self._saldo, 2)

    def pode_apostar(self, valor: float) -> bool:
        return 0 < valor <= self._saldo

    def jogar(self, escolha: str, aposta: float) -> RoundResult:
        escolha_normalizada = escolha.strip().lower()
        if escolha_normalizada not in {"cara", "coroa"}:
            raise ValueError("A escolha precisa ser 'cara' ou 'coroa'.")
        if not self.pode_apostar(aposta):
            raise ValueError("A aposta precisa ser positiva e menor ou igual ao saldo.")

        resultado = random.choice(["cara", "coroa"])
        venceu = escolha_normalizada == resultado

        if venceu:
            self._saldo += aposta
        else:
            self._saldo -= aposta

        return RoundResult(
            escolha=escolha_normalizada,
            aposta=float(aposta),
            resultado_moeda=resultado,
            venceu=venceu,
        )
