# 🐍🍩 SnakeDonuts — Neon Arcade Edition

> Jogo de visão computacional retrô em tempo real onde você controla uma cobra neon usando apenas a ponta do seu dedo indicador em frente à webcam. Desenvolvido para o stand de Análise e Desenvolvimento de Sistemas (ADS) na Unimar Aberta.

---

## 🎯 COMO FUNCIONA O CONTROLE POR VISÃO COMPUTACIONAL

1. **Rastreamento Sem Contato:** A webcam capta a mão do visitante utilizando a biblioteca MediaPipe Hands.
2. **Filtro Adaptativo de Movimento:** Um suavizador exponencial em tempo real converte as coordenadas da ponta do dedo indicador (Landmark 8) em movimento contínuo da cabeça da cobra, sem tremores nem atrasos.
3. **Pausa e Retomada Justa:** Caso o participante retire a mão por instantes, o jogo congela a simulação de forma limpa até a mão ser reposicionada, sem causar autocolisão ou mortes injustas.

---

## 🚩 AS 5 FASES E SEUS OBJETIVOS

A progressão do SnakeDonuts é baseada em **fases estruturadas com objetivos próprios**, onde a pontuação mede o desempenho e a conclusão do objetivo avança o nível:

| Fase | Nome | Objetivo | Mecânica Central & Desafio |
| :---: | :--- | :--- | :--- |
| **Fase 1** | **AQUECIMENTO** | Coletar **5 Donuts** | Aprendizado básico sem fantasmas. Ao coletar o 5º donut, surge o **Anel do Sonic** (`AnelSonic.gif`) para demonstrar o conceito de escudo. |
| **Fase 2** | **COMBO RUSH** | Alcançar **Combo x3** | Donuts surgem em posições estratégicas para construção de ritmo. Ao atingir x3, surge o **Donut Dourado** que conclui a fase. |
| **Fase 3** | **CAÇA FANTASMA** | Sobreviver **15 segundos** ao Fantasma | Fantasma perseguidor ativado. Durante a perseguição, surge a **Maçã Encantada** concedendo poder temporário para devorar o fantasma. |
| **Fase 4** | **SURPRESA** | Coletar **2 Cubos do Mario** | O 1º Cubo (`cuboMario.png`) concede benefício positivo. O 2º Cubo apresenta risco moderado. Poção e Coração surgem contextualmente. |
| **Fase 5** | **REI DO ARCADE** | Sobreviver **20s** e somar **600 pts** | Fantasma em alta velocidade com investidas sinalizadas a cada 3s. Concluir concede o Jackpot e libera o **Modo Infinito**. |

---

## 🍩 TABELA DE ITENS E POWER-UPS

| Asset Visual | Nome no Jogo | Função & Efeito | Pontuação |
| :---: | :--- | :--- | :---: |
| `Donut.png` | **DONUT** | Alimento padrão que faz a cobra crescer. | **+100 pts** |
| `donut_dourado.png` | **DONUT DOURADO** | Recompensa especial por combo ou cubo surpresa. | **+400 pts** |
| `AnelSonic.gif` | **ANEL DOURADO** | Animação em GIF que concede **Escudo Dourado** contra 1 colisão fatal. | **+50 pts** |
| `cuboMario.png` | **CUBO SURPRESA** | Caixa do Mario que sorteia poderes ou desafios contextuais. | **+100 pts** *(+ efeito)* |
| `enchanted_apple.gif` | **MAÇÃ ENCANTADA** | Animação em GIF que concede invencibilidade temporária e permite devorar fantasmas. | **+150 pts** |
| `coracao.png` | **CORAÇÃO PIXEL** | Coração do Minecraft de item raro que concede **Segunda Chance** ao colidir. | **+50 pts** |
| `Potion.png` | **POÇÃO MÁGICA** | Reduz o comprimento da cauda quando a cobra estiver muito longa. | **+50 pts** |
| `coin.png` | **SUPER MOEDA** | Item de alto valor e escolha de risco opcional. | **+250 pts** |

---

## 💯 SISTEMA DE PONTUAÇÃO

Pontuação e progressão de fase são separadas. O combo multiplica os pontos da partida, mas a fase só avança cumprindo o objetivo estipulado.

* **Donut Comum:** 100 pontos
* **Donut Dourado:** 400 pontos
* **Conclusão de Fase:** 300 pontos
* **Sobreviver à Perseguição do Fantasma:** 500 pontos
* **Devorar Fantasma (sob efeito da Maçã):** 800 pontos
* **Cubo Surpresa:** 100 pontos + efeito
* **Anel do Sonic, Coração e Poção:** 50 pontos (itens defensivos)
* **Objetivo Opcional / Super Moeda:** 250 a 500 pontos
* **Jackpot Final (Fase 5):** 1.000 pontos

---

## ⌨️ CONTROLES DO OPERADOR DO STAND

| Tecla / Gesto | Ação | Descrição |
| :---: | :--- | :--- |
| **`0`** | **Ajuda Modal** | Exibe tela translúcida com instruções rápidas do evento. |
| **`1`** | **Trocar Câmera** | Alterna entre webcams USB conectadas no computador. |
| **`2` / `TAB`** | **Tela Cheia** | Alterna modo janela / fullscreen para monitor ou telão. |
| **`3`** | **Espelhar Vídeo** | Inverte horizontalmente o feed da câmera (efeito espelho). |
| **`4`** | **Reiniciar Partida** | Reinicia imediatamente a partida do nível 1. |
| **`5`** | **Som On/Off** | Ativa ou desativa os efeitos sonoros procedurais. |
| **`6` / `ENTER`** | **Confirmar / Ação** | Inicia partida ou confirma iniciais no Hall da Fama. |
| **`ESC`** | **Sair** | Encerra o jogo e libera a webcam. |
| ✊ **Mão Fechada 2x** | **Atalho Sem Teclado** | Fechar o punho duas vezes aciona o restart da partida. |

---

## 📥 INSTALAÇÃO

### Requisitos do Sistema
* Python 3.9, 3.10, 3.11 ou 3.12
* Webcam USB conectada e funcional

```bash
# 1. Clonar o repositório
git clone https://github.com/lorocks51987/SnakeDonuts.git
cd SnakeDonuts

# 2. Criar ambiente virtual (opcional)
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt
```

---

## 🚀 COMO EXECUTA R

No Windows, basta dar dois cliques no arquivo:
```text
INICIAR_JOGO.bat
```
Ou executar diretamente pelo terminal Python:
```bash
python main.py
```

---

## 📁 ESTRUTURA DO PROJETO

```text
SnakeDonuts/
├── assets/
│   ├── backgrounds/
│   │   ├── title_screen_arcade_v2.png
│   │   └── game_over_arcade_v2.png
│   ├── sprites/
│   │   ├── Donut.png
│   │   ├── donut_dourado.png
│   │   ├── Potion.png
│   │   ├── coin.png
│   │   ├── ghost1.png
│   │   ├── ghost2.png
│   │   ├── ghost3.png
│   │   ├── coracao.png
│   │   └── cuboMario.png
│   └── animations/
│       ├── AnelSonic.gif
│       └── enchanted_apple.gif
├── docs/
│   └── media/
├── main.py
├── game_config.py
├── game_state.py
├── game_renderer.py
├── game_audio.py
├── leaderboard_manager.py
├── stand_utils.py
├── SnakeDonuts.py
├── leaderboard.json
├── stand_config.json
├── INICIAR_JOGO.bat
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🛠️ TECNOLOGIAS UTILIZADAS

* **Python 3.10+** — Linguagem principal
* **OpenCV (`cv2`)** — Processamento de vídeo em tempo real e renderização
* **MediaPipe (`cvzone.HandTrackingModule`)** — Rastreamento neural da mão
* **Pillow (`PIL`)** — Decodificação e animação de frames GIF
* **NumPy** — Manipulação de matrizes de imagem e transparência alpha

---

## 🏫 RECOMENDAÇÕES PARA A UNIMAR ABERTA

* **Iluminação Frontal:** Posicionar a câmera com iluminação vindo de frente para facilitar o rastreamento do indicador.
* **Distância Ideal:** Manter o visitante entre 1,0 m e 1,5 m de distância do sensor da câmera.
* **Modo Attract:** Deixar na tela inicial quando não houver jogadores no momento para demonstrar automaticamente como jogar aos visitantes.

---

## ⚠️ LIMITAÇÕES CONHECIDAS

* **Iluminação Fraca:** Ambientes muito escuros ou com forte contraluz podem afetar a precisão da detecção MediaPipe.
* **Múltiplas Mãos:** O sistema é configurado para focar na mão principal do participante ativo.

---

## 🎓 CRÉDITOS

Desenvolvido para o stand da mostra de tecnologia da **Unimar Aberta** pelo curso de **Análise e Desenvolvimento de Sistemas (ADS)**.
