"""
=============================================================================
             CONFIGURAÇÕES E BALANCEAMENTO - SNAKEDONUTS
=============================================================================
Central de constantes, balanceamento de gameplay, paleta oficial Neon Arcade
e definições dos estados do jogo para o stand na Unimar Aberta.
=============================================================================
"""

import os
from enum import Enum

# =============================================================================
# DIRETÓRIOS E ASSETS
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

def get_asset_path(filename):
    """Localiza asset na pasta assets/ ou na raiz como fallback."""
    p_assets = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(p_assets):
        return p_assets
    p_root = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(p_root):
        return p_root
    return p_assets

# =============================================================================
# PALETA OFICIAL NEON ARCADE (Cores em BGR para OpenCV)
# =============================================================================
# Cyber Green: #00FF88 -> (136, 255, 0)
COLOR_CYBER_GREEN = (136, 255, 0)
# Electric Cyan: #00E5FF -> (255, 229, 0)
COLOR_ELECTRIC_CYAN = (255, 229, 0)
# Synth Pink: #FF007F -> (127, 0, 255)
COLOR_SYNTH_PINK = (127, 0, 255)
# Golden Glow: #FFD700 -> (0, 215, 255)
COLOR_GOLDEN_GLOW = (0, 215, 255)
# Ghost Crimson: #FF3232 -> (50, 50, 255)
COLOR_GHOST_CRIMSON = (50, 50, 255)
# Dark Void: #0A0D14 -> (20, 13, 10)
COLOR_DARK_VOID = (20, 13, 10)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (180, 185, 200)

# =============================================================================
# RESOLUÇÃO E CÂMERA
# =============================================================================
LARGURA_PADRAO = 1280
ALTURA_PADRAO = 720
DETECTION_CON = 0.80
MAX_HANDS = 1

# Margens da área de spawn e movimentação
MARGEM_SPAWN_X = 90
MARGEM_SPAWN_Y_TOP = 110   # Abaixo do HUD
MARGEM_SPAWN_Y_BOTTOM = 85 # Acima da barra de status

# =============================================================================
# PONTUAÇÃO BASE
# =============================================================================
SCORE_DONUT = 100
SCORE_APPLE = 150
SCORE_POTION = 100
SCORE_COIN = 250
SCORE_RING = 150
SCORE_HEART = 200
SCORE_SURPRISE_CUBE_BASE = 100
SCORE_GHOST_EATEN = 500

def get_level_bonus(level: int) -> int:
    """Bônus concedido ao subir de nível: nível * 200."""
    return level * 200

# Multiplicadores de Combo
COMBO_TIERS = (
    (1, 1),
    (2, 2),
    (4, 3),
    (7, 5),
    (11, 8)
)
COMBO_WINDOW_BASE = 2.8 # segundos

# =============================================================================
# TEMPOS E COOLDOWNS (em segundos, time.monotonic)
# =============================================================================
DURACAO_MACA = 8.0
DURACAO_INVENCIBILIDADE = 6.0
DURACAO_POTION = 7.0
DURACAO_COIN = 6.0
DURACAO_RING = 10.0
DURACAO_HEART = 8.0
DURACAO_CUBE = 8.0
DURACAO_GHOST = 7.0

# Invulnerabilidades
INVULNERABILIDADE_POS_ESCUDO = 1.0  # 1s após anel salvar
INVULNERABILIDADE_SEGUNDA_CHANCE = 2.0 # 2s após coração salvar

# Temporizadores de Nível e Telas
DURACAO_BANNER_LEVEL_UP = 0.85 # segundos para exibição do banner de nível
TEMPO_TOLERANCIA_PERDA_MAO = 1.2 # segundos de tolerância antes de pausar
TEMPO_OCIOSO_ATTRACT = 3.5 # segundos sem mão antes de entrar em modo apresentação

# =============================================================================
# COBRA E FÍSICA
# =============================================================================
COMPRIMENTO_INICIAL = 160
CRESCIMENTO_DONUT = 35
DISTANCIA_SEGURA_AUTOCOLISAO = 140.0 # distância física segura ao longo da espinha (evita colisão no próprio pescoço)
VELOCIDADE_GHOST_BASE = 160.0 # pixels por segundo (independente de FPS)

# =============================================================================
# DEFINIÇÃO DOS NÍVEIS
# =============================================================================
LEVEL_DEFINITIONS = {
    1: {
        "nome": "AQUECIMENTO",
        "desc": "Donuts normais. Ritmo acessivel!",
        "min_score": 0,
        "combo_window": 3.0,
        "ghost_speed": 160.0,
        "unlocked_items": []
    },
    2: {
        "nome": "CORRERIA ACUCARADA",
        "desc": "Maca e Moeda liberadas! Combos em destaque.",
        "min_score": 400,
        "combo_window": 2.8,
        "ghost_speed": 190.0,
        "unlocked_items": ["apple", "coin"]
    },
    3: {
        "nome": "CACA FANTASMA",
        "desc": "Pocao e Anel Dourado liberados! Fantasmas rondam.",
        "min_score": 1000,
        "combo_window": 2.6,
        "ghost_speed": 220.0,
        "unlocked_items": ["apple", "coin", "potion", "ring"]
    },
    4: {
        "nome": "CAIXA DE SURPRESAS",
        "desc": "Cubo Surpresa liberado! Janela de combo mais rapida.",
        "min_score": 1800,
        "combo_window": 2.4,
        "ghost_speed": 250.0,
        "unlocked_items": ["apple", "coin", "potion", "ring", "cube"]
    },
    5: {
        "nome": "SEGUNDA CHANCE",
        "desc": "Coracao Pixel raro liberado! Fantasmas implacaveis.",
        "min_score": 2800,
        "combo_window": 2.2,
        "ghost_speed": 280.0,
        "unlocked_items": ["apple", "coin", "potion", "ring", "cube", "heart"]
    }
}

# =============================================================================
# EFEITOS DO CUBO SURPRESA
# =============================================================================
class CubeEffect(Enum):
    BONUS_POINTS = "BONUS_POINTS"          # +300 pontos
    SHRINK_BODY = "SHRINK_BODY"            # Redução de 35% do corpo
    GOLDEN_SHIELD = "GOLDEN_SHIELD"        # Ativa escudo do Anel Dourado
    INVINCIBILITY = "INVINCIBILITY"        # 5 segundos de invencibilidade
    FREEZE_COMBO = "FREEZE_COMBO"          # Combo congelado por 5s
    GOLDEN_DONUT = "GOLDEN_DONUT"          # Transforma donut atual em dourado
    SPAWN_GHOST = "SPAWN_GHOST"            # Invoca fantasma imediatamente (risco)
    SPEED_GHOST = "SPEED_GHOST"            # Aumenta temporariamente vel. do fantasma (risco)
    TIGHT_COMBO = "TIGHT_COMBO"            # Reduz janela de combo por alguns segundos (risco)

# Probabilidades de sorteio do Cubo Surpresa (pesos)
# Efeitos positivos (total de peso ~85%)
CUBE_POSITIVE_WEIGHTS = {
    CubeEffect.BONUS_POINTS: 25,
    CubeEffect.SHRINK_BODY: 15,
    CubeEffect.GOLDEN_SHIELD: 15,
    CubeEffect.INVINCIBILITY: 10,
    CubeEffect.FREEZE_COMBO: 10,
    CubeEffect.GOLDEN_DONUT: 10,
}

# Efeitos de risco (total de peso ~15%)
CUBE_RISK_WEIGHTS = {
    CubeEffect.SPAWN_GHOST: 8,
    CubeEffect.SPEED_GHOST: 4,
    CubeEffect.TIGHT_COMBO: 3,
}

# =============================================================================
# ESTADOS FORMAIS DO JOGO
# =============================================================================
class GameStateEnum(Enum):
    ATTRACT = "ATTRACT"                      # Modo demonstração com telas arcade
    PLAYING = "PLAYING"                      # Partida ativa e normal
    PAUSED_TRACKING = "PAUSED_TRACKING"      # Mão perdida momentaneamente (pausa justa)
    GAME_OVER = "GAME_OVER"                  # Tela de morte / recorde
    ENTERING_INITIALS = "ENTERING_INITIALS"  # Entrada das 3 iniciais para TOP 5
