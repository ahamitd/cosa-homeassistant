"""COSA Smart Thermostat Config Flow."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CosaAPI, CosaAPIError, CosaAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Kullanıcı girişini doğrula."""
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    email = data["email"]
    password = data["password"]
    
    _LOGGER.info("COSA login denemesi: %s", email)
    
    # 1. Login yap ve token al
    token = await api.login(email, password)
    _LOGGER.info("Login başarılı, token alındı")
    
    # 2. Endpoint'leri al
    endpoints = await api.get_endpoints(token)
    _LOGGER.info("Endpoint sayısı: %d", len(endpoints))
    
    if not endpoints:
        _LOGGER.error("Kullanıcıya ait endpoint bulunamadı")
        raise CannotConnect("Cihaz bulunamadı")
    
    # İlk endpoint'i kullan
    first_endpoint = endpoints[0]
    endpoint_id = first_endpoint.get("id") or first_endpoint.get("_id")
    device_name = first_endpoint.get("name", "COSA Termostat")
    
    _LOGGER.info("Endpoint bulundu: id=%s, name=%s", endpoint_id, device_name)
    
    return {
        "title": f"COSA Termostat ({email})",
        "token": token,
        "endpoint_id": endpoint_id,
        "device_name": device_name,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """COSA config flow handler."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """İlk kurulum adımı."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                await self.async_set_unique_id(user_input["email"])
                self._abort_if_unique_id_configured()
                
                entry_data = {
                    "email": user_input["email"],
                    "password": user_input["password"],
                    "token": info["token"],
                    "endpoint_id": info["endpoint_id"],
                    "device_name": info["device_name"],
                }
                
                return self.async_create_entry(
                    title=info["title"],
                    data=entry_data,
                )
                
            except CosaAuthError as err:
                _LOGGER.error("Kimlik doğrulama hatası: %s", err)
                errors["base"] = "invalid_auth"
            except CosaAPIError as err:
                _LOGGER.error("API hatası: %s", err)
                errors["base"] = "cannot_connect"
            except CannotConnect as err:
                _LOGGER.error("Bağlantı hatası: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Beklenmeyen hata: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Bağlantı kurulamadı hatası."""


class InvalidAuth(HomeAssistantError):
    """Geçersiz kimlik bilgileri hatası."""
