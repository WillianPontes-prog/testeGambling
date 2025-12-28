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
    "BAR": "💎", # Changed BAR to Diamond for better visual
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
        self.master.configure(bg="#1f1f2e")

        self.game: SlotMachine | None = None
        self._animando = False
        self._passos_reel: list[int] = [0, 0, 0]
        self._limites_reel: list[int] = [0, 0, 0]
        self._resultado_pendente: SpinResult | None = None
        self._ultima_aposta = 0.0
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None
        self._reel_states: list[tuple[str, str, str]] = [
            ("❓", "❓", "❓") for _ in range(3)
        ]

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        
        estilo.configure("TFrame", background="#1f1f2e")
        estilo.configure("TLabel", background="#1f1f2e", foreground="#ffffff", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 10, "bold"), background="#3d3d5c", foreground="#ffffff", borderwidth=0)
        estilo.map("TButton", background=[("active", "#4d4d70")])
        estilo.configure("Action.TButton", background="#ffcc00", foreground="#0f0f1a", font=("Segoe UI", 12, "bold"))
        estilo.map("Action.TButton", background=[("active", "#ffaa00")])

        main_frame = ttk.Frame(self.master, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Título Estilizado
        title_lbl = tk.Label(
            main_frame, text="🎰 SUPER SLOTS 🎰", 
            font=("Segoe UI", 24, "bold"), bg="#1f1f2e", fg="#ffcc00"
        )
        title_lbl.pack(pady=(0, 20))

        # --- Máquina Visual ---
        machine_frame = tk.Frame(main_frame, bg="#2c3e50", bd=10, relief="ridge", padx=15, pady=15)
        machine_frame.pack()

        # Display dos Reels
        reels_container = tk.Frame(machine_frame, bg="#000000", bd=5, relief="sunken")
        reels_container.pack()

        self.reel_columns: list[list[tk.Label]] = []
        for idx in range(3):
            coluna_frame = tk.Frame(reels_container, bg="#ffffff", padx=2, pady=0)
            coluna_frame.pack(side="left", padx=2)

            coluna_labels: list[tk.Label] = []
            for linha in range(3):
                # Linha do meio é a linha de pagamento
                is_payline = (linha == 1)
                bg_color = "#ffffff"
                fg_color = "#000000"
                
                label = tk.Label(
                    coluna_frame,
                    text="❓",
                    font=("Segoe UI Emoji", 40),
                    width=2,
                    height=1,
                    bg=bg_color,
                    fg=fg_color,
                    relief="flat",
                    bd=0
                )
                label.pack(pady=1)
                coluna_labels.append(label)
            self.reel_columns.append(coluna_labels)

        # Indicador de Linha de Pagamento
        payline_indicator = tk.Frame(machine_frame, bg="#ff0000", height=4)
        payline_indicator.place(relx=0, rely=0.5, relwidth=1, anchor="w")
        # (Isso pode ficar feio se não alinhar perfeitamente, vamos simplificar com setas laterais)
        payline_indicator.destroy() # Remove previous attempt
        
        # Setas indicando o meio
        tk.Label(machine_frame, text="▶", bg="#2c3e50", fg="#ff0000", font=("Arial", 20)).place(x=-5, y=110)
        tk.Label(machine_frame, text="◀", bg="#2c3e50", fg="#ff0000", font=("Arial", 20)).place(x=330, y=110) # Ajustar X conforme necessário


        # --- Painel de Controle ---
        control_panel = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        control_panel.pack(fill="x")

        # Info Saldo
        info_frame = ttk.Frame(control_panel)
        info_frame.pack(fill="x", pady=5)
        
        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(info_frame, textvariable=self.saldo_var, font=("Segoe UI", 14, "bold"), foreground="#00ff88").pack()

        # Aposta e Botão
        action_frame = ttk.Frame(control_panel)
        action_frame.pack(fill="x", pady=10)

        ttk.Label(action_frame, text="Aposta:").pack(side="left")
        self.aposta_var = tk.StringVar(value="10,00")
        self.aposta_entry = ttk.Entry(action_frame, textvariable=self.aposta_var, width=10)
        self.aposta_entry.pack(side="left", padx=5)

        self.spin_button = ttk.Button(action_frame, text="GIRAR!", command=self._girar, state="disabled", style="Action.TButton")
        self.spin_button.pack(side="left", padx=20, fill="x", expand=True)

        # Status
        self.status_var = tk.StringVar(value="Insira saldo para jogar.")
        status_lbl = tk.Label(main_frame, textvariable=self.status_var, bg="#1f1f2e", fg="#aaaaaa", font=("Segoe UI", 10), wraplength=350)
        status_lbl.pack(pady=5)

        # Config Inicial (Hidden)
        self.saldo_inicial_var = tk.StringVar(value="200,00")


    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self._atualizar_saldo_compartilhado()
        self.status_var.set("Pronto para jogar!")
        self._iniciar_jogo_auto() # Auto-init se tiver carteira

    def _iniciar_jogo_auto(self) -> None:
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo > 0:
                self.game = SlotMachine(saldo)
                self._atualizar_saldo()
                self._habilitar_controles(True)
                self._resetar_reels()

    def _habilitar_controles(self, habilitar: bool) -> None:
        estado = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state=estado)
        self.spin_button.configure(state=estado)

    def _girar(self) -> None:
        if self.game is None:
            # Tentar iniciar se não tiver jogo (caso sem carteira)
            try:
                saldo = float(self.saldo_inicial_var.get().replace(",", "."))
                self.game = SlotMachine(saldo)
            except:
                pass

        if self.game is None or self._animando:
            return
            
        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Aposta inválida.")
            return
            
        if not self.game.pode_apostar(aposta):
            messagebox.showwarning("Saldo", "Saldo insuficiente.")
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
        self._limites_reel = [random.randint(15, 25), random.randint(25, 35), random.randint(35, 45)]
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
                    # Preparar parada no símbolo correto
                    topo, _, base = self._reel_states[idx] # Mantém contexto visual anterior? Não, gera aleatório
                    # Precisamos garantir que o símbolo do meio seja o resultado
                    simbolo_final = self._resultado_pendente.symbols[idx]
                    # Gerar vizinhos aleatórios
                    vizinho_cima = random.choice(list(SYMBOL_EMOJIS.values()))
                    vizinho_baixo = random.choice(list(SYMBOL_EMOJIS.values()))
                    strip = (vizinho_cima, SYMBOL_EMOJIS.get(simbolo_final, "❓"), vizinho_baixo)
                else:
                    strip = self._gerar_strip_animacao()
                
                self._atualizar_coluna(idx, coluna, strip)
                self._passos_reel[idx] += 1

        if completo:
            self._finalizar_spin()
            return

        # Velocidade variável (efeito de parada)
        progresso = max(self._passos_reel) / max(self._limites_reel)
        delay = int(50 + progresso * 100)
        self.master.after(delay, self._rotacionar)

    def _finalizar_spin(self) -> None:
        self._animando = False
        if self._resultado_pendente is None:
            self._habilitar_controles(True)
            return

        # Garantir visual final correto
        for idx, (coluna, simbolo) in enumerate(zip(self.reel_columns, self._resultado_pendente.symbols)):
            # Recuperar o que está na tela
            current_strip = self._reel_states[idx]
            # O meio já deve estar certo pela lógica do _rotacionar, mas vamos forçar
            topo, _, base = current_strip
            centro = SYMBOL_EMOJIS.get(simbolo, "❓")
            self._atualizar_coluna(idx, coluna, (topo, centro, base), highlight=True)

        self._mostrar_resultado(self._resultado_pendente)
        self._resultado_pendente = None

        if self.game and self.game.saldo > 0:
            self._habilitar_controles(True)
        else:
            self._habilitar_controles(False)
            self.status_var.set("Saldo esgotado.")

    def _mostrar_resultado(self, resultado: SpinResult) -> None:
        if resultado.venceu:
            ganho_liquido = resultado.ganho - resultado.aposta
            msg = f"VENCEU! Ganhou {formatar_reais(resultado.ganho)}!"
            self.status_var.set(msg)
            # Efeito visual de vitória (piscar?) - simplificado aqui
        else:
            self.status_var.set(f"Tente novamente. Perdeu {formatar_reais(self._ultima_aposta)}.")

        self._atualizar_saldo()
        if self.wallet and self.game:
            self._sincronizar_carteira()

    def _resetar_reels(self) -> None:
        self._reel_states = [("❓", "❓", "❓") for _ in range(3)]
        for idx, coluna in enumerate(self.reel_columns):
            self._atualizar_coluna(idx, coluna, ("❓", "❓", "❓"))

    def _gerar_strip_animacao(self) -> tuple[str, str, str]:
        simbolos = random.choices(list(SYMBOL_EMOJIS.values()), k=3)
        return (simbolos[0], simbolos[1], simbolos[2])

    def _atualizar_coluna(self, indice: int, coluna: list[tk.Label], strip: tuple[str, str, str], highlight: bool = False) -> None:
        topo, centro, base = strip
        
        # Cores normais
        bg_normal = "#ffffff"
        fg_normal = "#cccccc" # Desfocado
        
        # Cores destaque (linha do meio)
        bg_highlight = "#fff8e1" if highlight else "#ffffff"
        fg_highlight = "#000000"
        
        coluna[0].configure(text=topo, fg=fg_normal, bg=bg_normal)
        coluna[1].configure(text=centro, fg=fg_highlight, bg=bg_highlight)
        coluna[2].configure(text=base, fg=fg_normal, bg=bg_normal)
        
        self._reel_states[indice] = strip

    def _atualizar_saldo(self) -> None:
        if self.game:
            self.saldo_var.set(f"Saldo: {formatar_reais(self.game.saldo)}")

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
        self.saldo_var.set(f"Saldo: {formatar_reais(self.wallet.saldo)}")

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

def run_app() -> None:
    raiz = tk.Tk()
    app = SlotMachineApp(raiz)
    raiz.mainloop()
