"""Interface gráfica para o caça-níquel."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Protocol

from .game import SYMBOL_NAMES, SlotMachine, SpinResult

SYMBOL_EMOJIS = {
    "CHERRY": "🍒",
    "LEMON": "🍋",
    "ORANGE": "🍊",
    "PLUM": "🍇",
    "BELL": "🔔",
    "STAR": "⭐",
    "BAR": "🟥",
    "SEVEN": "7️⃣",
}


def formatar_reais(valor: float) -> str:
    return f"R${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class CarteiraProtocol(Protocol):
    saldo: float

    def depositar(self, valor: float) -> None: ...

    def retirar(self, valor: float) -> bool: ...


class SlotMachineApp:
    """Janela e animação do caça-níquel."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Caça-Níquel")
        self.master.resizable(False, False)

        self.game: SlotMachine | None = None
        self._animando = False
        self._passos_reel: list[int] = [0, 0, 0]
        self._limites_reel: list[int] = [0, 0, 0]
        self._resultado_pendente: SpinResult | None = None
        self._ultima_aposta = 0.0
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None
        self._reel_states: list[tuple[str, str, str]] = [
            ("⬛", "⬜", "⬛") for _ in range(3)
        ]

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")

        frame = ttk.Frame(self.master, padding=20)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Caça-Níquel", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 15)
        )

        ttk.Label(frame, text="Saldo inicial:").grid(row=1, column=0, sticky="W")
        self.saldo_inicial_var = tk.StringVar(value="200,00")
        self.saldo_inicial_entry = ttk.Entry(frame, textvariable=self.saldo_inicial_var, width=12)
        self.saldo_inicial_entry.grid(row=1, column=1, sticky="W")
        ttk.Button(frame, text="Iniciar", command=self._iniciar_jogo).grid(row=1, column=2, padx=(10, 0))

        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(frame, textvariable=self.saldo_var, font=("Segoe UI", 12, "bold")).grid(
            row=2, column=0, columnspan=3, pady=(10, 15)
        )

        self.reels_frame = ttk.Frame(frame, padding=10, style="Reels.TFrame")
        self.reels_frame.grid(row=3, column=0, columnspan=3)
        estilo.configure("Reels.TFrame", background="#101520")
        estilo.configure("Reel.TFrame", background="#0f141d")

        self.reel_columns: list[list[tk.Label]] = []
        for idx in range(3):
            coluna_frame = ttk.Frame(self.reels_frame, padding=4, style="Reel.TFrame")
            coluna_frame.grid(row=0, column=idx, padx=6)

            coluna_labels: list[tk.Label] = []
            for linha in range(3):
                destaque = linha == 1
                label = tk.Label(
                    coluna_frame,
                    text="⬛",
                    font=("Segoe UI Emoji", 30),
                    width=2,
                    height=1,
                    bg="#1f2a3a" if destaque else "#141b26",
                    fg="#e0e5ec" if destaque else "#9aa4b3",
                    relief="raised" if destaque else "sunken",
                    bd=4 if destaque else 2,
                    padx=8,
                    pady=4,
                )
                label.grid(row=linha, column=0, pady=2)
                coluna_labels.append(label)
            self.reel_columns.append(coluna_labels)

        ttk.Label(frame, text="Aposta:").grid(row=4, column=0, sticky="W", pady=(15, 0))
        self.aposta_var = tk.StringVar(value="10,00")
        self.aposta_entry = ttk.Entry(frame, textvariable=self.aposta_var, width=12, state="disabled")
        self.aposta_entry.grid(row=4, column=1, sticky="W", pady=(15, 0))

        self.spin_button = ttk.Button(frame, text="Girar", command=self._girar, state="disabled")
        self.spin_button.grid(row=4, column=2, padx=(10, 0), pady=(15, 0))

        self.status_var = tk.StringVar(
            value="Defina o saldo inicial e clique em Iniciar para começar a jogar."
        )
        ttk.Label(frame, textvariable=self.status_var, wraplength=340).grid(
            row=5, column=0, columnspan=3, pady=(15, 0)
        )

        ttk.Button(frame, text="Sair", command=self.master.destroy).grid(row=6, column=2, sticky="E", pady=(20, 0))

    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self.saldo_inicial_entry.configure(state="disabled")
        self.saldo_inicial_var.set(f"{wallet.saldo:.2f}".replace(".", ","))
        self._atualizar_saldo_compartilhado()
        self.status_var.set("Saldo compartilhado carregado. Clique em Iniciar para jogar.")

    def _iniciar_jogo(self) -> None:
        if self._animando:
            return
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo <= 0:
                messagebox.showwarning("Carteira vazia", "Adicione saldo na tela principal para continuar jogando.")
                return
            self.game = SlotMachine(saldo)
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Saldo inválido", "Informe um número válido para o saldo inicial.")
                return
            if saldo <= 0:
                messagebox.showerror("Saldo inválido", "O saldo inicial precisa ser maior que zero.")
                return
            self.game = SlotMachine(saldo)
        self._atualizar_saldo()
        self._habilitar_controles(True)
        self.status_var.set("Saldo definido! Escolha sua aposta e clique em Girar.")
        self._resetar_reels()
        sugestao = min(10.0, self.game.saldo)
        self.aposta_var.set(self._formatar_entrada(sugestao))

    def _habilitar_controles(self, habilitar: bool) -> None:
        estado = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state=estado)
        self.spin_button.configure(state=estado)

    def _girar(self) -> None:
        if self.game is None or self._animando:
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

        self._ultima_aposta = aposta
        resultado = self.game.girar(aposta)
        self._resultado_pendente = resultado
        self._animar_reels()

    def _animar_reels(self) -> None:
        self._animando = True
        self._habilitar_controles(False)
        self.status_var.set("Girando...")
        self._passos_reel = [0, 0, 0]
        self._limites_reel = [random.randint(24, 32), random.randint(32, 40), random.randint(40, 50)]
        self._rotacionar()

    def _rotacionar(self) -> None:
        if not self._animando:
            return

        completo = True
        for idx, coluna in enumerate(self.reel_columns):
            if self._passos_reel[idx] < self._limites_reel[idx]:
                completo = False
                prestes_a_parar = self._passos_reel[idx] + 1 >= self._limites_reel[idx]
                if prestes_a_parar and self._resultado_pendente is not None:
                    topo, _, base = self._reel_states[idx]
                    simbolo_final = self._resultado_pendente.symbols[idx]
                    strip = (topo, SYMBOL_EMOJIS.get(simbolo_final, "⬜"), base)
                else:
                    strip = self._gerar_strip_animacao()
                self._atualizar_coluna(idx, coluna, strip)
                self._passos_reel[idx] += 1

        if completo:
            self._finalizar_spin()
            return

        progresso = max(self._passos_reel) / max(self._limites_reel)
        delay = int(30 + progresso * 90)
        self.master.after(delay, self._rotacionar)

    def _finalizar_spin(self) -> None:
        self._animando = False
        if self._resultado_pendente is None:
            self._habilitar_controles(True)
            return

        for idx, (coluna, simbolo) in enumerate(zip(self.reel_columns, self._resultado_pendente.symbols)):
            topo, _, base = self._reel_states[idx]
            centro = SYMBOL_EMOJIS.get(simbolo, "⬜")
            self._atualizar_coluna(idx, coluna, (topo, centro, base))

        self._mostrar_resultado(self._resultado_pendente)
        self._resultado_pendente = None

        if self.game and self.game.saldo > 0:
            self._habilitar_controles(True)
            sugestao = min(self.game.saldo, max(self.game.saldo * 0.1, self._ultima_aposta))
            self.aposta_var.set(self._formatar_entrada(sugestao))
        else:
            self._habilitar_controles(False)
            self.status_var.set("Saldo esgotado. Defina um novo saldo inicial para continuar jogando.")

    def _mostrar_resultado(self, resultado: SpinResult) -> None:
        if resultado.venceu:
            ganho_liquido = resultado.ganho - resultado.aposta
            if ganho_liquido <= 0:
                mensagem = (
                    f"Você recuperou {formatar_reais(resultado.ganho)}. "
                    f"Saldo: {formatar_reais(self.game.saldo if self.game else 0)}."
                )
            else:
                mensagem = (
                    f"Você ganhou {formatar_reais(resultado.ganho)}! "
                    f"Lucro líquido: {formatar_reais(ganho_liquido)}. "
                    f"Saldo: {formatar_reais(self.game.saldo if self.game else 0)}."
                )
        else:
            mensagem = (
                f"Sem combinações. Você perdeu {formatar_reais(self._ultima_aposta)}. "
                f"Saldo: {formatar_reais(self.game.saldo if self.game else 0)}."
            )

        self.status_var.set(mensagem)
        self._atualizar_saldo()
        if self.wallet and self.game:
            self._sincronizar_carteira()

    def _resetar_reels(self) -> None:
        self._reel_states = [("⬛", "⬜", "⬛") for _ in range(3)]
        for coluna in self.reel_columns:
            for idx, lbl in enumerate(coluna):
                simbolo = "⬛" if idx != 1 else "⬜"
                cor = "#9aa4b3" if idx != 1 else "#f0f3f8"
                bg = "#141b26" if idx != 1 else "#1f2a3a"
                borda = 2 if idx != 1 else 4
                estilo = "sunken" if idx != 1 else "raised"
                lbl.configure(text=simbolo, fg=cor, bg=bg, bd=borda, relief=estilo)

    def _gerar_strip_animacao(self) -> tuple[str, str, str]:
        simbolos = random.choices(SYMBOL_NAMES, k=3)
        return tuple(SYMBOL_EMOJIS.get(nome, "⬜") for nome in simbolos)

    def _atualizar_coluna(self, indice: int, coluna: list[tk.Label], strip: tuple[str, str, str]) -> None:
        topo, centro, base = strip
        coluna[0].configure(text=topo, fg="#b4bdc9", bg="#141b26", relief="sunken", bd=2)
        coluna[1].configure(text=centro, fg="#f7f9fb", bg="#1f2a3a", relief="raised", bd=4)
        coluna[2].configure(text=base, fg="#b4bdc9", bg="#141b26", relief="sunken", bd=2)
        self._reel_states[indice] = strip

    def _atualizar_saldo(self) -> None:
        if self.game:
            self.saldo_var.set(f"Saldo: {formatar_reais(self.game.saldo)}")
        else:
            self.saldo_var.set("Saldo: R$0,00")

    def _sincronizar_carteira(self) -> None:
        if not (self.wallet and self.game):
            return
        diferenca = round(self.game.saldo - self.wallet.saldo, 2)
        if diferenca > 0:
            self.wallet.depositar(diferenca)
        elif diferenca < 0:
            self.wallet.retirar(-diferenca)
        self._atualizar_saldo_compartilhado()

    def _atualizar_saldo_compartilhado(self) -> None:
        if not self.wallet:
            return
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

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

    @staticmethod
    def _formatar_entrada(valor: float) -> str:
        return f"{valor:.2f}".replace(".", ",")


def run_app() -> None:
    raiz = tk.Tk()
    app = SlotMachineApp(raiz)
    raiz.mainloop()
