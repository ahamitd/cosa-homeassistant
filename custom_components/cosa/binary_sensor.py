"""COSA Binary Sensor Platform."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Binary sensor platformunu kur."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        CosaConnectedSensor(coordinator, config_entry),
        CosaHeatingSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class CosaBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """COSA Base Binary Sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, config_entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}


class CosaConnectedSensor(CosaBaseBinarySensor):
    """Bağlantı Durumu Sensörü."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "connected", "Bağlantı")

    @property
    def is_on(self) -> bool:
        device = self._endpoint.get("device", {})
        return device.get("isConnected", False)


class CosaHeatingSensor(CosaBaseBinarySensor):
    """Isıtma Durumu Sensörü."""

    _attr_device_class = BinarySensorDeviceClass.HEAT

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "heating", "Isıtma")

    @property
    def is_on(self) -> bool:
        return self._endpoint.get("combiState") == "on"
