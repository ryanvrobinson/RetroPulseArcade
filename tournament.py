import os
import json
from constants import ALL_GAME_KEYS

FAKE_RIVAL_NAMES = {
    "PixelFox", "TurboCat", "StarByte", "NeonFox", "GlitchKid",
    "SunnyDash", "EchoWave", "ByteHero", "CloudHop", "PulseFan", "YOU"
}

class TournamentManager:
    def __init__(self, filename="tournament.json"):
        self.filename = filename
        self._player_name = ""
        self.rivals = []
        self.players = {}
        self.player_scores = {k: 0 for k in ALL_GAME_KEYS}
        self.player_points = 0
        self.load()

    @property
    def player_name(self):
        return self._player_name

    @player_name.setter
    def player_name(self, name):
        clean_name = str(name).strip() if name else ""
        if clean_name:
            if self._player_name and self._player_name in self.players:
                self.players[self._player_name] = {
                    "points": self.player_points,
                    "scores": dict(self.player_scores)
                }
            self._player_name = clean_name
            if clean_name in self.players:
                self.player_points = self.players[clean_name].get("points", 0)
                loaded_scores = self.players[clean_name].get("scores", {})
                self.player_scores = {k: loaded_scores.get(k, 0) for k in ALL_GAME_KEYS}
            else:
                self.player_points = 0
                self.player_scores = {k: 0 for k in ALL_GAME_KEYS}
                self.players[clean_name] = {
                    "points": 0,
                    "scores": dict(self.player_scores)
                }
        else:
            self._player_name = ""

    def _sync_rivals(self):
        self.rivals = [
            {"name": name, "points": pdata["points"], "scores": pdata["scores"]}
            for name, pdata in self.players.items()
            if name != self._player_name and name not in FAKE_RIVAL_NAMES
        ]

    def load(self):
        if not os.path.exists(self.filename):
            self.save()
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)

                raw_name = str(data.get("player_name", "")).strip()
                self._player_name = "" if raw_name in FAKE_RIVAL_NAMES else raw_name

                # Migrate scores safely: prune obsolete sky_flap and dino_run
                raw_scores = data.get("player_scores", {})
                self.player_scores = {k: raw_scores.get(k, 0) for k in ALL_GAME_KEYS}
                self.player_points = data.get("player_points", 0)

                self.players = {}
                raw_players = data.get("players", {})
                if isinstance(raw_players, dict):
                    for pname, pdata in raw_players.items():
                        clean_pname = str(pname).strip()
                        if clean_pname and clean_pname not in FAKE_RIVAL_NAMES:
                            p_scores = pdata.get("scores", {})
                            self.players[clean_pname] = {
                                "points": pdata.get("points", 0),
                                "scores": {k: p_scores.get(k, 0) for k in ALL_GAME_KEYS}
                            }

                if self._player_name:
                    if self._player_name not in self.players:
                        self.players[self._player_name] = {
                            "points": self.player_points,
                            "scores": dict(self.player_scores)
                        }
                    else:
                        self.player_points = self.players[self._player_name]["points"]
                        self.player_scores = self.players[self._player_name]["scores"]

                self._sync_rivals()
        except Exception:
            pass

    def save(self):
        try:
            if self._player_name:
                self.players[self._player_name] = {
                    "points": self.player_points,
                    "scores": dict(self.player_scores)
                }

            self._sync_rivals()

            data = {
                "player_name": self._player_name,
                "player_scores": self.player_scores,
                "player_points": self.player_points,
                "rivals": self.rivals,
                "players": self.players
            }
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_score(self, game_key):
        return self.player_scores.get(game_key, 0)

    def record_game(self, game_key, score):
        old_best = self.player_scores.get(game_key, 0)
        is_new_best = score > old_best
        if is_new_best:
            self.player_scores[game_key] = score

        added_pts = int(score * 0.15)
        self.player_points += added_pts

        prev_rank = self.get_current_rank()

        if self._player_name:
            self.players[self._player_name] = {
                "points": self.player_points,
                "scores": dict(self.player_scores)
            }

        self.save()
        new_rank = self.get_current_rank()

        return {
            "score": score,
            "best": max(old_best, score),
            "is_best": is_new_best,
            "added_pts": added_pts,
            "prev_rank": prev_rank,
            "new_rank": new_rank,
            "rank_climbed": new_rank < prev_rank
        }

    def get_current_rank(self):
        if not self.players:
            return 1
        standings = sorted(self.players.items(), key=lambda item: item[1].get("points", 0), reverse=True)
        for i, (name, _) in enumerate(standings):
            if name == self._player_name:
                return i + 1
        return len(standings) + 1

    def get_overall_standings(self):
        standings = []
        for name, pdata in self.players.items():
            if name and name not in FAKE_RIVAL_NAMES:
                standings.append({
                    "name": name,
                    "points": pdata.get("points", 0),
                    "is_player": (name == self._player_name)
                })
        standings.sort(key=lambda x: x["points"], reverse=True)
        return standings[:10]

    def get_game_standings(self, game_key):
        standings = []
        for name, pdata in self.players.items():
            if name and name not in FAKE_RIVAL_NAMES:
                scores = pdata.get("scores", {})
                standings.append({
                    "name": name,
                    "score": scores.get(game_key, 0),
                    "is_player": (name == self._player_name)
                })
        standings.sort(key=lambda x: x["score"], reverse=True)
        return standings[:10]

tournament_manager = TournamentManager()

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.defaults = {"sound": True, "shake": True}
        self.data = dict(self.defaults)
        self.load()

    def load(self):
        if not os.path.exists(self.filename):
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    self.data.update(d)
        except Exception:
            pass

    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get(self, key):
        return self.data.get(key, self.defaults.get(key, True))

    def toggle(self, key):
        self.data[key] = not self.get(key)
        self.save()
        return self.data[key]

settings_manager = SettingsManager()