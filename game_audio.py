"""
=============================================================================
             MOTOR DE ÁUDIO RETRÔ PROCEDURAL COM FILA SINGLE-WORKER
=============================================================================
Executa efeitos sonoros retrô de forma assíncrona usando uma única thread
trabalhadora (worker) e uma fila thread-safe. Elimina a criação desenfreada de
threads, previne sobrecarga de CPU e protege o jogo contra qualquer falha
de hardware ou ausência do módulo winsound no Windows.
=============================================================================
"""

import queue
import threading
import time

try:
    import winsound
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class GameAudio:
    """Motor de áudio seguro com worker único e fila de eventos sonoros."""

    def __init__(self, max_queue_size=6):
        self.muted = False
        self.queue = queue.Queue(maxsize=max_queue_size)
        self._last_played = {}
        self._worker_thread = None
        self._running = True

        if AUDIO_AVAILABLE:
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

    def set_muted(self, muted: bool):
        self.muted = bool(muted)

    def is_muted(self) -> bool:
        return self.muted

    def toggle_muted(self) -> bool:
        self.muted = not self.muted
        return self.muted

    def play(self, sound_type: str, min_interval: float = 0.04):
        """Enfileira um som para execução, limitando sons repetitivos muito frequentes."""
        if not AUDIO_AVAILABLE or self.muted:
            return

        now = time.monotonic()
        last = self._last_played.get(sound_type, 0.0)
        if now - last < min_interval:
            return
        self._last_played[sound_type] = now

        try:
            # Se a fila estiver cheia, descarta o som mais antigo para evitar acúmulo e atraso
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except queue.Empty:
                    pass
            self.queue.put_nowait(sound_type)
        except queue.Full:
            pass

    def _worker_loop(self):
        while self._running:
            try:
                sound_type = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if not self.muted:
                    self._execute_sound(sound_type)
            except Exception:
                # Falha sonora nunca deve derrubar o worker nem o jogo
                pass
            finally:
                self.queue.task_done()

    def _execute_sound(self, sound_type: str):
        if not AUDIO_AVAILABLE or self.muted:
            return

        # Frequência e duração em milissegundos
        if sound_type == "donut":
            winsound.Beep(650, 35)
            winsound.Beep(880, 40)
        elif sound_type == "coin":
            winsound.Beep(988, 40)
            winsound.Beep(1318, 70)
        elif sound_type == "potion":
            winsound.Beep(800, 35)
            winsound.Beep(600, 35)
            winsound.Beep(450, 45)
        elif sound_type == "ring":
            winsound.Beep(1046, 50)
            winsound.Beep(1318, 50)
            winsound.Beep(1568, 60)
        elif sound_type == "heart":
            winsound.Beep(523, 50)
            winsound.Beep(659, 50)
            winsound.Beep(784, 50)
            winsound.Beep(1046, 70)
        elif sound_type == "cube":
            winsound.Beep(784, 40)
            winsound.Beep(988, 40)
            winsound.Beep(1175, 60)
        elif sound_type == "shield_break":
            # Som estridente de escudo quebrando
            winsound.Beep(1400, 40)
            winsound.Beep(1050, 50)
            winsound.Beep(700, 60)
        elif sound_type == "second_chance":
            # Fanfarra rápida de reviver
            for freq in (440, 554, 659, 880):
                winsound.Beep(freq, 40)
        elif sound_type == "powerup":
            for freq in (523, 659, 784, 1046):
                winsound.Beep(freq, 35)
        elif sound_type == "ghost_eat":
            winsound.Beep(400, 50)
            winsound.Beep(800, 70)
        elif sound_type == "game_over":
            for freq in (440, 370, 311, 261):
                winsound.Beep(freq, 75)
        elif sound_type == "combo":
            winsound.Beep(1100, 40)
            winsound.Beep(1400, 60)
        elif sound_type == "level_up":
            for freq in (587, 740, 880, 1175):
                winsound.Beep(freq, 40)
        elif sound_type == "record":
            for freq in (659, 659, 659, 523, 659, 784, 392):
                winsound.Beep(freq, 55)
        elif sound_type == "start":
            winsound.Beep(523, 40)
            winsound.Beep(784, 60)


# Instância global singleton
audio = GameAudio()
