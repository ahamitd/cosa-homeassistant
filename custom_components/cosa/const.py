"""Constants for COSA Smart Thermostat integration.

Bu dosya COSA termostat entegrasyonu için tüm sabitleri içerir.
API endpoint'leri gerçek mobil uygulama trafiğinden alınmıştır.
"""
from datetime import timedelta

# =============================================================================
# DOMAIN VE PLATFORM
# =============================================================================
DOMAIN = "cosa"
PLATFORMS = ["climate", "sensor"]

# =============================================================================
# API KONFİGÜRASYONU
# Gerçek Cosa mobil uygulaması API trafiğinden alınmıştır
# =============================================================================
API_BASE_URL = "https://kiwi-api.nuvia.com.tr"
API_TIMEOUT = 30

# =============================================================================
# API ENDPOINT'LERİ
# POST /api/users/login → Login
# POST /api/endpoints/getEndpoints → Endpoint listesi (cihaz listesi)
# POST /api/endpoints/getEndpoint → Tek endpoint detayı
# POST /api/endpoints/setMode → Mod değiştirme
# POST /api/endpoints/setTargetTemperatures → Sıcaklık ayarı
# =============================================================================
ENDPOINT_LOGIN = "/api/users/login"
ENDPOINT_GET_ENDPOINTS = "/api/endpoints/getEndpoints"
ENDPOINT_GET_ENDPOINT = "/api/endpoints/getEndpoint"
ENDPOINT_SET_MODE = "/api/endpoints/setMode"
ENDPOINT_SET_TARGET_TEMPERATURES = "/api/endpoints/setTargetTemperatures"

# =============================================================================
# HTTP HEADER'LARI
# Gerçek Cosa iOS uygulaması User-Agent'ı kullanılıyor
# =============================================================================
HEADER_USER_AGENT = "Cosa/1 CFNetwork/3860.200.71 Darwin/25.1.0"
HEADER_CONTENT_TYPE = "application/json"
HEADER_PROVIDER = "cosa"

# =============================================================================
# MOD DEĞERLERİ
# API'de kullanılan mod isimleri
# =============================================================================
# Ana modlar (mode parametresi için)
MODE_MANUAL = "manual"
MODE_AUTO = "auto"
MODE_SCHEDULE = "schedule"

# Option değerleri (manual mod için option parametresi)
OPTION_HOME = "home"       # Ev modu
OPTION_SLEEP = "sleep"     # Uyku modu
OPTION_AWAY = "away"       # Dışarı modu
OPTION_CUSTOM = "custom"   # Kullanıcı modu
OPTION_FROZEN = "frozen"   # Kapalı modu (donma koruması)

# =============================================================================
# HOME ASSISTANT PRESET MOD İSİMLERİ
# =============================================================================
PRESET_HOME = "home"
PRESET_SLEEP = "sleep"
PRESET_AWAY = "away"
PRESET_CUSTOM = "custom"
PRESET_AUTO = "auto"
PRESET_SCHEDULE = "schedule"

# =============================================================================
# SICAKLIK LİMİTLERİ
# =============================================================================
MIN_TEMP = 5.0
MAX_TEMP = 32.0
TEMP_STEP = 0.5

# =============================================================================
# GÜNCELLEME ARALIĞI
# Her 10 saniyede bir API'den veri çekilecek
# =============================================================================
SCAN_INTERVAL = timedelta(seconds=10)
