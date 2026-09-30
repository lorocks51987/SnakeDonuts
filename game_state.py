"""
=============================================================================
             MOTOR DE ESTADO E REGRAS DO JOGO - SNAKEDONUTS
=============================================================================
Gerencia toda a física, colisões, estados, progressão, combos e itens
do SnakeDonuts de forma desacoplada da GUI e da captura de vídeo.
Permite execução 100% autônoma (headless) em suítes de testes unitários.
=============================================================================
"""

import math
import random
import time
from typing import List, Tuple, Optional, Dict, Any

from game_config import (
    GameStateEnum,
    CubeEffect,
    LEVEL_DEFINITIONS,
    CUBE_POSITIVE_WEIGHTS,
    CUBE_RISK_WEIGHTS,
    LARGURA_PADRAO,
    ALTURA_PADRAO,
    MARGEM_SPAWN_X,
    MARGEM_SPAWN_Y_TOP,
    MARGEM_SPAWN_Y_BOTTOM,
    SCORE_DONUT,
    SCORE_APPLE,
    SCORE_POTION,
    SCORE_COIN,
    SCORE_RING,
    SCORE_HEART,
    SCORE_SURPRISE_CUBE_BASE,
    SCORE_GHOST_EATEN,
    get_level_bonus,
    COMBO_TIERS,
    COMBO_WINDOW_BASE,
    DURACAO_MACA,
    DURACAO_INVENCIBILIDADE,
    DURACAO_POTION,
    DURACAO_COIN,
    DURACAO_RING,
    DURACAO_HEART,
    DURACAO_CUBE,
    DURACAO_GHOST,
    INVULNERABILIDADE_POS_ESCUDO,
    INVULNERABILIDADE_SEGUNDA_CHANCE,
    DURACAO_BANNER_LEVEL_UP,
    TEMPO_TOLERANCIA_PERDA_MAO,
    TEMPO_OCIOSO_ATTRACT,
    COMPRIMENTO_INICIAL,
    CRESCIMENTO_DONUT,
    DISTANCIA_SEGURA_AUTOCOLISAO,
    LIMIAR_SALTO_TELEPORTE,
    VELOCIDADE_GHOST_BASE,
    COLOR_CYBER_GREEN,
    COLOR_ELECTRIC_CYAN,
    COLOR_SYNTH_PINK,
    COLOR_GOLDEN_GLOW,
    COLOR_GHOST_CRIMSON,
    COLOR_WHITE
)
from game_audio import audio
from leaderboard_manager import StandLeaderboard


# =============================================================================
# ESTRUTURAS VISUAIS LEVES (PARTÍCULAS E TEXTOS FLUTUANTES)
# =============================================================================
class Particle:
    """Partícula com movimento e atenuação baseados em tempo real (dt)."""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(140.0, 380.0) # pixels por segundo
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.radius = random.uniform(4.0, 8.0)
        self.life = 1.0 # 1.0 a 0.0
        self.decay = random.uniform(1.8, 3.2) # decaimento por segundo

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= (0.1 ** dt) # amortecimento independente de FPS
        self.vy *= (0.1 ** dt)
        self.life -= self.decay * dt
        self.radius = max(1.0, self.radius * (0.5 ** dt))
        return self.life > 0.0


class FloatingText:
    """Texto animado que sobe e desaparece com base em dt."""
    def __init__(self, text: str, x: float, y: float, color=(0, 255, 255), scale=1.0, duration=1.0):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.scale = scale
        self.life = 1.0
        self.decay = 1.0 / max(0.2, duration)
        self.vy = -65.0 # pixels por segundo para cima

    def update(self, dt: float) -> bool:
        self.y += self.vy * dt
        self.life -= self.decay * dt
        return self.life > 0.0


# =============================================================================
# GERENCIADOR DE SPAWN BASEADO EM TEMPO MONOTÔNICO
# =============================================================================
class SpawnManager:
    """Agenda itens com verificação geométrica e regras de tempo estritas."""
    def __init__(self, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO):
        self.largura = largura
        self.altura = altura
        self.next_special_spawn_time = time.monotonic() + 3.0
        self.min_special_interval = 4.5 # cooldown entre spawns de itens especiais

    def get_safe_position(self, avoid_points: List[Tuple[float, float]], min_dist: float = 120.0) -> Tuple[int, int]:
        """Tenta encontrar uma posição segura longe da cobra, HUD e itens."""
        for _ in range(25):
            rx = random.randint(MARGEM_SPAWN_X, self.largura - MARGEM_SPAWN_X)
            ry = random.randint(MARGEM_SPAWN_Y_TOP, self.altura - MARGEM_SPAWN_Y_BOTTOM)
            safe = True
            for px, py in avoid_points:
                if math.hypot(rx - px, ry - py) < min_dist:
                    safe = False
                    break
            if safe:
                return (rx, ry)
        # Fallback se todas as tentativas colidirem
        return (random.randint(MARGEM_SPAWN_X, self.largura - MARGEM_SPAWN_X),
                random.randint(MARGEM_SPAWN_Y_TOP, self.altura - MARGEM_SPAWN_Y_BOTTOM))


# =============================================================================
# CLASSE DE ESTADO E LÓGICA PRINCIPAL (HEADLESS & TESTÁVEL)
# =============================================================================
class SnakeGameState:
    """Motor completo de estado do SnakeDonuts sem dependências gráficas."""

    def __init__(self, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO, leaderboard: Optional[StandLeaderboard] = None):
        self.largura = largura
        self.altura = altura
        self.leaderboard = leaderboard if leaderboard is not None else StandLeaderboard()
        self.spawner = SpawnManager(largura, altura)

        # Estado da Máquina
        self.state = GameStateEnum.ATTRACT
        self.previous_state = GameStateEnum.ATTRACT

        # Cobra e Rastro
        self.points: List[List[int]] = []
        self.lengths: List[float] = []
        self.current_length: float = 0.0
        self.allowed_length: float = COMPRIMENTO_INICIAL
        self.smooth_head: Optional[List[float]] = None

        # Donut Comum / Dourado
        self.food_pos: Tuple[int, int] = (largura // 2, altura // 2)
        self.is_golden_donut: bool = False
        self.golden_donut_timer: float = 0.0

        # Itens Especiais Ativos (Apenas 1 item especial comum ativo por vez)
        self.special_item_type: Optional[str] = None
        self.special_item_pos: Tuple[int, int] = (0, 0)
        self.special_item_timer: float = 0.0
        self.special_item_max_duration: float = 0.0

        # Fantasma
        self.ghost_active: bool = False
        self.ghost_pos: List[float] = [0.0, 0.0]
        self.ghost_timer: float = 0.0
        self.ghost_dir: int = 1
        self.ghost_speed: float = VELOCIDADE_GHOST_BASE
        self.ghost_speed_boost_timer: float = 0.0

        # Power-ups e Proteções
        self.invincible_powerup_timer: float = 0.0
        self.invulnerable_safety_timer: float = 0.0
        self.has_shield: bool = False     # Anel Dourado
        self.has_extra_life: bool = False # Coração Pixel

        # Cubo Surpresa
        self.first_cube_in_game: bool = True
        self.active_cube_announcement: Optional[str] = None
        self.cube_announcement_timer: float = 0.0
        self.cube_announcement_color: Tuple[int, int, int] = COLOR_GOLDEN_GLOW

        # Combos
        self.combo_count: int = 0
        self.combo_multiplier: int = 1
        self.combo_time_remaining: float = 0.0
        self.combo_window_max: float = COMBO_WINDOW_BASE
        self.combo_frozen_timer: float = 0.0
        self.combo_tight_timer: float = 0.0
        self.max_combo: int = 1

        # Nível e Progressão
        self.level: int = 1
        self.level_up_banner_timer: float = 0.0
        self.level_up_message: str = ""
        self.unlocked_items: List[str] = []

        # Pontuação e Estatísticas
        self.score: int = 0
        self.score_scale_anim: float = 1.0
        self.stats: Dict[str, Any] = {
            "survival_time": 0.0,
            "donuts_eaten": 0,
            "ghosts_eaten": 0,
            "special_items_collected": 0,
            "shield_saves": 0,
            "heart_saves": 0,
            "max_combo": 1,
            "final_level": 1
        }

        # Entrada de Iniciais (Hall da Fama)
        self.qualifies_top5: bool = False
        self.record_rank: int = 0
        self.player_initials: List[str] = ["A", "D", "S"]
        self.selected_initial_idx: int = 0
        self.initials_confirmed: bool = False

        # Tracking e Tempo
        self.last_update_time: float = time.monotonic()
        self.last_hand_seen_time: float = time.monotonic()
        self.shake_timer: float = 0.0

        # Partículas e Efeitos
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

        # Inicializa comida inicial
        self.spawn_food()

    # -------------------------------------------------------------------------
    # RESET E CONTROLE DE SESSÃO
    # -------------------------------------------------------------------------
    def start_game(self):
        """Inicia uma nova partida competitiva."""
        self.state = GameStateEnum.PLAYING
        self.points.clear()
        self.lengths.clear()
        self.current_length = 0.0
        self.allowed_length = COMPRIMENTO_INICIAL
        self.smooth_head = None

        self.score = 0
        self.level = 1
        self.unlocked_items.clear()
        self.ghost_speed = LEVEL_DEFINITIONS[1]["ghost_speed"]
        self.combo_window_max = LEVEL_DEFINITIONS[1]["combo_window"]
        self.combo_count = 0
        self.combo_multiplier = 1
        self.combo_time_remaining = 0.0
        self.max_combo = 1

        self.has_shield = False
        self.has_extra_life = False
        self.invincible_powerup_timer = 0.0
        self.invulnerable_safety_timer = 0.0
        self.first_cube_in_game = True

        self.special_item_type = None
        self.special_item_pos = (0, 0)
        self.special_item_timer = 0.0
        self.special_item_max_duration = 0.0

        self.ghost_active = False
        self.ghost_speed_boost_timer = 0.0

        self.is_golden_donut = False
        self.golden_donut_timer = 0.0

        self.combo_frozen_timer = 0.0
        self.combo_tight_timer = 0.0

        self.shake_timer = 0.0
        self.last_hand_seen_time = time.monotonic()
        self.last_update_time = time.monotonic()

        self.particles.clear()
        self.floating_texts.clear()
        self.level_up_banner_timer = 0.0
        self.active_cube_announcement = None
        self.cube_announcement_timer = 0.0

        self.stats = {
            "survival_time": 0.0,
            "donuts_eaten": 0,
            "ghosts_eaten": 0,
            "special_items_collected": 0,
            "shield_saves": 0,
            "heart_saves": 0,
            "max_combo": 1,
            "final_level": 1
        }

        self.qualifies_top5 = False
        self.record_rank = 0
        self.initials_confirmed = False
        self.player_initials = ["A", "D", "S"]
        self.selected_initial_idx = 0

        self.spawner.next_special_spawn_time = time.monotonic() + 3.0
        self.spawn_food()
        audio.play("start")

    def end_game(self):
        """Finaliza a partida e avalia recordes."""
        self.state = GameStateEnum.GAME_OVER
        self.stats["max_combo"] = self.max_combo
        self.stats["final_level"] = self.level
        self.trigger_shake(0.5)

        self.qualifies_top5 = self.leaderboard.is_top_score(self.score)
        if self.qualifies_top5:
            self.state = GameStateEnum.ENTERING_INITIALS
            self.record_rank = self.leaderboard.get_rank(self.score)
            audio.play("record")
        else:
            audio.play("game_over")

    def confirm_initials_and_finish(self):
        """Salva as iniciais no TOP 5 e transiciona para tela de Game Over / Attract."""
        if self.qualifies_top5 and not self.initials_confirmed:
            name = "".join(self.player_initials).upper()
            self.leaderboard.add_score(name, self.score)
            self.initials_confirmed = True
        self.state = GameStateEnum.GAME_OVER

    # -------------------------------------------------------------------------
    # SPAWN DE ITENS E FANTASMAS
    # -------------------------------------------------------------------------
    def spawn_food(self):
        """Spawna o Donut em local seguro."""
        avoid = [self.points[-1]] if self.points else [(self.largura // 2, self.altura // 2)]
        if self.special_item_type:
            avoid.append(self.special_item_pos)
        self.food_pos = self.spawner.get_safe_position(avoid, min_dist=100.0)

    def spawn_ghost(self):
        """Spawna o fantasma afastado da cobra."""
        self.ghost_active = True
        self.ghost_timer = DURACAO_GHOST
        hx, hy = self.points[-1] if self.points else (self.largura // 2, self.altura // 2)
        gx = MARGEM_SPAWN_X if hx > self.largura // 2 else self.largura - MARGEM_SPAWN_X
        gy = random.randint(MARGEM_SPAWN_Y_TOP, self.altura - MARGEM_SPAWN_Y_BOTTOM)
        self.ghost_pos = [float(gx), float(gy)]

    def _attempt_spawn_special_item(self, now: float):
        """Agendador determinístico de itens especiais baseado em tempo e nível."""
        if self.special_item_type is not None:
            return
        if now < self.spawner.next_special_spawn_time:
            return

        unlocked = []
        for lvl in range(1, self.level + 1):
            if lvl in LEVEL_DEFINITIONS:
                unlocked.extend(LEVEL_DEFINITIONS[lvl]["unlocked_items"])
        unlocked = list(dict.fromkeys(unlocked))

        if not unlocked:
            self.spawner.next_special_spawn_time = now + 2.0
            return

        # Pesos e probabilidades dos itens disponíveis
        pool = []
        if "apple" in unlocked:
            pool.extend(["apple"] * 25)
        if "coin" in unlocked:
            pool.extend(["coin"] * 25)
        if "potion" in unlocked:
            pool.extend(["potion"] * 20)
        if "ring" in unlocked:
            pool.extend(["ring"] * 18)
        if "cube" in unlocked:
            pool.extend(["cube"] * 12)
        if "heart" in unlocked:
            pool.extend(["heart"] * 4) # Raro no nível 5+

        if not pool:
            return

        chosen_item = random.choice(pool)
        avoid = [self.food_pos]
        if self.points:
            avoid.append(self.points[-1])
        if self.ghost_active:
            avoid.append((self.ghost_pos[0], self.ghost_pos[1]))

        pos = self.spawner.get_safe_position(avoid, min_dist=120.0)

        durations = {
            "apple": DURACAO_MACA,
            "potion": DURACAO_POTION,
            "coin": DURACAO_COIN,
            "ring": DURACAO_RING,
            "cube": DURACAO_CUBE,
            "heart": DURACAO_HEART
        }

        self.special_item_type = chosen_item
        self.special_item_pos = pos
        self.special_item_timer = durations.get(chosen_item, 7.0)
        self.special_item_max_duration = self.special_item_timer
        self.spawner.next_special_spawn_time = now + self.special_item_timer + self.spawner.min_special_interval

    # -------------------------------------------------------------------------
    # COMBOS, PONTUAÇÃO E PROGRESSÃO
    # -------------------------------------------------------------------------
    def _update_combo_tier(self):
        """Calcula o multiplicador de combo com tiers explícitos (x1, x2, x3, x5, x8)."""
        mult = 1
        for threshold, tier in COMBO_TIERS:
            if self.combo_count >= threshold:
                mult = tier
        self.combo_multiplier = mult
        if mult > self.max_combo:
            self.max_combo = mult

    def register_eat(self, base_points: int, item_name: str, pos: Tuple[int, int], color: Tuple[int, int, int]):
        """Registra pontuação com combo e atualiza estatísticas."""
        # Se combo não estiver expirado, incrementa
        if self.combo_time_remaining > 0.0:
            self.combo_count += 1
        else:
            self.combo_count = 1

        self._update_combo_tier()

        # Tempo da janela de combo
        janela = self.combo_window_max
        if self.combo_tight_timer > 0.0:
            janela = 1.6 # Janela mais apertada por efeito do cubo
        self.combo_time_remaining = janela

        gained = base_points * self.combo_multiplier
        self.score += gained
        self.score_scale_anim = 1.35

        mult_str = f" (x{self.combo_multiplier})" if self.combo_multiplier > 1 else ""
        self.floating_texts.append(FloatingText(f"+{gained}{mult_str}", pos[0], pos[1], color, 1.0, 1.1))
        self.emit_particles(pos[0], pos[1], color, count=16)

        if self.combo_multiplier > 1:
            audio.play("combo")

        # Checa Progressão de Nível
        self._check_level_progression()

    def _check_level_progression(self):
        """Verifica se o jogador atingiu os pontos necessários para o próximo nível."""
        current_lvl = self.level
        next_lvl = current_lvl + 1

        target_score = None
        if next_lvl in LEVEL_DEFINITIONS:
            target_score = LEVEL_DEFINITIONS[next_lvl]["min_score"]
        else:
            # Níveis 6 em diante
            target_score = 10000 + (next_lvl - 5) * 6000

        if self.score >= target_score:
            self.level = next_lvl
            bonus = get_level_bonus(self.level)
            self.score += bonus

            lvl_info = LEVEL_DEFINITIONS.get(self.level, {
                "nome": f"ZONA NEON {self.level}",
                "desc": "Fantasmas mais rapidos e combos intensos!",
                "combo_window": max(1.8, 2.2 - (self.level - 5) * 0.1),
                "ghost_speed": min(340.0, 270.0 + (self.level - 5) * 15.0),
                "unlocked_items": []
            })

            self.ghost_speed = lvl_info["ghost_speed"]
            self.combo_window_max = lvl_info["combo_window"]
            self.level_up_message = f"NIVEL {self.level}: {lvl_info['nome']}!\n{lvl_info['desc']}"
            self.level_up_banner_timer = DURACAO_BANNER_LEVEL_UP
            audio.play("level_up")
            self.floating_texts.append(
                FloatingText(f"BONUS NIVEL +{bonus}!", self.largura // 2 - 100, 100, COLOR_CYBER_GREEN, 1.2, 1.4)
            )

    # -------------------------------------------------------------------------
    # LÓGICA DO CUBO SURPRESA
    # -------------------------------------------------------------------------
    def apply_surprise_cube(self, pos: Tuple[int, int]):
        """Sorteia e aplica um efeito claramente anunciado com balanceamento justo."""
        if self.first_cube_in_game:
            # O primeiro cubo é garantidamente positivo
            pool = []
            for effect, weight in CUBE_POSITIVE_WEIGHTS.items():
                pool.extend([effect] * weight)
            chosen = random.choice(pool)
            self.first_cube_in_game = False
        else:
            pool = []
            for effect, weight in CUBE_POSITIVE_WEIGHTS.items():
                pool.extend([effect] * weight)
            for effect, weight in CUBE_RISK_WEIGHTS.items():
                pool.extend([effect] * weight)
            chosen = random.choice(pool)

        # Pontuação base do cubo
        self.register_eat(SCORE_SURPRISE_CUBE_BASE, "CUBO SURPRESA", pos, COLOR_GOLDEN_GLOW)
        self.stats["special_items_collected"] += 1
        audio.play("cube")

        # Aplicação dos Efeitos
        if chosen == CubeEffect.BONUS_POINTS:
            bonus = 300
            self.score += bonus
            self.active_cube_announcement = "+300 PONTOS EXTRAS!"
            self.cube_announcement_color = COLOR_CYBER_GREEN
        elif chosen == CubeEffect.SHRINK_BODY:
            self.allowed_length = max(COMPRIMENTO_INICIAL, int(self.allowed_length * 0.65))
            self.active_cube_announcement = "CORPO REDUZIDO EM 35%!"
            self.cube_announcement_color = COLOR_ELECTRIC_CYAN
        elif chosen == CubeEffect.GOLDEN_SHIELD:
            self.has_shield = True
            self.active_cube_announcement = "ESCUDO DOURADO ATIVADO!"
            self.cube_announcement_color = COLOR_GOLDEN_GLOW
        elif chosen == CubeEffect.INVINCIBILITY:
            self.invincible_powerup_timer = 5.0
            self.active_cube_announcement = "INVENCIVEL POR 5 SEGUNDOS!"
            self.cube_announcement_color = COLOR_CYBER_GREEN
        elif chosen == CubeEffect.FREEZE_COMBO:
            self.combo_frozen_timer = 5.0
            self.active_cube_announcement = "COMBO CONGELADO POR 5S!"
            self.cube_announcement_color = COLOR_ELECTRIC_CYAN
        elif chosen == CubeEffect.GOLDEN_DONUT:
            self.is_golden_donut = True
            self.golden_donut_timer = 8.0
            self.active_cube_announcement = "DONUT DOURADO SURGIU!"
            self.cube_announcement_color = COLOR_GOLDEN_GLOW
        elif chosen == CubeEffect.SPAWN_GHOST:
            self.spawn_ghost()
            self.active_cube_announcement = "ALERTA: FANTASMA INVOCADO!"
            self.cube_announcement_color = COLOR_GHOST_CRIMSON
        elif chosen == CubeEffect.SPEED_GHOST:
            self.ghost_speed_boost_timer = 5.0
            self.active_cube_announcement = "FANTASMA ACELERADO POR 5S!"
            self.cube_announcement_color = COLOR_GHOST_CRIMSON
        elif chosen == CubeEffect.TIGHT_COMBO:
            self.combo_tight_timer = 5.0
            self.active_cube_announcement = "JANELA DE COMBO REDUZIDA!"
            self.cube_announcement_color = COLOR_SYNTH_PINK

        self.cube_announcement_timer = 2.2

    # -------------------------------------------------------------------------
    # MECÂNICAS DE SALVAMENTO: ESCUDO & CORAÇÃO PIXEL
    # -------------------------------------------------------------------------
    def handle_fatal_collision(self, cause: str) -> bool:
        """
        Intercepta uma colisão fatal:
        1. Anel Dourado consome e salva.
        2. Coração Pixel consome e concede Segunda Chance.
        3. Caso contrário, aciona Game Over.
        Retorna True se o jogador foi salvo, False se resultou em Game Over.
        """
        if self.invincible_powerup_timer > 0.0 or self.invulnerable_safety_timer > 0.0:
            return True # Imune

        # 1. Anel Dourado (Escudo)
        if self.has_shield:
            self.has_shield = False
            self.stats["shield_saves"] += 1
            self.invulnerable_safety_timer = INVULNERABILIDADE_POS_ESCUDO
            self.floating_texts.append(
                FloatingText("SALVO PELO ANEL!", self.largura // 2 - 120, self.altura // 2 - 30, COLOR_GOLDEN_GLOW, 1.4, 1.3)
            )
            px = self.points[-1][0] if self.points else self.largura // 2
            py = self.points[-1][1] if self.points else self.altura // 2
            self.emit_particles(px, py, COLOR_GOLDEN_GLOW, count=28)
            self.trigger_shake(0.25)
            audio.play("shield_break")

            if cause == "ghost":
                self.ghost_active = False # Remove o fantasma que colidiu
            return True

        # 2. Coração Pixel (Segunda Chance)
        if self.has_extra_life:
            self.has_extra_life = False
            self.stats["heart_saves"] += 1

            # Reduz comprimento para no maximo 45% do anterior, preservando pelo menos o inicial
            self.allowed_length = max(COMPRIMENTO_INICIAL, int(self.allowed_length * 0.45))
            # Limpa rastro antigo para evitar autocolisão imediata
            if self.points:
                last_pt = list(self.points[-1])
                self.points = [last_pt]
                self.lengths = [0.0]
                self.current_length = 0.0

            # Remove fantasma e encerra combo
            self.ghost_active = False
            self.combo_count = 0
            self.combo_multiplier = 1
            self.combo_time_remaining = 0.0

            # 2 segundos de invulnerabilidade
            self.invulnerable_safety_timer = INVULNERABILIDADE_SEGUNDA_CHANCE

            self.floating_texts.append(
                FloatingText("SEGUNDA CHANCE!", self.largura // 2 - 130, self.altura // 2 - 30, COLOR_GHOST_CRIMSON, 1.5, 1.6)
            )
            px = self.points[-1][0] if self.points else self.largura // 2
            py = self.points[-1][1] if self.points else self.altura // 2
            self.emit_particles(px, py, COLOR_GHOST_CRIMSON, count=32)
            self.trigger_shake(0.4)
            audio.play("second_chance")
            return True

        # 3. Morte Fatal
        self.end_game()
        return False

    # -------------------------------------------------------------------------
    # VERIFICAÇÃO DE AUTOCOLISÃO POR DISTÂNCIA FÍSICA E SEGMENTOS
    # -------------------------------------------------------------------------
    def check_self_collision(self, hx: int, hy: int) -> bool:
        """
        Verifica autocolisão baseada em distância física ao longo do corpo da cobra
        e distância euclidiana a segmentos, independente de velocidade ou FPS.
        """
        if self.invincible_powerup_timer > 0.0 or self.invulnerable_safety_timer > 0.0:
            return False

        # Proteção essencial: a cobra não pode colidir consigo mesma antes de comer
        # donuts suficientes para fazer uma volta de 180 graus (mínimo de 2 donuts)
        if self.stats["donuts_eaten"] < 2 or self.current_length < 230.0:
            return False

        if len(self.points) < 16 or self.current_length < DISTANCIA_SEGURA_AUTOCOLISAO * 1.5:
            return False

        # Percorre o corpo de trás para frente (da cauda em direção à cabeça)
        # Ignora os segmentos cuja distância acumulada até a cabeça seja < DISTANCIA_SEGURA_AUTOCOLISAO
        accum_dist = 0.0
        n = len(self.points)
        for i in range(n - 1, 0, -1):
            seg_len = self.lengths[i]
            accum_dist += seg_len
            if accum_dist > DISTANCIA_SEGURA_AUTOCOLISAO:
                p1 = self.points[i - 1]
                p2 = self.points[i]
                # Distância do ponto (hx, hy) ao segmento de reta p1-p2
                d = self._dist_point_to_segment((hx, hy), p1, p2)
                if d < 14.0:
                    return True
        return False

    @staticmethod
    def _dist_point_to_segment(p: Tuple[int, int], a: List[int], b: List[int]) -> float:
        px, py = p
        ax, ay = a
        bx, by = b
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = ax + t * dx
        proj_y = ay + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    # -------------------------------------------------------------------------
    # ATUALIZAÇÃO DO FRAME DO JOGO (COM DELTA TIME dt)
    # -------------------------------------------------------------------------
    def update(self, raw_head: Optional[Tuple[int, int]], dt: Optional[float] = None) -> GameStateEnum:
        """
        Atualiza o estado do jogo baseado em tempo delta (dt).
        raw_head: coordenadas (x, y) do indicador detectado ou None se não detectado.
        """
        now = time.monotonic()
        if dt is None:
            dt = max(0.001, min(0.1, now - self.last_update_time))
        self.last_update_time = now

        # Atualiza efeitos visuais
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]
        if self.shake_timer > 0.0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
        if self.level_up_banner_timer > 0.0:
            self.level_up_banner_timer = max(0.0, self.level_up_banner_timer - dt)
        if self.cube_announcement_timer > 0.0:
            self.cube_announcement_timer = max(0.0, self.cube_announcement_timer - dt)

        # Se estiver em Game Over ou aguardando iniciais, não simula física da cobra
        if self.state in (GameStateEnum.GAME_OVER, GameStateEnum.ENTERING_INITIALS):
            return self.state

        # Gerenciamento de Presença da Mão e Estados
        if raw_head is not None:
            self.last_hand_seen_time = now
            if self.state == GameStateEnum.ATTRACT:
                # Visitante aproximou a mão: inicia partida!
                self.start_game()
            elif self.state == GameStateEnum.PAUSED_TRACKING:
                # Retomada da mão após breve perda
                self.state = GameStateEnum.PLAYING
                # Reinicialização suave da cabeça sem quebrar o corpo
                rx, ry = raw_head
                if self.points:
                    px, py = self.points[-1]
                    d_resume = math.hypot(rx - px, ry - py)
                    if d_resume > LIMIAR_SALTO_TELEPORTE:
                        # Reapareceu distante: translada o corpo inteiro para a nova posição mantendo integridade
                        dx = rx - px
                        dy = ry - py
                        for pt in self.points:
                            pt[0] += int(round(dx))
                            pt[1] += int(round(dy))
                self.smooth_head = [float(rx), float(ry)]
        else:
            # Mão ausente: simulação de movimento pausada
            tempo_sem_mao = now - self.last_hand_seen_time
            if self.state == GameStateEnum.PLAYING:
                if tempo_sem_mao > TEMPO_OCIOSO_ATTRACT:
                    self.state = GameStateEnum.ATTRACT
                elif tempo_sem_mao > TEMPO_TOLERANCIA_PERDA_MAO:
                    self.state = GameStateEnum.PAUSED_TRACKING
            elif self.state == GameStateEnum.PAUSED_TRACKING:
                if tempo_sem_mao > TEMPO_OCIOSO_ATTRACT:
                    self.state = GameStateEnum.ATTRACT

            # Retorna imediatamente sem processar movimento da cabeça
            return self.state

        if self.state != GameStateEnum.PLAYING:
            return self.state

        # Atualiza tempo de sobrevivência
        self.stats["survival_time"] += dt

        # Atualiza temporizadores de power-ups
        if self.invincible_powerup_timer > 0.0:
            self.invincible_powerup_timer = max(0.0, self.invincible_powerup_timer - dt)
        if self.invulnerable_safety_timer > 0.0:
            self.invulnerable_safety_timer = max(0.0, self.invulnerable_safety_timer - dt)
        if self.is_golden_donut:
            self.golden_donut_timer -= dt
            if self.golden_donut_timer <= 0.0:
                self.is_golden_donut = False
        if self.ghost_speed_boost_timer > 0.0:
            self.ghost_speed_boost_timer = max(0.0, self.ghost_speed_boost_timer - dt)
        if self.combo_tight_timer > 0.0:
            self.combo_tight_timer = max(0.0, self.combo_tight_timer - dt)

        # Atualização da barra de Combo (congela se efeito do cubo estiver ativo)
        if self.combo_frozen_timer > 0.0:
            self.combo_frozen_timer = max(0.0, self.combo_frozen_timer - dt)
        else:
            if self.combo_time_remaining > 0.0:
                self.combo_time_remaining = max(0.0, self.combo_time_remaining - dt)
                if self.combo_time_remaining <= 0.0:
                    self.combo_count = 0
                    self.combo_multiplier = 1

        # ---------------------------------------------------------------------
        # MOVIMENTAÇÃO DA CABEÇA E RASTRO DA COBRA
        # ---------------------------------------------------------------------
        rx, ry = raw_head
        if self.smooth_head is None or not self.points:
            self.smooth_head = [float(rx), float(ry)]
            cx, cy = int(rx), int(ry)
            self.points = [[cx, cy]]
            self.lengths = [0.0]
            self.current_length = 0.0
        else:
            px, py = self.points[-1]
            dist_raw = math.hypot(rx - px, ry - py)

            if dist_raw > LIMIAR_SALTO_TELEPORTE:
                # Salto extremo / teletransporte detectado (ex: troca de mão): reancora no novo ponto
                self.smooth_head = [float(rx), float(ry)]
                cx, cy = int(rx), int(ry)
                self.points.append([cx, cy])
                self.lengths.append(0.0)
            else:
                # Filtro adaptativo ultra fluido e responsivo (acompanha o dedo sem lag e sem tremer)
                d_target = math.hypot(rx - self.smooth_head[0], ry - self.smooth_head[1])
                if d_target > 40.0:
                    tau = 0.025  # Movimento ágil: resposta instantânea sem atraso
                elif d_target > 10.0:
                    tau = 0.045  # Movimento médio: transição suave e orgânica
                else:
                    tau = 0.090  # Mão quase parada: absorve ruído do sensor MediaPipe

                alpha_smooth = 1.0 - math.exp(-dt / tau)
                self.smooth_head[0] += (rx - self.smooth_head[0]) * alpha_smooth
                self.smooth_head[1] += (ry - self.smooth_head[1]) * alpha_smooth
                cx, cy = int(round(self.smooth_head[0])), int(round(self.smooth_head[1]))

                dist = math.hypot(cx - px, cy - py)
                if dist > 3.0:
                    self.points.append([cx, cy])
                    self.lengths.append(dist)
                    self.current_length += dist

        while self.current_length > self.allowed_length and len(self.lengths) > 1 and len(self.points) > 1:
            self.current_length = max(0.0, self.current_length - self.lengths.pop(1))
            self.points.pop(0)

        # ---------------------------------------------------------------------
        # SPAWN DE ITENS ESPECIAIS
        # ---------------------------------------------------------------------
        self._attempt_spawn_special_item(now)

        # Atualiza timer do item especial na tela
        if self.special_item_type is not None:
            self.special_item_timer -= dt
            if self.special_item_timer <= 0.0:
                self.special_item_type = None

        # ---------------------------------------------------------------------
        # COLISÃO COM DONUT
        # ---------------------------------------------------------------------
        fx, fy = self.food_pos
        if math.hypot(cx - fx, cy - fy) < 48.0:
            if self.is_golden_donut:
                self.register_eat(300, "DONUT DOURADO!", (fx, fy), COLOR_GOLDEN_GLOW)
                self.is_golden_donut = False
            else:
                self.register_eat(SCORE_DONUT, "DONUT", (fx, fy), COLOR_SYNTH_PINK)
            self.allowed_length += CRESCIMENTO_DONUT
            self.stats["donuts_eaten"] += 1
            self.spawn_food()
            audio.play("donut")

        # ---------------------------------------------------------------------
        # COLISÃO COM ITEM ESPECIAL
        # ---------------------------------------------------------------------
        if self.special_item_type is not None:
            ix, iy = self.special_item_pos
            if math.hypot(cx - ix, cy - iy) < 48.0:
                item = self.special_item_type
                self.special_item_type = None

                if item == "apple":
                    self.invincible_powerup_timer = DURACAO_INVENCIBILIDADE
                    self.register_eat(SCORE_APPLE, "MACA ENCANTADA!", (ix, iy), COLOR_CYBER_GREEN)
                    self.stats["special_items_collected"] += 1
                    audio.play("powerup")
                elif item == "potion":
                    self.allowed_length = max(COMPRIMENTO_INICIAL, int(self.allowed_length * 0.55))
                    self.register_eat(SCORE_POTION, "POCAO MAGICA!", (ix, iy), COLOR_ELECTRIC_CYAN)
                    self.stats["special_items_collected"] += 1
                    audio.play("potion")
                elif item == "coin":
                    self.register_eat(SCORE_COIN, "SUPER MOEDA!", (ix, iy), COLOR_GOLDEN_GLOW)
                    self.stats["special_items_collected"] += 1
                    self.spawn_ghost()
                    audio.play("coin")
                elif item == "ring":
                    if self.has_shield:
                        # Segundo anel coletado concede pontos extras sem acumular escudo
                        self.register_eat(SCORE_RING * 2, "ANEL BÔNUS!", (ix, iy), COLOR_GOLDEN_GLOW)
                    else:
                        self.has_shield = True
                        self.register_eat(SCORE_RING, "ANEL DOURADO!", (ix, iy), COLOR_GOLDEN_GLOW)
                    self.stats["special_items_collected"] += 1
                    audio.play("ring")
                elif item == "heart":
                    if self.has_extra_life:
                        self.register_eat(SCORE_HEART * 2, "VIDA BÔNUS!", (ix, iy), COLOR_GHOST_CRIMSON)
                    else:
                        self.has_extra_life = True
                        self.register_eat(SCORE_HEART, "CORACAO PIXEL!", (ix, iy), COLOR_GHOST_CRIMSON)
                    self.stats["special_items_collected"] += 1
                    audio.play("heart")
                elif item == "cube":
                    self.apply_surprise_cube((ix, iy))

        # ---------------------------------------------------------------------
        # FANTASMA (MOVIMENTO POR dt E COLISÃO)
        # ---------------------------------------------------------------------
        if self.ghost_active:
            self.ghost_timer -= dt
            if self.ghost_timer <= 0.0:
                self.ghost_active = False
            else:
                gx, gy = self.ghost_pos
                dx = cx - gx
                dy = cy - gy
                dist_g = math.hypot(dx, dy)
                if dist_g > 1.0:
                    speed = self.ghost_speed
                    if self.ghost_speed_boost_timer > 0.0:
                        speed *= 1.5
                    # Se jogador estiver invencível, fantasma foge!
                    if self.invincible_powerup_timer > 0.0:
                        dx = -dx * 1.15
                        dy = -dy * 1.15

                    ndx = (dx / dist_g) * speed * dt
                    ndy = (dy / dist_g) * speed * dt

                    self.ghost_dir = 1 if ndx > 0 else -1
                    gx = max(float(MARGEM_SPAWN_X), min(float(self.largura - MARGEM_SPAWN_X), gx + ndx))
                    gy = max(float(MARGEM_SPAWN_Y_TOP), min(float(self.altura - MARGEM_SPAWN_Y_BOTTOM), gy + ndy))
                    self.ghost_pos = [gx, gy]

                # Colisão com fantasma
                if math.hypot(cx - gx, cy - gy) < 46.0:
                    if self.invincible_powerup_timer > 0.0:
                        self.ghost_active = False
                        self.register_eat(SCORE_GHOST_EATEN, "FANTASMA DEVORADO!", (int(gx), int(gy)), COLOR_CYBER_GREEN)
                        self.stats["ghosts_eaten"] += 1
                        audio.play("ghost_eat")
                    else:
                        saved = self.handle_fatal_collision(cause="ghost")
                        if not saved:
                            return self.state

        # ---------------------------------------------------------------------
        # AUTOCOLISÃO
        # ---------------------------------------------------------------------
        if self.check_self_collision(cx, cy):
            saved = self.handle_fatal_collision(cause="self")
            if not saved:
                return self.state

        return self.state

    def trigger_shake(self, duration: float = 0.35):
        self.shake_timer = duration

    def emit_particles(self, x: float, y: float, color: Tuple[int, int, int], count: int = 16):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
