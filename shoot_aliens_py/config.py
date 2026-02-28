import json
from pathlib import Path
from typing import Any, Dict

"""Configuration loader with defaults and deep-merge support."""


DEFAULT_CONFIG: Dict[str, Any] = {
    "window": {"width": 1280, "height": 720, "fps": 60},
    "player": {"speed": 8, "lives": 3, "max_lives": 5},
    "bullet": {
        "cooldown_ms": 200,
        "rapid_fire_cooldown_ms": 100,
        "rapid_fire_duration_ms": 5000,
    },
    "enemy": {
        "base_spawn_ms": 750,
        "min_spawn_ms": 250,
        "spawn_step_ms": 40,
        "max_enemies": 14,
        "stage_score_step": 150,
        "tough": {
            "chance_base": 0.15,
            "chance_per_stage": 0.02,
            "chance_max": 0.45,
            "speed_base_min": 3,
            "speed_base_max": 5,
            "speed_stage_div": 3,
            "speed_cap": 9,
            "hp": 3,
            "score": 25,
        },
        "regular": {
            "speed_base_min": 2,
            "speed_base_max": 4,
            "speed_stage_div": 4,
            "speed_cap": 7,
            "hp": 1,
            "score": 10,
        },
    },
    "powerups": {"drop_chance": 0.12, "heal_max_lives": 5},
    "colors": {"background": [5, 5, 20], "text": [240, 240, 240]},
    "background": {"layers": 3, "stars_per_layer": 60},
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override dict into base, returning a new dict."""
    result: Dict[str, Any] = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: Path | None = None) -> Dict[str, Any]:
    """Load config from JSON if present, merged over defaults."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        return deep_merge(DEFAULT_CONFIG, user_cfg)
    return DEFAULT_CONFIG
