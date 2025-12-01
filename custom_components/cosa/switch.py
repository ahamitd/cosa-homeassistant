"""COSA Switch Platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Switch platformunu kur."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data.get("coordinator")
    api = entry_data.get("api")
    endpoint_id = entry_data.get("endpoint_id")
    token = entry_data.get("token")
    
    if not coordinator or not api or not endpoint_id:
        return
    
    entities = [
        CosaChildLockSwitch(coordinator, config_entry, api, endpoint_id, token),
    ]
    
    async_add_entities(entities)


class CosaChildLockSwitch(CoordinatorEntity, SwitchEntity):
    """Çocuk Kilidi Switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:lock-outline"

    def __init__(self, coordinator, config_entry: ConfigEntry, api, endpoint_id: str, token: str) -> None:
        super().__init__(coordinator)
        self._api = api
        self._endpoint_id = endpoint_id
        self._token = token
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_child_lock"
        self._attr_name = "Çocuk Kilidi"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def is_on(self) -> bool:
        return self._endpoint.get("childLock", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Çocuk kilidini aç."""
        try:
            await self._api.set_child_lock(self._endpoint_id, True, self._token)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Çocuk kilidi açılamadı: %s", ex)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Çocuk kilidini kapat."""
        try:
            await self._api.set_child_lock(self._endpoint_id, False, self._token)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Çocuk kilidi kapatılamadı: %s", ex)
