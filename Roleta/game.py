"""Regras e utilidades do jogo de roleta."""

from __future__ import annotations

from dataclasses import dataclass
import random

VERMELHOS = {
    1,
    3,
    5,
    7,
    9,
    12,
    14,
    16,
    18,
    19,
    21,
    23,
    25,
    27,
    30,
    32,
    34,
    36,
}

PRETOS = set(range(1, 37)) - VERMELHOS


@dataclass
class SpinResult:
    numero: int
    cor: str
    aposta_cor: str
    venceu: bool
    ganho: float


class RouletteGame:
    """Mantém o saldo e resolve jogadas da roleta europeia."""

    def __init__(self, saldo_inicial: float) -> None:
        if saldo_inicial <= 0:
            raise ValueError("O saldo inicial precisa ser maior que zero.")
        self._saldo = float(saldo_inicial)

    @property
    def saldo(self) -> float:
        return round(self._saldo, 2)

    def pode_apostar(self, valor: float) -> bool:
        return 0 < valor <= self._saldo

    def girar(self, cor_escolhida: str, aposta: float) -> SpinResult:
        cor_normalizada = cor_escolhida.strip().lower()
        if cor_normalizada not in {"vermelho", "preto", "verde"}:
            raise ValueError("A cor precisa ser 'vermelho', 'preto' ou 'verde'.")
        if not self.pode_apostar(aposta):
            raise ValueError("A aposta precisa ser positiva e menor ou igual ao saldo.")

        numero = random.randint(0, 36)
        cor_resultado = self._cor_do_numero(numero)
        venceu = cor_resultado == cor_normalizada

        ganho = 0.0
        if venceu:
            if cor_normalizada == "verde":
                ganho = aposta * 35
            else:
                ganho = aposta
            self._saldo += ganho
        else:
            self._saldo -= aposta

        return SpinResult(
            numero=numero,
            cor=cor_resultado,
            aposta_cor=cor_normalizada,
            venceu=venceu,
            ganho=ganho,
        )

    @staticmethod
    def _cor_do_numero(numero: int) -> str:
        if numero == 0:
            return "verde"
        if numero in VERMELHOS:
            return "vermelho"
        return "preto"
