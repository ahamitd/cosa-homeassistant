"""COSA Smart Thermostat Integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CosaAPI, CosaAPIError
from .const import DOMAIN, PLATFORMS, CONF_ENDPOINT_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kur."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    endpoint_id = entry.data.get(CONF_ENDPOINT_ID)
    
    try:
        # Login
        login_result = await api.login(email, password)
        if not login_result.get("ok"):
            _LOGGER.error("Giriş başarısız")
            return False
        
        token = login_result.get("token")
        
        # Endpoint ID yoksa ilk cihazı al
        if not endpoint_id:
            endpoints = await api.get_endpoints(token)
            if not endpoints:
                _LOGGER.error("Cihaz bulunamadı")
                return False
            endpoint_id = endpoints[0].get("id")
        
        # Detaylı bilgi al
        detail = await api.get_endpoint_detail(endpoint_id, token)
        
        # Hava durumu al
        place_id = detail.get("place")
        forecast = {}
        if place_id:
            forecast = await api.get_forecast(place_id, token)
        
        hass.data[DOMAIN][entry.entry_id] = {
            "api": api,
            "email": email,
            "password": password,
            "token": token,
            "endpoint_id": endpoint_id,
            "device_name": detail.get("name", "COSA Termostat"),
            "endpoint_detail": detail,
            "forecast": forecast,
            "place_id": place_id,
        }
        
    except CosaAPIError as err:
        _LOGGER.error("API hatası: %s", err)
        return False
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
