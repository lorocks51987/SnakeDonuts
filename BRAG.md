# 🏆 BRAG DOCUMENT — SNAKEDONUTS: NEON ARCADE EDITION
### *Relatório Executivo de Engenharia, Inovação e Conquistas Técnicas*
**Evento:** Mostra de Tecnologia e Inovação — Unimar Aberta  
**Repositório Oficial:** [github.com/lorocks51987/SnakeDonuts](https://github.com/lorocks51987/SnakeDonuts)  
**Branch:** `main` | **Status:** 100% Funcional, Testado e Publicado  

---

## 🎯 1. Visão Geral da Missão

Transformar o protótipo inicial do `SnakeDonuts` em uma experiência de arcade contemporânea ("Neon Arcade"), sólida, visualmente deslumbrante e estritamente confiável para operação contínua e autônoma durante a Unimar Aberta. 

O projeto foi inteiramente refatorado e desacoplado, saindo de um script monolítico para uma arquitetura orientada a serviços modulares, coberta por 23 testes automatizados, física baseada em tempo delta monotônico, tolerância a falhas elétricas com persistência atômica e inteligência artificial biométrica via Google MediaPipe e OpenCV.

---

## 🚀 2. Principais Conquistas Técnicas e Entregas

### 🏗️ A. Arquitetura Modular Desacoplada (Clean Architecture)
A base de código foi dividida em 6 subsistemas independentes com responsabilidade única:
- **`game_config.py`**: Central de tokens da paleta Neon Arcade (Cyber Green, Electric Cyan, Synth Pink, Golden Glow, Ghost Crimson), balanceamento de pontuação, progressão de 5+ níveis e parâmetros de câmera.
- **`game_audio.py`**: Motor de efeitos sonoros procedural retrô (via `winsound.Beep`) com fila dedicada thread-safe em worker background único, eliminando micro-travamentos (stuttering) no pipeline gráfico.
- **`leaderboard_manager.py`**: Hall da Fama TOP 5 com validação estrutural de JSON, critério de desempate determinístico e gravação atômica via `tempfile` com substituição segura no SO (`os.replace`).
- **`game_state.py`**: Motor de física desacoplado da interface gráfica. Executa 100% headless, gerenciando colisão geométrica ponto-a-segmento, rastreamento da cobra por distância euclidiana, teletransporte seguro, combos exponenciais (x1 até x8) e itens especiais.
- **`game_renderer.py`**: Renderizador visual com alpha blending matricial otimizado, partículas neon, textos flutuantes com fade out, telas temáticas oficiais v2 e fallback procedural automático caso assets sejam removidos.
- **`main.py` & `stand_utils.py`**: Orquestrador com seleção inteligente de webcam, downscaling para 640x360 na inferência de rede neural (garantindo baixíssima latência) e suporte a atalhos de stand (`1` câmera, `2` fullscreen, `3` espelho, `4` restart, `5` mute).

---

### 🛡️ B. Resolução de Bugs Críticos Identificados

| ID | Problema Diagnosticado | Causa Raiz | Solução Implementada | Validação |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | Reset Incompleto entre Partidas | Temporizadores e buffs da partida anterior persistiam após reinício. | Reset explícito em `start_game()` de todos os timers (`combo_frozen_timer`, `ghost_speed_boost_timer`, `special_item_timer`, `shake_timer`, etc.). | Teste unitário dedicado cobrindo 100% dos estados. |
| **P1** | Travamento da Cobra após Salto Rápido (>90px) | Detecção de salto adotava `smooth_head`, mas mantinha cauda no ponto antigo sem anexar novo ponto, gerando ciclo infinito. | Reancoragem imediata da cabeça e injeção do novo ponto na trajetória (`dist = 0.0`), reestabelecendo fluxo contínuo. Supressão de linhas cruzando a tela. | Teste de trajetória e movimento contínuo pós-salto. |
| **P1** | Coração Pixel Encurtava Abaixo do Inicial | Expressão `min(COMPRIMENTO_INICIAL, len * 0.45)` reduzia a cobra a tamanhos minúsculos (ex: 90px). | Correção para `max(COMPRIMENTO_INICIAL, int(len * 0.45))`, garantindo pelo menos o tamanho inicial de 160px. | Testes unitários com cobras longas e curtas. |
| **P2** | Instrução de Reinício Dessincronizada | Tela anunciava "mostre a mão" em GAME_OVER, mas o jogo requeria gesto de punho fechado 2x ou tecla. | Atualização do texto do card para `"Pressione [4], [6] ou [ENTER]"` e `"(Ou feche a mao 2x na camera)"`. | Validação de renderização e correspondência funcional. |
| **P3** | Caracteres Quebrados no Ranking (`1??`, `2??`) | `cv2.putText` corrompia o byte ordinal `º`. | Padronização internacional de fliperama para `1.`, `2.`, `3.`, `4.`, `5.`. | Capturas de tela limpas e sem caracteres corrompidos. |
| **P3** | Obstrução Visual na Tela de Demonstração (Attract) | Painel central cobria o título, a cobra mascote e o donut. | Redesenho para card inferior compacto (`980x185px` a `y=505`) com carrossel dinâmico de 3 dicas a cada 3,5s. Topo 500px 100% desobstruído. | Captura oficial `assets/screenshot_title_screen.png`. |

---

### 🧪 C. Testes Automatizados e Confiabilidade Extrema

- **23 testes unitários automatizados** em [test_game_logic.py](file:///C:/dev/Opencv/SnakeDonuts/test_game_logic.py).
- Tempo total de execução: **~5 segundos** (100% de sucesso).
- **Independência Total de Diretório:** Testes passam executados dentro de `SnakeDonuts` ou descobertos a partir do repositório pai (`C:\dev\Opencv`), graças ao bootstrap em `__init__.py` e `get_asset_path()`.
- **Cobertura:**
  - Sistema de pontuação e colisão do Donut.
  - Multiplicadores de combo (x1 a x8) e expiração temporal.
  - Congelamento de combo via Cubo Surpresa.
  - Regra de ouro: Primeiro Cubo Surpresa é garantidamente positivo.
  - Absorção de colisão fatal pelo Escudo do Anel Dourado.
  - Segunda Chance do Coração Pixel e preservação do comprimento inicial.
  - Movimento do Fantasma matematicamente independente de FPS (Euler discretization).
  - Prevenção de segmento gigante e continuidade de trajetória após salto da mão.
  - Gravação atômica do Leaderboard e recuperação graciosa de JSON corrompido.
  - Desempate determinístico no Hall da Fama.
  - Bounds de segurança do Spawner (longe do HUD superior e bordas).
  - Renderização sintética de todos os 5 estados do jogo sem GUI / Webcam.
  - Fachada retrocompatível `SnakeDonutsGame`.
  - Validação de dimensões e canal alpha (4 canais RGBA) de todos os sprites.
  - Fallback procedural gracioso em caso de assets ausentes.

---

### 🎨 D. Propriedade Intelectual e Identidade Visual

- Criação de novos sprites de alta resolução com canal alfa real (`anel_dourado.png`, `coracao_pixel.png`, `cubo_surpresa.png`, `donut_dourado.png`), garantindo total segurança de direitos autorais para apresentação pública e institucional da Universidade de Marília (Unimar).
- Preservação intacta de todos os assets originais do usuário (`AnelSonic.gif`, `coracao.png`, `cuboMario.png`) na pasta `assets/`.
- Documentação transparente no `README.md` sobre a política de sprites e paleta Neon Arcade.

---

### 📦 E. Publicação e Distribuição

- Repositório Git independente inicializado em `C:\dev\Opencv\SnakeDonuts`.
- Conectado com sucesso ao GitHub: `https://github.com/lorocks51987/SnakeDonuts.git`.
- Branch padrão configurada: `main`.
- Todos os arquivos de código, assets, testes, documentação e lançador em 1 clique (`INICIAR_JOGO.bat`) commitados e sincronizados com a nuvem.
