# app/actions/light_actions.py

import requests

from ..config_loader import load_settings

# Predefined color temperatures in Kelvin
COLOR_TEMPERATURE_PRESETS_KELVIN = {
    "warm": 2700,
    "natural": 4000,
    "cool": 6000,
}

# --- Load Home Assistant configuration ---
HA_URL = None
HA_TOKEN = None
DEFAULT_LIGHT_ENTITY_IDS = []

try:
    config_la = load_settings()

    ha_config = config_la.get("home_assistant", {})
    HA_URL = ha_config.get("base_url")
    HA_TOKEN = ha_config.get("long_lived_access_token")

    # ИЗМЕНЕНО: Обновлен путь для загрузки списка default_lights из новой структуры с device_groups
    DEFAULT_LIGHT_ENTITY_IDS = ha_config.get("device_groups", {}).get("default_lights", [])

    if not HA_URL or not HA_TOKEN:
        raise ValueError("Home Assistant URL or token not found in configs/settings.yaml")
    if not DEFAULT_LIGHT_ENTITY_IDS:
        print("Light_Actions warning: default_lights list not found or empty in settings.")
    print("Light_Actions: Home Assistant configuration and default lights loaded.")

except Exception as e:
    print(f"Critical error in Light_Actions: Failed to load HA configuration: {e}")
    HA_URL = None
    HA_TOKEN = None
    DEFAULT_LIGHT_ENTITY_IDS = []
# --- End configuration loading ---


def _call_ha_light_service(service_name: str, entity_ids: list, service_data: dict = None) -> dict:
    if not HA_URL or not HA_TOKEN:
        return {"success": False, "error": "Light_Actions: Home Assistant configuration not loaded."}
    if not entity_ids:
        return {"success": False, "error": "Light_Actions: No entity_id specified for controlling lights."}

    api_url = f"{HA_URL}/api/services/light/{service_name}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    # ИЗМЕНЕНО: Home Assistant ожидает entity_id в виде строки, даже для нескольких устройств (через запятую).
    # Превращаем наш список в такую строку. Это исправляет "тихий" баг.
    payload = {"entity_id": ",".join(entity_ids)}
    
    if service_data:
        payload.update(service_data)

    print(f"Light_Actions (HA Service Call): URL='{api_url}', Payload='{payload}'")

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Light_Actions (HA Service Response): Status={response.status_code}, Content='{response.text[:100]}...'")
        return {"success": True, "message": f"Home Assistant service light.{service_name} for {entity_ids} called successfully."}

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error: {http_err}. Response: {http_err.response.text[:200]}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except requests.exceptions.RequestException as req_err:
        error_message = f"Network error: {req_err}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}


def turn_on(entity_ids: list = None, brightness_percent: int = None, kelvin: int = None):
    """Turn on the specified lights.

    Args:
        entity_ids (list, optional): Light entity IDs. Defaults to DEFAULT_LIGHT_ENTITY_IDS.
        brightness_percent (int, optional): Brightness from 0 to 100 percent.
        kelvin (int, optional): Color temperature in Kelvin.

    Returns:
        dict: Result of the Home Assistant service call.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    service_data = {}
    if brightness_percent is not None:
        if not 0 <= brightness_percent <= 100:
            return {"success": False, "error": "Яркость должна быть от 0 до 100%"}
        service_data["brightness_pct"] = brightness_percent
    if kelvin is not None:
        # You can add validation for allowed Kelvin values for your bulbs
        # if you know them (e.g., 2000-6500K). For now we keep a simple check.
        if kelvin < 1000 or kelvin > 10000:
            return {"success": False, "error": "Значение цветовой температуры (Kelvin) некорректно."}
        service_data["color_temp_kelvin"] = kelvin

    print(f"Light_Actions: Включить свет для {targets} с данными: {service_data if service_data else 'нет доп. данных'}")
    return _call_ha_light_service("turn_on", targets, service_data if service_data else None)


def turn_off(entity_ids: list = None):
    """Turn off the specified lights.

    Args:
        entity_ids (list, optional): Light entity IDs. Defaults to DEFAULT_LIGHT_ENTITY_IDS.

    Returns:
        dict: Result of the Home Assistant service call.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Выключить свет для {targets}")
    return _call_ha_light_service("turn_off", targets)


def toggle(entity_ids: list = None):
    """Toggle the state of the specified lights.

    Args:
        entity_ids (list, optional): Light entity IDs. Defaults to DEFAULT_LIGHT_ENTITY_IDS.

    Returns:
        dict: Result of the Home Assistant service call.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Переключить свет для {targets}")
    return _call_ha_light_service("toggle", targets)


def set_brightness(brightness_percent: int, entity_ids: list = None):
    """Set brightness for the specified lights.

    Args:
        brightness_percent (int): Brightness from 0 to 100 percent.
        entity_ids (list, optional): Light entity IDs. Defaults to DEFAULT_LIGHT_ENTITY_IDS.

    Returns:
        dict: Result of the Home Assistant service call.
    """
    print(f"Light_Actions: Установить яркость {brightness_percent}% для {entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS}")
    return turn_on(entity_ids=entity_ids, brightness_percent=brightness_percent)


def set_color_temperature(temperature_value, entity_ids: list = None):
    """Set light color temperature.

    Args:
        temperature_value (int | str): Kelvin value or preset name ("warm", "natural", "cool").
        entity_ids (list, optional): Light entity IDs. Defaults to DEFAULT_LIGHT_ENTITY_IDS.

    Returns:
        dict: Result of the Home Assistant service call.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    kelvin_to_set = None

    if isinstance(temperature_value, (int, float)):  # Numeric value means Kelvin
        kelvin_to_set = int(temperature_value)
        print(f"Light_Actions: Установить цветовую температуру {kelvin_to_set}K для {targets}")
    elif isinstance(temperature_value, str) and temperature_value.lower() in COLOR_TEMPERATURE_PRESETS_KELVIN:
        kelvin_to_set = COLOR_TEMPERATURE_PRESETS_KELVIN[temperature_value.lower()]
        print(f"Light_Actions: Установить цветовую температуру '{temperature_value}' ({kelvin_to_set}K) для {targets}")
    else:
        error_msg = f"Неизвестное значение для цветовой температуры: {temperature_value}. Используйте 'warm', 'cool', 'natural' или число в Кельвинах."
        print(f"Light_Actions: {error_msg}")
        return {"success": False, "error": error_msg}

    # Calling light.turn_on with color_temp_kelvin will also turn on the light if it was off
    return turn_on(entity_ids=targets, kelvin=kelvin_to_set)