"""COSA Smart Thermostat API Client."""

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
    ENDPOINT_GET_FORECAST,
    ENDPOINT_SET_COMBI_SETTINGS,
    ENDPOINT_SET_DEVICE_SETTINGS,
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

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._session = session
        self._own_session = False
        self._token: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Session al veya oluştur."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Kendi oluşturduğumuz session'ı kapat."""
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    def _get_base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": HEADER_USER_AGENT,
            "Content-Type": HEADER_CONTENT_TYPE,
            "provider": HEADER_PROVIDER,
            "Accept": "*/*",
        }

    def _get_auth_headers(self, token: Optional[str] = None) -> dict[str, str]:
        headers = self._get_base_headers()
        use_token = token or self._token
        if use_token:
            headers["authtoken"] = use_token
        return headers

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Login ve token al."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_LOGIN}"
        payload = {"email": email, "password": password}
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_base_headers(),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    return {"ok": False, "code": error_code}
                
                token = data.get("authToken")
                if token:
                    self._token = token
                
                return {"ok": True, "token": token}
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_endpoints(self, token: Optional[str] = None) -> list[dict[str, Any]]:
        """Endpoint listesini al."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINTS}"
        
        try:
            async with session.post(
                url, json={}, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    return []
                
                return data.get("endpoints", [])
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_endpoint_detail(self, endpoint_id: str, token: Optional[str] = None) -> dict[str, Any]:
        """Endpoint detaylarını al."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINT}"
        payload = {"endpoint": endpoint_id}
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    raise CosaAPIError(f"API hatası: {data.get('code')}")
                
                return data.get("endpoint", {})
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_forecast(self, place_id: str, token: Optional[str] = None) -> dict[str, Any]:
        """Hava durumu tahminini al."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_GET_FORECAST}"
        payload = {"place": place_id}
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    return {}
                
                
                _LOGGER.debug("Rapor verisi alındı - keys: %s", list(data.keys()) if data else "None")
                # report içindeki yapıyı kontrol et
                report = data.get("report", {})
                if report:
                    _LOGGER.debug("Rapor verisi - report keys: %s", list(report.keys()) if isinstance(report, dict) else "list/other")
                    if isinstance(report, dict):
                        _LOGGER.debug("Rapor verisi - report.stats: %s", bool(report.get("stats")))
                        _LOGGER.debug("Rapor verisi - report.summary: %s", bool(report.get("summary")))
                return data
                
        except aiohttp.ClientError:
            return {}

    async def set_mode(
        self, endpoint_id: str, mode: str, option: Optional[str] = None, token: Optional[str] = None
    ) -> bool:
        """Mod değiştir."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_SET_MODE}"
        payload: dict[str, Any] = {"endpoint": endpoint_id, "mode": mode}
        if option:
            payload["option"] = option
        
        _LOGGER.debug("set_mode payload: %s", payload)
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                _LOGGER.debug("set_mode response: %s", data)
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_target_temperatures(
        self, endpoint_id: str,
        home: float, away: float, sleep: float, custom: float,
        token: Optional[str] = None
    ) -> bool:
        """Hedef sıcaklıkları ayarla."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_SET_TARGET_TEMPERATURES}"
        payload = {
            "endpoint": endpoint_id,
            "targetTemperatures": {
                "home": home, "away": away, "sleep": sleep, "custom": custom
            }
        }
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                _LOGGER.debug("set_target_temperatures response: %s", data)
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_combi_settings(
        self, endpoint_id: str, 
        child_lock: bool,
        heating: bool = True,
        token: Optional[str] = None
    ) -> bool:
        """Kombi ayarlarını (çocuk kilidi, ısıtma) ayarla."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_SET_COMBI_SETTINGS}"
        payload = {
            "endpoint": endpoint_id,
            "combiSettings": {
                "childLock": child_lock,
                "heating": heating
            }
        }
        
        _LOGGER.debug("set_combi_settings payload: %s", payload)
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                _LOGGER.debug("set_combi_settings response: %s", data)
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            _LOGGER.error("set_combi_settings error: %s", err)
            return False

    async def set_device_settings(
        self, endpoint_id: str, 
        calibration: float,
        open_window_enable: Optional[bool] = None,
        open_window_duration: int = 30,
        token: Optional[str] = None
    ) -> bool:
        """Cihaz ayarlarını (kalibrasyon, açık pencere) ayarla."""
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_SET_DEVICE_SETTINGS}"
        payload: dict[str, Any] = {
            "endpoint": endpoint_id,
            "calibration": calibration,
        }
        
        if open_window_enable is not None:
            payload["openWindowEnable"] = open_window_enable
            if open_window_enable:
                payload["openWindowDuration"] = open_window_duration
        
        _LOGGER.debug("set_device_settings payload: %s", payload)
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                _LOGGER.debug("set_device_settings response: %s", data)
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            _LOGGER.error("set_device_settings error: %s", err)
            return False

    async def get_reports(self, endpoint_id: str, token: Optional[str] = None) -> dict[str, Any]:
        """Rapor verilerini al (son 24 saat)."""
        from .const import ENDPOINT_GET_REPORTS
        session = await self._get_session()
        url = f"{API_BASE_URL}{ENDPOINT_GET_REPORTS}"
        payload = {"endpoint": endpoint_id}
        
        try:
            async with session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    _LOGGER.warning("Rapor verisi alınamadı")
                    return {}
                
                
                _LOGGER.debug("Rapor verisi alındı - keys: %s", list(data.keys()) if data else "None")
                # report içindeki yapıyı kontrol et
                report = data.get("report", {})
                if report:
                    _LOGGER.debug("Rapor verisi - report keys: %s", list(report.keys()) if isinstance(report, dict) else "list/other")
                    if isinstance(report, dict):
                        _LOGGER.debug("Rapor verisi - report.stats: %s", bool(report.get("stats")))
                        _LOGGER.debug("Rapor verisi - report.summary: %s", bool(report.get("summary")))
                return data
                
        except aiohttp.ClientError as err:
            _LOGGER.warning("Rapor verisi alınamadı: %s", err)
            return {}
