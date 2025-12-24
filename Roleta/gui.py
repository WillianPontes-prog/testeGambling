"""Interface gráfica da roleta."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Protocol

from .game import PRETOS, VERMELHOS, RouletteGame, SpinResult

WHEEL_SEQUENCE = [
    0,
    32,
    15,
    19,
    4,
    21,
    2,
    25,
    17,
    34,
    6,
    27,
    13,
    36,
    11,
    30,
    8,
    23,
    10,
    5,
    24,
    16,
    33,
    1,
    20,
    14,
    31,
    9,
    22,
    18,
    29,
    7,
    28,
    12,
    35,
    3,
    26,
]

SEGMENT_ANGLE = 360 / len(WHEEL_SEQUENCE)
POINTER_ANGLE = 90.0
NUMBER_TO_INDEX = {numero: indice for indice, numero in enumerate(WHEEL_SEQUENCE)}


def formatar_reais(valor: float) -> str:
    return f"R${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class CarteiraProtocol(Protocol):
    saldo: float

    def depositar(self, valor: float) -> None: ...

    def retirar(self, valor: float) -> bool: ...


class RouletteApp:
    """Janela com controles para jogar a roleta."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Roleta")
        self.master.resizable(False, False)

        self.game: RouletteGame | None = None
        self._ultima_aposta = 0.0
        self._resultado_pendente: SpinResult | None = None
        self._angulo_atual = 0.0
        self._animacao_offsets: list[float] = []
        self._animacao_total = 0

        self.canvas_center = 170
        self.raio_externo = 140
        self.raio_interno = 80

        self.pointer: int | None = None
        self.texto_numero: int | None = None
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")

        frame = ttk.Frame(self.master, padding=20)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Jogo de Roleta", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 15)
        )

        ttk.Label(frame, text="Saldo inicial:").grid(row=1, column=0, sticky="W")
        self.saldo_inicial_var = tk.StringVar(value="200,00")
        self.saldo_inicial_entry = ttk.Entry(frame, textvariable=self.saldo_inicial_var, width=15)
        self.saldo_inicial_entry.grid(row=1, column=1, sticky="W")
        self.iniciar_btn = ttk.Button(frame, text="Iniciar", command=self._iniciar_jogo)
        self.iniciar_btn.grid(row=1, column=2, padx=(10, 0))

        self.canvas = tk.Canvas(frame, width=340, height=340, highlightthickness=0, bg="#161626")
        self.canvas.grid(row=2, column=0, columnspan=3, pady=20)
        self._desenhar_roleta(self._angulo_atual)
        self.texto_numero = self.canvas.create_text(
            self.canvas_center,
            self.canvas_center,
            text="",
            fill="#fafafa",
            font=("Segoe UI", 34, "bold"),
            tags="pointer",
        )
        self.pointer = self.canvas.create_polygon(
            self.canvas_center - 14,
            22,
            self.canvas_center + 14,
            22,
            self.canvas_center,
            48,
            fill="#ffd54f",
            outline="#b8860b",
            width=2,
            tags="pointer",
        )
        self.canvas.tag_raise("pointer")

        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(frame, textvariable=self.saldo_var, font=("Segoe UI", 12, "bold")).grid(
            row=3, column=0, columnspan=3, pady=(0, 10)
        )

        ttk.Label(frame, text="Aposta:").grid(row=4, column=0, sticky="W")
        self.aposta_var = tk.StringVar(value="20,00")
        self.aposta_entry = ttk.Entry(frame, textvariable=self.aposta_var, width=15, state="disabled")
        self.aposta_entry.grid(row=4, column=1, sticky="W")

        self.cor_var = tk.StringVar(value="vermelho")
        opcoes_frame = ttk.Frame(frame)
        opcoes_frame.grid(row=4, column=2, padx=(10, 0))
        self.radio_vermelho = ttk.Radiobutton(
            opcoes_frame, text="Vermelho", value="vermelho", variable=self.cor_var, state="disabled"
        )
        self.radio_vermelho.grid(row=0, column=0, padx=(0, 5))
        self.radio_preto = ttk.Radiobutton(
            opcoes_frame, text="Preto", value="preto", variable=self.cor_var, state="disabled"
        )
        self.radio_preto.grid(row=0, column=1, padx=(0, 5))
        self.radio_verde = ttk.Radiobutton(
            opcoes_frame, text="Verde (0)", value="verde", variable=self.cor_var, state="disabled"
        )
        self.radio_verde.grid(row=0, column=2)

        self.botao_girar = ttk.Button(frame, text="Girar", command=self._girar, state="disabled")
        self.botao_girar.grid(row=5, column=0, columnspan=3, pady=(15, 0))

        self.status_var = tk.StringVar(
            value="Defina o saldo inicial, escolha a cor e gire a roleta. Verde paga 35x quando acerta."
        )
        ttk.Label(frame, textvariable=self.status_var, wraplength=360).grid(
            row=6, column=0, columnspan=3, pady=(12, 0)
        )

        ttk.Button(frame, text="Sair", command=self.master.destroy).grid(row=7, column=2, sticky="E", pady=(20, 0))

    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self.saldo_inicial_entry.configure(state="disabled")
        self.saldo_inicial_var.set(f"{wallet.saldo:.2f}".replace(".", ","))
        self.saldo_var.set(f"Saldo: {formatar_reais(wallet.saldo)}")
        self.status_var.set("Saldo compartilhado carregado. Clique em Iniciar.")

    def _iniciar_jogo(self) -> None:
        if self._animacao_offsets:
            return
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo <= 0:
                messagebox.showwarning("Carteira vazia", "Adicione saldo na tela principal para continuar jogando.")
                return
            self.game = RouletteGame(saldo)
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Saldo inválido", "Informe um número válido para o saldo inicial.")
                return
            if saldo <= 0:
                messagebox.showerror("Saldo inválido", "O saldo inicial precisa ser maior que zero.")
                return
            self.game = RouletteGame(saldo)
        self._atualizar_saldo()
        self._habilitar_controles(True)
        self.status_var.set("Saldo definido! Faça sua aposta e clique em girar.")
        self._resultado_pendente = None
        self._resetar_roleta()
        sugestao = min(20.0, self.game.saldo)
        self.aposta_var.set(self._formatar_entrada(sugestao))

    def _habilitar_controles(self, habilitar: bool) -> None:
        estado = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state=estado)
        self.radio_vermelho.configure(state=estado)
        self.radio_preto.configure(state=estado)
        self.radio_verde.configure(state=estado)
        self.botao_girar.configure(state=estado)

    def _girar(self) -> None:
        if self.game is None or self._animacao_offsets:
            return

        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Aposta inválida", "Informe um número válido para a aposta.")
            return

        if not self.game.pode_apostar(aposta):
            messagebox.showwarning(
                "Aposta inválida",
                "A aposta precisa ser maior que zero e não pode ultrapassar o saldo atual.",
            )
            return

        cor = self.cor_var.get()
        self._ultima_aposta = aposta
        self._resultado_pendente = self.game.girar(cor, aposta)
        self.status_var.set("Girando...")
        self._habilitar_controles(False)
        if self.texto_numero is not None:
            self.canvas.itemconfig(self.texto_numero, text="")
        self._preparar_animacao(self._resultado_pendente.numero)

    def _preparar_animacao(self, numero: int) -> None:
        alvo_base = self._offset_para_numero(numero)
        voltas = 6
        alvo = alvo_base + 360 * voltas
        inicio = self._angulo_atual
        passos = 90
        offsets = []
        for indice in range(1, passos + 1):
            t = indice / passos
            progresso = 1 - pow(1 - t, 3)  # ease-out suave
            offsets.append(inicio + (alvo - inicio) * progresso)
        self._animacao_offsets = offsets
        self._animacao_total = len(offsets)
        self._executar_animacao()

    def _executar_animacao(self) -> None:
        if not self._animacao_offsets:
            self._finalizar_animacao()
            return

        offset = self._animacao_offsets.pop(0)
        self._angulo_atual = offset % 360
        self._desenhar_roleta(self._angulo_atual)

        passos_restantes = len(self._animacao_offsets)
        progresso = 1 - (passos_restantes / self._animacao_total if self._animacao_total else 1)
        delay = int(18 + progresso * 90)
        self.master.after(delay, self._executar_animacao)

    def _finalizar_animacao(self) -> None:
        if self._resultado_pendente is None:
            self._habilitar_controles(True)
            return

        self._desenhar_roleta(self._angulo_atual)
        self._exibir_resultado(self._resultado_pendente)
        self._resultado_pendente = None
        self._animacao_total = 0

        if self.game and self.game.saldo > 0:
            self._habilitar_controles(True)
        else:
            self._habilitar_controles(False)
            self.status_var.set("Saldo zerado. Informe um novo saldo inicial para continuar jogando.")

    def _exibir_resultado(self, resultado: SpinResult) -> None:
        if self.texto_numero is not None:
            self.canvas.itemconfig(self.texto_numero, text=str(resultado.numero))

        saldo_atual = self.game.saldo if self.game else 0.0

        if resultado.venceu:
            if resultado.cor == "verde":
                mensagem = (
                    f"Zero! Você ganhou {formatar_reais(resultado.ganho)}. "
                    f"Saldo: {formatar_reais(saldo_atual)}."
                )
            else:
                mensagem = (
                    f"Você acertou {resultado.cor}! Ganhou {formatar_reais(resultado.ganho)}. "
                    f"Saldo: {formatar_reais(saldo_atual)}."
                )
        else:
            mensagem = (
                f"Caiu {resultado.numero} {resultado.cor}. Você perdeu {formatar_reais(self._ultima_aposta)}. "
                f"Saldo: {formatar_reais(saldo_atual)}."
            )
        self.status_var.set(mensagem)
        self._atualizar_saldo()

        if self.game:
            sugestao = min(self.game.saldo, max(resultado.ganho or 0, self.game.saldo * 0.1))
            self.aposta_var.set(self._formatar_entrada(max(sugestao, 0)))
        if self.wallet and self.game:
            self._sincronizar_carteira()

    def _resetar_roleta(self) -> None:
        self._desenhar_roleta(self._angulo_atual)
        if self.texto_numero is not None:
            self.canvas.itemconfig(self.texto_numero, text="")

    def _desenhar_roleta(self, offset: float) -> None:
        self.canvas.delete("wheel")
        cx = cy = self.canvas_center
        raio_ext = self.raio_externo
        raio_int = self.raio_interno

        self.canvas.create_oval(
            cx - raio_ext - 8,
            cy - raio_ext - 8,
            cx + raio_ext + 8,
            cy + raio_ext + 8,
            outline="#44445f",
            width=6,
            tags="wheel",
        )

        for indice, numero in enumerate(WHEEL_SEQUENCE):
            inicio = offset + indice * SEGMENT_ANGLE
            cor_segmento = self._cor_para_segmento(numero)
            self.canvas.create_arc(
                cx - raio_ext,
                cy - raio_ext,
                cx + raio_ext,
                cy + raio_ext,
                start=inicio,
                extent=SEGMENT_ANGLE + 0.4,
                fill=cor_segmento,
                outline="#070711",
                width=1,
                tags="wheel",
            )

            mid = math.radians(inicio + SEGMENT_ANGLE / 2)
            texto_raio = (raio_ext + raio_int) / 2
            x = cx + math.cos(mid) * texto_raio
            y = cy - math.sin(mid) * texto_raio
            cor_texto = "#f0f0f0" if numero != 0 else "#102510"
            self.canvas.create_text(
                x,
                y,
                text=str(numero),
                fill=cor_texto,
                font=("Segoe UI", 11, "bold"),
                tags="wheel",
            )

        self.canvas.create_oval(
            cx - raio_int,
            cy - raio_int,
            cx + raio_int,
            cy + raio_int,
            fill="#0f0f1d",
            outline="#444460",
            width=2,
            tags="wheel",
        )

        self.canvas.create_oval(
            cx - 26,
            cy - 26,
            cx + 26,
            cy + 26,
            fill="#1d1d2f",
            outline="#7a7aa5",
            width=2,
            tags="wheel",
        )

        self.canvas.create_oval(
            cx - 8,
            cy - 8,
            cx + 8,
            cy + 8,
            fill="#c0c0c0",
            outline="#9090a0",
            width=1,
            tags="wheel",
        )

        self.canvas.tag_raise("pointer")

    def _sincronizar_carteira(self) -> None:
        if not (self.wallet and self.game):
            return
        diferenca = round(self.game.saldo - self.wallet.saldo, 2)
        if diferenca > 0:
            self.wallet.depositar(diferenca)
        elif diferenca < 0:
            self.wallet.retirar(-diferenca)
        saldo_atual = self.wallet.saldo
        self.saldo_var.set(f"Saldo: {formatar_reais(saldo_atual)}")
        try:
            aposta_atual = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            aposta_atual = 0.0
        if saldo_atual <= 0:
            self.aposta_var.set("0,00")
        elif aposta_atual > saldo_atual:
            self.aposta_var.set(self._formatar_entrada(saldo_atual))

    def _offset_para_numero(self, numero: int) -> float:
        indice = NUMBER_TO_INDEX[numero]
        centro_segmento = indice * SEGMENT_ANGLE + SEGMENT_ANGLE / 2
        return POINTER_ANGLE - centro_segmento

    def _atualizar_saldo(self) -> None:
        if self.game:
            self.saldo_var.set(f"Saldo: {formatar_reais(self.game.saldo)}")
        else:
            self.saldo_var.set("Saldo: R$0,00")

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

    @staticmethod
    def _formatar_entrada(valor: float) -> str:
        return f"{valor:.2f}".replace(".", ",")

    @staticmethod
    def _cor_para_segmento(numero: int) -> str:
        if numero == 0:
            return "#2f9d61"
        if numero in VERMELHOS:
            return "#c62828"
        if numero in PRETOS:
            return "#1a1a1a"
        return "#202030"


def run_app() -> None:
    raiz = tk.Tk()
    app = RouletteApp(raiz)
    raiz.mainloop()
