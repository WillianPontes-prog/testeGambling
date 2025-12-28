"""Interface gráfica da roleta."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Protocol

from .game import PRETOS, VERMELHOS, RouletteGame, SpinResult

WHEEL_SEQUENCE = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
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
        self.master.configure(bg="#1f1f2e")

        self.game: RouletteGame | None = None
        self._ultima_aposta = 0.0
        self._resultado_pendente: SpinResult | None = None
        self._angulo_atual = 0.0
        self._animacao_offsets: list[float] = []
        self._animacao_total = 0

        self.canvas_center = 150
        self.raio_externo = 120
        self.raio_interno = 70

        self.pointer: int | None = None
        self.texto_numero: int | None = None
        self.wallet: CarteiraProtocol | None = None
        self._saldo_factory: Callable[[], float] | None = None
        
        self.selected_bet_type = tk.StringVar(value="") # "vermelho", "preto", "verde"

        self._montar_interface()

    def _montar_interface(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        
        # Configuração de estilos
        estilo.configure("TFrame", background="#1f1f2e")
        estilo.configure("TLabel", background="#1f1f2e", foreground="#ffffff", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 10, "bold"), background="#3d3d5c", foreground="#ffffff", borderwidth=0)
        estilo.map("TButton", background=[("active", "#4d4d70")])
        estilo.configure("Action.TButton", background="#00ff88", foreground="#0f0f1a")
        estilo.map("Action.TButton", background=[("active", "#00cc6a")])
        
        # Layout Principal: Esquerda (Mesa), Direita (Roda e Controles)
        main_frame = ttk.Frame(self.master, padding=20)
        main_frame.pack(fill="both", expand=True)

        # --- Coluna da Esquerda: Mesa de Apostas ---
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, padx=(0, 20), sticky="n")

        ttk.Label(left_panel, text="Mesa de Apostas", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        
        self.board_frame = tk.Frame(left_panel, bg="#0f0f1a", padx=10, pady=10, relief="sunken", bd=2)
        self.board_frame.pack()

        self.bet_buttons: list[tk.Button] = []

        # Botão Zero (Verde)
        self._criar_botao_mesa(self.board_frame, "0", "verde", 0, 0, colspan=3, width=16)

        # Grade de Números 1-36
        # Layout: 3 colunas, 12 linhas
        for i in range(1, 37):
            cor = "vermelho" if i in VERMELHOS else "preto"
            row = (i - 1) // 3 + 1
            col = (i - 1) % 3
            self._criar_botao_mesa(self.board_frame, str(i), cor, row, col)

        # Apostas Externas (Vermelho / Preto)
        self._criar_botao_mesa(self.board_frame, "Vermelho", "vermelho", 13, 0, colspan=1, width=4, text_color="#ff4444")
        self._criar_botao_mesa(self.board_frame, "Preto", "preto", 13, 2, colspan=1, width=4, text_color="#888888")
        # Espaço no meio
        tk.Label(self.board_frame, text="OU", bg="#0f0f1a", fg="#555").grid(row=13, column=1)


        # --- Coluna da Direita: Roda e Controles ---
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="n")

        # Info Saldo
        info_frame = ttk.Frame(right_panel)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(info_frame, text="Saldo Inicial:").pack(anchor="w")
        self.saldo_inicial_var = tk.StringVar(value="200,00")
        self.saldo_inicial_entry = ttk.Entry(info_frame, textvariable=self.saldo_inicial_var)
        self.saldo_inicial_entry.pack(fill="x", pady=(2, 5))
        
        self.iniciar_btn = ttk.Button(info_frame, text="Carregar Saldo", command=self._iniciar_jogo)
        self.iniciar_btn.pack(fill="x")

        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(info_frame, textvariable=self.saldo_var, font=("Segoe UI", 12, "bold"), foreground="#00ff88").pack(pady=(10, 0))

        # Canvas Roda
        self.canvas = tk.Canvas(right_panel, width=300, height=300, highlightthickness=0, bg="#1f1f2e")
        self.canvas.pack(pady=10)
        self._desenhar_roleta(self._angulo_atual)
        
        # Pointer e Texto Central
        self.texto_numero = self.canvas.create_text(
            self.canvas_center, self.canvas_center,
            text="", fill="#fafafa", font=("Segoe UI", 28, "bold"), tags="pointer"
        )
        self.pointer = self.canvas.create_polygon(
            self.canvas_center - 10, 15,
            self.canvas_center + 10, 15,
            self.canvas_center, 35,
            fill="#ffd54f", outline="#b8860b", width=2, tags="pointer"
        )
        self.canvas.tag_raise("pointer")

        # Controles de Aposta
        control_frame = ttk.Frame(right_panel)
        control_frame.pack(fill="x", pady=10)

        ttk.Label(control_frame, text="Sua Aposta (R$):").pack(anchor="w")
        self.aposta_var = tk.StringVar(value="20,00")
        self.aposta_entry = ttk.Entry(control_frame, textvariable=self.aposta_var, state="disabled")
        self.aposta_entry.pack(fill="x", pady=(2, 10))

        self.lbl_selecao = ttk.Label(control_frame, text="Selecione na mesa...", font=("Segoe UI", 10, "italic"))
        self.lbl_selecao.pack(pady=(0, 10))

        self.botao_girar = ttk.Button(control_frame, text="GIRAR ROLETA", command=self._girar, state="disabled", style="Action.TButton")
        self.botao_girar.pack(fill="x", ipady=5)

        self.status_var = tk.StringVar(value="Bem-vindo à Roleta.")
        ttk.Label(right_panel, textvariable=self.status_var, wraplength=300, justify="center").pack(pady=10)

        ttk.Button(right_panel, text="Sair", command=self.master.destroy).pack(side="bottom", anchor="e", pady=10)


    def _criar_botao_mesa(self, parent, text, tipo, row, col, colspan=1, width=4, text_color="white"):
        """Cria um botão na mesa de apostas."""
        bg_color = "#1a1a1a" # Preto padrão
        if tipo == "vermelho":
            bg_color = "#c62828"
        elif tipo == "verde":
            bg_color = "#2e7d32"
        
        btn = tk.Button(
            parent, text=text, font=("Segoe UI", 9, "bold"),
            bg=bg_color, fg=text_color,
            activebackground="#ffffff", activeforeground=bg_color,
            relief="raised", bd=1, width=width, height=1,
            command=lambda: self._selecionar_aposta(tipo, text)
        )
        btn.grid(row=row, column=col, columnspan=colspan, padx=1, pady=1, sticky="nsew")
        self.bet_buttons.append(btn)

    def _selecionar_aposta(self, tipo: str, texto: str) -> None:
        if self.game is None:
            return
        
        self.selected_bet_type.set(tipo)
        
        # Feedback visual
        display_text = f"Apostando em: {texto} ({tipo.upper()})"
        if tipo == "vermelho":
            self.lbl_selecao.configure(text=display_text, foreground="#ff6b6b")
        elif tipo == "preto":
            self.lbl_selecao.configure(text=display_text, foreground="#aaaaaa")
        else:
            self.lbl_selecao.configure(text=display_text, foreground="#00ff88")
            
        # Atualizar bordas dos botões (simples highlight)
        # (Opcional: Implementar highlight mais complexo se sobrar tempo)

    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self.saldo_inicial_entry.configure(state="disabled")
        self.saldo_inicial_var.set(f"{wallet.saldo:.2f}".replace(".", ","))
        self.saldo_var.set(f"Saldo: {formatar_reais(wallet.saldo)}")
        self.status_var.set("Saldo carregado. Clique em Carregar Saldo.")

    def _iniciar_jogo(self) -> None:
        if self._animacao_offsets:
            return
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo <= 0:
                messagebox.showwarning("Carteira vazia", "Adicione saldo no Hub.")
                return
            self.game = RouletteGame(saldo)
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Erro", "Saldo inválido.")
                return
            if saldo <= 0:
                messagebox.showerror("Erro", "Saldo deve ser positivo.")
                return
            self.game = RouletteGame(saldo)
            
        self._atualizar_saldo()
        self._habilitar_controles(True)
        self.status_var.set("Faça sua aposta na mesa e clique em Girar.")
        self._resetar_roleta()
        sugestao = min(20.0, self.game.saldo)
        self.aposta_var.set(self._formatar_entrada(sugestao))
        self.iniciar_btn.configure(state="disabled")

    def _habilitar_controles(self, habilitar: bool) -> None:
        estado = "normal" if habilitar else "disabled"
        self.aposta_entry.configure(state=estado)
        self.botao_girar.configure(state=estado)
        # Botões da mesa
        for btn in self.bet_buttons:
            btn.configure(state=estado)

    def _girar(self) -> None:
        if self.game is None or self._animacao_offsets:
            return

        tipo_aposta = self.selected_bet_type.get()
        if not tipo_aposta:
            messagebox.showwarning("Aposta", "Selecione uma opção na mesa de apostas!")
            return

        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Valor de aposta inválido.")
            return

        if not self.game.pode_apostar(aposta):
            messagebox.showwarning("Saldo Insuficiente", "Aposta maior que o saldo.")
            return

        self._ultima_aposta = aposta
        # O jogo atual só suporta apostar em COR.
        # A mesa permite clicar em números, mas mapeamos para a cor do número.
        # Isso é uma limitação do backend que mantivemos para não quebrar a lógica.
        # O usuário clica no "14" (Vermelho) -> Aposta no Vermelho.
        
        self._resultado_pendente = self.game.girar(tipo_aposta, aposta)
        self.status_var.set("Girando...")
        self._habilitar_controles(False)
        if self.texto_numero is not None:
            self.canvas.itemconfig(self.texto_numero, text="")
        self._preparar_animacao(self._resultado_pendente.numero)

    def _preparar_animacao(self, numero: int) -> None:
        alvo_base = self._offset_para_numero(numero)
        voltas = 5
        alvo = alvo_base + 360 * voltas
        inicio = self._angulo_atual
        passos = 80
        offsets = []
        for indice in range(1, passos + 1):
            t = indice / passos
            progresso = 1 - pow(1 - t, 3)
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
        delay = int(20 + progresso * 100)
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
            self.status_var.set("Saldo zerado.")

    def _exibir_resultado(self, resultado: SpinResult) -> None:
        if self.texto_numero is not None:
            self.canvas.itemconfig(self.texto_numero, text=str(resultado.numero))

        saldo_atual = self.game.saldo if self.game else 0.0

        if resultado.venceu:
            msg = f"VENCEU! Caiu {resultado.numero} ({resultado.cor}). Ganhou {formatar_reais(resultado.ganho)}."
            self.status_var.set(msg)
        else:
            msg = f"Perdeu. Caiu {resultado.numero} ({resultado.cor})."
            self.status_var.set(msg)
            
        self._atualizar_saldo()
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

        # Borda externa
        self.canvas.create_oval(
            cx - raio_ext - 5, cy - raio_ext - 5,
            cx + raio_ext + 5, cy + raio_ext + 5,
            outline="#44445f", width=4, tags="wheel"
        )

        for indice, numero in enumerate(WHEEL_SEQUENCE):
            inicio = offset + indice * SEGMENT_ANGLE
            cor_segmento = self._cor_para_segmento(numero)
            self.canvas.create_arc(
                cx - raio_ext, cy - raio_ext,
                cx + raio_ext, cy + raio_ext,
                start=inicio, extent=SEGMENT_ANGLE + 0.5,
                fill=cor_segmento, outline="#070711", width=1, tags="wheel"
            )
            
            # Texto
            mid = math.radians(inicio + SEGMENT_ANGLE / 2)
            texto_raio = (raio_ext + raio_int) / 2
            x = cx + math.cos(mid) * texto_raio
            y = cy - math.sin(mid) * texto_raio
            cor_texto = "#ffffff" if numero != 0 else "#000000"
            self.canvas.create_text(
                x, y, text=str(numero), fill=cor_texto,
                font=("Segoe UI", 9, "bold"), tags="wheel", angle=0
            )

        # Centro
        self.canvas.create_oval(
            cx - raio_int, cy - raio_int,
            cx + raio_int, cy + raio_int,
            fill="#1f1f2e", outline="#444460", width=2, tags="wheel"
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
        self.saldo_var.set(f"Saldo: {formatar_reais(self.wallet.saldo)}")

    def _offset_para_numero(self, numero: int) -> float:
        indice = NUMBER_TO_INDEX[numero]
        centro_segmento = indice * SEGMENT_ANGLE + SEGMENT_ANGLE / 2
        return POINTER_ANGLE - centro_segmento

    def _atualizar_saldo(self) -> None:
        if self.game:
            self.saldo_var.set(f"Saldo: {formatar_reais(self.game.saldo)}")

    @staticmethod
    def _converter_para_float(texto: str) -> float:
        limpo = texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(limpo)

    @staticmethod
    def _formatar_entrada(valor: float) -> str:
        return f"{valor:.2f}".replace(".", ",")

    @staticmethod
    def _cor_para_segmento(numero: int) -> str:
        if numero == 0: return "#00ff88" # Verde neon
        if numero in VERMELHOS: return "#ff4444" # Vermelho
        return "#222222" # Preto

def run_app() -> None:
    raiz = tk.Tk()
    app = RouletteApp(raiz)
    raiz.mainloop()
