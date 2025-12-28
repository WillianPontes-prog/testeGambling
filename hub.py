"""Interface central para escolher o jogo e compartilhar a carteira."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from CaraOuCoroa.gui import CoinGameApp
from Roleta.gui import RouletteApp
from CacaNiquel.gui import SlotMachineApp
from Truco.gui import TrucoApp


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
        self.master.configure(bg="#1f1f2e")

        self.wallet: Wallet | None = None

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        
        estilo.configure("TFrame", background="#1f1f2e")
        estilo.configure("TLabel", background="#1f1f2e", foreground="#ffffff", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 10, "bold"), background="#3d3d5c", foreground="#ffffff", borderwidth=0)
        estilo.map("TButton", background=[("active", "#4d4d70")])
        estilo.configure("Action.TButton", background="#00ff88", foreground="#0f0f1a", font=("Segoe UI", 11, "bold"))
        estilo.map("Action.TButton", background=[("active", "#00cc6a")])
        
        # Container Principal
        main_frame = ttk.Frame(self.master, padding=30)
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header_frame, text="CASINO HUB", 
            font=("Segoe UI", 28, "bold"), bg="#1f1f2e", fg="#00ff88"
        ).pack()
        
        tk.Label(
            header_frame, text="Escolha seu jogo e boa sorte!", 
            font=("Segoe UI", 12), bg="#1f1f2e", fg="#aaaaaa"
        ).pack(pady=(5, 0))

        # Área da Carteira
        wallet_frame = tk.Frame(main_frame, bg="#2a2a3d", bd=2, relief="groove", padx=15, pady=15)
        wallet_frame.pack(fill="x", pady=(0, 25))

        tk.Label(wallet_frame, text="SUA CARTEIRA", font=("Segoe UI", 10, "bold"), bg="#2a2a3d", fg="#aaaaaa").pack(anchor="w")
        
        self.wallet_info = tk.StringVar(value="R$ --")
        tk.Label(wallet_frame, textvariable=self.wallet_info, font=("Segoe UI", 24, "bold"), bg="#2a2a3d", fg="#ffffff").pack(anchor="w", pady=5)

        controls_frame = tk.Frame(wallet_frame, bg="#2a2a3d")
        controls_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(controls_frame, text="Depósito Inicial:", bg="#2a2a3d", fg="#ffffff").pack(side="left")
        self.saldo_var = tk.StringVar(value="300,00")
        entry = ttk.Entry(controls_frame, textvariable=self.saldo_var, width=10)
        entry.pack(side="left", padx=10)
        
        ttk.Button(controls_frame, text="Carregar / Adicionar", command=self._criar_carteira, style="Action.TButton").pack(side="left")


        # Grid de Jogos
        games_frame = ttk.Frame(main_frame)
        games_frame.pack(fill="both", expand=True)
        
        # Configurar grid 2x2
        games_frame.columnconfigure(0, weight=1)
        games_frame.columnconfigure(1, weight=1)
        games_frame.rowconfigure(0, weight=1)
        games_frame.rowconfigure(1, weight=1)

        self._criar_botao_jogo(games_frame, "Cara ou Coroa", "🪙", "cara", 0, 0)
        self._criar_botao_jogo(games_frame, "Roleta", "🎡", "roleta", 0, 1)
        self._criar_botao_jogo(games_frame, "Caça-Níquel", "🎰", "slot", 1, 0)
        self._criar_botao_jogo(games_frame, "Truco", "🃏", "truco", 1, 1)

        # Footer
        ttk.Button(main_frame, text="Sair do Casino", command=self.master.destroy).pack(side="bottom", anchor="e", pady=(20, 0))
        
        self.status_info = tk.StringVar(value="Crie uma carteira para começar.")
        tk.Label(main_frame, textvariable=self.status_info, bg="#1f1f2e", fg="#aaaaaa", font=("Segoe UI", 9)).pack(side="bottom", pady=10)

    def _criar_botao_jogo(self, parent, nome, icone, comando_key, row, col):
        """Cria um card de jogo."""
        frame = tk.Frame(parent, bg="#3d3d5c", bd=0, highlightthickness=1, highlightbackground="#4d4d70")
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Hover effect
        def on_enter(e): frame.config(bg="#4d4d70")
        def on_leave(e): frame.config(bg="#3d3d5c")
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        
        # Conteúdo clicável
        def on_click(e): self._abrir_jogo(comando_key)
        
        lbl_icon = tk.Label(frame, text=icone, font=("Segoe UI Emoji", 32), bg="#3d3d5c", fg="#ffffff")
        lbl_icon.pack(expand=True, pady=(15, 5))
        lbl_icon.bind("<Button-1>", on_click)
        lbl_icon.bind("<Enter>", lambda e: on_enter(None)) # Propagate hover
        
        lbl_name = tk.Label(frame, text=nome, font=("Segoe UI", 12, "bold"), bg="#3d3d5c", fg="#ffffff")
        lbl_name.pack(pady=(0, 15))
        lbl_name.bind("<Button-1>", on_click)
        lbl_name.bind("<Enter>", lambda e: on_enter(None))

        frame.bind("<Button-1>", on_click)

    def _criar_carteira(self) -> None:
        try:
            saldo = self._converter_para_float(self.saldo_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Saldo inválido.")
            return
        if saldo <= 0:
            messagebox.showerror("Erro", "Saldo deve ser positivo.")
            return

        if self.wallet is None:
            self.wallet = Wallet(saldo)
            self.status_info.set("Carteira criada!")
        else:
            diferenca = saldo - self.wallet.saldo
            if diferenca > 0:
                self.wallet.depositar(diferenca)
            elif diferenca < 0:
                if not self.wallet.retirar(-diferenca):
                    messagebox.showwarning("Erro", "Não é possível reduzir abaixo do saldo atual.")
                    return
            self.status_info.set("Carteira atualizada!")
        self._atualizar_label_saldo()

    def _abrir_jogo(self, jogo: str) -> None:
        if self.wallet is None:
            messagebox.showwarning("Atenção", "Crie a carteira antes de jogar.")
            return

        janela = tk.Toplevel(self.master)
        janela.grab_set()

        if jogo == "cara":
            app = CoinGameApp(janela)
        elif jogo == "roleta":
            app = RouletteApp(janela)
        elif jogo == "slot":
            app = SlotMachineApp(janela)
        else:
            app = TrucoApp(janela)

        app.set_wallet(self.wallet, lambda w=self.wallet: w.saldo)
        janela.protocol("WM_DELETE_WINDOW", lambda: self._fechar_jogo(janela))

    def _fechar_jogo(self, janela: tk.Toplevel) -> None:
        if messagebox.askyesno("Sair", "Voltar ao Hub?"):
            janela.destroy()
            self._atualizar_label_saldo()

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

    def _atualizar_label_saldo(self) -> None:
        if self.wallet:
            self.wallet_info.set(f"{formatar_reais(self.wallet.saldo)}")
        else:
            self.wallet_info.set("R$ --")


def run_app() -> None:
    raiz = tk.Tk()
    app = HubApp(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    run_app()
