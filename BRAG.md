# 🏆 BRAG DOCUMENT — SNAKEDONUTS: NEON ARCADE EDITION
### *Relatório Técnico de Engenharia, Inovação e Entregas*
**Evento:** Mostra de Tecnologia e Inovação — Unimar Aberta  
**Repositório Oficial:** [github.com/lorocks51987/SnakeDonuts](https://github.com/lorocks51987/SnakeDonuts)  
**Branch:** `main` | **Status:** Testado e Validado via Suíte Automatizada (Pendente Validação Presencial no Stand)  

---

## 🎯 1. Visão Geral da Missão

Transformar o protótipo inicial do `SnakeDonuts` em uma experiência de arcade contemporânea ("Neon Arcade"), sólida, visualmente atraente e confiável para operação no stand da Unimar Aberta. 

O projeto foi inteiramente refatorado e desacoplado, migrando de um script monolítico para uma arquitetura orientada a módulos com responsabilidade única, coberta por 23 testes automatizados, física com delta time monotônico, gravação atômica tolerante a desligamentos abruptos e detecção de landmarks articulares da mão via visão computacional (Google MediaPipe e OpenCV).

---

## 🚀 2. Principais Conquistas Técnicas e Entregas

### 🏗️ A. Arquitetura Modular Desacoplada (Clean Architecture)
A base de código foi dividida em 6 subsistemas independentes:
- **[`game_config.py`](game_config.py)**: Central de tokens da paleta Neon Arcade (*Cyber Green*, *Electric Cyan*, *Synth Pink*, *Golden Glow*, *Ghost Crimson*), balanceamento de pontuação, progressão de 5+ níveis e parâmetros de câmera.
- **[`game_audio.py`](game_audio.py)**: Motor de efeitos sonoros procedural retrô (via `winsound.Beep`) com fila dedicada thread-safe em worker background único, reduzindo significativamente o risco de micro-travamentos (*stuttering*) no pipeline gráfico.
- **[`leaderboard_manager.py`](leaderboard_manager.py)**: Hall da Fama TOP 5 com validação estrutural de JSON, critério de desempate determinístico e gravação atômica via `tempfile` com substituição segura no SO (`os.replace`).
- **[`game_state.py`](game_state.py)**: Motor de física desacoplado da interface gráfica. Executa de forma autônoma (*headless*), gerenciando colisão geométrica ponto-a-segmento, rastreamento da cobra por distância euclidiana, teletransporte seguro, combos progressivos (x1 até x8) e novos itens especiais.
- **[`game_renderer.py`](game_renderer.py)**: Renderizador visual com alpha blending matricial otimizado, partículas neon, textos flutuantes com fade out, telas temáticas v2 e fallback procedural automático caso arquivos sejam ausentes ou corrompidos.
- **[`main.py`](main.py) & [`stand_utils.py`](stand_utils.py)**: Orquestrador com seleção automática de webcam, downscaling para 640x360 na inferência de rede neural (para menor latência) e suporte a atalhos de stand (`1` câmera, `2` fullscreen, `3` espelho, `4` restart, `5` mute).

---

### 🛡️ B. Resolução de Problemas Críticos Identificados

| ID | Problema Diagnosticado | Causa Raiz | Solução Implementada | Validação |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | Reset Incompleto entre Partidas | Temporizadores e buffs da partida anterior persistiam após reinício. | Reset explícito em `start_game()` de todos os timers (`combo_frozen_timer`, `ghost_speed_boost_timer`, `special_item_timer`, `shake_timer`, etc.). | Teste unitário dedicado cobrindo 100% dos estados. |
| **P1** | Travamento da Cobra após Salto Rápido (>90px) | Detecção de salto adotava `smooth_head`, mas mantinha cauda no ponto antigo sem anexar novo ponto, gerando ciclo infinito. | Reancoragem imediata da cabeça e injeção do novo ponto na trajetória (`dist = 0.0`), reestabelecendo fluxo contínuo. Supressão de linhas cruzando a tela. | Teste de trajetória e movimento contínuo pós-salto. |
| **P1** | Coração Pixel Encurtava Abaixo do Inicial | Expressão `min(COMPRIMENTO_INICIAL, len * 0.45)` reduzia a cobra a tamanhos minúsculos (ex: 90px). | Correção para `max(COMPRIMENTO_INICIAL, int(len * 0.45))`, garantindo pelo menos o tamanho inicial de 160px. | Testes unitários com cobras longas e curtas. |
| **P2** | Instrução de Reinício Dessincronizada | Tela anunciava "mostre a mão" em GAME_OVER, mas o jogo requeria gesto de punho fechado 2x ou tecla. | Atualização do texto do card para `"Pressione [4], [6] ou [ENTER]"` e `"(Ou feche a mao 2x na camera)"`. | Validação de renderização e correspondência funcional. |
| **P3** | Caracteres Quebrados no Ranking (`1??`, `2??`) | `cv2.putText` corrompia o byte ordinal `º`. | Padronização internacional de fliperama para `1.`, `2.`, `3.`, `4.`, `5.`. | Capturas de tela limpas e sem caracteres corrompidos. |
| **P3** | Obstrução Visual na Tela de Demonstração (Attract) | Painel central cobria o título, a cobra mascote e o donut. | Redesenho para card inferior compacto (`980x185px` a `y=505`) com carrossel dinâmico de 3 dicas a cada 3,5s. Topo 500px 100% desobstruído. | Captura oficial [`assets/screenshot_title_screen.png`](assets/screenshot_title_screen.png). |

---

### 🧪 C. Testes Automatizados e Resiliência do Sistema

- **23 testes unitários automatizados** em [`test_game_logic.py`](test_game_logic.py).
- Tempo total de execução: **~5 segundos** (100% de aprovação).
- **Independência de Diretório:** Testes passam tanto dentro de `SnakeDonuts` quanto descobertos a partir do repositório pai (`C:\dev\Opencv`), graças ao bootstrap em [`__init__.py`](__init__.py) e `get_asset_path()`.
- **Cobertura de Regras de Negócio:**
  - Sistema de pontuação e colisão do Donut.
  - Multiplicadores de combo (x1 a x8) e expiração temporal.
  - Congelamento de combo via Cubo Surpresa.
  - Regra de ouro: Primeiro Cubo Surpresa é garantidamente positivo.
  - Absorção de colisão fatal pelo Escudo do Anel Dourado.
  - Segunda Chance do Coração Pixel e preservação do comprimento inicial.
  - Movimento do Fantasma matematicamente independente de FPS (discretização de Euler).
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

- Criação de novos sprites pixel/arcade otimizados (96×96) com canal alfa real RGBA (`anel_dourado.png`, `coracao_pixel.png`, `cubo_surpresa.png`, `donut_dourado.png`), resguardando a Universidade de Marília (Unimar) contra marcas e propriedades intelectuais de terceiros (Sonic, Mario).
- Preservação intacta de todos os assets originais do usuário (`AnelSonic.gif`, `coracao.png`, `cuboMario.png`) na pasta `assets/`.
- Documentação transparente no [`README.md`](README.md) sobre a política de sprites e paleta Neon Arcade.

---

### 📦 E. Publicação e Distribuição

- Repositório Git independente inicializado e sincronizado no GitHub: [`https://github.com/lorocks51987/SnakeDonuts.git`](https://github.com/lorocks51987/SnakeDonuts.git).
- Branch padrão configurada: `main`.
- Todos os arquivos de código, assets, testes, documentação e lançador em 1 clique ([`INICIAR_JOGO.bat`](INICIAR_JOGO.bat)) versionados na nuvem.

---

## 🎬 3. Pacote Promocional e Material do Stand (Execução do Brag)

Em complemento ao relatório técnico, foram desenvolvidos e integrados ao repositório todos os componentes audiovisuais e promocionais:

1. **Demonstração em Vídeo e Animação de Gameplay:**
   - **GIF Animado:** [`assets/gameplay_demo.gif`](assets/gameplay_demo.gif) (incorporado diretamente no `README.md`).
   - **Vídeo em Alta Resolução:** [`assets/gameplay_demo.mp4`](assets/gameplay_demo.mp4) (gerado via simulação coreografada em 720p @ 25 FPS).
   - Demonstra a transição fluida do Attract Mode para a partida, coleta de donuts com multiplicação de combo (x1 a x3), absorção de impacto pelo Anel Dourado (Escudo), ativação do Cubo Surpresa, perseguição do fantasma vermelho e devoração sob o efeito da Maçã Encantada.

2. **Roteiro Oficial de Demonstração no Stand:**
   - Documento completo em [`ROTEIRO_STAND.md`](ROTEIRO_STAND.md): Pitch de entrada de 30 segundos, condução passo a passo do visitante, guia de atalhos do operador e respostas prontas para perguntas técnicas da banca e professores.

3. **Material Promocional e de Divulgação:**
   - Documento completo em [`MATERIAL_PROMOCIONAL.md`](MATERIAL_PROMOCIONAL.md): Textos oficiais para redes sociais (LinkedIn profissional e Instagram dinâmico), cartaz de regras rápidas para impressão ao lado do stand e notas de lançamento da edição especial de fliperama.

---

## 📋 4. Próxima Etapa Técnica

Embora os 23 testes automatizados garantam o comportamento correto da lógica e a demonstração em vídeo valide o renderizador gráfico, o ensaio presencial de 5 a 10 minutos com o operador humano em frente à webcam do stand é recomendado para calibrar a iluminação do local e a altura ideal do tripé da câmera.
