# 🎤 ROTEIRO OFICIAL DE APRESENTAÇÃO NO STAND — UNIMAR ABERTA
### *Guia Prático para os Apresentadores do Projeto SnakeDonuts (ADS)*

---

## 🎯 1. Visão Geral e Preparação Inicial do Stand

Antes de abrir o stand para os visitantes da Unimar Aberta:
1. Conecte a webcam USB a cerca de **1,20m de altura**, apontada para a área onde o jogador ficará em pé (a **1,0m a 1,5m** de distância).
2. Dê dois cliques em **`INICIAR_JOGO.bat`**.
3. Pressione **`2`** ou **`TAB`** para colocar o jogo em **Tela Cheia** na TV ou monitor.
4. Verifique a iluminação: a luz deve ser frontal ou difusa no teto; evite lâmpadas ou janelas de alta intensidade diretamente atrás do jogador (contra-luz).
5. O jogo deve estar exibindo a **Tela Inicial (Attract Mode)**, com o card inferior exibindo as dicas em carrossel.

---

## ⚡ 2. O "Hook" de Entrada (Como Atrair Quem Passa no Corredor)

Quando visitantes (estudantes de ensino médio, pais, professores) olharem para o stand, use uma destas abordagens:

> 🗣️ **Apresentador:** *"Olá! Já jogou o clássico jogo da cobrinha sem encostar em nada, controlando ela no ar só com o dedo indicador?"*

> 🗣️ **Variação Rápida:** *"Quer testar a IA de visão computacional do nosso curso? Venha tentar bater o recorde do dia no fliperama!"*

---

## 🎮 3. Condução do Jogador (Etapa por Etapa)

### Passo 1: O Início (0 a 10 segundos)
- Peça para o visitante se posicionar na marca no chão.
- Peça para ele levantar a mão direita e apontar o dedo indicador para a tela.
- Assim que o MediaPipe detectar o dedo, o jogo sai do modo Attract e inicia automaticamente com o som clássico de partida.
> 🗣️ **Dica:** *"Olha lá! A cabeça da cobra já se conectou na ponta do seu indicador. Mova a mão suavemente para guiar a cobra até o primeiro Donut rosa."*

### Passo 2: Os Combos e o Crescimento (10 a 30 segundos)
- Assim que ele come o primeiro donut:
> 🗣️ **Dica:** *"Perfeito! Cada donut que você come aumenta o corpo da cobra e inicia a barra de combo azul ali em cima. Se você pegar o próximo donut antes da barra esvaziar, você sobe o multiplicador: 2x, 3x, até 8x a pontuação!"*

### Passo 3: Os Itens Especiais e Riscos (30 a 60 segundos)
- Quando surgir o **Anel Dourado**:
> 🗣️ **Dica:** *"Aquele anel dourado é o seu Escudo! Pega ele! Se você encostar no próprio corpo, o anel absorve a batida e salva você."*
- Quando surgir o **Cubo Surpresa**:
> 🗣️ **Dica:** *"O Cubo Surpresa é a roleta arcade. O primeiro da partida sempre dá coisa boa: ou congela seu combo, encurta a cobra, ou dá invencibilidade!"*
- Quando o **Fantasma vermelho** surgir:
> 🗣️ **Dica:** *"Atenção! Aquele fantasma está te perseguindo com física real. Desvie dele ou pegue a Maçã verde para ficar invencível e devorá-lo!"*

### Passo 4: Fim da Partida e Registro de Recorde
- Caso o jogador colida e não tenha mais vidas/escudo:
- A tela de Game Over aparece com a fanfarra arcade.
- Se a pontuação dele entrar no TOP 5 do Stand:
> 🗣️ **Dica:** *"Parabéns, você entrou no TOP 5 da Unimar Aberta! Digite as 3 letras do seu nome usando o teclado e aperte ENTER para gravar seu recorde no Hall da Fama!"*
- Para o próximo jogador:
> 🗣️ **Dica:** *"Para jogar de novo, basta apertar a tecla 4 ou fechar a mão duas vezes na frente da câmera!"*

---

## 🧠 4. Perguntas Frequentes (FAQ) da Banca e Professores

| Pergunta Típica | Resposta Técnica Recomendada |
| :--- | :--- |
| **"Que tecnologias vocês usaram?"** | *"Desenvolvemos em Python utilizando OpenCV para captura e processamento matricial de vídeo em tempo real, e a rede neural Google MediaPipe Hands para detecção dos 21 landmarks articulares da mão sem necessidade de sensores vestíveis."* |
| **"Como garantem que o jogo não trave ou engasgue?"** | *"Otimizamos o pipeline rodando a inferência de IA em resolução reduzida (640x360) com downscale bilinear, e o áudio é processado em uma thread separada via fila assíncrona. Toda a física usa tempo delta (dt), então a velocidade da cobra e do fantasma é matematicamente constante mesmo sob oscilações de FPS."* |
| **"E se cair a energia do stand?"** | *"O sistema de recordes utiliza gravação atômica em disco. Ele grava primeiro num arquivo temporário e faz substituição atômica no sistema operacional, impedindo que o JSON fique corrompido em caso de desligamento abrupto."* |
| **"Por que não usar controles físicos?"** | *"A proposta foi explorar a Interação Humano-Computador (IHC) natural através de visão computacional, demonstrando como algoritmos de machine learning podem transformar qualquer câmera comum em uma interface de jogo imersiva e acessível."* |

---

## ⌨️ 5. Guia Rápido de Teclas de Emergência para o Operador

- **`1`**: Alterna entre câmeras USB conectadas.
- **`2`** ou **`TAB`**: Alterna modo Tela Cheia.
- **`3`**: Inverte o espelhamento horizontal (se a câmera estiver invertida).
- **`4`**: Reinicia a partida imediatamente.
- **`5`**: Liga / Desliga o som (Mudo).
- **`ESC`**: Fecha o jogo com segurança liberando a câmera.
