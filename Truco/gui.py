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

        frame = ttk.Frame(self.master, padding=20)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Truco", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=4, pady=(0, 10)
        )

        ttk.Label(frame, text="Saldo inicial:").grid(row=1, column=0, sticky="W")
        self.saldo_inicial_var = tk.StringVar(value="250,00")
        self.saldo_inicial_entry = ttk.Entry(frame, textvariable=self.saldo_inicial_var, width=14)
        self.saldo_inicial_entry.grid(row=1, column=1, sticky="W")
        self.iniciar_btn = ttk.Button(frame, text="Iniciar", command=self._iniciar_jogo)
        self.iniciar_btn.grid(row=1, column=2, padx=(10, 0))

        self.saldo_var = tk.StringVar(value="Saldo: R$0,00")
        ttk.Label(frame, textvariable=self.saldo_var, font=("Segoe UI", 12, "bold")).grid(
            row=2, column=0, columnspan=4, pady=(6, 15)
        )

        ttk.Label(frame, text="Aposta:").grid(row=3, column=0, sticky="W")
        self.aposta_var = tk.StringVar(value="20,00")
        self.aposta_entry = ttk.Entry(frame, textvariable=self.aposta_var, width=10, state="disabled")
        self.aposta_entry.grid(row=3, column=1, sticky="W")

        self.pedir_truco_btn = ttk.Button(frame, text="Pedir Truco", command=self._pedir_truco, state="disabled")
        self.pedir_truco_btn.grid(row=3, column=2, padx=(10, 0))

        self.multiplicador_var = tk.StringVar(value="Multiplicador: 1x")
        ttk.Label(frame, textvariable=self.multiplicador_var).grid(row=3, column=3, sticky="E", padx=(15, 0))

        self.match_var = tk.StringVar(value=f"Partida: Você 0 x 0 (meta {self._match_goal} pontos)")
        ttk.Label(frame, textvariable=self.match_var, font=("Segoe UI", 11, "bold")).grid(
            row=4, column=0, columnspan=4, pady=(8, 4)
        )

        self.pontos_var = tk.StringVar(value="Placar da mão: Você 0 x 0 Adversário")
        ttk.Label(frame, textvariable=self.pontos_var, font=("Segoe UI", 11)).grid(
            row=5, column=0, columnspan=4, pady=(0, 6)
        )

        info_frame = ttk.Frame(frame)
        info_frame.grid(row=6, column=0, columnspan=4, pady=(4, 8), sticky="EW")
        info_frame.columnconfigure(2, weight=1)
        ttk.Label(info_frame, text="Vira:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="W")
        self.vira_card_label = tk.Label(
            info_frame,
            text="--",
            font=("Segoe UI Symbol", 20, "bold"),
            width=4,
            height=1,
            bg="#202b3a",
            fg="#f1f5f9",
            bd=4,
            relief="raised",
        )
        self.vira_card_label.grid(row=0, column=1, padx=(8, 14))
        self.manilha_var = tk.StringVar(value="Manilha: --")
        ttk.Label(info_frame, textvariable=self.manilha_var).grid(row=0, column=2, sticky="W")

        self.player_last_card_var = tk.StringVar(value="Sua última carta: --")
        ttk.Label(frame, textvariable=self.player_last_card_var).grid(
            row=7, column=0, columnspan=4, sticky="W"
        )

        self.ai_last_card_var = tk.StringVar(value="Carta do adversário: --")
        ttk.Label(frame, textvariable=self.ai_last_card_var).grid(
            row=8, column=0, columnspan=4, sticky="W", pady=(0, 6)
        )

        self.cartas_frame = ttk.Frame(frame, padding=10)
        self.cartas_frame.grid(row=9, column=0, columnspan=4)
        self.carta_buttons: list[tk.Button] = []
        for idx in range(3):
            btn = tk.Button(
                self.cartas_frame,
                text="--",
                width=4,
                height=2,
                font=("Segoe UI Symbol", 20, "bold"),
                bg="#202b3a",
                fg="#f1f5f9",
                activebackground="#2a3b52",
                activeforeground="#ffffff",
                relief="raised",
                bd=4,
                command=lambda i=idx: self._jogar_carta(i),
            )
            btn.grid(row=0, column=idx, padx=8)
            btn.configure(state="disabled")
            self.carta_buttons.append(btn)

        self.status_var = tk.StringVar(value="Defina o saldo inicial e clique em Iniciar.")
        ttk.Label(frame, textvariable=self.status_var, wraplength=420).grid(
            row=10, column=0, columnspan=4, pady=(15, 10)
        )

        botoes_frame = ttk.Frame(frame)
        botoes_frame.grid(row=11, column=0, columnspan=4, pady=(10, 0))
        self.nova_mao_btn = ttk.Button(botoes_frame, text="Nova mão", command=self._nova_mao, state="disabled")
        self.nova_mao_btn.grid(row=0, column=0, padx=(0, 10))
        self.nova_partida_btn = ttk.Button(
            botoes_frame, text="Nova partida", command=self._nova_partida, state="disabled"
        )
        self.nova_partida_btn.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(botoes_frame, text="Sair", command=self.master.destroy).grid(row=0, column=2)

    def set_wallet(self, wallet: CarteiraProtocol, saldo_factory: Callable[[], float]) -> None:
        self.wallet = wallet
        self._saldo_factory = saldo_factory
        self.saldo_inicial_entry.configure(state="disabled")
        self.saldo_inicial_var.set(f"{wallet.saldo:.2f}".replace(".", ","))
        self._atualizar_saldo_compartilhado()
        self.status_var.set("Saldo compartilhado carregado. Clique em Iniciar para jogar.")
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
                messagebox.showerror("Saldo inválido", "Informe um número válido para o saldo inicial.")
                return
        if saldo is None or saldo <= 0:
            messagebox.showerror("Saldo inválido", "O saldo precisa ser maior que zero.")
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
            messagebox.showerror("Não foi possível iniciar", str(exc))
            return

        self._aposta_base = aposta
        self._mao_ativa = True
        self._atualizar_interface_mao()
        self.status_var.set("Mão iniciada! Escolha uma carta para jogar.")
        self._habilitar_controles(True)
        self.nova_mao_btn.configure(state="disabled")
        self.nova_partida_btn.configure(state="disabled")
        self.pedir_truco_btn.configure(state="normal")
        self.iniciar_btn.configure(state="disabled")
        self._limpar_cartas_jogadas()
        self._atualizar_match_points()

    def _obter_aposta(self) -> float | None:
        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            messagebox.showerror("Aposta inválida", "Informe um número válido para a aposta.")
            return None
        if aposta <= 0:
            messagebox.showwarning("Aposta inválida", "A aposta precisa ser maior que zero.")
            return None
        if self.wallet:
            saldo_disponivel = self.wallet.saldo
        elif self.game:
            saldo_disponivel = self.game.saldo
        else:
            try:
                saldo_disponivel = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                saldo_disponivel = 0
        if aposta > saldo_disponivel:
            messagebox.showwarning("Aposta inválida", "A aposta não pode ultrapassar o saldo atual.")
            return None
        return aposta

    def _jogar_carta(self, indice: int) -> None:
        if not self.game:
            return
        try:
            resultado = self.game.jogar_carta(indice)
        except (RuntimeError, IndexError) as exc:
            messagebox.showerror("Ação inválida", str(exc))
            return
        hand_finished = resultado.hand_finished
        self._repor_cartas(habilitar=not hand_finished)
        self.player_last_card_var.set(
            f"Sua última carta: {resultado.player_card.describe()} ({resultado.player_card.label()})"
        )
        self.ai_last_card_var.set(
            f"Carta do adversário: {resultado.ai_card.describe()} ({resultado.ai_card.label()})"
        )
        self.pontos_var.set(
            f"Placar da mão: Você {resultado.player_points} x {resultado.ai_points} Adversário"
        )
        if resultado.round_winner == "player":
            self.status_var.set("Você levou a rodada!")
        elif resultado.round_winner == "ai":
            self.status_var.set("O adversário venceu a rodada.")
        else:
            self.status_var.set("Empate na rodada. Vale a próxima.")

        self._atualizar_multiplicador(resultado.multiplier)
        self._atualizar_saldo(resultado.saldo)
        self._atualizar_match_points(resultado.player_match_points, resultado.ai_match_points)

        if hand_finished:
            mensagem_final = "A mão terminou empatada."
            if resultado.hand_winner == "player":
                mensagem_final = (
                    f"Você venceu a mão! Ganhou {formatar_reais(self._aposta_base * resultado.multiplier)}."
                )
            elif resultado.hand_winner == "ai":
                mensagem_final = (
                    f"O adversário venceu a mão. Perdeu {formatar_reais(self._aposta_base * resultado.multiplier)}."
                )
            self.status_var.set(mensagem_final)
            self._mao_ativa = False
            self._habilitar_controles(False)
            self.pedir_truco_btn.configure(state="disabled")
            if self.wallet:
                self._sincronizar_carteira()
            else:
                self._atualizar_saldo(self.game.saldo if self.game else resultado.saldo)

            if resultado.match_winner:
                vencedor_texto = "Você" if resultado.match_winner == "player" else "O adversário"
                self.status_var.set(
                    f"{mensagem_final} {vencedor_texto} alcançou {self._match_goal} pontos na partida!"
                )
                self.nova_mao_btn.configure(state="disabled")
                self.nova_partida_btn.configure(state="normal")
                self.iniciar_btn.configure(state="normal")
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
            self.player_last_card_var.set("Sua última carta: --")
            self.ai_last_card_var.set("Carta do adversário: correu do Truco.")
            if self.game:
                self.pontos_var.set(
                    f"Placar da mão: Você {self.game.player_points} x {self.game.ai_points} Adversário"
                )
            if self.wallet:
                self._sincronizar_carteira()
            else:
                self._atualizar_saldo(self.game.saldo)
            if self.game and self.game.partida_encerrada():
                vencedor = "Você" if self.game.vencedor_partida() == "player" else "O adversário"
                self.status_var.set(
                    f"{resultado.message} {vencedor} alcançou {self._match_goal} pontos na partida!"
                )
                self.nova_mao_btn.configure(state="disabled")
                self.nova_partida_btn.configure(state="normal")
                self.iniciar_btn.configure(state="normal")
            else:
                self.nova_mao_btn.configure(state="normal")
            return
        self.status_var.set(resultado.message)
        if not resultado.accepted:
            self.pedir_truco_btn.configure(state="disabled")

    def _nova_mao(self) -> None:
        if not self.game:
            return
        if self.game.partida_encerrada():
            messagebox.showinfo(
                "Partida encerrada",
                "A partida já terminou. Clique em Nova partida ou Iniciar para recomeçar.",
            )
            return
        if self.wallet and self.wallet.saldo <= 0:
            messagebox.showwarning("Saldo esgotado", "Adicione saldo no hub para continuar jogando.")
            return
        aposta = self._obter_aposta()
        if aposta is None:
            return
        try:
            self.game.iniciar_partida(aposta)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Aposta inválida", str(exc))
            return
        self._aposta_base = aposta
        self._mao_ativa = True
        self._repor_cartas()
        self._atualizar_interface_mao()
        self._habilitar_controles(True)
        self.pedir_truco_btn.configure(state="normal")
        self.nova_partida_btn.configure(state="disabled")
        self.iniciar_btn.configure(state="disabled")
        self._limpar_cartas_jogadas()
        self.status_var.set("Nova mão iniciada! Boa sorte.")

    def _nova_partida(self) -> None:
        if self.wallet and self._saldo_factory:
            saldo = self._saldo_factory()
            if saldo <= 0:
                messagebox.showwarning("Saldo insuficiente", "Adicione saldo no hub para reiniciar a partida.")
                return
        else:
            try:
                saldo = self._converter_para_float(self.saldo_inicial_var.get())
            except ValueError:
                messagebox.showerror("Saldo inválido", "Informe um número válido para reiniciar a partida.")
                return
            if saldo <= 0:
                messagebox.showerror("Saldo inválido", "O saldo precisa ser maior que zero.")
                return

        if self.game is None:
            self.game = TrucoGame(saldo)
        else:
            self.game.reiniciar_partida(saldo)

        self._mao_ativa = False
        self._habilitar_controles(False)
        self._repor_cartas(habilitar=False)
        self._limpar_cartas_jogadas()
        self._atualizar_match_points()
        self._atualizar_vira("--")
        self.manilha_var.set("Manilha: --")
        self.pontos_var.set("Placar da mão: Você 0 x 0 Adversário")
        self._atualizar_saldo(self.game.saldo)

        sugestao = min(max(self.game.saldo * 0.1, 10.0), self.game.saldo)
        self.aposta_var.set(self._formatar_entrada(sugestao))

        self.pedir_truco_btn.configure(state="disabled")
        self.nova_mao_btn.configure(state="disabled")
        self.nova_partida_btn.configure(state="disabled")
        self.iniciar_btn.configure(state="normal")
        self.status_var.set("Partida reiniciada! Ajuste a aposta e clique em Iniciar para jogar.")

    def _habilitar_controles(self, habilitar: bool) -> None:
        if habilitar:
            self.aposta_entry.configure(state="disabled")
        else:
            self.aposta_entry.configure(state="normal")

    def _repor_cartas(self, habilitar: bool = True) -> None:
        if not self.game:
            for botao in self.carta_buttons:
                botao.configure(command=lambda: None)
                self._estilizar_botao_carta(botao, "--", False)
            return

        for idx, carta in enumerate(self.game.player_hand):
            botao = self.carta_buttons[idx]
            botao.configure(command=lambda i=idx: self._jogar_carta(i))
            self._estilizar_botao_carta(botao, carta.label(), habilitar)

        for idx in range(len(self.game.player_hand), len(self.carta_buttons)):
            botao = self.carta_buttons[idx]
            botao.configure(command=lambda: None)
            self._estilizar_botao_carta(botao, "--", False)

    def _estilizar_botao_carta(self, botao: tk.Button, texto: str, habilitado: bool) -> None:
        vermelho = any(simbolo in texto for simbolo in ("♥", "♦"))
        fg = "#ff8a8a" if vermelho else "#f1f5f9"
        bg = "#202b3a" if habilitado else "#141c27"
        botao.configure(
            text=texto,
            fg=fg,
            bg=bg,
            activeforeground="#ffffff",
            activebackground="#2a3b52",
            relief="raised" if habilitado else "sunken",
            bd=4 if habilitado else 2,
            state="normal" if habilitado else "disabled",
        )

    def _limpar_cartas_jogadas(self) -> None:
        self.player_last_card_var.set("Sua última carta: --")
        self.ai_last_card_var.set("Carta do adversário: --")

    def _atualizar_vira(self, texto: str) -> None:
        exibicao = texto if texto else "--"
        vermelho = any(simbolo in exibicao for simbolo in ("♥", "♦"))
        fg = "#ff8a8a" if vermelho else "#f1f5f9"
        self.vira_card_label.configure(text=exibicao, fg=fg)

    def _atualizar_match_points(self, jogador: int | None = None, adversario: int | None = None) -> None:
        if jogador is None or adversario is None:
            if self.game:
                jogador = self.game.player_match_points
                adversario = self.game.ai_match_points
            else:
                jogador = adversario = 0
        texto = f"Partida: Você {jogador} x {adversario} (meta {self._match_goal} pontos)"
        if self.game and self.game.partida_encerrada():
            vencedor = self.game.vencedor_partida()
            if vencedor == "player":
                texto += " - Você venceu!"
            elif vencedor == "ai":
                texto += " - Adversário venceu."
        self.match_var.set(texto)

    def _atualizar_interface_mao(self) -> None:
        if not self.game:
            return
        self._repor_cartas()
        estado = self.game.estado_mao()
        vira = estado["vira"] or "--"
        manilha = estado["manilha"] or "--"
        self._atualizar_vira(vira)
        self.manilha_var.set(f"Manilha: {manilha}")
        self.pontos_var.set(
            f"Placar da mão: Você {estado['player_points']} x {estado['ai_points']} Adversário"
        )
        self._atualizar_match_points(estado["player_match_points"], estado["ai_match_points"])
        self._atualizar_multiplicador(self.game.multiplicador)
        self._atualizar_saldo(self.game.saldo)
        self._limpar_cartas_jogadas()

    def _atualizar_multiplicador(self, multiplicador: int) -> None:
        self.multiplicador_var.set(f"Multiplicador: {multiplicador}x")

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
        saldo_atual = self.wallet.saldo
        self.saldo_var.set(f"Saldo: {formatar_reais(saldo_atual)}")
        try:
            aposta = self._converter_para_float(self.aposta_var.get())
        except ValueError:
            aposta = 0.0
        if saldo_atual <= 0:
            self.aposta_var.set("0,00")
        elif aposta > saldo_atual:
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
    app = TrucoApp(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    run_app()
