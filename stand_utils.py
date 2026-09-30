"""
=============================================================================
             STAND UTILS - SNAKEDONUTS (ADS UNIMAR ABERTA)
=============================================================================
Utilitários visuais, gerencimento de câmera, som procedural e interface
padronizada para o jogo SnakeDonuts em stands de eventos e feiras acadêmicas.
Totalmente autocontido e desacoplado de dependências externas.
=============================================================================
"""

import os
import json
import time
import threading
import cv2
import numpy as np

# =============================================================================
# CONFIGURAÇÃO PADRÃO DO STAND
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'stand_config.json')

CONFIG_PADRAO = {
    'camera_index': 0,
    'largura_desejada': 1280,
    'altura_desejada': 720,
    'espelhar_video': True,
    'audio_muted': False,
    'tela_cheia': False,
    'camera_ja_espelhada': False,
    'game_title': 'SNAKEDONUTS'
}

def carregar_config():
    """Carrega as configurações locais ou cria com valores padrão."""
    config = dict(CONFIG_PADRAO)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            for chave, padrao in CONFIG_PADRAO.items():
                valor = dados.get(chave, padrao)
                if type(valor) is type(padrao):
                    if isinstance(padrao, int) and not isinstance(padrao, bool):
                        minimo, maximo = (0, 9) if chave == 'camera_index' else (1, 4096)
                        if not minimo <= valor <= maximo:
                            continue
                    config[chave] = valor
        except Exception as e:
            print(f"[CONFIG] Usando config padrao: {e}")
    else:
        salvar_config(config)
    return config

def salvar_config(config):
    """Persiste configurações no disco."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CONFIG] Erro ao salvar config: {e}")


AUDIO_MUTED = False

# =============================================================================
# GLASSMORPHISM CARD (ALTA PERFORMANCE COM ROI DIRETA)
# =============================================================================
def desenhar_retangulo_arredondado(img, pt1, pt2, cor_fundo, cor_borda, raio=14, alpha=0.85, espessura_borda=1):
    """
    Desenha um card de vidro translúcido (Glassmorphism) com cantos arredondados,
    operando diretamente na Região de Interesse (ROI) para máxima eficiência e fluidez.
    """
    x1, y1 = pt1
    x2, y2 = pt2
    ih, iw = img.shape[:2]
    x1 = max(0, min(iw - 1, int(x1)))
    y1 = max(0, min(ih - 1, int(y1)))
    x2 = max(0, min(iw, int(x2)))
    y2 = max(0, min(ih, int(y2)))
    w = x2 - x1
    h = y2 - y1

    if w <= 0 or h <= 0:
        return img

    roi = img[y1:y2, x1:x2]
    overlay = np.full_like(roi, cor_fundo)
    r = max(0, min(int(raio), (w - 1) // 2, (h - 1) // 2))
    mask = np.zeros((h, w), np.uint8)
    cv2.rectangle(mask, (r, 0), (w - r - 1, h - 1), 255, -1)
    cv2.rectangle(mask, (0, r), (w - 1, h - r - 1), 255, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(mask, (cx, cy), r, 255, -1)

    blended = cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0)
    roi[mask > 0] = blended[mask > 0]

    if espessura_borda > 0:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(roi, contours, -1, cor_borda, espessura_borda, cv2.LINE_AA)

    return img

# =============================================================================
# BUSCA INTELIGENTE DE CÂMERA & HOT-PLUGGING
# =============================================================================
def _abrir_camera(idx, largura, altura, permitir_preta=False):
    backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
    cap = cv2.VideoCapture(idx, backend)
    try:
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            for _ in range(5):
                ok, frame = cap.read()
                if ok and frame is not None and frame.size:
                    if permitir_preta or np.mean(frame) > 1.0:
                        return cap
    except cv2.error:
        pass
    cap.release()
    return None

def encontrar_camera(indices=None, retornar_indice=False):
    """Encontra e inicializa a melhor webcam ativa no stand."""
    config = carregar_config()
    if indices is None:
        indices = list(dict.fromkeys([config['camera_index'], 0, 1, 2, 3]))

    for idx in indices:
        cap = _abrir_camera(idx, config['largura_desejada'], config['altura_desejada'], permitir_preta=False)
        if cap is not None:
            print(f"[CAMERA] Conectada com sinal de video: indice {idx}")
            return (cap, idx) if retornar_indice else cap

    for idx in indices:
        cap = _abrir_camera(idx, config['largura_desejada'], config['altura_desejada'], permitir_preta=True)
        if cap is not None:
            print(f"[CAMERA] Conectada (fallback): indice {idx}")
            return (cap, idx) if retornar_indice else cap

    return (None, None) if retornar_indice else None

def trocar_camera(cap_atual, camera_idx_atual, largura=1280, altura=720, indices_max=4):
    """Alterna ciclicamente entre webcams conectadas com tecla 1."""
    indices_max = max(indices_max, camera_idx_atual + 1)
    for permitir_preta in (False, True):
        for step in range(1, indices_max):
            idx = (camera_idx_atual + step) % indices_max
            cap = _abrir_camera(idx, largura, altura, permitir_preta=permitir_preta)
            if cap is not None:
                if cap_atual is not None:
                    cap_atual.release()
                return cap, idx
    return cap_atual, camera_idx_atual

# =============================================================================
# DECODIFICAÇÃO DE TECLADO STAND
# =============================================================================
def decodificar_tecla(key_raw):
    """Decodifica com precisão códigos de 32 bits de cv2.waitKeyEx."""
    if key_raw is None or key_raw in [-1, 255, 0]:
        return None, None

    if key_raw in [0x7B0000, 8060928, 123, 65481, 63247]:
        return "F12", None

    func_keys = {
        0x700000: "F1", 0x710000: "F2", 0x720000: "F3", 0x730000: "F4",
        0x740000: "F5", 0x750000: "F6", 0x760000: "F7", 0x770000: "F8",
        0x780000: "F9", 0x790000: "F10", 0x7A0000: "F11",
        65470: "F1", 65471: "F2", 65472: "F3", 65473: "F4",
        65474: "F5", 65475: "F6", 65476: "F7", 65477: "F8",
        65478: "F9", 65479: "F10", 65480: "F11"
    }
    if key_raw in func_keys:
        return func_keys[key_raw], None

    if key_raw in [0x260000, 2490368, 65362]:
        return "UP", None
    if key_raw in [0x280000, 2621440, 65364]:
        return "DOWN", None
    if key_raw in [0x250000, 2424832, 65361]:
        return "LEFT", None
    if key_raw in [0x270000, 2555904, 65363]:
        return "RIGHT", None
    if key_raw in [0x2E0000, 3014656, 127, 65535]:
        return "DELETE", None

    controles = {
        27: ("ESC", None),
        13: ("ENTER", None),
        10: ("ENTER", None),
        9: ("TAB", None),
        8: ("BACKSPACE", None),
        26: ("CTRL_Z", None),
        32: ("SPACE", " "),
    }
    if key_raw in controles:
        return controles[key_raw]

    if 32 <= key_raw <= 126:
        return "CHAR", chr(key_raw)

    return None, None

ATALHOS = {
    '0': 'AJUDA', '1': 'CAMERA', '2': 'TELA', '3': 'ESPELHO',
    '4': 'REINICIAR', '5': 'SOM', '6': 'ACAO', '7': 'MODO',
    '8': 'DESFAZER', '9': 'CALIBRACAO'
}

def comando_stand(key_raw):
    cmd, char = decodificar_tecla(key_raw)
    return ATALHOS.get(char, cmd), char

# =============================================================================
# ÁUDIO RETRÔ PROCEDURAL
# =============================================================================
try:
    import winsound
    import queue

    _sound_queue = queue.Queue(maxsize=10)
    def _audio_worker():
        while True:
            try:
                beeps = _sound_queue.get(timeout=0.5)
            except Exception:
                continue
            try:
                if not AUDIO_MUTED:
                    for freq, dur in beeps:
                        winsound.Beep(freq, dur)
            except Exception:
                pass
            finally:
                _sound_queue.task_done()

    _audio_thread = threading.Thread(target=_audio_worker, daemon=True)
    _audio_thread.start()

    def _beep_bg(*beeps):
        if AUDIO_MUTED:
            return
        try:
            if _sound_queue.full():
                try:
                    _sound_queue.get_nowait()
                    _sound_queue.task_done()
                except Exception:
                    pass
            _sound_queue.put_nowait(beeps)
        except Exception:
            pass

    def som_acerto():
        _beep_bg((988, 70), (1318, 110))

    def som_erro():
        _beep_bg((440, 90), (370, 90))

    def som_tick():
        _beep_bg((880, 40))

    def som_vitoria():
        _beep_bg((523, 60), (659, 60), (784, 60), (1046, 60))

    def som_fim():
        _beep_bg((440, 90), (370, 90), (311, 90))

except ImportError:
    def som_acerto(): pass
    def som_erro(): pass
    def som_tick(): pass
    def som_vitoria(): pass
    def som_fim(): pass

# =============================================================================
# FORMATO E PROPORÇÃO DA TELA
# =============================================================================
def ajustar_frame(img):
    """Enquadra em 1280x720 mantendo aspect ratio sem distorcer webcam."""
    h, w = img.shape[:2]
    escala = min(1280 / w, 720 / h)
    nw, nh = max(1, round(w * escala)), max(1, round(h * escala))
    tela = np.zeros((720, 1280, 3), dtype=np.uint8)
    x, y = (1280 - nw) // 2, (720 - nh) // 2
    tela[y:y + nh, x:x + nw] = cv2.resize(img, (nw, nh))
    return tela

def texto_ajustado(img, texto, origem, largura, escala=0.55, cor=(220, 225, 235), espessura=1):
    """Renderiza texto com auto-scale para não estourar caixas de diálogo."""
    fonte = cv2.FONT_HERSHEY_DUPLEX
    tamanho = cv2.getTextSize(texto, fonte, escala, espessura)[0][0]
    if tamanho > largura:
        escala *= largura / tamanho
    cv2.putText(img, texto, origem, fonte, escala, cor, espessura, cv2.LINE_AA)

def janela_aberta(nome):
    try:
        return cv2.getWindowProperty(nome, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False

# =============================================================================
# INTERFACE STAND (PAINEL INFERIOR & POPUP DE AJUDA)
# =============================================================================
class InterfaceStand:
    """Controlador de tela, áudio, espelho e comandos operacionais do stand."""
    def __init__(self, nome, titulo, camera_idx, extras=()):
        global AUDIO_MUTED
        self.config = carregar_config()
        self.nome, self.titulo, self.camera_idx = nome, titulo, camera_idx
        self.espelhar = self.config.get('espelhar_video', True)
        self.fullscreen = self.config.get('tela_cheia', False)
        self.ajuda = False
        self.extras = extras
        self.aviso = ''
        self.aviso_ate = 0
        self.falha_camera = False
        AUDIO_MUTED = self.config.get('audio_muted', False)

        cv2.namedWindow(nome, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(nome, 1280, 720)
        self.aplicar_tela()

    def aplicar_tela(self):
        cv2.setWindowProperty(self.nome, cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL)

    def ler(self, cap):
        ok, frame = cap.read()
        self.falha_camera = not ok or frame is None
        if self.falha_camera:
            return np.zeros((720, 1280, 3), np.uint8)
        return ajustar_frame(frame)

    def tratar(self, cmd, cap):
        global AUDIO_MUTED
        if cmd == 'AJUDA':
            self.ajuda = not self.ajuda
        elif cmd in ('TELA', 'TAB'):
            self.fullscreen = not self.fullscreen
            self.aplicar_tela()
        elif cmd == 'ESPELHO':
            self.espelhar = not self.espelhar
        elif cmd == 'SOM':
            AUDIO_MUTED = not AUDIO_MUTED
        elif cmd == 'CAMERA':
            cap, novo = trocar_camera(cap, self.camera_idx,
                                      self.config['largura_desejada'], self.config['altura_desejada'])
            self.aviso = ('Nenhuma outra camera disponivel' if novo == self.camera_idx
                          else f'Camera alterada: indice {novo}')
            self.camera_idx = novo
            self.aviso_ate = time.monotonic() + 3
        return cap

    def mostrar(self, img, detalhe=''):
        h, w = img.shape[:2]
        
        cv2.rectangle(img, (0, h - 66), (w, h), (10, 12, 18), -1)
        cv2.line(img, (20, h - 66), (w - 20, h - 66), (0, 220, 255), 1)

        som = 'OFF' if AUDIO_MUTED else 'ON'
        espelho = 'ON' if self.espelhar else 'OFF'

        texto_ajustado(img, f'ADS / UNIMAR ABERTA  |  {self.titulo}', (22, h - 42), 520, cor=(0, 255, 140))
        texto_ajustado(img, f'CAM {self.camera_idx}  |  ESPELHO {espelho}  |  SOM {som}  {detalhe}',
                       (565, h - 42), w - 585, escala=0.45)
        texto_ajustado(img, '[0] Ajuda   [1] Camera   [2] Tela cheia   [3] Espelho   [4] Reiniciar   [5] Som   [6] Acao   [ESC] Sair',
                       (22, h - 16), w - 44, escala=0.49)

        if self.falha_camera or time.monotonic() < self.aviso_ate:
            aviso = 'Camera desconectada. Reconecte ou pressione [1] para trocar.' if self.falha_camera else self.aviso
            cv2.rectangle(img, (260, h - 120), (1020, h - 76), (20, 28, 45), -1)
            texto_ajustado(img, aviso, (280, h - 91), 720, cor=(0, 220, 255))

        if self.ajuda:
            desenhar_retangulo_arredondado(img, (240, 115), (1040, 625), (12, 14, 22), (0, 220, 255), alpha=0.97)
            texto_ajustado(img, 'CONTROLES DO STAND', (280, 157), 710, 0.8, (0, 220, 255), 2)
            linhas = [
                '0  Abrir / fechar esta ajuda',
                '1  Trocar webcam   |   2  Tela cheia   |   3  Espelhar',
                '4  Reiniciar partida   |   5  Ligar / silenciar som',
                '6 / ENTER  Acao principal / Jogar novamente   |   ESC  Sair',
                'Atalhos funcionam com a fileira superior ou teclado numerico com Num Lock',
                *self.extras
            ]
            for i, linha in enumerate(linhas):
                texto_ajustado(img, linha, (280, 203 + i * 36), 720, 0.51)

        cv2.imshow(self.nome, img)
        key = cv2.waitKeyEx(1)
        if not janela_aberta(self.nome):
            return 'ESC', None
        return comando_stand(key)
