"""
=============================================================================
             GERENCIADOR ATÔMICO DO HALL DA FAMA (LEADERBOARD)
=============================================================================
Gerencia os recordes TOP 5 do stand com validação rigorosa de dados JSON,
tratamento de empates determinístico e gravação atômica com arquivo temporário
para proteger contra desligamentos abruptos ou falhas de energia no stand.
Permite configurar arquivos de teste independentes.
=============================================================================
"""

import os
import json
import time
import tempfile

DEFAULT_RECORDS = [
    {"name": "ADS", "score": 350, "date": "Recorde"},
    {"name": "UNI", "score": 240, "date": "Stand"},
    {"name": "DEV", "score": 180, "date": "Top"},
    {"name": "SNK", "score": 120, "date": "Arcade"},
    {"name": "BOB", "score": 80,  "date": "Player"}
]


class StandLeaderboard:
    """Gerenciador seguro e atômico do Leaderboard do stand."""

    def __init__(self, filepath=None):
        if filepath is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.filepath = os.path.join(script_dir, "leaderboard.json")
        else:
            self.filepath = filepath
        self.scores = self.load()

    def _sanitize_entry(self, entry, index_hint=0):
        """Valida e sanitiza uma única entrada do leaderboard."""
        if not isinstance(entry, dict):
            return None

        # Validação do nome
        name_raw = entry.get("name", "ADS")
        if not isinstance(name_raw, str) or not name_raw.strip():
            name = "ADS"
        else:
            # Apenas 3 caracteres alfanuméricos em caixa alta
            clean_name = "".join(c for c in name_raw if c.isalnum()).upper()
            name = clean_name[:3] if clean_name else "ADS"

        # Validação de pontuação
        score_raw = entry.get("score", None)
        try:
            score = int(score_raw)
            if score < 0:
                return None
        except (ValueError, TypeError):
            return None

        # Validação de data/label
        date_raw = entry.get("date", "Stand")
        date_str = str(date_raw)[:16] if date_raw else "Stand"

        return {
            "name": name,
            "score": score,
            "date": date_str,
            "_order": index_hint
        }

    def load(self):
        """Carrega e valida o JSON, ignorando entradas corrompidas com segurança."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    valid_entries = []
                    for idx, item in enumerate(data):
                        clean = self._sanitize_entry(item, index_hint=idx)
                        if clean is not None:
                            valid_entries.append(clean)

                    if valid_entries:
                        # Ordenação por score decrescente; empates mantêm a ordem original (_order)
                        valid_entries.sort(key=lambda x: (-x["score"], x["_order"]))
                        # Remove a chave interna _order antes de salvar em memória
                        clean_top = [
                            {"name": e["name"], "score": e["score"], "date": e["date"]}
                            for e in valid_entries[:5]
                        ]
                        return clean_top
            except Exception as e:
                print(f"[LEADERBOARD] Aviso ao carregar {self.filepath}: {e}. Restaurando padrao.")

        return [dict(r) for r in DEFAULT_RECORDS]

    def save(self):
        """Gravação atômica via arquivo temporário no mesmo diretório para evitar corrupção."""
        target_dir = os.path.dirname(os.path.abspath(self.filepath))
        os.makedirs(target_dir, exist_ok=True)

        try:
            # Cria temporário no mesmo diretório para garantir que a substituição atômica seja no mesmo filesystem
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
                temp_name = tf.name
                json.dump(self.scores, tf, indent=2, ensure_ascii=False)
                tf.flush()
                os.fsync(tf.fileno())

            # Substituição atômica no SO
            os.replace(temp_name, self.filepath)
        except Exception as e:
            print(f"[LEADERBOARD] Erro ao salvar ranking em {self.filepath}: {e}")
            if "temp_name" in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except Exception:
                    pass

    def is_top_score(self, score: int) -> bool:
        """Retorna True se a pontuação se qualifica para o TOP 5."""
        if score <= 0:
            return False
        if len(self.scores) < 5:
            return True
        return score > self.scores[-1]["score"]

    def get_rank(self, score: int) -> int:
        """Determina a posição de 1 a 5 para uma pontuação."""
        rank = 1
        for item in self.scores:
            if score > item["score"]:
                return rank
            rank += 1
        return min(rank, 5)

    def add_score(self, name: str, score: int, date_str: str = None) -> int:
        """Adiciona pontuação, reordena de forma determinística e persiste atomicamente."""
        if score <= 0:
            return -1

        clean_name = "".join(c for c in str(name) if c.isalnum()).upper()[:3] or "ADS"
        if not date_str:
            date_str = time.strftime("%H:%M")

        new_entry = {
            "name": clean_name,
            "score": int(score),
            "date": date_str
        }

        # Desempate consistente: quem fez a pontuação agora fica atrás de quem já possuía a pontuação
        candidates = list(self.scores)
        inserted = False
        for idx, entry in enumerate(candidates):
            if new_entry["score"] > entry["score"]:
                candidates.insert(idx, new_entry)
                inserted = True
                break

        if not inserted and len(candidates) < 5:
            candidates.append(new_entry)

        self.scores = candidates[:5]
        self.save()
        return self.get_rank(score)

    def get_high_score(self) -> int:
        """Retorna o maior recorde atual."""
        return self.scores[0]["score"] if self.scores else 0
