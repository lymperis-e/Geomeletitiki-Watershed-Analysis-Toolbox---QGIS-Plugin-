import os
import json


def get_settings_path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "settings.json")


def read_settings():
    with open(get_settings_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings):
    with open(get_settings_path(), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def get_setting(key):
    settings = read_settings()
    return settings.get(key, None)


def set_setting(key, value):
    settings = read_settings()
    settings[key] = value
    save_settings(settings)


def meteo_stations_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets",
        "meteo_stations.gpkg",
    )


def cn_conditions_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "conditions"
    )
