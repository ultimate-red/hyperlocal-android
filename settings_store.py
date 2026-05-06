from kivy.storage.jsonstore import JsonStore

_store = JsonStore("hyperlocal_settings.json")

FONT_SIZES = {"Small": 1, "Medium": 1.5, "Large": 2, "XL": 2.5}
DEFAULT_FONT = "Medium"


def get_font_label():
    try:
        return _store.get("app")["font_size"]
    except Exception:
        return DEFAULT_FONT


def get_font_scale():
    return FONT_SIZES.get(get_font_label(), FONT_SIZES[DEFAULT_FONT])


def save_setting(key, value):
    data = dict(_store.get("app")) if _store.exists("app") else {}
    data[key] = value
    _store.put("app", **data)
