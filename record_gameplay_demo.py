"""
=============================================================================
         GERADOR DE GAMEPLAY DEMO (VÍDEO MP4 E GIF) - SNAKEDONUTS
=============================================================================
Gera uma demonstração realista de gameplay do SnakeDonuts Neon Arcade
em alta qualidade para materiais promocionais, documentação e GitHub:
- assets/gameplay_demo.mp4 (720p @ 25 FPS)
- assets/gameplay_demo.gif (640x360 @ 15 FPS para embedding no README)
=============================================================================
"""

import os
import sys
import math
import numpy as np
import cv2
from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from game_config import (
    LARGURA_PADRAO,
    ALTURA_PADRAO,
    GameStateEnum,
    COLOR_CYBER_GREEN,
    COLOR_ELECTRIC_CYAN,
    COLOR_SYNTH_PINK,
    COLOR_GOLDEN_GLOW,
    COLOR_GHOST_CRIMSON,
    COLOR_DARK_VOID,
    CubeEffect
)
from leaderboard_manager import StandLeaderboard
from game_state import SnakeGameState
from game_renderer import SnakeGameRenderer


def generate_ambient_background(w=1280, h=720):
    """Cria um fundo simulando a visão da webcam no stand com iluminação neon ambiente."""
    bg = np.zeros((h, w, 3), dtype=np.uint8)
    # Gradiente vertical suave azul-noite / violeta escuro de estande de tecnologia
    for y in range(h):
        ratio = y / h
        b = int(22 + ratio * 15)
        g = int(14 + ratio * 10)
        r = int(16 + ratio * 18)
        bg[y, :] = (b, g, r)

    # Grade sutil de arena arcade no chão
    grid_color = (35, 25, 32)
    for x in range(0, w, 80):
        cv2.line(bg, (x, 0), (x, h), grid_color, 1)
    for y in range(0, h, 80):
        cv2.line(bg, (0, y), (w, y), grid_color, 1)

    # Vinheta nas bordas
    mask = np.zeros((h, w), dtype=np.float32)
    cv2.circle(mask, (w // 2, h // 2), int(w * 0.55), 1.0, -1)
    mask = cv2.GaussianBlur(mask, (151, 151), 70)
    for c in range(3):
        bg[:, :, c] = (bg[:, :, c] * (0.65 + 0.35 * mask)).astype(np.uint8)

    return bg


def bezier_curve(p0, p1, p2, p3, t):
    """Interpolação cúbica de Bezier para movimento suave da mão."""
    u = 1.0 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return (int(x), int(y))


def record_demo():
    print("[DEMO] Inicializando simulação de gameplay oficial...")
    w, h = LARGURA_PADRAO, ALTURA_PADRAO
    leaderboard = StandLeaderboard()
    game = SnakeGameState(w, h, leaderboard=leaderboard)
    renderer = SnakeGameRenderer(w, h)

    base_bg = generate_ambient_background(w, h)

    fps = 25
    dt = 1.0 / fps
    total_seconds = 12.0
    total_frames = int(fps * total_seconds)

    output_mp4 = os.path.join(_SCRIPT_DIR, "assets", "gameplay_demo.mp4")
    output_gif = os.path.join(_SCRIPT_DIR, "assets", "gameplay_demo.gif")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_mp4, fourcc, fps, (w, h))

    gif_frames = []

    # Roteiro coreografado da demonstração
    # 0.0s - 1.5s: Modo Attract
    # 1.5s - 4.0s: Início da partida, coleta 2 Donuts, combo x1 -> x2
    # 4.0s - 6.5s: Coleta Anel Dourado (Escudo Ativo) + 3º Donut (combo x3)
    # 6.5s - 8.5s: Cubo Surpresa surge e é coletado -> Invocação de Fantasma!
    # 8.5s - 10.5s: Coleta Maçã Encantada (Invencível Rainbow) e devora o Fantasma!
    # 10.5s - 12.0s: Nível 2 desbloqueado, finalização da demonstração

    game.state = GameStateEnum.ATTRACT
    current_hand = (640, 360)
    sim_time = 0.0

    print(f"[DEMO] Renderizando {total_frames} quadros coreografados...")

    for f in range(total_frames):
        sim_time = f * dt

        # Gerenciamento de eventos da simulação
        if sim_time < 1.4:
            # Attract mode
            rendered = renderer.render(base_bg, game)
        elif 1.4 <= sim_time < 1.6:
            # Mão se aproxima: ativa start_game
            if game.state == GameStateEnum.ATTRACT:
                game.start_game()
                game.food_pos = (500, 320)
            current_hand = (640, 450)
            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)
        elif 1.6 <= sim_time < 4.0:
            # Trajetória curva para comer Donut 1 e Donut 2
            t = (sim_time - 1.6) / 2.4
            if t < 0.5:
                # Em direção ao Donut 1
                p_sub = t / 0.5
                current_hand = bezier_curve((640, 450), (580, 380), (520, 340), (500, 320), p_sub)
                if p_sub >= 0.95 and game.food_pos == (500, 320):
                    game.food_pos = (780, 260) # Próximo donut
            else:
                # Em direção ao Donut 2
                p_sub = (t - 0.5) / 0.5
                current_hand = bezier_curve((500, 320), (580, 280), (700, 240), (780, 260), p_sub)
                if p_sub >= 0.95 and game.food_pos == (780, 260):
                    # Spawna Anel Dourado
                    game.special_item_type = "ring"
                    game.special_item_pos = (920, 460)
                    game.special_item_timer = 8.0
                    game.special_item_max_duration = 8.0
                    game.food_pos = (600, 520)

            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)

        elif 4.0 <= sim_time < 6.5:
            # Vai até o Anel Dourado e obtém o Escudo
            t = (sim_time - 4.0) / 2.5
            current_hand = bezier_curve((780, 260), (860, 320), (920, 390), (920, 460), t)
            if t >= 0.92 and game.has_shield:
                # Spawna Cubo Surpresa
                game.special_item_type = "cube"
                game.special_item_pos = (520, 420)
                game.special_item_timer = 8.0
                game.special_item_max_duration = 8.0

            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)

        elif 6.5 <= sim_time < 8.5:
            # Vai até o Cubo Surpresa
            t = (sim_time - 6.5) / 2.0
            current_hand = bezier_curve((920, 460), (800, 490), (660, 450), (520, 420), t)
            if t >= 0.92 and not game.ghost_active:
                # Efeito do cubo: Invocação de Fantasma!
                game.spawn_ghost()
                game.ghost_pos = [200.0, 180.0]
                game.ghost_timer = 9.0
                game.active_cube_announcement = "ALERTA: FANTASMA INVOCADO!"
                game.cube_announcement_color = COLOR_GHOST_CRIMSON
                game.cube_announcement_timer = 2.0
                # Spawna Maçã Encantada
                game.special_item_type = "apple"
                game.special_item_pos = (350, 260)
                game.special_item_timer = 8.0
                game.special_item_max_duration = 8.0

            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)

        elif 8.5 <= sim_time < 10.5:
            # Vai até a Maçã Encantada, ganha invencibilidade e ataca o Fantasma
            t = (sim_time - 8.5) / 2.0
            if t < 0.5:
                # Rumo à Maçã
                p_sub = t / 0.5
                current_hand = bezier_curve((520, 420), (460, 360), (400, 300), (350, 260), p_sub)
            else:
                # Rumo ao Fantasma
                p_sub = (t - 0.5) / 0.5
                gx, gy = int(game.ghost_pos[0]), int(game.ghost_pos[1])
                current_hand = bezier_curve((350, 260), (300, 230), (250, 200), (gx, gy), p_sub)

            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)

        else:
            # 10.5s - 12.0s: Nível 2 e vitória da demonstração
            t = (sim_time - 10.5) / 1.5
            current_hand = bezier_curve((current_hand[0], current_hand[1]), (640, 300), (800, 360), (640, 360), t)
            if game.level < 2:
                game.level = 2
                game.score = 1250
                game.level_up_banner_timer = 1.8
                game.level_up_info = ("NIVEL 2", "CORRERIA ACUCARADA", "MACA & SUPER MOEDA!")
            game.update(current_hand, dt=dt)
            rendered = renderer.render(base_bg, game)

        # Gravação no MP4
        writer.write(rendered)

        # Amostragem para o GIF (15 FPS, resolução otimizada 640x360 para carregar rápido na web)
        if f % 2 == 0:
            frame_small = cv2.resize(rendered, (640, 360), interpolation=cv2.INTER_AREA)
            # Converte BGR para RGB para o Pillow
            rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
            gif_frames.append(Image.fromarray(rgb_small))

    writer.release()
    print(f"[DEMO] Vídeo MP4 gravado com sucesso: {output_mp4} ({os.path.getsize(output_mp4) / 1024:.1f} KB)")

    print("[DEMO] Otimizando e exportando animação GIF...")
    if gif_frames:
        # Salva GIF com paleta adaptativa
        gif_frames[0].save(
            output_gif,
            save_all=True,
            append_images=gif_frames[1:],
            duration=int(1000 / 12), # ~12 fps no GIF
            loop=0,
            optimize=True
        )
        print(f"[DEMO] GIF exportado com sucesso: {output_gif} ({os.path.getsize(output_gif) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    record_demo()
