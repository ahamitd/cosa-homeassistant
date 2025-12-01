"""COSA Config Flow."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .api import CosaAPI
from .const import DOMAIN, CONF_ENDPOINT_ID

_LOGGER = logging.getLogger(__name__)


class CosaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """COSA config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._email: str | None = None
        self._password: str | None = None
        self._token: str | None = None
        self._endpoints: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """İlk adım - kullanıcı bilgileri."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            api = CosaAPI()
            try:
                # Login
                login_result = await api.login(email, password)
                
                if not login_result.get("ok"):
                    errors["base"] = "invalid_auth"
                else:
                    self._email = email
                    self._password = password
                    self._token = login_result.get("token")
                    
                    # Endpoint'leri al
                    endpoints = await api.get_endpoints()
                    if endpoints:
                        self._endpoints = endpoints
                        
                        if len(endpoints) == 1:
                            # Tek cihaz varsa direkt ekle
                            endpoint = endpoints[0]
                            return self.async_create_entry(
                                title=endpoint.get("name", "COSA"),
                                data={
                                    CONF_EMAIL: email,
                                    CONF_PASSWORD: password,
                                    CONF_ENDPOINT_ID: endpoint.get("id"),
                                },
                            )
                        else:
                            # Birden fazla cihaz varsa seçtir
                            return await self.async_step_select_endpoint()
                    else:
                        errors["base"] = "no_devices"
            except Exception as ex:
                _LOGGER.error("Login hatası: %s", ex)
                errors["base"] = "cannot_connect"
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_endpoint(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Cihaz seçimi adımı."""
        if user_input is not None:
            endpoint_id = user_input[CONF_ENDPOINT_ID]
            
            # Seçilen endpoint'in ismini bul
            endpoint_name = "COSA"
            for ep in self._endpoints:
                if ep.get("id") == endpoint_id:
                    endpoint_name = ep.get("name", "COSA")
                    break
            
            return self.async_create_entry(
                title=endpoint_name,
                data={
                    CONF_EMAIL: self._email,
                    CONF_PASSWORD: self._password,
                    CONF_ENDPOINT_ID: endpoint_id,
                },
            )

        # Endpoint seçeneklerini oluştur
        endpoint_options = {
            ep.get("id"): ep.get("name", f"Cihaz {i+1}")
            for i, ep in enumerate(self._endpoints)
        }

        return self.async_show_form(
            step_id="select_endpoint",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENDPOINT_ID): vol.In(endpoint_options),
                }
            ),
        )
