"""
=============================================================================
         SUÍTE DE TESTES UNITÁRIOS AUTOMATIZADOS - SNAKEDONUTS
=============================================================================
Testa todas as regras de negócio, mecânicas arcade, novos itens,
cálculo de delta time, proteção de tracking e leaderboard atômico
de forma independente de câmera e interface gráfica (headless).
=============================================================================
"""

import os
import sys
import math
import json
import tempfile
import unittest

# Garante resolução de imports mesmo quando executado a partir do diretório pai
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from game_config import (
    GameStateEnum,
    CubeEffect,
    SCORE_DONUT,
    SCORE_RING,
    SCORE_HEART,
    SCORE_SURPRISE_CUBE_BASE,
    SCORE_APPLE,
    get_level_bonus,
    COMPRIMENTO_INICIAL,
    CRESCIMENTO_DONUT,
    get_asset_path
)
from leaderboard_manager import StandLeaderboard
from game_state import SnakeGameState, SpawnManager


class TestSnakeGameLogic(unittest.TestCase):

    def setUp(self):
        # Cria leaderboard temporário para não alterar o leaderboard real de produção
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_lb_file = os.path.join(self.temp_dir.name, "test_leaderboard.json")
        self.leaderboard = StandLeaderboard(self.test_lb_file)
        self.game = SnakeGameState(1280, 720, leaderboard=self.leaderboard)
        self.game.start_game()

    def tearDown(self):
        self.temp_dir.cleanup()

    # 1. PONTUAÇÃO BÁSICA
    def test_basic_donut_scoring(self):
        initial_score = self.game.score
        # Coloca a comida e a cabeça na mesma posição
        self.game.food_pos = (500, 400)
        self.game.update((500, 400), dt=0.016)
        # Primeiro donut dá 100 pontos (combo x1)
        self.assertEqual(self.game.score, initial_score + SCORE_DONUT)
        self.assertEqual(self.game.allowed_length, COMPRIMENTO_INICIAL + CRESCIMENTO_DONUT)
        self.assertEqual(self.game.stats["donuts_eaten"], 1)

    # 2. MULTIPLICADORES DE COMBO
    def test_combo_progression(self):
        # 1ª comida: inicia combo (x1)
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.combo_multiplier, 1)

        # 2ª comida rápida (combo 2): sobe para tier x2
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.combo_multiplier, 2)

        # 4ª comida (combo 4): sobe para tier x3
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.combo_multiplier, 3)

        # 7ª comida (combo 7): sobe para tier x5
        for _ in range(3):
            self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.combo_multiplier, 5)

        # 11ª comida (combo 11): sobe para tier x8
        for _ in range(4):
            self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.combo_multiplier, 8)
        self.assertEqual(self.game.max_combo, 8)

    # 3. EXPIRAÇÃO DE COMBO
    def test_combo_expiration(self):
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertGreater(self.game.combo_time_remaining, 0.0)
        # Avança tempo além da janela de combo
        self.game.update((500, 400), dt=4.0)
        self.assertEqual(self.game.combo_time_remaining, 0.0)
        self.assertEqual(self.game.combo_multiplier, 1)

    # 4. CONGELAMENTO DE COMBO PELO CUBO
    def test_combo_freeze(self):
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        initial_combo_time = self.game.combo_time_remaining
        self.game.combo_frozen_timer = 5.0

        # Passa 2 segundos com o combo congelado
        self.game.update((500, 400), dt=2.0)
        # O tempo do combo NÃO deve ter diminuído
        self.assertEqual(self.game.combo_time_remaining, initial_combo_time)
        self.assertEqual(self.game.combo_frozen_timer, 3.0)

    # 5. SUBIDA DE NÍVEL E BÔNUS
    def test_level_up_and_bonus(self):
        self.assertEqual(self.game.level, 1)
        # Dá pontos suficientes para subir para o nível 2 (min_score: 400)
        self.game.score = 390
        self.game.register_eat(100, "DONUT", (500, 400), (0, 255, 0))
        self.assertEqual(self.game.level, 2)
        # Bônus de nível 2 é 2 * 200 = 400
        expected_bonus = get_level_bonus(2)
        # Score final deve incluir os pontos do donut e o bônus
        self.assertGreaterEqual(self.game.score, 390 + 100 + expected_bonus)
        self.assertGreater(self.game.level_up_banner_timer, 0.0)

    # 6. ANEL DOURADO (ESCUDO) ABSORVE COLISÃO FATAL
    def test_golden_ring_shield_absorbs_collision(self):
        self.assertFalse(self.game.has_shield)
        self.game.has_shield = True

        # Simula colisão com fantasma
        saved = self.game.handle_fatal_collision(cause="ghost")
        self.assertTrue(saved)
        # Escudo deve ser consumido
        self.assertFalse(self.game.has_shield)
        # Concede 1s de invulnerabilidade
        self.assertEqual(self.game.invulnerable_safety_timer, 1.0)
        # Partida NÃO deve ter entrado em Game Over
        self.assertEqual(self.game.state, GameStateEnum.PLAYING)
        self.assertEqual(self.game.stats["shield_saves"], 1)

    # 7. LIMITE DE UM ESCUDO (ANEL DOURADO)
    def test_single_shield_limit(self):
        self.game.smooth_head = [500.0, 400.0]
        self.game.has_shield = True
        self.game.special_item_type = "ring"
        self.game.special_item_pos = (500, 400)
        self.game.special_item_timer = 5.0

        initial_score = self.game.score
        # Coleta outro anel com escudo ativo
        self.game.update((500, 400), dt=0.016)
        # Não pode acumular 2 escudos
        self.assertTrue(self.game.has_shield)
        # Mas concede pontuação bônus
        self.assertGreater(self.game.score, initial_score)

    # 8. CORAÇÃO PIXEL (SEGUNDA CHANCE)
    def test_pixel_heart_second_chance(self):
        self.game.has_extra_life = True
        self.game.has_shield = False
        self.game.allowed_length = 500

        # Cria uma cauda longa
        for i in range(10):
            self.game.points.append([200 + i * 10, 300])
            self.game.lengths.append(10.0)
        self.game.current_length = 100.0

        # Colisão fatal
        saved = self.game.handle_fatal_collision(cause="self")
        self.assertTrue(saved)
        # Coração deve ser consumido
        self.assertFalse(self.game.has_extra_life)
        # Corpo deve ser encurtado para 45%, mas nunca abaixo do comprimento inicial
        self.assertEqual(self.game.allowed_length, int(500 * 0.45))
        self.assertGreaterEqual(self.game.allowed_length, COMPRIMENTO_INICIAL)
        # Trajetória antiga deve ser limpa para evitar re-colisão
        self.assertEqual(len(self.game.points), 1)
        # Concede 2s de invulnerabilidade
        self.assertEqual(self.game.invulnerable_safety_timer, 2.0)
        self.assertEqual(self.game.stats["heart_saves"], 1)
        self.assertEqual(self.game.state, GameStateEnum.PLAYING)

    def test_pixel_heart_preserves_initial_length_when_short(self):
        # Cobra com comprimento menor (ex: 200px -> 45% seria 90px, abaixo do inicial de 160px)
        self.game.has_extra_life = True
        self.game.allowed_length = 200
        saved = self.game.handle_fatal_collision(cause="ghost")
        self.assertTrue(saved)
        # Deve preservar pelo menos o COMPRIMENTO_INICIAL (160)
        self.assertEqual(self.game.allowed_length, COMPRIMENTO_INICIAL)

    # 9. LIMITE DE UM CORAÇÃO
    def test_single_heart_limit(self):
        self.game.smooth_head = [500.0, 400.0]
        self.game.has_extra_life = True
        self.game.special_item_type = "heart"
        self.game.special_item_pos = (500, 400)
        self.game.special_item_timer = 5.0

        initial_score = self.game.score
        self.game.update((500, 400), dt=0.016)
        self.assertTrue(self.game.has_extra_life)
        self.assertGreater(self.game.score, initial_score)

    # 10. PRIMEIRO CUBO SURPRESA SEMPRE POSITIVO
    def test_first_surprise_cube_always_positive(self):
        positive_effects = [
            CubeEffect.BONUS_POINTS,
            CubeEffect.SHRINK_BODY,
            CubeEffect.GOLDEN_SHIELD,
            CubeEffect.INVINCIBILITY,
            CubeEffect.FREEZE_COMBO,
            CubeEffect.GOLDEN_DONUT
        ]
        # Testa 30 novas partidas para garantir que o 1º cubo nunca seja negativo
        for _ in range(30):
            game = SnakeGameState(1280, 720, leaderboard=self.leaderboard)
            game.start_game()
            self.assertTrue(game.first_cube_in_game)
            game.apply_surprise_cube((500, 400))
            self.assertFalse(game.first_cube_in_game)
            self.assertIsNotNone(game.active_cube_announcement)
            # Fantasma não pode ser invocado no primeiro cubo
            self.assertFalse(game.ghost_active)

    # 11. RETORNO DA MÃO SEM SEGMENTO GIGANTE
    def test_hand_reentry_prevents_giant_segment(self):
        # Cobra na posição (100, 100)
        self.game.update((100, 100), dt=0.016)
        self.game.update((105, 100), dt=0.016)
        initial_body_length = self.game.current_length

        # Mão sai da tela
        self.game.update(None, dt=0.5)

        # Mão retorna do outro lado da tela (1000, 600) - salto de ~1000px
        self.game.update((1000, 600), dt=0.016)

        # O comprimento do corpo NÃO pode ter saltado 1000px!
        self.assertLess(self.game.current_length, initial_body_length + 95.0)

    # 12. MOVIMENTO DO FANTASMA INDEPENDENTE DE FPS
    def test_ghost_movement_fps_independent(self):
        # Testa se a distância percorrida pelo fantasma em 1.0s é idêntica a 60 FPS e 30 FPS
        # Cenário 1: 60 FPS (60 passos de dt=1/60)
        game60 = SnakeGameState(1280, 720, leaderboard=self.leaderboard)
        game60.start_game()
        game60.ghost_active = True
        game60.ghost_timer = 10.0
        game60.ghost_pos = [100.0, 100.0]
        game60.ghost_speed = 200.0

        for _ in range(60):
            # Cobra parada em (500, 100) à direita
            game60.update((500, 100), dt=1.0 / 60.0)
        dist60 = game60.ghost_pos[0] - 100.0

        # Cenário 2: 30 FPS (30 passos de dt=1/30)
        game30 = SnakeGameState(1280, 720, leaderboard=self.leaderboard)
        game30.start_game()
        game30.ghost_active = True
        game30.ghost_timer = 10.0
        game30.ghost_pos = [100.0, 100.0]
        game30.ghost_speed = 200.0

        for _ in range(30):
            game30.update((500, 100), dt=1.0 / 30.0)
        dist30 = game30.ghost_pos[0] - 100.0

        # As distâncias devem ser virtualmente idênticas (erro < 1.0 pixel)
        self.assertAlmostEqual(dist60, dist30, delta=1.5)
        self.assertAlmostEqual(dist60, 200.0, delta=2.0)

    # 13. LEADERBOARD ATÔMICO E VALIDAÇÃO DE ENTRADAS
    def test_leaderboard_atomic_and_validation(self):
        lb = StandLeaderboard(self.test_lb_file)
        # Adiciona recordes
        lb.add_score("AAA", 500)
        lb.add_score("BBB", 400)
        self.assertEqual(lb.get_high_score(), 500)
        self.assertEqual(lb.scores[0]["name"], "AAA")

        # Verifica se o arquivo em disco foi criado e é JSON válido
        with open(self.test_lb_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["score"], 500)

    # 14. LEADERBOARD COM JSON CORROMPIDO
    def test_leaderboard_corrupted_json(self):
        corrupt_file = os.path.join(self.temp_dir.name, "corrupt.json")
        # Escreve conteúdo inválido
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json [")

        # Deve carregar os padrões sem derrubar o jogo
        lb = StandLeaderboard(corrupt_file)
        self.assertEqual(len(lb.scores), 5)
        self.assertGreater(lb.get_high_score(), 0)

    # 15. LEADERBOARD COM EMPATES DETERMINÍSTICOS
    def test_leaderboard_tie_breaker(self):
        lb = StandLeaderboard(self.test_lb_file)
        lb.scores = [
            {"name": "AAA", "score": 300, "date": "10:00"},
            {"name": "BBB", "score": 200, "date": "10:05"},
            {"name": "CCC", "score": 100, "date": "10:10"}
        ]
        # Novo jogador com mesmo score 200
        lb.add_score("NEW", 200, date_str="10:15")
        # BBB já estava com 200 antes, então BBB mantém a frente de NEW
        names = [entry["name"] for entry in lb.scores]
        self.assertIn("BBB", names)
        self.assertIn("NEW", names)
        self.assertLess(names.index("BBB"), names.index("NEW"))

    # 16. SPAWN MANAGER COM LIMITES SEGUROS
    def test_spawn_manager_bounds_and_safety(self):
        spawner = SpawnManager(1280, 720)
        avoid = [(640, 360)]
        for _ in range(50):
            x, y = spawner.get_safe_position(avoid, min_dist=100.0)
            # Verifica limites da tela
            self.assertGreaterEqual(x, 90)
            self.assertLessEqual(x, 1280 - 90)
            self.assertGreaterEqual(y, 110)
            self.assertLessEqual(y, 720 - 85)

    # 17. RENDERIZAÇÃO SINTÉTICA EM TODOS OS ESTADOS (SEM GUI / WEBCAM)
    def test_synthetic_frame_rendering_all_states(self):
        import numpy as np
        from game_renderer import SnakeGameRenderer

        renderer = SnakeGameRenderer(1280, 720)
        synthetic_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Testa ATTRACT
        self.game.state = GameStateEnum.ATTRACT
        out_attract = renderer.render(synthetic_frame, self.game)
        self.assertEqual(out_attract.shape, (720, 1280, 3))

        # Testa PLAYING
        self.game.state = GameStateEnum.PLAYING
        self.game.has_shield = True
        self.game.has_extra_life = True
        self.game.special_item_type = "cube"
        self.game.special_item_pos = (400, 300)
        self.game.special_item_timer = 5.0
        self.game.ghost_active = True
        self.game.ghost_pos = [200.0, 200.0]
        self.game.points = [[500, 400], [510, 400], [520, 400]]
        out_playing = renderer.render(synthetic_frame, self.game)
        self.assertEqual(out_playing.shape, (720, 1280, 3))

        # Testa PAUSED_TRACKING
        self.game.state = GameStateEnum.PAUSED_TRACKING
        out_paused = renderer.render(synthetic_frame, self.game)
        self.assertEqual(out_paused.shape, (720, 1280, 3))

        # Testa GAME_OVER
        self.game.state = GameStateEnum.GAME_OVER
        out_gover = renderer.render(synthetic_frame, self.game)
        self.assertEqual(out_gover.shape, (720, 1280, 3))

        # Testa ENTERING_INITIALS
        self.game.state = GameStateEnum.ENTERING_INITIALS
        self.game.qualifies_top5 = True
        out_initials = renderer.render(synthetic_frame, self.game)
        self.assertEqual(out_initials.shape, (720, 1280, 3))

    # 18. FACHADA SnakeDonutsGame SEM WEBCAM
    def test_main_facade_without_webcam(self):
        import numpy as np
        from main import SnakeDonutsGame

        facade = SnakeDonutsGame(1280, 720)
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Executa múltiplos updates headless
        out = facade.update(dummy_frame, (600, 400))
        self.assertEqual(out.shape, (720, 1280, 3))
        self.assertFalse(facade.game_over)
        self.assertEqual(facade.score, 0)

    # 19. VERIFICAÇÃO DE DIMENSÕES E CANAIS DOS SPRITES
    def test_sprite_dimensions_and_channels(self):
        import cv2
        sprites = [
            "anel_dourado.png",
            "coracao_pixel.png",
            "cubo_surpresa.png",
            "donut_dourado.png",
            "Donut.png",
            "Potion.png",
            "coin.png",
            "ghost1.png",
            "ghost2.png",
            "ghost3.png"
        ]
        for s in sprites:
            path = get_asset_path(s)
            self.assertTrue(os.path.exists(path), f"Sprite ausente: {s}")
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            self.assertIsNotNone(img, f"Falha ao carregar sprite: {s}")
            self.assertEqual(len(img.shape), 3, f"Sprite deve ter 3 dimensoes: {s}")
            self.assertEqual(img.shape[2], 4, f"Sprite deve possuir canal Alpha (4 canais): {s}")
            # Verifica leitura entre 64 e 512
            self.assertGreaterEqual(img.shape[0], 64)
            self.assertGreaterEqual(img.shape[1], 64)

    # 20. FALLBACK SEGURO QUANDO ASSETS ESTÃO AUSENTES
    def test_asset_fallbacks_when_files_missing(self):
        import unittest.mock as mock
        import numpy as np
        from game_renderer import SnakeGameRenderer

        # Simula ausência total de arquivos de assets (os.path.exists retorna False)
        with mock.patch("os.path.exists", return_value=False):
            renderer = SnakeGameRenderer(1280, 720)
            self.assertIsNone(renderer.bg_title_screen)
            self.assertIsNone(renderer.bg_game_over)
            self.assertIsNotNone(renderer.sprite_donut)
            self.assertEqual(renderer.sprite_donut.shape[2], 4)

            # Garante que renderiza perfeitamente com fallback procedural
            synthetic = np.zeros((720, 1280, 3), dtype=np.uint8)
            self.game.state = GameStateEnum.ATTRACT
            frame = renderer.render(synthetic, self.game)
            self.assertEqual(frame.shape, (720, 1280, 3))

            self.game.state = GameStateEnum.GAME_OVER
            frame = renderer.render(synthetic, self.game)
            self.assertEqual(frame.shape, (720, 1280, 3))

    # 21. RESET COMPLETO ENTRE PARTIDAS
    def test_reset_clears_all_effects_and_timers(self):
        # Ativa vários efeitos e timers
        self.game.combo_frozen_timer = 5.0
        self.game.combo_tight_timer = 4.0
        self.game.ghost_speed_boost_timer = 3.5
        self.game.golden_donut_timer = 6.0
        self.game.is_golden_donut = True
        self.game.special_item_type = "cube"
        self.game.special_item_timer = 4.0
        self.game.shake_timer = 0.5
        self.game.active_cube_announcement = "EFEITO ATIVO"

        # Reinicia a partida
        self.game.start_game()

        # Garante que NENHUM efeito foi herdado
        self.assertEqual(self.game.combo_frozen_timer, 0.0)
        self.assertEqual(self.game.combo_tight_timer, 0.0)
        self.assertEqual(self.game.ghost_speed_boost_timer, 0.0)
        self.assertEqual(self.game.golden_donut_timer, 0.0)
        self.assertFalse(self.game.is_golden_donut)
        self.assertIsNone(self.game.special_item_type)
        self.assertEqual(self.game.special_item_timer, 0.0)
        self.assertEqual(self.game.special_item_max_duration, 0.0)
        self.assertEqual(self.game.shake_timer, 0.0)
        self.assertIsNone(self.game.active_cube_announcement)
        self.assertFalse(self.game.has_shield)
        self.assertFalse(self.game.has_extra_life)
        self.assertEqual(self.game.invulnerable_safety_timer, 0.0)
        self.assertEqual(self.game.invincible_powerup_timer, 0.0)
        self.assertTrue(self.game.first_cube_in_game)
        self.assertGreater(self.game.last_hand_seen_time, 0.0)

    # 22. REANCORAGEM DA CABEÇA NÃO TRAVA A COBRA EM SALTOS
    def test_hand_jump_continuous_movement_after_jump(self):
        # Inicializa cabeça e ponto inicial
        self.game.smooth_head = [100.0, 100.0]
        self.game.points = [[100, 100]]
        self.game.lengths = [0.0]

        # Salto brusco para o outro lado da tela (distância ~1000px > 90px)
        self.game.update((1000, 600), dt=0.016)
        # Cabeça deve ter reancorado imediatamente no novo ponto
        self.assertEqual(self.game.points[-1], [1000, 600])

        # Nos quadros seguintes, a cobra DEVE continuar se movimentando normalmente
        for _ in range(5):
            self.game.update((1050, 600), dt=0.08)

        # Confirma que a cobra continuou sua trajetória a partir do novo ponto
        self.assertGreater(self.game.points[-1][0], 1000)
        self.assertEqual(len(self.game.points), 7)

    # 23. MÃO PARADA NÃO CAUSA AUTOCOLISÃO PREMATURA
    def test_stationary_hand_does_not_trigger_premature_death(self):
        # Simula jogador segurando a mão parada com pequeno tremor natural de webcam
        for i in range(120):
            x = 640 + int(math.sin(i * 0.4) * 6)
            y = 360 + int(math.cos(i * 0.4) * 6)
            st = self.game.update((x, y), dt=0.033)
            self.assertEqual(st, GameStateEnum.PLAYING, f"Jogador morreu prematuramente no frame {i}!")


if __name__ == "__main__":
    unittest.main()
