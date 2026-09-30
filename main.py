"""
=============================================================================
                      SNAKEDONUTS (STAND UNIMAR ABERTA)
=============================================================================
Jogo de visão computacional controlado pela ponta do indicador,
desenvolvido para uso presencial no stand da Mostra de Tecnologia e Inovação.

Arquitetura Modular:
- game_config: Paleta oficial Neon Arcade, constantes e balanceamento
- game_audio: Motor de áudio retrô procedural com fila thread-safe
- leaderboard_manager: Hall da Fama TOP 5 atômico com validação
- game_state: Lógica de física, colisões, combo x1..x8, novos itens arcade
- game_renderer: Renderizador visual com telas oficiais v2 e sprites seguros
=============================================================================
"""

import os
import sys
import warnings

# Silencia logs ruidosos do TensorFlow, MediaPipe e Abseil antes das importações
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['GLOG_minloglevel'] = '3'
os.environ['ABSL_LOGGING_LEVEL'] = '3'
warnings.filterwarnings('ignore')

import time
import math
from typing import Optional
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector

# Módulos locais autocontidos
import stand_utils
from game_config import (
    LARGURA_PADRAO,
    ALTURA_PADRAO,
    DETECTION_CON,
    MAX_HANDS,
    GameStateEnum,
    COLOR_CYBER_GREEN,
    COLOR_ELECTRIC_CYAN,
    COLOR_SYNTH_PINK,
    COLOR_GOLDEN_GLOW,
    COLOR_GHOST_CRIMSON
)
from game_audio import audio
from leaderboard_manager import StandLeaderboard
from game_state import SnakeGameState
from game_renderer import SnakeGameRenderer


# =============================================================================
# ADAPTADOR DE COMPATIBILIDADE RETROATIVA (SnakeDonutsGame)
# =============================================================================
class SnakeDonutsGame:
    """
    Fachada retrocompatível para importações externas ou integrações legadas.
    Encapsula o motor de regras (SnakeGameState) e o renderizador (SnakeGameRenderer).
    """
    def __init__(self, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO):
        self.largura = largura
        self.altura = altura
        self.leaderboard = StandLeaderboard()
        self.state_engine = SnakeGameState(largura, altura, leaderboard=self.leaderboard)
        self.renderer = SnakeGameRenderer(largura, altura)
        self.state_engine.start_game()

    @property
    def score(self):
        return self.state_engine.score

    @property
    def level(self):
        return self.state_engine.level

    @property
    def game_over(self):
        return self.state_engine.state in (GameStateEnum.GAME_OVER, GameStateEnum.ENTERING_INITIALS)

    @property
    def points(self):
        return self.state_engine.points

    @property
    def lengths(self):
        return self.state_engine.lengths

    @property
    def current_length(self):
        return self.state_engine.current_length

    @property
    def smooth_head(self):
        return self.state_engine.smooth_head

    @smooth_head.setter
    def smooth_head(self, val):
        self.state_engine.smooth_head = val

    def reset_game(self):
        self.state_engine.start_game()

    def update(self, img_main: np.ndarray, raw_head, fingers=None):
        if raw_head == (0, 0):
            raw_head = None
        self.state_engine.update(raw_head)
        return self.renderer.render(img_main, self.state_engine)

    def handle_key(self, cmd, char):
        handle_game_input(self.state_engine, cmd, char)


# =============================================================================
# CONTROLE DE ENTRADA (TECLADO DO STAND E INICIAIS)
# =============================================================================
def handle_game_input(game: SnakeGameState, cmd: Optional[str], char: Optional[str]):
    """Processa comandos do operador do stand e digitação de iniciais no Game Over."""
    if game.state == GameStateEnum.ENTERING_INITIALS:
        if char and char.isalpha():
            game.player_initials[game.selected_initial_idx] = char.upper()
            game.selected_initial_idx = min(2, game.selected_initial_idx + 1)
            audio.play("donut")
            return
        elif cmd == 'LEFT':
            game.selected_initial_idx = max(0, game.selected_initial_idx - 1)
            audio.play("donut")
            return
        elif cmd == 'RIGHT':
            game.selected_initial_idx = min(2, game.selected_initial_idx + 1)
            audio.play("donut")
            return
        elif cmd == 'BACKSPACE':
            game.player_initials[game.selected_initial_idx] = " "
            game.selected_initial_idx = max(0, game.selected_initial_idx - 1)
            audio.play("donut")
            return
        elif cmd in ('ENTER', 'ACAO'):
            game.confirm_initials_and_finish()
            audio.play("start")
            return

    if game.state == GameStateEnum.GAME_OVER:
        if cmd in ('REINICIAR', 'ACAO', 'ENTER') or char in ('4', '6'):
            game.start_game()
            return

    if game.state == GameStateEnum.ATTRACT:
        if cmd in ('REINICIAR', 'ACAO', 'ENTER') or char in ('4', '6'):
            game.start_game()
            return

    if cmd == 'REINICIAR' or char == '4':
        game.start_game()


# =============================================================================
# LOOP PRINCIPAL DO SISTEMA NO STAND
# =============================================================================
def main():
    cap = None
    detector = None

    try:
        print("[STAND] Inicializando SnakeDonuts (Edicao Arcade Unimar Aberta)...")
        cap, camera_idx = stand_utils.encontrar_camera(retornar_indice=True)
        if cap is None:
            print("[ERRO] Nenhuma webcam detectada! Conecte a camera USB do stand.")
            raise RuntimeError("Webcam indisponivel. Conecte uma camera e tente novamente.")

        largura_real = LARGURA_PADRAO
        altura_real = ALTURA_PADRAO
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura_real)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura_real)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Detector de Mãos com MediaPipe
        detector = HandDetector(detectionCon=DETECTION_CON, maxHands=MAX_HANDS)

        # Instanciação dos Motores Principais
        leaderboard = StandLeaderboard()
        game = SnakeGameState(largura_real, altura_real, leaderboard=leaderboard)
        renderer = SnakeGameRenderer(largura_real, altura_real)

        nome_janela = "SnakeDonuts | ADS UNIMAR ABERTA"
        ui = stand_utils.InterfaceStand(
            nome_janela, 'SNAKEDONUTS ARCADE', camera_idx,
            extras=(
                'Guie a cobra com a ponta do indicador. Evite corpo e fantasmas.',
                '4  Reiniciar partida   |   6 / ENTER  Acao / Confirmar Recorde',
                'Itens: Anel (Escudo), Coracao (Segunda Chance), Cubo (Surpresa)',
                'Power-ups: Maca (Invencivel), Pocao (Encurtar), Moeda (+Pontos)'
            )
        )

        audio.set_muted(stand_utils.AUDIO_MUTED)
        audio.play("start")

        # Controles de Gesto e Timing
        hand_closed_counter = 0
        last_hand_state = False
        last_frame_time = time.monotonic()

        while True:
            # Cálculo de Delta Time Monotônico
            current_time = time.monotonic()
            dt = max(0.001, min(0.066, current_time - last_frame_time))
            last_frame_time = current_time

            # Captura de Quadro
            img = ui.ler(cap)
            if ui.espelhar:
                img = cv2.flip(img, 1)

            # Otimização Crítica de Latência: inferência do MediaPipe em 640x360
            scale_w, scale_h = 640, 360
            img_small = cv2.resize(img, (scale_w, scale_h), interpolation=cv2.INTER_LINEAR)
            hand_result = detector.findHands(img_small, draw=False, flipType=False)
            hands = hand_result[0] if isinstance(hand_result, tuple) else hand_result

            raw_head = None
            if hands and len(hands) > 0:
                scale_factor_x = largura_real / scale_w
                scale_factor_y = altura_real / scale_h
                lmList = hands[0].get('lmList', []) if isinstance(hands[0], dict) else []
                try:
                    fingers = detector.fingersUp(hands[0])
                except Exception:
                    fingers = None

                if len(lmList) > 8:
                    raw_head = (int(lmList[8][0] * scale_factor_x), int(lmList[8][1] * scale_factor_y))

                # Reconhecimento do gesto de mão fechada (punho cerrado) para reiniciar
                if fingers is not None:
                    is_closed = all(f == 0 for f in fingers)
                    if last_hand_state != is_closed:
                        if is_closed and game.state in (GameStateEnum.GAME_OVER, GameStateEnum.ENTERING_INITIALS):
                            hand_closed_counter += 1
                            if hand_closed_counter >= 2:
                                if game.state == GameStateEnum.ENTERING_INITIALS:
                                    game.confirm_initials_and_finish()
                                game.start_game()
                                hand_closed_counter = 0
                        last_hand_state = is_closed

            # Atualização do Estado do Jogo com dt
            game.update(raw_head, dt=dt)

            # Renderização com Telas Oficiais v2 e Sprites Neon
            img_rendered = renderer.render(img, game)

            # Apresentação na Janela e Tratamento de Teclas do Stand
            cmd, char = ui.mostrar(img_rendered, f'Nv {game.level} | Combo x{game.combo_multiplier}')
            cap = ui.tratar(cmd, cap)

            if cmd == 'ESC':
                break

            # Sincroniza estado de som do stand com o motor de áudio
            audio.set_muted(stand_utils.AUDIO_MUTED)

            # Tratamento de teclas de comando e entrada de iniciais
            handle_game_input(game, cmd, char)

            # Se trocou câmera ou espelhamento, limpa rastro para evitar artefatos visuais
            if cmd in ('CAMERA', 'ESPELHO'):
                game.points.clear()
                game.lengths.clear()
                game.current_length = 0.0
                game.smooth_head = None

    finally:
        print("[STAND] Finalizando SnakeDonuts e liberando recursos...")
        if cap is not None:
            cap.release()
        if detector is not None and hasattr(detector, 'hands') and detector.hands is not None:
            detector.hands.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
