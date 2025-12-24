"""Interface gráfica para o jogo Cara ou Coroa."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from typing import Callable, Protocol

from .game import CoinGame, RoundResult


def formatar_reais(valor: float) -> str:
    return f"R${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class CarteiraProtocol(Protocol):
    saldo: float

    def depositar(self, valor: float) -> None: ...

    def retirar(self, valor: float) -> bool: ...


class CoinGameApp:
    """Janela principal do jogo."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Cara ou Coroa")
        self.master.resizable(False, False)

        self.game: CoinGame | None = None
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None
        self.em_animacao = False
        self._aposta_em_andamento: float | None = None
        self._escolha_em_andamento: str | None = None

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")

        quadro = ttk.Frame(self.master, padding=20)
        quadro.grid(row=0, column=0, sticky="NSEW")

        titulo = ttk.Label(quadro, text="Jogo de Cara ou Coroa", font=("Segoe UI", 16, "bold"))
        titulo.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # Saldo inicial
        ttk.Label(quadro, text="Saldo inicial:").grid(row=1, column=0, sticky="W")
        self.saldo_inicial_var = tk.StringVar(value="100,00")
        self.saldo_inicial_entry = ttk.Entry(quadro, textvariable=self.saldo_inicial_var, width=15)
        self.saldo_inicial_entry.grid(row=1, column=1, sticky="W")
        self.iniciar_btn = ttk.Button(quadro, text="Iniciar", command=self._iniciar_jogo)
        self.iniciar_btn.grid(row=1, column=2, padx=(10, 0))

        # Canvas da moeda
        self.canvas = tk.Canvas(quadro, width=220, height=220, highlightthickness=0, bg="#1f1f2e")
        self.canvas.grid(row=2, column=0, columnspan=3, pady=20)
        self.moeda = self.canvas.create_oval(40, 40, 180, 180, fill="#d4af37", outline="#b8860b", width=6)
        self.texto_moeda = self.canvas.create_text(
            110,
            110,
            text="",
            fill="#1f1f2e",
            font=("Segoe UI", 28, "bold"),
        )

        # Saldo atual
        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        saldo_label = ttk.Label(quadro, textvariable=self.saldo_var, font=("Segoe UI", 12, "bold"))
        saldo_label.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        # Aposta
        ttk.Label(quadro, text="Aposta:").grid(row=4, column=0, sticky="W")
        self.aposta_var = tk.StringVar(value="10,00")
        self.aposta_entry = ttk.Entry(quadro, textvariable=self.aposta_var, width=15, state="disabled")
        self.aposta_entry.grid(row=4, column=1, sticky="W")

        botoes_frame = ttk.Frame(quadro)
        botoes_frame.grid(row=4, column=2, padx=(10, 0))
        self.botao_cara = ttk.Button(botoes_frame, text="Cara", state="disabled", command=lambda: self._apostar("cara"))
        self.botao_cara.grid(row=0, column=0, padx=(0, 5))
        self.botao_coroa = ttk.Button(botoes_frame, text="Coroa", state="disabled", command=lambda: self._apostar("coroa"))
        self.botao_coroa.grid(row=0, column=1)

        self.status_var = tk.StringVar(value="Informe um saldo inicial para jogar.")
        status_label = ttk.Label(
            quadro,
            textvariable=self.status_var,
            wraplength=320,
            font=("Segoe UI", 10),
        )
        status_label.grid(row=5, column=0, columnspan=3, pady=(15, 10))

        sair_btn = ttk.Button(quadro, text="Sair", command=self.master.destroy)
        sair_btn.grid(row=6, column=2, sticky="E")

    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self.saldo_inicial_entry.configure(state="disabled")
        self.saldo_inicial_var.set(f"{wallet.saldo:.2f}".replace(".", ","))
        self.saldo_var.set(f"Saldo: {formatar_reais(wallet.saldo)}")
        self.status_var.set("Saldo compartilhado carregado. Clique em Iniciar.")

    def _iniciar_jogo(self) -> None:
        if self.em_animacao:
            return

        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo <= 0:
                messagebox.showwarning("Carteira vazia", "Adicione saldo na tela principal para continuar jogando.")
                return
            self.game = CoinGame(saldo)
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Valor inválido", "Informe um número válido para o saldo inicial.")
                return

            if saldo <= 0:
                messagebox.showerror("Saldo inválido", "O saldo inicial precisa ser maior que zero.")
                return

            self.game = CoinGame(saldo)
        self._atualizar_saldo()
        self.status_var.set("Saldo definido! Faça sua aposta.")
        self._habilitar_apostas(True)
        self._resetar_moeda()
        valor_sugerido = min(self.game.saldo, 10.0)
        self.aposta_var.set(self._formatar_entrada(valor_sugerido))

    def _apostar(self, escolha: str) -> None:
        if self.game is None or self.em_animacao:
            return

        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Valor inválido", "Informe um número válido para a aposta.")
            return

        if not self.game.pode_apostar(aposta):
            messagebox.showwarning(
                "Aposta inválida",
                "A aposta precisa ser maior que zero e não pode ultrapassar o saldo atual.",
            )
            return

        self._aposta_em_andamento = aposta
        self._escolha_em_andamento = escolha
        self.status_var.set("Girando a moeda...")
        self._habilitar_apostas(False)
        self._inicio_animacao()

    def _inicio_animacao(self) -> None:
        self.em_animacao = True
        self._passos_animacao = 18
        self._indice_animacao = 0
        self._animar_moeda()

    def _animar_moeda(self) -> None:
        if not self.em_animacao:
            return

        gradientes = ["#d4af37", "#ffd700", "#f5c242", "#e6b422"]
        textos = ["Cara", "", "Coroa", ""]

        cor = gradientes[self._indice_animacao % len(gradientes)]
        texto = textos[self._indice_animacao % len(textos)]

        self.canvas.itemconfig(self.moeda, fill=cor)
        self.canvas.itemconfig(self.texto_moeda, text=texto, fill="#1f1f2e")

        self._indice_animacao += 1
        if self._indice_animacao <= self._passos_animacao:
            self.master.after(80, self._animar_moeda)
        else:
            self.em_animacao = False
            self.master.after(120, self._finalizar_aposta)

    def _finalizar_aposta(self) -> None:
        if self.game is None or self._aposta_em_andamento is None or self._escolha_em_andamento is None:
            return

        resultado = self.game.jogar(self._escolha_em_andamento, self._aposta_em_andamento)
        self._exibir_resultado(resultado)

        self._aposta_em_andamento = None
        self._escolha_em_andamento = None

        if self.game.saldo > 0:
            self._habilitar_apostas(True)
            self.aposta_entry.focus_set()
        else:
            self.status_var.set("Seu saldo zerou. Defina um novo saldo inicial para continuar jogando.")
            self._habilitar_apostas(False)

    def _exibir_resultado(self, resultado: RoundResult) -> None:
        cor = "#4caf50" if resultado.venceu else "#f44336"
        self.canvas.itemconfig(self.moeda, fill="#d4af37")
        self.canvas.itemconfig(self.texto_moeda, text=resultado.resultado_moeda.upper(), fill=cor)

        if resultado.venceu:
            mensagem = (
                f"Você ganhou {formatar_reais(resultado.aposta)}! "
                f"Novo saldo: {formatar_reais(self.game.saldo)}."
            )
        else:
            mensagem = (
                f"Você perdeu {formatar_reais(resultado.aposta)}. "
                f"Novo saldo: {formatar_reais(self.game.saldo)}."
            )

        self.status_var.set(mensagem)
        self._atualizar_saldo()
        proxima_aposta = min(self.game.saldo, resultado.aposta)
        self.aposta_var.set(self._formatar_entrada(max(proxima_aposta, 0)))
        if self.wallet:
            self._sincronizar_carteira()

    def _habilitar_apostas(self, habilitar: bool) -> None:
        estado = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state=estado)
        self.botao_cara.configure(state=estado)
        self.botao_coroa.configure(state=estado)

    def _atualizar_saldo(self) -> None:
        if self.game:
            self.saldo_var.set(f"Saldo: {formatar_reais(self.game.saldo)}")
        else:
            self.saldo_var.set("Saldo: R$0,00")

    def _resetar_moeda(self) -> None:
        self.canvas.itemconfig(self.moeda, fill="#d4af37")
        self.canvas.itemconfig(self.texto_moeda, text="")

    def _sincronizar_carteira(self) -> None:
        if self.wallet and self.game:
            diferenca = round(self.game.saldo - self.wallet.saldo, 2)
            if diferenca > 0:
                self.wallet.depositar(diferenca)
            elif diferenca < 0:
                self.wallet.retirar(-diferenca)

            novo_saldo = self.wallet.saldo
            self.saldo_var.set(f"Saldo: {formatar_reais(novo_saldo)}")

            try:
                aposta_atual = self._converter_para_float(self.aposta_var.get())
            except ValueError:
                aposta_atual = 0.0

            if novo_saldo <= 0:
                self.aposta_var.set("0,00")
            else:
                self.aposta_var.set(self._formatar_entrada(min(novo_saldo, aposta_atual)))

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpou = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpou)

    @staticmethod
    def _formatar_entrada(valor: float) -> str:
        return f"{valor:.2f}".replace(".", ",")


def run_app() -> None:
    raiz = tk.Tk()
    app = CoinGameApp(raiz)
    raiz.mainloop()
