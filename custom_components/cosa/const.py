"""Constants for COSA Smart Thermostat integration."""
from datetime import timedelta

# Domain ve Platform
DOMAIN = "cosa"
PLATFORMS = ["climate", "sensor", "binary_sensor", "switch", "number"]

# Config Keys
CONF_ENDPOINT_ID = "endpoint_id"

# API Konfigürasyonu
API_BASE_URL = "https://kiwi-api.nuvia.com.tr"
API_TIMEOUT = 60

# API Endpoint'leri
ENDPOINT_LOGIN = "/api/users/login"
ENDPOINT_GET_ENDPOINTS = "/api/endpoints/getEndpoints"
ENDPOINT_GET_ENDPOINT = "/api/endpoints/getEndpoint"
ENDPOINT_SET_MODE = "/api/endpoints/setMode"
ENDPOINT_SET_TARGET_TEMPERATURES = "/api/endpoints/setTargetTemperatures"
ENDPOINT_GET_FORECAST = "/api/places/getForecast"
ENDPOINT_SET_SCHEDULE = "/api/endpoints/setSchedule"
ENDPOINT_SET_COMBI_SETTINGS = "/api/endpoints/setCombiSettings"
ENDPOINT_SET_DEVICE_SETTINGS = "/api/endpoints/setDeviceSettings"
ENDPOINT_GET_REPORTS = "/api/endpoints/getReportsAnalyzed"

# HTTP Header'ları
HEADER_USER_AGENT = "Cosa/1 CFNetwork/3860.200.71 Darwin/25.1.0"
HEADER_CONTENT_TYPE = "application/json"
HEADER_PROVIDER = "cosa"

# Mod Değerleri
MODE_MANUAL = "manual"
MODE_AUTO = "auto"
MODE_SCHEDULE = "schedule"
MODE_TURBO = "turbo"
MODE_VENTILATION = "ventilation"

# Option Değerleri
OPTION_HOME = "home"
OPTION_SLEEP = "sleep"
OPTION_AWAY = "away"
OPTION_CUSTOM = "custom"
OPTION_FROZEN = "frozen"

# Preset Modları
PRESET_HOME = "home"
PRESET_SLEEP = "sleep"
PRESET_AWAY = "away"
PRESET_MANUAL = "manual"
PRESET_AUTOMATIC = "automatic"
PRESET_WEEKLY = "weekly"

# Sıcaklık Limitleri
MIN_TEMP = 5.0
MAX_TEMP = 32.0
TEMP_STEP = 0.1  # 0.1 derece adım

# Kalibrasyon Limitleri
CALIBRATION_MIN = -5.0
CALIBRATION_MAX = 5.0
CALIBRATION_STEP = 0.1

# Güncelleme Aralığı - 10 saniye
SCAN_INTERVAL = timedelta(seconds=10)
UPDATE_INTERVAL = timedelta(seconds=10)

# Batarya Seviyeleri
BATTERY_LEVELS = {
    "level0": 0,
    "level1": 25,
    "level2": 50,
    "level3": 75,
    "level4": 100,
}

# Operation Modları
OPERATION_HEATING = "heating"
OPERATION_COOLING = "cooling"

# Hava Durumu İkonları (Home Assistant formatı)
WEATHER_ICONS = {
    "clear-day": "sunny",
    "clear-night": "clear-night",
    "partly-cloudy-day": "partlycloudy",
    "partly-cloudy-night": "partlycloudy",
    "cloudy": "cloudy",
    "rain": "rainy",
    "snow": "snowy",
    "wind": "windy",
    "fog": "fog",
}

# Hava Durumu Türkçe Çevirileri
WEATHER_TRANSLATIONS = {
    "clear-day": "Güneşli",
    "clear-night": "Açık (Gece)",
    "partly-cloudy-day": "Parçalı Bulutlu",
    "partly-cloudy-night": "Parçalı Bulutlu (Gece)",
    "cloudy": "Bulutlu",
    "rain": "Yağmurlu",
    "snow": "Karlı",
    "wind": "Rüzgarlı",
    "fog": "Sisli",
    "sunny": "Güneşli",
    "partlycloudy": "Parçalı Bulutlu",
    "rainy": "Yağmurlu",
    "snowy": "Karlı",
    "windy": "Rüzgarlı",
}
