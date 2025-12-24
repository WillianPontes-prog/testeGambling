"""Interface central para escolher o jogo e compartilhar a carteira."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from CaraOuCoroa.gui import CoinGameApp
from Roleta.gui import RouletteApp
from CacaNiquel.gui import SlotMachineApp


def formatar_reais(valor: float) -> str:
    return f"R${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class Wallet:
    """Gerencia uma carteira compartilhada."""

    def __init__(self, saldo_inicial: float) -> None:
        if saldo_inicial <= 0:
            raise ValueError("A carteira precisa começar com saldo positivo.")
        self._saldo = float(saldo_inicial)

    @property
    def saldo(self) -> float:
        return round(self._saldo, 2)

    def depositar(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("Depósito não pode ser negativo.")
        self._saldo += valor

    def retirar(self, valor: float) -> bool:
        if valor < 0:
            raise ValueError("Valor inválido.")
        if valor > self._saldo:
            return False
        self._saldo -= valor
        return True


class HubApp:
    """Janela principal para escolher jogos e gerenciar carteira."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Arcade de Apostas")
        self.master.resizable(False, False)

        self.wallet: Wallet | None = None

        self._montar_interface()

    def _montar_interface(self) -> None:
        frame = ttk.Frame(self.master, padding=20)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Arcade de Apostas", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 15)
        )

        ttk.Label(frame, text="Saldo inicial da carteira:").grid(row=1, column=0, sticky="W")
        self.saldo_var = tk.StringVar(value="300,00")
        self.saldo_entry = ttk.Entry(frame, textvariable=self.saldo_var, width=14)
        self.saldo_entry.grid(row=1, column=1, sticky="W")

        ttk.Button(frame, text="Criar/Atualizar Carteira", command=self._criar_carteira).grid(
            row=2, column=0, columnspan=2, pady=(10, 15)
        )

        self.wallet_info = tk.StringVar(value="Saldo atual: --")
        ttk.Label(frame, textvariable=self.wallet_info, font=("Segoe UI", 12, "bold")).grid(
            row=3, column=0, columnspan=2, pady=(0, 15)
        )

        ttk.Label(frame, text="Escolha um jogo:").grid(row=4, column=0, columnspan=2, sticky="W")

        botao_cara = ttk.Button(frame, text="Cara ou Coroa", command=lambda: self._abrir_jogo("cara"))
        botao_cara.grid(row=5, column=0, sticky="EW", pady=4)

        botao_roleta = ttk.Button(frame, text="Roleta", command=lambda: self._abrir_jogo("roleta"))
        botao_roleta.grid(row=6, column=0, sticky="EW", pady=4)

        botao_slot = ttk.Button(frame, text="Caça-Níquel", command=lambda: self._abrir_jogo("slot"))
        botao_slot.grid(row=7, column=0, sticky="EW", pady=4)

        self.status_info = tk.StringVar(value="Crie uma carteira para começar.")
        ttk.Label(frame, textvariable=self.status_info, wraplength=260).grid(
            row=8, column=0, columnspan=2, pady=(10, 0)
        )

        ttk.Button(frame, text="Sair", command=self.master.destroy).grid(row=9, column=1, sticky="E", pady=(18, 0))

    def _criar_carteira(self) -> None:
        try:
            saldo = self._converter_para_float(self.saldo_var.get())
        except ValueError:
            messagebox.showerror("Saldo inválido", "Informe um número válido para o saldo inicial.")
            return
        if saldo <= 0:
            messagebox.showerror("Saldo inválido", "O saldo precisa ser positivo.")
            return

        if self.wallet is None:
            self.wallet = Wallet(saldo)
            self.status_info.set("Carteira criada! Escolha um jogo para começar.")
        else:
            diferenca = saldo - self.wallet.saldo
            if diferenca > 0:
                self.wallet.depositar(diferenca)
            elif diferenca < 0:
                if not self.wallet.retirar(-diferenca):
                    messagebox.showwarning(
                        "Saldo insuficiente",
                        "Não é possível reduzir para menos que o saldo atual. Faça novas apostas para diminuir.",
                    )
                    return
            self.status_info.set("Carteira atualizada!")
        self._atualizar_label_saldo()

    def _abrir_jogo(self, jogo: str) -> None:
        if self.wallet is None:
            messagebox.showwarning("Carteira necessária", "Crie a carteira antes de jogar.")
            return

        janela = tk.Toplevel(self.master)
        janela.grab_set()

        if jogo == "cara":
            app = CoinGameApp(janela)
        elif jogo == "roleta":
            app = RouletteApp(janela)
        else:
            app = SlotMachineApp(janela)

        app.set_wallet(self.wallet, lambda w=self.wallet: w.saldo)
        janela.protocol("WM_DELETE_WINDOW", lambda: self._fechar_jogo(janela))

    def _fechar_jogo(self, janela: tk.Toplevel) -> None:
        if messagebox.askyesno("Fechar jogo", "Deseja fechar este jogo e voltar ao hub?"):
            janela.destroy()
            self.status_info.set(f"Saldo atual da carteira: {formatar_reais(self.wallet.saldo)}")
            self._atualizar_label_saldo()

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

    def _atualizar_label_saldo(self) -> None:
        if self.wallet:
            self.wallet_info.set(f"Saldo atual: {formatar_reais(self.wallet.saldo)}")
        else:
            self.wallet_info.set("Saldo atual: --")


def run_app() -> None:
    raiz = tk.Tk()
    app = HubApp(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    run_app()
