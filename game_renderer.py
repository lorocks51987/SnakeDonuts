"""
=============================================================================
             RENDERIZADOR GRÁFICO OFICIAL NEON ARCADE - SNAKEDONUTS
=============================================================================
Renderizador gráfico profissional para displays HD (1280x720) do stand.
Carrega uma única vez as artes oficiais:
- assets/title_screen_arcade_v2.png (Modo Demonstração / Attract)
- assets/game_over_arcade_v2.png (Tela de Game Over / Recorde)
- Sprites originais com transparência real (Donut, Anel Dourado, Coração Pixel,
  Cubo Surpresa, Poção, Moeda, Fantasmas e Maçã).
Possui fallback procedural automático em caso de arquivos corrompidos ou ausentes.
=============================================================================
"""

import os
import math
import time
from typing import Optional, Tuple, List, Dict
import cv2
import numpy as np
from PIL import Image

from game_config import (
    get_asset_path,
    GameStateEnum,
    COLOR_CYBER_GREEN,
    COLOR_ELECTRIC_CYAN,
    COLOR_SYNTH_PINK,
    COLOR_GOLDEN_GLOW,
    COLOR_GHOST_CRIMSON,
    COLOR_DARK_VOID,
    COLOR_WHITE,
    COLOR_GRAY,
    LEVEL_DEFINITIONS
)
from game_state import SnakeGameState
import stand_utils


# =============================================================================
# BLENDING ULTRA-SEGURO DE SPRITES PNG COM ALPHA TRANSPARENTE
# =============================================================================
def safe_overlay_png(img_back: np.ndarray, img_front: np.ndarray, pos: Tuple[int, int]) -> np.ndarray:
    """
    Sobrepõe imagem RGBA sobre imagem BGR de destino com recorte seguro de bordas,
    garantindo que coordenadas fora da tela nunca causem erro de indexação.
    """
    if img_front is None or img_front.size == 0:
        return img_back

    bx, by = int(pos[0]), int(pos[1])
    bh, bw = img_back.shape[:2]
    fh, fw = img_front.shape[:2]

    # Verifica se está completamente fora
    if bx + fw <= 0 or by + fh <= 0 or bx >= bw or by >= bh:
        return img_back

    # Recorte da imagem frontal
    fx1 = max(0, -bx)
    fy1 = max(0, -by)
    fx2 = min(fw, bw - bx)
    fy2 = min(fh, bh - by)

    # Recorte correspondente na imagem de fundo
    gx1 = max(0, bx)
    gy1 = max(0, by)
    gx2 = min(bw, bx + fw)
    gy2 = min(bh, by + fh)

    if fx2 <= fx1 or fy2 <= fy1 or gx2 <= gx1 or gy2 <= gy1:
        return img_back

    front_crop = img_front[fy1:fy2, fx1:fx2]
    back_crop = img_back[gy1:gy2, gx1:gx2]

    if front_crop.shape[2] == 4:
        alpha = front_crop[:, :, 3].astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=2)
        front_bgr = front_crop[:, :, :3].astype(np.float32)
        back_bgr = back_crop.astype(np.float32)
        blended = front_bgr * alpha + back_bgr * (1.0 - alpha)
        img_back[gy1:gy2, gx1:gx2] = blended.astype(np.uint8)
    else:
        img_back[gy1:gy2, gx1:gx2] = front_crop[:, :, :3]

    return img_back


# =============================================================================
# CLASSE PRINCIPAL DO RENDERIZADOR
# =============================================================================
class SnakeGameRenderer:
    """Gerenciador central de renderização com carregamento único de assets."""

    def __init__(self, largura: int = 1280, altura: int = 720):
        self.largura = largura
        self.altura = altura

        # Carregamento ÚNICO das Telas Oficiais Arcade v2
        self.bg_title_screen = self._load_background("title_screen_arcade_v2.png")
        self.bg_game_over = self._load_background("game_over_arcade_v2.png")

        # Carregamento ÚNICO dos Sprites
        self.sprite_donut = self._load_sprite("Donut.png", 76, fallback_color=(255, 105, 180))
        self.sprite_donut_gold = self._load_sprite("donut_dourado.png", 76, fallback_color=(0, 215, 255))
        self.sprite_potion = self._load_sprite("Potion.png", 80, fallback_color=(255, 0, 0))
        self.sprite_coin = self._load_sprite("coin.png", 82, fallback_color=(0, 215, 255))
        self.sprite_ring = self._load_sprite("anel_dourado.png", 84, fallback_color=(0, 215, 255))
        self.sprite_heart = self._load_sprite("coracao_pixel.png", 84, fallback_color=(50, 50, 255))
        self.sprite_cube = self._load_sprite("cubo_surpresa.png", 84, fallback_color=(0, 215, 255))

        # Ícones do HUD (36x36)
        self.hud_icon_shield = cv2.resize(self.sprite_ring, (36, 36)) if self.sprite_ring is not None else None
        self.hud_icon_heart = cv2.resize(self.sprite_heart, (36, 36)) if self.sprite_heart is not None else None

        # Fantasmas
        self.sprite_ghost1 = self._load_sprite("ghost1.png", 76, fallback_color=(180, 180, 180))
        self.sprite_ghost2 = self._load_sprite("ghost2.png", 76, fallback_color=(180, 180, 180))
        self.sprite_ghost3 = self._load_sprite("ghost3.png", 76, fallback_color=(50, 50, 255)) # Assustado

        # Animação da Maçã
        self.apple_frames = self._load_apple_gif()
        self.apple_frame_idx = 0

    def _load_background(self, filename: str) -> Optional[np.ndarray]:
        """Carrega e ajusta resolução da imagem de fundo uma única vez."""
        path = get_asset_path(filename)
        if os.path.exists(path):
            try:
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                if img is not None and img.size > 0:
                    return cv2.resize(img, (self.largura, self.altura), interpolation=cv2.INTER_LINEAR)
            except Exception as e:
                print(f"[RENDERER] Aviso ao carregar background {filename}: {e}")
        return None

    def _load_sprite(self, filename: str, size: int, fallback_color: Tuple[int, int, int]) -> np.ndarray:
        """Carrega sprite RGBA com redimensionamento ou cria fallback procedural original."""
        path = get_asset_path(filename)
        if os.path.exists(path):
            try:
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None and img.size > 0:
                    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
            except Exception as e:
                print(f"[RENDERER] Aviso ao carregar sprite {filename}: {e}")

        # Fallback procedural seguro com transparência real
        fb = np.zeros((size, size, 4), dtype=np.uint8)
        cx, cy = size // 2, size // 2
        r = size // 2 - 3
        cv2.circle(fb, (cx, cy), r, (15, 15, 25, 240), -1, cv2.LINE_AA)
        cv2.circle(fb, (cx, cy), r - 4, fallback_color + (255,), -1, cv2.LINE_AA)
        cv2.circle(fb, (cx, cy), r, (0, 220, 255, 255), 2, cv2.LINE_AA)
        return fb

    def _load_apple_gif(self) -> List[np.ndarray]:
        """Carrega frames da maçã encantada com downsampling temporal."""
        frames = []
        path = get_asset_path("enchanted_apple.gif")
        if os.path.exists(path):
            try:
                with Image.open(path) as gif:
                    step = 5
                    for frame_idx in range(0, getattr(gif, "n_frames", 1), step):
                        gif.seek(frame_idx)
                        f_rgba = gif.convert("RGBA").resize((76, 76))
                        frames.append(cv2.cvtColor(np.array(f_rgba), cv2.COLOR_RGBA2BGRA))
            except Exception as e:
                print(f"[RENDERER] Aviso ao carregar GIF da maca: {e}")
        if not frames:
            fb = np.zeros((76, 76, 4), dtype=np.uint8)
            cv2.circle(fb, (38, 38), 34, (0, 230, 100, 255), -1, cv2.LINE_AA)
            frames.append(fb)
        return frames

    # =========================================================================
    # RENDERIZAÇÃO DO FRAME PRINCIPAL DE JOGO
    # =========================================================================
    def render(self, img_camera: np.ndarray, game: SnakeGameState) -> np.ndarray:
        """Renderiza o frame de acordo com o estado atual da máquina de estados."""
        now = time.monotonic()
        h, w = img_camera.shape[:2]

        # 1. Modo de Apresentação / Attract
        if game.state == GameStateEnum.ATTRACT:
            return self._render_attract_mode(img_camera, game, now)

        # 2. Tela de Game Over e Entrada de Iniciais
        if game.state in (GameStateEnum.GAME_OVER, GameStateEnum.ENTERING_INITIALS):
            return self._render_game_over_screen(img_camera, game, now)

        # 3. Partida em Andamento (PLAYING ou PAUSED_TRACKING)
        frame = img_camera.copy()

        # Efeito de Tremor de Tela (Shake)
        if game.shake_timer > 0.0:
            ox = np.random.randint(-5, 6)
            oy = np.random.randint(-5, 6)
            M = np.float32([[1, 0, ox], [0, 1, oy]])
            frame = cv2.warpAffine(frame, M, (w, h))

        # Desenha a Cobra Neon
        self._render_snake(frame, game, now)

        # Desenha o Donut (Pulsante e com rotação suave)
        self._render_food(frame, game, now)

        # Desenha Item Especial Ativo
        self._render_special_item(frame, game, now)

        # Desenha Fantasma Ativo
        self._render_ghost(frame, game, now)

        # Desenha Partículas e Textos Flutuantes
        for p in game.particles:
            pt = (int(p.x), int(p.y))
            cv2.circle(frame, pt, int(p.radius), p.color, -1, cv2.LINE_AA)

        for t in game.floating_texts:
            pt = (int(t.x), int(t.y))
            cv2.putText(frame, t.text, pt, cv2.FONT_HERSHEY_DUPLEX, t.scale, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(frame, t.text, pt, cv2.FONT_HERSHEY_DUPLEX, t.scale, t.color, 2, cv2.LINE_AA)

        # Banners Temporários (Subida de Nível e Efeito do Cubo Surpresa)
        self._render_banners(frame, game, now)

        # HUD Superior do Jogo
        self._render_hud(frame, game, now)

        # Se estiver em pausa de tracking
        if game.state == GameStateEnum.PAUSED_TRACKING:
            self._render_hand_paused_overlay(frame, now)

        return frame

    # -------------------------------------------------------------------------
    # DESENHO DA COBRA NEON (NEON ARCADE GLOW)
    # -------------------------------------------------------------------------
    def _render_snake(self, img: np.ndarray, game: SnakeGameState, now: float):
        n_pts = len(game.points)
        if n_pts < 2:
            return

        is_invincible = (game.invincible_powerup_timer > 0.0)
        is_safe = (game.invulnerable_safety_timer > 0.0)

        # Pisca se estiver em invulnerabilidade de segurança
        if is_safe and int(now * 12) % 2 == 0:
            return

        for i in range(1, n_pts):
            p1 = tuple(game.points[i - 1])
            p2 = tuple(game.points[i])
            if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) > 90.0:
                continue
            factor = i / n_pts
            thickness = int(10 + factor * 14)

            if is_invincible:
                # Efeito arco-íris neon pulsante
                hue = int((now * 140 + factor * 180) % 180)
                hsv_pix = np.uint8([[[hue, 255, 255]]])
                bgr = cv2.cvtColor(hsv_pix, cv2.COLOR_HSV2BGR)[0][0]
                color = (int(bgr[0]), int(bgr[1]), int(bgr[2]))
            else:
                # Gradiente oficial Neon Cyber: Cauda azul/verde -> Cabeça Cyber Green (#00FF88)
                b = int(255 * (1.0 - factor * 0.8))
                g = 255
                r = int(50 * (1.0 - factor))
                color = (b, g, r)

            cv2.line(img, p1, p2, color, thickness, cv2.LINE_AA)

        # Cabeça com Glow Neon
        hx, hy = game.points[-1]
        gr = 32 if not is_invincible else 40
        glow_color = COLOR_GOLDEN_GLOW if game.has_shield else (COLOR_ELECTRIC_CYAN if is_invincible else COLOR_CYBER_GREEN)

        gx1 = max(0, hx - gr)
        gy1 = max(0, hy - gr)
        gx2 = min(img.shape[1], hx + gr)
        gy2 = min(img.shape[0], hy + gr)
        if gx2 > gx1 and gy2 > gy1:
            glow_roi = img[gy1:gy2, gx1:gx2].copy()
            cv2.circle(glow_roi, (hx - gx1, hy - gy1), gr - 4, glow_color, -1)
            cv2.addWeighted(glow_roi, 0.40, img[gy1:gy2, gx1:gx2], 0.60, 0, img[gy1:gy2, gx1:gx2])

        # Núcleo branco da cabeça
        cv2.circle(img, (hx, hy), 16, COLOR_WHITE, -1, cv2.LINE_AA)

        # Anel de Escudo Dourado orbitando a cabeça
        if game.has_shield:
            pulse = math.sin(now * 8) * 3
            cv2.circle(img, (hx, hy), int(24 + pulse), COLOR_GOLDEN_GLOW, 2, cv2.LINE_AA)

        # Olhos arcade direcionados à comida
        fx, fy = game.food_pos
        ang = math.atan2(fy - hy, fx - hx)
        eye_dist = 6
        eye1_x = int(hx + math.cos(ang - 0.5) * eye_dist)
        eye1_y = int(hy + math.sin(ang - 0.5) * eye_dist)
        eye2_x = int(hx + math.cos(ang + 0.5) * eye_dist)
        eye2_y = int(hy + math.sin(ang + 0.5) * eye_dist)
        cv2.circle(img, (eye1_x, eye1_y), 3, (10, 10, 15), -1)
        cv2.circle(img, (eye2_x, eye2_y), 3, (10, 10, 15), -1)

    # -------------------------------------------------------------------------
    # ITENS E OBJETOS DO JOGO
    # -------------------------------------------------------------------------
    def _render_food(self, img: np.ndarray, game: SnakeGameState, now: float):
        fx, fy = game.food_pos
        scale = 1.0 + 0.08 * math.sin(now * 6)
        sprite = self.sprite_donut_gold if game.is_golden_donut else self.sprite_donut
        w = max(10, int(sprite.shape[1] * scale))
        h = max(10, int(sprite.shape[0] * scale))
        resized = cv2.resize(sprite, (w, h), interpolation=cv2.INTER_LINEAR)
        safe_overlay_png(img, resized, (fx - w // 2, fy - h // 2))

    def _render_special_item(self, img: np.ndarray, game: SnakeGameState, now: float):
        if game.special_item_type is None:
            return

        ix, iy = game.special_item_pos
        item = game.special_item_type

        # Efeito de piscar quando restarem menos de 1.8 segundos
        if game.special_item_timer < 1.8 and int(now * 8) % 2 == 0:
            return

        if item == "apple":
            frame = self.apple_frames[self.apple_frame_idx % len(self.apple_frames)]
            self.apple_frame_idx += 1
            safe_overlay_png(img, frame, (ix - frame.shape[1] // 2, iy - frame.shape[0] // 2))
        elif item == "potion":
            safe_overlay_png(img, self.sprite_potion, (ix - self.sprite_potion.shape[1] // 2, iy - self.sprite_potion.shape[0] // 2))
        elif item == "coin":
            scale = 1.0 + 0.08 * math.sin(now * 8)
            cw, ch = int(self.sprite_coin.shape[1] * scale), int(self.sprite_coin.shape[0] * scale)
            rc = cv2.resize(self.sprite_coin, (cw, ch))
            safe_overlay_png(img, rc, (ix - cw // 2, iy - ch // 2))
        elif item == "ring":
            scale = 1.0 + 0.09 * math.sin(now * 7)
            rw, rh = int(self.sprite_ring.shape[1] * scale), int(self.sprite_ring.shape[0] * scale)
            rr = cv2.resize(self.sprite_ring, (rw, rh))
            safe_overlay_png(img, rr, (ix - rw // 2, iy - rh // 2))
        elif item == "heart":
            scale = 1.0 + 0.12 * abs(math.sin(now * 5))
            hw, hh = int(self.sprite_heart.shape[1] * scale), int(self.sprite_heart.shape[0] * scale)
            rh = cv2.resize(self.sprite_heart, (hw, hh))
            safe_overlay_png(img, rh, (ix - hw // 2, iy - hh // 2))
        elif item == "cube":
            scale = 1.0 + 0.07 * math.sin(now * 6)
            cw, ch = int(self.sprite_cube.shape[1] * scale), int(self.sprite_cube.shape[0] * scale)
            rc = cv2.resize(self.sprite_cube, (cw, ch))
            safe_overlay_png(img, rc, (ix - cw // 2, iy - ch // 2))

    def _render_ghost(self, img: np.ndarray, game: SnakeGameState, now: float):
        if not game.ghost_active:
            return

        gx, gy = int(game.ghost_pos[0]), int(game.ghost_pos[1])
        if game.invincible_powerup_timer > 0.0:
            sprite = self.sprite_ghost3 # Assustado
        else:
            sprite = self.sprite_ghost2 if game.ghost_dir == 1 else self.sprite_ghost1

        # Pisca se estiver prestes a desaparecer
        if game.ghost_timer < 1.6 and int(now * 8) % 2 == 0:
            return

        safe_overlay_png(img, sprite, (gx - sprite.shape[1] // 2, gy - sprite.shape[0] // 2))

    # -------------------------------------------------------------------------
    # BANNERS CENTRAIS DE EVENTOS
    # -------------------------------------------------------------------------
    def _render_banners(self, img: np.ndarray, game: SnakeGameState, now: float):
        cx, cy = self.largura // 2, self.altura // 2

        # 1. Banner de Subida de Nível (~0.85s)
        if game.level_up_banner_timer > 0.0:
            bw, bh = 640, 110
            bx, by = cx - bw // 2, cy - bh // 2 - 40
            stand_utils.desenhar_retangulo_arredondado(
                img, (bx, by), (bx + bw, by + bh),
                cor_fundo=(12, 16, 26), cor_borda=COLOR_CYBER_GREEN, raio=14, alpha=0.94, espessura_borda=2
            )
            linhas = game.level_up_message.split("\n")
            cv2.putText(img, linhas[0], (bx + 30, by + 45), cv2.FONT_HERSHEY_DUPLEX, 1.0, COLOR_CYBER_GREEN, 2, cv2.LINE_AA)
            if len(linhas) > 1:
                cv2.putText(img, linhas[1], (bx + 30, by + 85), cv2.FONT_HERSHEY_DUPLEX, 0.58, COLOR_WHITE, 1, cv2.LINE_AA)

        # 2. Anúncio do Efeito do Cubo Surpresa
        if game.cube_announcement_timer > 0.0 and game.active_cube_announcement:
            bw, bh = 540, 70
            bx, by = cx - bw // 2, cy + 50
            stand_utils.desenhar_retangulo_arredondado(
                img, (bx, by), (bx + bw, by + bh),
                cor_fundo=(15, 12, 24), cor_borda=game.cube_announcement_color, raio=12, alpha=0.92, espessura_borda=2
            )
            cv2.putText(img, game.active_cube_announcement, (bx + 25, by + 45), cv2.FONT_HERSHEY_DUPLEX, 0.78, game.cube_announcement_color, 2, cv2.LINE_AA)

    # -------------------------------------------------------------------------
    # HUD SUPERIOR DO JOGO (COM ÍCONES E BARRAS DE STATUS)
    # -------------------------------------------------------------------------
    def _render_hud(self, img: np.ndarray, game: SnakeGameState, now: float):
        hud_h = 66
        hud_roi = img[0:hud_h, 0:self.largura]
        hud_bg = np.full(hud_roi.shape, COLOR_DARK_VOID, dtype=np.uint8)
        cv2.addWeighted(hud_bg, 0.88, hud_roi, 0.12, 0, hud_roi)
        cv2.line(img, (0, hud_h), (self.largura, hud_h), COLOR_ELECTRIC_CYAN, 2, cv2.LINE_AA)

        # Logo / Título
        cv2.putText(img, "ADS * UNIMAR ABERTA", (20, 24), cv2.FONT_HERSHEY_DUPLEX, 0.44, COLOR_ELECTRIC_CYAN, 1, cv2.LINE_AA)
        cv2.putText(img, "SNAKEDONUTS", (20, 52), cv2.FONT_HERSHEY_DUPLEX, 0.74, COLOR_WHITE, 2, cv2.LINE_AA)

        # Pontuação Central
        game.score_scale_anim = max(1.0, game.score_scale_anim - 0.03)
        score_str = f"SCORE: {game.score}"
        text_sz = cv2.getTextSize(score_str, cv2.FONT_HERSHEY_DUPLEX, 1.05 * game.score_scale_anim, 2)[0]
        cv2.putText(
            img, score_str, (self.largura // 2 - text_sz[0] // 2, 45),
            cv2.FONT_HERSHEY_DUPLEX, 1.05 * game.score_scale_anim, COLOR_CYBER_GREEN, 2, cv2.LINE_AA
        )

        # Nível e Top Score no canto direito
        high_score = max(game.score, game.leaderboard.get_high_score())
        top_str = f"TOP: {high_score}  [NV {game.level}]"
        cv2.putText(img, top_str, (self.largura - 320, 45), cv2.FONT_HERSHEY_DUPLEX, 0.72, COLOR_GOLDEN_GLOW, 2, cv2.LINE_AA)

        # Ícones de Proteção no HUD (Escudo do Anel e Coração Pixel)
        hud_icons_x = 240
        if game.has_shield and self.hud_icon_shield is not None:
            safe_overlay_png(img, self.hud_icon_shield, (hud_icons_x, 15))
            cv2.putText(img, "ESCUDO", (hud_icons_x + 42, 38), cv2.FONT_HERSHEY_DUPLEX, 0.45, COLOR_GOLDEN_GLOW, 1, cv2.LINE_AA)
            hud_icons_x += 130

        if game.has_extra_life and self.hud_icon_heart is not None:
            safe_overlay_png(img, self.hud_icon_heart, (hud_icons_x, 15))
            cv2.putText(img, "VIDA +1", (hud_icons_x + 42, 38), cv2.FONT_HERSHEY_DUPLEX, 0.45, COLOR_GHOST_CRIMSON, 1, cv2.LINE_AA)

        # Barra de Combo (Abaixo do HUD)
        if game.combo_multiplier > 1 or game.combo_time_remaining > 0.0:
            bw, bh = 240, 26
            bx = self.largura // 2 - bw // 2
            by = hud_h + 8

            prog = min(1.0, max(0.0, game.combo_time_remaining / game.combo_window_max))
            stand_utils.desenhar_retangulo_arredondado(
                img, (bx, by), (bx + bw, by + bh),
                cor_fundo=(12, 14, 24), cor_borda=COLOR_ELECTRIC_CYAN, raio=6, alpha=0.90
            )
            w_fill = int(bw * prog)
            if w_fill > 0:
                bar_col = COLOR_GOLDEN_GLOW if game.combo_frozen_timer > 0.0 else COLOR_SYNTH_PINK
                cv2.rectangle(img, (bx + 2, by + 2), (bx + w_fill - 2, by + bh - 2), bar_col, -1)

            lbl = f"COMBO x{game.combo_multiplier}!" if game.combo_frozen_timer <= 0.0 else f"CONGELADO x{game.combo_multiplier}!"
            cv2.putText(img, lbl, (bx + 40, by + 18), cv2.FONT_HERSHEY_DUPLEX, 0.55, COLOR_WHITE, 1, cv2.LINE_AA)

        # Barra de Invencibilidade (Canto Inferior Esquerdo)
        if game.invincible_powerup_timer > 0.0:
            pw, ph = 240, 26
            px, py = 20, self.altura - 95
            prog_inv = game.invincible_powerup_timer / 6.0
            stand_utils.desenhar_retangulo_arredondado(
                img, (px, py), (px + pw, py + ph),
                cor_fundo=(10, 14, 24), cor_borda=COLOR_CYBER_GREEN, raio=8, alpha=0.88
            )
            w_fill = int(pw * prog_inv)
            if w_fill > 0:
                cv2.rectangle(img, (px + 2, py + 2), (px + w_fill - 2, py + ph - 2), COLOR_CYBER_GREEN, -1)
            cv2.putText(
                img, f"INVENCIVEL: {game.invincible_powerup_timer:.1f}s", (px + 12, py + 18),
                cv2.FONT_HERSHEY_DUPLEX, 0.48, COLOR_WHITE, 1, cv2.LINE_AA
            )

    # -------------------------------------------------------------------------
    # AVISO DE PERDA MOMENTÂNEA DE TRACKING (PAUSA JUSTA)
    # -------------------------------------------------------------------------
    def _render_hand_paused_overlay(self, img: np.ndarray, now: float):
        cx, cy = self.largura // 2, self.altura // 2
        bw, bh = 560, 80
        bx, by = cx - bw // 2, cy - bh // 2
        stand_utils.desenhar_retangulo_arredondado(
            img, (bx, by), (bx + bw, by + bh),
            cor_fundo=(12, 14, 26), cor_borda=COLOR_ELECTRIC_CYAN, raio=12, alpha=0.92, espessura_borda=2
        )
        blink = int(now * 4) % 2 == 0
        cor = COLOR_CYBER_GREEN if blink else COLOR_ELECTRIC_CYAN
        cv2.putText(img, "MAO NAO DETECTADA", (bx + 85, by + 42), cv2.FONT_HERSHEY_DUPLEX, 0.80, cor, 2, cv2.LINE_AA)
        cv2.putText(img, "Aponte o indicador na camera para continuar!", (bx + 55, by + 68), cv2.FONT_HERSHEY_DUPLEX, 0.46, COLOR_WHITE, 1, cv2.LINE_AA)

    # -------------------------------------------------------------------------
    # MODO DEMONSTRAÇÃO / ATTRACT MODE (TELA INICIAL OFICIAL v2)
    # -------------------------------------------------------------------------
    def _render_attract_mode(self, img_camera: np.ndarray, game: SnakeGameState, now: float) -> np.ndarray:
        h, w = img_camera.shape[:2]

        # Usa arte oficial title_screen_arcade_v2.png se disponível, senão fallback procedural
        if self.bg_title_screen is not None:
            canvas = self.bg_title_screen.copy()
        else:
            canvas = img_camera.copy()
            cv2.rectangle(canvas, (0, 0), (w, h), COLOR_DARK_VOID, -1)

        cx = w // 2

        # Card de Instruções Inferior (Preserva a arte do título e mascote no topo e centro)
        cw, ch = 980, 185
        cx1 = cx - cw // 2
        cy1 = h - ch - 30

        stand_utils.desenhar_retangulo_arredondado(
            canvas, (cx1, cy1), (cx1 + cw, cy1 + ch),
            cor_fundo=(10, 12, 22), cor_borda=COLOR_ELECTRIC_CYAN, raio=14, alpha=0.92, espessura_borda=2
        )

        blink = int(now * 3) % 2 == 0
        cor_pisca = COLOR_CYBER_GREEN if blink else COLOR_ELECTRIC_CYAN
        cv2.putText(canvas, "* MOSTRE SUA MAO PARA JOGAR *", (cx - 210, cy1 + 32), cv2.FONT_HERSHEY_DUPLEX, 0.78, cor_pisca, 2, cv2.LINE_AA)
        cv2.line(canvas, (cx1 + 30, cy1 + 45), (cx1 + cw - 30, cy1 + 45), (45, 55, 75), 1, cv2.LINE_AA)

        # Alternância automática de páginas de dicas (a cada 3.5s)
        pagina_dica = int(now / 3.5) % 2
        if pagina_dica == 0:
            dicas = [
                ("1. Aponte o indicador para guiar a cobra e devorar Donuts", COLOR_CYBER_GREEN),
                ("2. Anel Dourado: Escudo contra colisoes  |  Coracao Pixel: Segunda Chance", COLOR_GOLDEN_GLOW),
            ]
        else:
            dicas = [
                ("1. Cubo Surpresa sorteia power-ups beneficos ou desafios arcade", COLOR_SYNTH_PINK),
                ("2. Encadeie coletas rapidas para ativar multiplicadores de combo ate x8!", COLOR_ELECTRIC_CYAN),
            ]

        for i, (txt, cor) in enumerate(dicas):
            cv2.putText(canvas, txt, (cx1 + 40, cy1 + 75 + i * 26), cv2.FONT_HERSHEY_DUPLEX, 0.49, cor, 1, cv2.LINE_AA)

        cv2.line(canvas, (cx1 + 30, cy1 + 135), (cx1 + cw - 30, cy1 + 135), (45, 55, 75), 1, cv2.LINE_AA)

        # Destaque do Recorde no rodapé do card
        high = game.leaderboard.get_high_score()
        top_name = game.leaderboard.scores[0]["name"] if game.leaderboard.scores else "ADS"
        cv2.putText(canvas, f"RECORDE DO STAND: {top_name} - {high} PTS   |   ADS UNIMAR ABERTA", (cx - 270, cy1 + 162), cv2.FONT_HERSHEY_DUPLEX, 0.52, COLOR_CYBER_GREEN, 1, cv2.LINE_AA)

        return canvas

    # -------------------------------------------------------------------------
    # TELA DE GAME OVER & ENTRADA DE INICIAIS (ARTE OFICIAL v2)
    # -------------------------------------------------------------------------
    def _render_game_over_screen(self, img_camera: np.ndarray, game: SnakeGameState, now: float) -> np.ndarray:
        h, w = img_camera.shape[:2]

        # Fundo oficial game_over_arcade_v2.png se disponível, senão fallback
        if self.bg_game_over is not None:
            canvas = self.bg_game_over.copy()
        else:
            canvas = img_camera.copy()
            cv2.rectangle(canvas, (0, 0), (w, h), COLOR_DARK_VOID, -1)

        cx = w // 2
        cy = h // 2

        card_w, card_h = 760, 520
        card_x = cx - card_w // 2
        card_y = cy - card_h // 2 - 15

        borda_cor = COLOR_CYBER_GREEN if game.qualifies_top5 else COLOR_GHOST_CRIMSON
        stand_utils.desenhar_retangulo_arredondado(
            canvas, (card_x, card_y), (card_x + card_w, card_y + card_h),
            cor_fundo=(10, 12, 20), cor_borda=borda_cor, raio=16, alpha=0.92, espessura_borda=2
        )

        cv2.putText(canvas, "GAME OVER", (cx - 170, card_y + 50), cv2.FONT_HERSHEY_DUPLEX, 1.7, (0, 0, 200), 5, cv2.LINE_AA)
        cv2.putText(canvas, "GAME OVER", (cx - 170, card_y + 50), cv2.FONT_HERSHEY_DUPLEX, 1.7, COLOR_WHITE, 2, cv2.LINE_AA)
        cv2.line(canvas, (card_x + 30, card_y + 70), (card_x + card_w - 30, card_y + 70), (45, 55, 75), 1, cv2.LINE_AA)

        # Resumo da Pontuação e Conquistas
        score_str = f"{game.score} PONTOS"
        text_sz = cv2.getTextSize(score_str, cv2.FONT_HERSHEY_DUPLEX, 1.35, 2)[0]
        cv2.putText(canvas, score_str, (cx - text_sz[0] // 2, card_y + 115), cv2.FONT_HERSHEY_DUPLEX, 1.35, COLOR_CYBER_GREEN, 2, cv2.LINE_AA)

        # Estatísticas da Partida (Linha Compacta)
        stats_line = f"Nivel: {game.level}   |   Maior Combo: x{game.max_combo}   |   Sobreviveu: {int(game.stats['survival_time'])}s"
        cv2.putText(canvas, stats_line, (cx - 240, card_y + 148), cv2.FONT_HERSHEY_DUPLEX, 0.50, COLOR_WHITE, 1, cv2.LINE_AA)

        # Se qualificado para o TOP 5: Modo Entrada de 3 Iniciais
        if game.qualifies_top5 and not game.initials_confirmed:
            rank_str = f"PARABENS! VOCE ALCANCOU O {game.record_rank}. LUGAR!"
            cv2.putText(canvas, rank_str, (cx - 210, card_y + 185), cv2.FONT_HERSHEY_DUPLEX, 0.65, COLOR_GOLDEN_GLOW, 2, cv2.LINE_AA)
            cv2.putText(canvas, "DIGITE OU ESCOLHA SUAS 3 INICIAIS:", (cx - 170, card_y + 215), cv2.FONT_HERSHEY_DUPLEX, 0.50, COLOR_WHITE, 1, cv2.LINE_AA)

            slot_w, slot_h = 58, 62
            gap = 18
            start_x = cx - (3 * slot_w + 2 * gap) // 2

            for i in range(3):
                sx = start_x + i * (slot_w + gap)
                sy = card_y + 235
                is_sel = (i == game.selected_initial_idx)
                cor_slot = COLOR_CYBER_GREEN if is_sel else (45, 55, 75)
                cor_letra = COLOR_WHITE if is_sel else COLOR_GRAY

                stand_utils.desenhar_retangulo_arredondado(
                    canvas, (sx, sy), (sx + slot_w, sy + slot_h),
                    (20, 25, 38), cor_slot, raio=8, alpha=0.95, espessura_borda=2 if is_sel else 1
                )
                char_str = game.player_initials[i]
                cv2.putText(canvas, char_str, (sx + 16, sy + 46), cv2.FONT_HERSHEY_DUPLEX, 1.25, cor_letra, 2, cv2.LINE_AA)

            cv2.putText(canvas, "Digite letras [A-Z], use [<- / ->] e confirme com [ENTER]", (cx - 240, card_y + 328), cv2.FONT_HERSHEY_DUPLEX, 0.48, COLOR_ELECTRIC_CYAN, 1, cv2.LINE_AA)

        else:
            # Hall da Fama TOP 5
            cv2.putText(canvas, "HALL DA FAMA - TOP 5 DO STAND", (cx - 150, card_y + 185), cv2.FONT_HERSHEY_DUPLEX, 0.56, COLOR_GOLDEN_GLOW, 1, cv2.LINE_AA)
            top_y = card_y + 210
            for idx, entry in enumerate(game.leaderboard.scores[:5]):
                cor_linha = COLOR_CYBER_GREEN if idx == 0 else COLOR_WHITE
                p_str = f"{idx + 1}."
                n_str = entry.get("name", "ADS")
                s_str = f"{entry.get('score', 0)} PTS"
                d_str = entry.get("date", "Stand")
                linha_format = f"{p_str}  {n_str:<4}  .....  {s_str:>8}  ({d_str})"
                cv2.putText(canvas, linha_format, (cx - 180, top_y + idx * 24), cv2.FONT_HERSHEY_DUPLEX, 0.50, cor_linha, 1, cv2.LINE_AA)

        # Estatísticas Especiais (Donuts, Fantasmas e Salvamentos)
        cv2.line(canvas, (card_x + 30, card_y + 355), (card_x + card_w - 30, card_y + 355), (45, 55, 75), 1, cv2.LINE_AA)
        saves_info = f"Donuts: {game.stats['donuts_eaten']}   |   Fantasmas Devorados: {game.stats['ghosts_eaten']}   |   Salvo por Anel/Coracao: {game.stats['shield_saves'] + game.stats['heart_saves']}x"
        cv2.putText(canvas, saves_info, (cx - 260, card_y + 382), cv2.FONT_HERSHEY_DUPLEX, 0.44, COLOR_GRAY, 1, cv2.LINE_AA)

        # Instruções de Reinício para o Stand
        cv2.putText(canvas, "Pressione [4], [6] ou [ENTER] para jogar novamente", (cx - 235, card_y + 425), cv2.FONT_HERSHEY_DUPLEX, 0.60, COLOR_WHITE, 1, cv2.LINE_AA)
        cv2.putText(canvas, "(Ou feche a mao 2x na camera para reiniciar)", (cx - 200, card_y + 455), cv2.FONT_HERSHEY_DUPLEX, 0.48, COLOR_ELECTRIC_CYAN, 1, cv2.LINE_AA)

        return canvas
