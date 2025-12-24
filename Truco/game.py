"""Lógica simplificada para uma partida de Truco."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional

RANK_ORDER = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
SUITS = ["ouros", "espadas", "copas", "paus"]
SUIT_NAMES = {
    "ouros": "Ouros",
    "espadas": "Espadas",
    "copas": "Copas",
    "paus": "Paus",
}
SUIT_SYMBOLS = {
    "ouros": "♦",
    "espadas": "♠",
    "copas": "♥",
    "paus": "♣",
}
SUIT_STRENGTH = {
    "paus": 4,
    "copas": 3,
    "espadas": 2,
    "ouros": 1,
}


@dataclass(frozen=True)
class Card:
    """Representa uma carta do baralho."""

    rank: str
    suit: str

    def label(self) -> str:
        simbolo = SUIT_SYMBOLS.get(self.suit, "")
        return f"{self.rank}{simbolo}"

    def describe(self) -> str:
        return f"{self.rank} de {SUIT_NAMES.get(self.suit, self.suit.capitalize())}"


@dataclass(slots=True)
class TrucoPlayResult:
    """Resultado de uma rodada ao jogar uma carta."""

    player_card: Card
    ai_card: Card
    round_winner: str | None
    player_points: int
    ai_points: int
    round_index: int
    hand_finished: bool
    hand_winner: str | None
    saldo: float
    multiplier: int
    player_match_points: int
    ai_match_points: int
    match_winner: str | None


@dataclass(slots=True)
class TrucoRaiseResult:
    """Retorno ao pedir Truco."""

    accepted: bool
    folded: bool
    multiplier: int
    message: str


class TrucoGame:
    """Gerencia uma mão rápida de Truco contra um adversário virtual."""

    def __init__(self, saldo: float) -> None:
        self.saldo = round(float(saldo), 2)
        self._deck: list[Card] = []
        self.player_hand: list[Card] = []
        self.ai_hand: list[Card] = []
        self.vira: Card | None = None
        self.manilha_rank: str | None = None
        self.aposta_base: float = 0.0
        self.multiplicador: int = 1
        self.rodada_atual: int = 1
        self.player_points = 0
        self.ai_points = 0
        self._vantagem: Optional[str] = None
        self._ativa = False
        self.player_match_points = 0
        self.ai_match_points = 0
        self.match_goal = 12
        self._partida_finalizada = False
        self._vencedor_partida: str | None = None

    def pode_apostar(self, valor: float) -> bool:
        return valor > 0 and valor <= self.saldo

    def iniciar_partida(self, aposta: float) -> None:
        if not self.pode_apostar(aposta):
            raise ValueError("Aposta inválida para o saldo atual.")
        if self._partida_finalizada:
            raise RuntimeError("A partida já terminou. Reinicie para jogar novamente.")
        self.aposta_base = round(float(aposta), 2)
        self._resetar_estado()
        self._distribuir_cartas()
        self._ativa = True

    def pedir_truco(self) -> TrucoRaiseResult:
        if not self._ativa:
            return TrucoRaiseResult(False, False, self.multiplicador, "A rodada já terminou.")
        if self.multiplicador >= 3:
            return TrucoRaiseResult(True, False, self.multiplicador, "O Truco já está valendo.")

        novo_multiplicador = 3
        potencial = self.aposta_base * novo_multiplicador
        if potencial > self.saldo:
            return TrucoRaiseResult(False, False, self.multiplicador, "Saldo insuficiente para aceitar o Truco.")

        self.multiplicador = novo_multiplicador
        if self._decidir_truco_ai():
            return TrucoRaiseResult(True, False, self.multiplicador, "O adversário aceitou! Agora vale 3x.")

        self.player_points = 2
        self._finalizar_mao("player")
        self._ativa = False
        return TrucoRaiseResult(False, True, self.multiplicador, "O adversário correu. Você levou a mão.")

    def jogar_carta(self, indice: int) -> TrucoPlayResult:
        if not self._ativa:
            if self._partida_finalizada:
                raise RuntimeError("A partida terminou. Reinicie para continuar jogando.")
            raise RuntimeError("Nenhuma mão em andamento.")
        if indice < 0 or indice >= len(self.player_hand):
            raise IndexError("Índice de carta inválido.")

        carta_jogador = self.player_hand.pop(indice)
        carta_ai = self._escolher_carta_ai()
        vencedor = self._comparar_cartas(carta_jogador, carta_ai)
        if vencedor == "player":
            self.player_points += 1
            self._vantagem = "player"
        elif vencedor == "ai":
            self.ai_points += 1
            self._vantagem = "ai"

        self.rodada_atual += 1
        terminou = self._verificar_finalizacao()
        ganhador_mao: str | None = None
        if terminou:
            ganhador_mao = self._determinar_ganhador_mao()
            if ganhador_mao:
                self._finalizar_mao(ganhador_mao)
            self._ativa = False

        return TrucoPlayResult(
            player_card=carta_jogador,
            ai_card=carta_ai,
            round_winner=vencedor,
            player_points=self.player_points,
            ai_points=self.ai_points,
            round_index=self.rodada_atual - 1,
            hand_finished=terminou,
            hand_winner=ganhador_mao if terminou else None,
            saldo=self.saldo,
            multiplier=self.multiplicador,
            player_match_points=self.player_match_points,
            ai_match_points=self.ai_match_points,
            match_winner=self._vencedor_partida,
        )

    def cartas_para_display(self, cartas: Iterable[Card]) -> List[str]:
        return [c.label() for c in cartas]

    def estado_mao(self) -> dict[str, object]:
        return {
            "vira": self.vira.label() if self.vira else "",
            "manilha": self.manilha_rank or "",
            "multiplicador": self.multiplicador,
            "player_points": self.player_points,
            "ai_points": self.ai_points,
            "player_match_points": self.player_match_points,
            "ai_match_points": self.ai_match_points,
            "goal": self.match_goal,
            "match_winner": self._vencedor_partida,
        }

    def _resetar_estado(self) -> None:
        self._deck = [Card(rank, suit) for rank in RANK_ORDER for suit in SUITS]
        random.shuffle(self._deck)
        self.player_hand.clear()
        self.ai_hand.clear()
        self.vira = None
        self.manilha_rank = None
        self.multiplicador = 1
        self.rodada_atual = 1
        self.player_points = 0
        self.ai_points = 0
        self._vantagem = None

    def _distribuir_cartas(self) -> None:
        self.player_hand = [self._deck.pop() for _ in range(3)]
        self.ai_hand = [self._deck.pop() for _ in range(3)]
        self.vira = self._deck.pop()
        self.manilha_rank = RANK_ORDER[(RANK_ORDER.index(self.vira.rank) + 1) % len(RANK_ORDER)]

    def _escolher_carta_ai(self) -> Card:
        if not self.ai_hand:
            raise RuntimeError("O adversário está sem cartas.")
        melhor_carta = max(self.ai_hand, key=self._forca_carta)
        self.ai_hand.remove(melhor_carta)
        return melhor_carta

    def _comparar_cartas(self, jogador: Card, adversario: Card) -> str | None:
        forca_jogador = self._forca_carta(jogador)
        forca_ai = self._forca_carta(adversario)
        if forca_jogador > forca_ai:
            return "player"
        if forca_ai > forca_jogador:
            return "ai"
        if self._vantagem:
            return self._vantagem
        return None

    def _forca_carta(self, carta: Card) -> int:
        if carta.rank == self.manilha_rank:
            return 100 + SUIT_STRENGTH.get(carta.suit, 0)
        return RANK_ORDER.index(carta.rank)

    def _verificar_finalizacao(self) -> bool:
        if self.player_points == 2 or self.ai_points == 2:
            return True
        if self.rodada_atual > 3:
            return True
        return False

    def _determinar_ganhador_mao(self) -> str | None:
        if self.player_points > self.ai_points:
            return "player"
        if self.ai_points > self.player_points:
            return "ai"
        if self._vantagem:
            return self._vantagem
        return "player"

    def _finalizar_mao(self, vencedor: str) -> None:
        valor = round(self.aposta_base * self.multiplicador, 2)
        if vencedor == "player":
            self.saldo += valor
            self.player_match_points = min(self.match_goal, self.player_match_points + self.multiplicador)
        else:
            self.saldo -= valor
            self.ai_match_points = min(self.match_goal, self.ai_match_points + self.multiplicador)
        self.saldo = round(self.saldo, 2)
        if self.player_match_points >= self.match_goal or self.ai_match_points >= self.match_goal:
            self._partida_finalizada = True
            self._vencedor_partida = "player" if self.player_match_points >= self.match_goal else "ai"
        else:
            self._vencedor_partida = None

    def _decidir_truco_ai(self) -> bool:
        total_ai = sum(self._forca_carta(c) for c in self.ai_hand)
        media_ai = total_ai / max(len(self.ai_hand), 1)
        limiar = 20
        if self.ai_points > self.player_points:
            limiar += 4
        if media_ai >= limiar:
            return True
        return random.random() < 0.4

    def reiniciar_partida(self, saldo: float | None = None) -> None:
        if saldo is not None:
            self.saldo = round(float(saldo), 2)
        self.player_match_points = 0
        self.ai_match_points = 0
        self._partida_finalizada = False
        self._vencedor_partida = None
        self._ativa = False
        self.player_hand.clear()
        self.ai_hand.clear()
        self._deck.clear()
        self.aposta_base = 0.0
        self.multiplicador = 1
        self.rodada_atual = 1
        self.player_points = 0
        self.ai_points = 0
        self._vantagem = None
        self.vira = None
        self.manilha_rank = None

    def partida_encerrada(self) -> bool:
        return self._partida_finalizada

    def vencedor_partida(self) -> str | None:
        return self._vencedor_partida


__all__ = [
    "Card",
    "TrucoGame",
    "TrucoPlayResult",
    "TrucoRaiseResult",
]
