"""Interface gráfica para o jogo de Truco."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Protocol

from .game import TrucoGame


def formatar_reais(valor: float) -> str:
    return f"R${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class CarteiraProtocol(Protocol):
    saldo: float
    def depositar(self, valor: float) -> None: ...
    def retirar(self, valor: float) -> bool: ...


class TrucoApp:
    """Janela principal para jogar Truco."""

    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Truco")
        self.master.resizable(False, False)
        self.master.configure(bg="#1f1f2e")

        self.game: TrucoGame | None = None
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None
        self._aposta_base: float = 0.0
        self._mao_ativa = False
        self._match_goal = 12

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        
        # Estilos
        estilo.configure("TFrame", background="#1f1f2e")
        estilo.configure("TLabel", background="#1f1f2e", foreground="#ffffff", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 10, "bold"), background="#3d3d5c", foreground="#ffffff", borderwidth=0)
        estilo.map("TButton", background=[("active", "#4d4d70")])
        estilo.configure("Action.TButton", background="#00ff88", foreground="#0f0f1a")
        estilo.map("Action.TButton", background=[("active", "#00cc6a")])
        estilo.configure("Danger.TButton", background="#ff6b6b", foreground="#ffffff")
        estilo.map("Danger.TButton", background=[("active", "#ff4444")])

        main_frame = ttk.Frame(self.master, padding=10)
        main_frame.pack(fill="both", expand=True)

        # --- Topo: Placar e Info ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 10))

        # Placar da Partida
        self.match_var = tk.StringVar(value=f"VOCÊ 0 x 0 ADVERSÁRIO")
        lbl_placar = tk.Label(
            top_frame, textvariable=self.match_var, 
            font=("Segoe UI", 16, "bold"), bg="#0f0f1a", fg="#00ff88",
            padx=10, pady=5, relief="sunken", bd=2
        )
        lbl_placar.pack(side="top", fill="x")
        
        # Info da Mão (Pontos da rodada, valor truco)
        info_hand_frame = ttk.Frame(top_frame)
        info_hand_frame.pack(fill="x", pady=5)
        
        self.pontos_var = tk.StringVar(value="Mão: 0 x 0")
        ttk.Label(info_hand_frame, textvariable=self.pontos_var, font=("Segoe UI", 11)).pack(side="left")
        
        self.multiplicador_var = tk.StringVar(value="Valor: 1x")
        ttk.Label(info_hand_frame, textvariable=self.multiplicador_var, font=("Segoe UI", 11, "bold"), foreground="#ffd700").pack(side="right")


        # --- Mesa de Jogo (Verde) ---
        self.table_frame = tk.Frame(main_frame, bg="#2e7d32", bd=5, relief="ridge", height=300)
        self.table_frame.pack(fill="both", expand=True, pady=10)
        self.table_frame.pack_propagate(False) # Manter tamanho fixo se possível

        # Área do Adversário (Cartas viradas)
        self.opponent_area = tk.Frame(self.table_frame, bg="#2e7d32")
        self.opponent_area.pack(side="top", pady=10)
        self.opponent_cards_labels = []
        for _ in range(3):
            lbl = tk.Label(
                self.opponent_area, text="🂠", font=("Segoe UI Symbol", 30),
                bg="#2e7d32", fg="#1b5e20"
            )
            lbl.pack(side="left", padx=5)
            self.opponent_cards_labels.append(lbl)

        # Área Central (Cartas jogadas e Vira)
        center_area = tk.Frame(self.table_frame, bg="#2e7d32")
        center_area.pack(expand=True)

        # Vira
        tk.Label(center_area, text="VIRA", bg="#2e7d32", fg="#a5d6a7", font=("Segoe UI", 8)).grid(row=0, column=0)
        self.vira_card_label = tk.Label(
            center_area, text="🂠", font=("Segoe UI Symbol", 24),
            bg="#2e7d32", fg="#ffffff", width=3
        )
        self.vira_card_label.grid(row=1, column=0, padx=20)

        # Cartas Jogadas (Adversário vs Jogador)
        play_area = tk.Frame(center_area, bg="#2e7d32")
        play_area.grid(row=1, column=1, padx=20)
        
        self.ai_played_label = tk.Label(play_area, text="", font=("Segoe UI Symbol", 24), bg="#2e7d32", fg="#ffffff")
        self.ai_played_label.pack(side="top", pady=5)
        
        self.player_played_label = tk.Label(play_area, text="", font=("Segoe UI Symbol", 24), bg="#2e7d32", fg="#ffffff")
        self.player_played_label.pack(side="bottom", pady=5)


        # Área do Jogador (Botões das cartas)
        self.player_area = tk.Frame(self.table_frame, bg="#2e7d32")
        self.player_area.pack(side="bottom", pady=10)
        
        self.carta_buttons: list[tk.Button] = []
        for idx in range(3):
            btn = tk.Button(
                self.player_area, text="--", width=4, height=2,
                font=("Segoe UI Symbol", 16, "bold"),
                bg="#f1f5f9", fg="#000000",
                relief="raised", bd=3,
                command=lambda i=idx: self._jogar_carta(i)
            )
            btn.pack(side="left", padx=10)
            btn.configure(state="disabled")
            self.carta_buttons.append(btn)


        # --- Controles Inferiores ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))

        # Linha 1: Ações de Jogo
        actions_frame = ttk.Frame(bottom_frame)
        actions_frame.pack(fill="x", pady=(0, 10))
        
        self.pedir_truco_btn = ttk.Button(actions_frame, text="PEDIR TRUCO!", command=self._pedir_truco, state="disabled", style="Danger.TButton")
        self.pedir_truco_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.nova_mao_btn = ttk.Button(actions_frame, text="Nova Mão", command=self._nova_mao, state="disabled")
        self.nova_mao_btn.pack(side="left", fill="x", expand=True, padx=5)

        # Linha 2: Configuração e Status
        config_frame = ttk.Frame(bottom_frame)
        config_frame.pack(fill="x")

        ttk.Label(config_frame, text="Aposta:").pack(side="left")
        self.aposta_var = tk.StringVar(value="20,00")
        self.aposta_entry = ttk.Entry(config_frame, textvariable=self.aposta_var, width=8)
        self.aposta_entry.pack(side="left", padx=5)

        self.iniciar_btn = ttk.Button(config_frame, text="Iniciar Jogo", command=self._iniciar_jogo, style="Action.TButton")
        self.iniciar_btn.pack(side="left", padx=5)

        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(config_frame, textvariable=self.saldo_var, font=("Segoe UI", 10, "bold")).pack(side="right")

        # Status Bar
        self.status_var = tk.StringVar(value="Bem-vindo ao Truco.")
        lbl_status = tk.Label(main_frame, textvariable=self.status_var, bg="#0f0f1a", fg="#ffffff", font=("Segoe UI", 9), pady=4)
        lbl_status.pack(fill="x", pady=(10, 0))
        
        # Saldo Inicial (Hidden logic mostly, but needed for init)
        self.saldo_inicial_var = tk.StringVar(value="250,00")


    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self._atualizar_saldo_compartilhado()
        self.status_var.set("Saldo carregado. Clique em Iniciar Jogo.")
        self._atualizar_match_points()

    def _iniciar_jogo(self) -> None:
        if self._mao_ativa:
            return

        saldo = None
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Erro", "Saldo inválido.")
                return
        
        if saldo is None or saldo <= 0:
            messagebox.showerror("Erro", "Saldo deve ser positivo.")
            return

        aposta = self._obter_aposta()
        if aposta is None:
            return

        if self.game is None or self.game.partida_encerrada():
            self.game = TrucoGame(saldo)
        else:
            self.game.saldo = round(float(saldo), 2)

        try:
            self.game.iniciar_partida(aposta)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Erro", str(exc))
            return

        self._aposta_base = aposta
        self._mao_ativa = True
        self._atualizar_interface_mao()
        self.status_var.set("Sua vez! Escolha uma carta.")
        self._habilitar_controles(True)
        self.nova_mao_btn.configure(state="disabled")
        self.pedir_truco_btn.configure(state="normal")
        self.iniciar_btn.configure(state="disabled")
        self._limpar_cartas_jogadas()
        self._atualizar_match_points()

    def _obter_aposta(self) -> float | None:
        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Aposta inválida.")
            return None
        if aposta <= 0:
            messagebox.showwarning("Aposta", "Aposta deve ser positiva.")
            return None
        
        saldo_disponivel = 0.0
        if self.wallet:
            saldo_disponivel = self.wallet.saldo
        elif self.game:
            saldo_disponivel = self.game.saldo
        else:
             # Fallback
             saldo_disponivel = 1000.0 

        if aposta > saldo_disponivel:
            messagebox.showwarning("Saldo", "Saldo insuficiente.")
            return None
        return aposta

    def _jogar_carta(self, indice: int) -> None:
        if not self.game:
            return
        try:
            resultado = self.game.jogar_carta(indice)
        except (RuntimeError, IndexError) as exc:
            messagebox.showerror("Erro", str(exc))
            return
            
        # Atualizar mesa visualmente
        self.player_played_label.configure(text=resultado.player_card.label(), fg=self._get_card_color(resultado.player_card.label()))
        self.ai_played_label.configure(text=resultado.ai_card.label(), fg=self._get_card_color(resultado.ai_card.label()))

        hand_finished = resultado.hand_finished
        self._repor_cartas(habilitar=not hand_finished)
        
        self.pontos_var.set(f"Mão: {resultado.player_points} x {resultado.ai_points}")
        
        if resultado.round_winner == "player":
            self.status_var.set("Você venceu a rodada!")
        elif resultado.round_winner == "ai":
            self.status_var.set("Adversário venceu a rodada.")
        else:
            self.status_var.set("Empate!")

        self._atualizar_multiplicador(resultado.multiplier)
        self._atualizar_saldo(resultado.saldo)
        self._atualizar_match_points(resultado.player_match_points, resultado.ai_match_points)

        if hand_finished:
            self._finalizar_mao(resultado)

    def _finalizar_mao(self, resultado):
        msg = "Mão empatada."
        if resultado.hand_winner == "player":
            msg = f"VOCÊ VENCEU A MÃO! (+{formatar_reais(self._aposta_base * resultado.multiplier)})"
        elif resultado.hand_winner == "ai":
            msg = f"ADVERSÁRIO VENCEU A MÃO. (-{formatar_reais(self._aposta_base * resultado.multiplier)})"
        
        self.status_var.set(msg)
        self._mao_ativa = False
        self._habilitar_controles(False)
        self.pedir_truco_btn.configure(state="disabled")
        
        if self.wallet:
            self._sincronizar_carteira()
        else:
            self._atualizar_saldo(self.game.saldo if self.game else resultado.saldo)

        if resultado.match_winner:
            vencedor = "VOCÊ" if resultado.match_winner == "player" else "ADVERSÁRIO"
            messagebox.showinfo("Fim de Jogo", f"{vencedor} venceu a partida!")
            self.iniciar_btn.configure(state="normal", text="Nova Partida")
            self.game = None # Reset game logic
        else:
            self.nova_mao_btn.configure(state="normal")

    def _pedir_truco(self) -> None:
        if not self.game:
            return
        resultado = self.game.pedir_truco()
        self._atualizar_multiplicador(self.game.multiplicador)
        self._atualizar_match_points()
        
        if resultado.folded:
            self.status_var.set(resultado.message)
            self._mao_ativa = False
            self.pedir_truco_btn.configure(state="disabled")
            self._habilitar_controles(False)
            self._repor_cartas(habilitar=False)
            
            # Adversário correu
            self.ai_played_label.configure(text="CORREU", fg="#ffffff", font=("Segoe UI", 12))
            
            if self.wallet:
                self._sincronizar_carteira()
            
            if self.game and self.game.partida_encerrada():
                messagebox.showinfo("Fim de Jogo", "Partida encerrada!")
                self.iniciar_btn.configure(state="normal", text="Nova Partida")
                self.game = None
            else:
                self.nova_mao_btn.configure(state="normal")
            return
            
        self.status_var.set(resultado.message)
        if not resultado.accepted:
            self.pedir_truco_btn.configure(state="disabled")

    def _nova_mao(self) -> None:
        if not self.game:
            return
        
        aposta = self._obter_aposta()
        if aposta is None:
            return
            
        try:
            self.game.iniciar_partida(aposta)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
            
        self._aposta_base = aposta
        self._mao_ativa = True
        self._repor_cartas()
        self._atualizar_interface_mao()
        self._habilitar_controles(True)
        self.pedir_truco_btn.configure(state="normal")
        self.iniciar_btn.configure(state="disabled")
        self._limpar_cartas_jogadas()
        self.status_var.set("Nova mão! Sua vez.")

    def _habilitar_controles(self, habilitar: bool) -> None:
        state = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state="disabled" if habilitar else "normal") # Inverso

    def _repor_cartas(self, habilitar: bool = True) -> None:
        if not self.game:
            return

        # Atualizar cartas do jogador
        for idx, carta in enumerate(self.game.player_hand):
            if idx < len(self.carta_buttons):
                botao = self.carta_buttons[idx]
                botao.configure(command=lambda i=idx: self._jogar_carta(i))
                self._estilizar_botao_carta(botao, carta.label(), habilitar)
        
        # Esconder botões extras se a mão diminuiu (não acontece no truco normal mas ok)
        for idx in range(len(self.game.player_hand), len(self.carta_buttons)):
            self._estilizar_botao_carta(self.carta_buttons[idx], "", False)
            
        # Atualizar cartas do oponente (visual apenas - quantidade)
        # No truco a gente não vê quantas cartas o oponente tem na mão facilmente na GUI simples,
        # mas podemos esconder os ícones se ele jogou.
        # Simplificação: manter os 3 ícones sempre por enquanto.

    def _estilizar_botao_carta(self, botao: tk.Button, texto: str, habilitado: bool) -> None:
        if not texto:
            botao.configure(text="", state="disabled", bg="#2e7d32", relief="flat") # Esconde
            return
            
        fg = self._get_card_color(texto)
        bg = "#f1f5f9" if habilitado else "#cfd8dc"
        botao.configure(
            text=texto, fg=fg, bg=bg,
            state="normal" if habilitado else "disabled",
            relief="raised" if habilitado else "sunken"
        )

    def _get_card_color(self, texto: str) -> str:
        if any(s in texto for s in ("♥", "♦")):
            return "#d32f2f" # Vermelho
        return "#000000" # Preto

    def _limpar_cartas_jogadas(self) -> None:
        self.player_played_label.configure(text="")
        self.ai_played_label.configure(text="")

    def _atualizar_interface_mao(self) -> None:
        if not self.game:
            return
        self._repor_cartas()
        estado = self.game.estado_mao()
        
        # Vira
        vira = estado["vira"] or "?"
        self.vira_card_label.configure(text=vira, fg=self._get_card_color(vira))
        
        self.pontos_var.set(f"Mão: {estado['player_points']} x {estado['ai_points']}")
        self._atualizar_match_points(estado["player_match_points"], estado["ai_match_points"])
        self._atualizar_multiplicador(self.game.multiplicador)
        self._atualizar_saldo(self.game.saldo)

    def _atualizar_match_points(self, jogador: int | None = None, adversario: int | None = None) -> None:
        if self.game:
            jogador = self.game.player_match_points
            adversario = self.game.ai_match_points
        else:
            jogador = adversario = 0
        self.match_var.set(f"VOCÊ {jogador} x {adversario} ADVERSÁRIO")

    def _atualizar_multiplicador(self, multiplicador: int) -> None:
        self.multiplicador_var.set(f"VALENDO: {multiplicador}x")

    def _atualizar_saldo(self, saldo: float) -> None:
        self.saldo_var.set(f"Saldo: {formatar_reais(saldo)}")

    def _sincronizar_carteira(self) -> None:
        if not (self.wallet and self.game):
            return
        diferenca = round(self.game.saldo - self.wallet.saldo, 2)
        if diferenca > 0:
            self.wallet.depositar(diferenca)
        elif diferenca < 0:
            self.wallet.retirar(-diferenca)
        self._atualizar_saldo_compartilhado()
        self._atualizar_match_points()

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
    app = TrucoApp(raiz)
    raiz.mainloop()
