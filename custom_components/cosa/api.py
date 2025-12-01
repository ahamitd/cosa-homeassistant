"""COSA Smart Thermostat API Client.

Bu modül COSA termostat API'si ile iletişimi sağlar.
Tüm endpoint'ler ve request body yapıları gerçek mobil uygulama
trafiğinden alınmıştır.

API Endpoint'leri:
- POST /api/users/login → JWT Token alma
- POST /api/endpoints/getEndpoints → Cihaz listesi
- POST /api/endpoints/getEndpoint → Tek cihaz detayı
- POST /api/endpoints/setMode → Mod değiştirme
- POST /api/endpoints/setTargetTemperatures → Sıcaklık ayarı
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ENDPOINT_LOGIN,
    ENDPOINT_GET_ENDPOINTS,
    ENDPOINT_GET_ENDPOINT,
    ENDPOINT_SET_MODE,
    ENDPOINT_SET_TARGET_TEMPERATURES,
    HEADER_USER_AGENT,
    HEADER_CONTENT_TYPE,
    HEADER_PROVIDER,
)

_LOGGER = logging.getLogger(__name__)


class CosaAPIError(Exception):
    """COSA API hatası."""
    pass


class CosaAuthError(CosaAPIError):
    """Kimlik doğrulama hatası."""
    pass


class CosaAPI:
    """COSA Termostat API İstemcisi."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """API istemcisini başlat."""
        self._session = session

    def _get_base_headers(self) -> dict[str, str]:
        """Temel HTTP header'larını döndür."""
        return {
            "User-Agent": HEADER_USER_AGENT,
            "Content-Type": HEADER_CONTENT_TYPE,
            "provider": HEADER_PROVIDER,
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }

    def _get_auth_headers(self, token: str) -> dict[str, str]:
        """Kimlik doğrulamalı header'ları döndür."""
        headers = self._get_base_headers()
        headers["authtoken"] = token
        return headers

    async def login(self, email: str, password: str) -> str:
        """Kullanıcı girişi yap ve JWT token al.
        
        API Request:
            POST https://kiwi-api.nuvia.com.tr/api/users/login
            Body: {"email": "<email>", "password": "<password>"}
        """
        url = f"{API_BASE_URL}{ENDPOINT_LOGIN}"
        
        payload = {
            "email": email,
            "password": password,
        }
        
        _LOGGER.debug("Login isteği gönderiliyor: %s", url)
        _LOGGER.debug("Login payload: email=%s", email)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_base_headers(),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("Login yanıtı: status=%s, body=%s", response.status, response_text[:500])
                
                # HTTP 401 = Unauthorized
                if response.status == 401:
                    _LOGGER.error("Geçersiz kimlik bilgileri (HTTP 401)")
                    raise CosaAuthError("Geçersiz e-posta veya şifre")
                
                # HTTP 200 ama içeride hata olabilir
                if response.status == 200:
                    try:
                        data = await response.json()
                    except Exception as e:
                        _LOGGER.error("JSON parse hatası: %s", e)
                        raise CosaAPIError(f"API yanıtı parse edilemedi: {response_text[:200]}")
                    
                    # API ok:0 dönerse hata var demektir
                    if isinstance(data, dict) and data.get("ok") == 0:
                        error_code = data.get("code", "unknown")
                        _LOGGER.error("API hata döndürdü: ok=0, code=%s", error_code)
                        # code 111 genellikle yanlış şifre/email
                        if error_code == 111:
                            raise CosaAuthError("Geçersiz e-posta veya şifre")
                        raise CosaAPIError(f"API hatası: code={error_code}")
                    
                    # Token'ı yanıttan çıkar
                    token = self._extract_token(data)
                    if not token:
                        _LOGGER.error("Token yanıtta bulunamadı: %s", data)
                        raise CosaAPIError("Token yanıtta bulunamadı")
                    
                    _LOGGER.info("COSA API'ye başarıyla giriş yapıldı")
                    return token
                
                # Diğer HTTP hataları
                _LOGGER.error("Login hatası: HTTP %s - %s", response.status, response_text[:200])
                raise CosaAPIError(f"Login başarısız: HTTP {response.status}")
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    def _extract_token(self, data: dict) -> Optional[str]:
        """API yanıtından token'ı çıkar."""
        # Olası token alanları
        token_keys = ["authtoken", "authToken", "token", "accessToken", "access_token"]
        
        # Doğrudan üst seviyede ara
        for key in token_keys:
            if key in data and isinstance(data[key], str):
                return data[key]
        
        # data wrapper içinde ara
        if "data" in data and isinstance(data["data"], dict):
            for key in token_keys:
                if key in data["data"] and isinstance(data["data"][key], str):
                    return data["data"][key]
        
        return None

    async def get_endpoints(self, token: str) -> list[dict[str, Any]]:
        """Kullanıcının tüm cihazlarını (endpoint'lerini) al."""
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINTS}"
        
        _LOGGER.debug("GetEndpoints isteği gönderiliyor: %s", url)
        
        try:
            async with self._session.post(
                url,
                json={},
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("GetEndpoints yanıtı: status=%s", response.status)
                
                if response.status == 401:
                    _LOGGER.warning("Token geçersiz veya süresi dolmuş")
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    _LOGGER.error("GetEndpoints hatası: %s - %s", response.status, response_text[:200])
                    raise CosaAPIError(f"GetEndpoints başarısız: HTTP {response.status}")
                
                data = await response.json()
                
                # API ok:0 dönerse hata var
                if isinstance(data, dict) and data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    _LOGGER.error("GetEndpoints API hatası: code=%s", error_code)
                    raise CosaAPIError(f"GetEndpoints hatası: code={error_code}")
                
                endpoints = data.get("endpoints", [])
                _LOGGER.debug("GetEndpoints yanıtı: %d endpoint bulundu", len(endpoints))
                return endpoints
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_endpoint_detail(self, token: str, endpoint_id: str) -> dict[str, Any]:
        """Tek bir endpoint'in detaylı bilgisini al."""
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINT}"
        
        payload = {"endpoint": endpoint_id}
        
        _LOGGER.debug("GetEndpoint isteği: %s - endpoint=%s", url, endpoint_id)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("GetEndpoint hatası: %s - %s", response.status, response_text[:200])
                    raise CosaAPIError(f"GetEndpoint başarısız: HTTP {response.status}")
                
                data = await response.json()
                
                if isinstance(data, dict) and data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    _LOGGER.error("GetEndpoint API hatası: code=%s", error_code)
                    raise CosaAPIError(f"GetEndpoint hatası: code={error_code}")
                
                return data.get("endpoint", data)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_mode(
        self,
        token: str,
        endpoint_id: str,
        mode: str,
        option: Optional[str] = None,
    ) -> bool:
        """Termostat modunu değiştir.
        
        Args:
            token: JWT auth token
            endpoint_id: Cihaz ID'si
            mode: "manual", "auto" veya "schedule"
            option: Manual mod için: "home", "sleep", "away", "custom", "frozen"
        """
        url = f"{API_BASE_URL}{ENDPOINT_SET_MODE}"
        
        payload: dict[str, Any] = {
            "endpoint": endpoint_id,
            "mode": mode,
        }
        
        # Manual mod için option gerekli
        if option:
            payload["option"] = option
        
        _LOGGER.debug("SetMode isteği: %s - payload=%s", url, payload)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("SetMode hatası: %s - %s", response.status, response_text[:200])
                    raise CosaAPIError(f"SetMode başarısız: HTTP {response.status}")
                
                data = await response.json()
                
                if isinstance(data, dict) and data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    _LOGGER.error("SetMode API hatası: code=%s", error_code)
                    raise CosaAPIError(f"SetMode hatası: code={error_code}")
                
                _LOGGER.info("Mod başarıyla değiştirildi: mode=%s, option=%s", mode, option)
                return True
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_target_temperatures(
        self,
        token: str,
        endpoint_id: str,
        home: float,
        away: float,
        sleep: float,
        custom: float,
    ) -> bool:
        """Hedef sıcaklıkları ayarla."""
        url = f"{API_BASE_URL}{ENDPOINT_SET_TARGET_TEMPERATURES}"
        
        payload = {
            "endpoint": endpoint_id,
            "targetTemperatures": {
                "home": home,
                "away": away,
                "sleep": sleep,
                "custom": custom,
            },
        }
        
        _LOGGER.debug("SetTargetTemperatures isteği: %s", url)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("SetTargetTemperatures hatası: %s - %s", response.status, response_text[:200])
                    raise CosaAPIError(f"SetTargetTemperatures başarısız: HTTP {response.status}")
                
                data = await response.json()
                
                if isinstance(data, dict) and data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    _LOGGER.error("SetTargetTemperatures API hatası: code=%s", error_code)
                    raise CosaAPIError(f"SetTargetTemperatures hatası: code={error_code}")
                
                _LOGGER.info("Hedef sıcaklıklar ayarlandı")
                return True
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err


def extract_endpoint_state(endpoint: dict[str, Any]) -> dict[str, Any]:
    """Endpoint verisinden durum bilgilerini çıkar.
    
    API yanıt formatı:
    {
        "id": "...",
        "name": "Evim",
        "temperature": 26.5,
        "humidity": 53.4,
        "targetTemperature": 26.6,
        "mode": "schedule",
        "option": "sleep",
        "operationMode": "heating",
        "isConnected": true,
        ...
    }
    """
    mode = endpoint.get("mode", "manual")
    option = endpoint.get("option", "home")
    
    # Sıcaklık hedefleri - detaylı bilgide farklı format
    if "homeTemperature" in endpoint:
        # Detaylı endpoint bilgisi
        target_temps = {
            "home": endpoint.get("homeTemperature", 20.0),
            "away": endpoint.get("awayTemperature", 15.0),
            "sleep": endpoint.get("sleepTemperature", 18.0),
            "custom": endpoint.get("customTemperature", 20.0),
        }
    else:
        # Liste formatı - targetTemperature var
        target_temps = {
            "home": 20.0,
            "away": 15.0,
            "sleep": 18.0,
            "custom": 20.0,
        }
    
    # Mevcut hedef sıcaklık
    current_target = endpoint.get("targetTemperature")
    if current_target is None:
        current_target = target_temps.get(option, 20.0)
    
    # combiState kontrolü
    combi_state = endpoint.get("combiState", "off")
    
    return {
        "endpoint_id": endpoint.get("id") or endpoint.get("_id"),
        "name": endpoint.get("name", "COSA Termostat"),
        "temperature": endpoint.get("temperature"),
        "humidity": endpoint.get("humidity"),
        "target_temperature": current_target,
        "mode": mode,
        "option": option,
        "combi_state": combi_state,
        "is_connected": endpoint.get("isConnected", False),
        "operation_mode": endpoint.get("operationMode", "heating"),
        "target_temperatures": target_temps,
    }
