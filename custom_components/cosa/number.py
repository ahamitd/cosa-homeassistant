"""COSA Number Platform."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CALIBRATION_MIN,
    CALIBRATION_MAX,
    CALIBRATION_STEP,
)

_LOGGER = logging.getLogger(__name__)

TEMPERATURE_MIN = 5.0
TEMPERATURE_MAX = 32.0
TEMPERATURE_STEP = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Number platformunu kur."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        CosaCalibrationNumber(coordinator, config_entry),
        CosaHomeTemperatureNumber(coordinator, config_entry),
        CosaAwayTemperatureNumber(coordinator, config_entry),
        CosaSleepTemperatureNumber(coordinator, config_entry),
        CosaCustomTemperatureNumber(coordinator, config_entry),
        CosaCombiWorkRangeNumber(coordinator, config_entry),
        CosaCombiStopRangeNumber(coordinator, config_entry),
        CosaOpenWindowDurationNumber(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class CosaCalibrationNumber(CoordinatorEntity, NumberEntity):
    """Sıcaklık Kalibrasyonu Number Entity."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = CALIBRATION_MIN
    _attr_native_max_value = CALIBRATION_MAX
    _attr_native_step = CALIBRATION_STEP
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:thermometer-check"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_calibration"
        self._attr_name = "Sıcaklık Kalibrasyonu"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_value: float | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def native_value(self) -> float | None:
        if self._optimistic_value is not None:
            return self._optimistic_value
        val = self._endpoint.get("calibration")
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator güncellemesini işle."""
        val = self._endpoint.get("calibration")
        try:
            real_value = float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            real_value = 0.0
        if self._optimistic_value is not None:
            if abs(real_value - self._optimistic_value) < 0.05:
                self._optimistic_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Kalibrasyonu ayarla."""
        self._optimistic_value = value
        self.async_write_ha_state()
        result = await self.coordinator.async_set_calibration(value)
        if not result:
            self._optimistic_value = None
            self.async_write_ha_state()


class CosaTemperatureNumberBase(CoordinatorEntity, NumberEntity):
    """Base class for temperature number entities."""

    _attr_has_entity_name = True
    _attr_native_min_value = TEMPERATURE_MIN
    _attr_native_max_value = TEMPERATURE_MAX
    _attr_native_step = TEMPERATURE_STEP
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER
    _temp_key: str = ""
    _preset_name: str = ""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_value: float | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def native_value(self) -> float | None:
        if self._optimistic_value is not None:
            return self._optimistic_value
        val = self._endpoint.get(self._temp_key)
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator güncellemesini işle."""
        val = self._endpoint.get(self._temp_key)
        try:
            real_value = float(val) if val is not None else None
        except (ValueError, TypeError):
            real_value = None
        if self._optimistic_value is not None and real_value is not None:
            if abs(real_value - self._optimistic_value) < 0.25:
                self._optimistic_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Sıcaklığı ayarla."""
        self._optimistic_value = value
        self.async_write_ha_state()
        result = await self.coordinator.async_set_preset_temperature(self._preset_name, value)
        if not result:
            self._optimistic_value = None
            self.async_write_ha_state()


class CosaHomeTemperatureNumber(CosaTemperatureNumberBase):
    """Evdeyim Sıcaklığı Number Entity."""

    _temp_key = "homeTemperature"
    _preset_name = "home"
    _attr_icon = "mdi:home-thermometer"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_home_temperature"
        self._attr_name = "Evdeyim Sıcaklığı"


class CosaAwayTemperatureNumber(CosaTemperatureNumberBase):
    """Dışarıdayım Sıcaklığı Number Entity."""

    _temp_key = "awayTemperature"
    _preset_name = "away"
    _attr_icon = "mdi:home-export-outline"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_away_temperature"
        self._attr_name = "Dışarıdayım Sıcaklığı"


class CosaSleepTemperatureNumber(CosaTemperatureNumberBase):
    """Uyku Sıcaklığı Number Entity."""

    _temp_key = "sleepTemperature"
    _preset_name = "sleep"
    _attr_icon = "mdi:bed"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_sleep_temperature"
        self._attr_name = "Uyku Sıcaklığı"


class CosaCustomTemperatureNumber(CosaTemperatureNumberBase):
    """Özel Sıcaklık Number Entity."""

    _temp_key = "customTemperature"
    _preset_name = "custom"
    _attr_icon = "mdi:thermometer-lines"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_custom_temperature"
        self._attr_name = "Özel Sıcaklık"


class CosaCombiWorkRangeNumber(CoordinatorEntity, NumberEntity):
    """Kombi Çalışma Aralığı (pidWindowLow) Number Entity."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 2.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:radiator"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_combi_work_range"
        self._attr_name = "Kombi Çalışma Aralığı"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_value: float | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def native_value(self) -> float | None:
        if self._optimistic_value is not None:
            return self._optimistic_value
        val = self._endpoint.get("pidWindowLow")
        if val is None:
            val = self._endpoint.get("combiSettings", {}).get("pidWindowLow", 0.1)
        return float(val) if val is not None else 0.1

    @callback
    def _handle_coordinator_update(self) -> None:
        real_value = self._endpoint.get("pidWindowLow")
        if real_value is None:
            real_value = self._endpoint.get("combiSettings", {}).get("pidWindowLow", 0.1)
        if self._optimistic_value is not None and real_value is not None:
            if abs(float(real_value) - self._optimistic_value) < 0.05:
                self._optimistic_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Çalışma aralığını ayarla."""
        self._optimistic_value = value
        self.async_write_ha_state()
        high = self._endpoint.get("pidWindowHigh")
        if high is None:
            high = self._endpoint.get("combiSettings", {}).get("pidWindowHigh", 0.2)
        result = await self.coordinator.async_set_combi_range(value, float(high or 0.2))
        if not result:
            self._optimistic_value = None
            self.async_write_ha_state()


class CosaCombiStopRangeNumber(CoordinatorEntity, NumberEntity):
    """Kombi Durma Aralığı (pidWindowHigh) Number Entity."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 2.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:radiator-disabled"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_combi_stop_range"
        self._attr_name = "Kombi Durma Aralığı"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_value: float | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def native_value(self) -> float | None:
        if self._optimistic_value is not None:
            return self._optimistic_value
        val = self._endpoint.get("pidWindowHigh")
        if val is None:
            val = self._endpoint.get("combiSettings", {}).get("pidWindowHigh", 0.2)
        return float(val) if val is not None else 0.2

    @callback
    def _handle_coordinator_update(self) -> None:
        real_value = self._endpoint.get("pidWindowHigh")
        if real_value is None:
            real_value = self._endpoint.get("combiSettings", {}).get("pidWindowHigh", 0.2)
        if self._optimistic_value is not None and real_value is not None:
            if abs(float(real_value) - self._optimistic_value) < 0.05:
                self._optimistic_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Durma aralığını ayarla."""
        self._optimistic_value = value
        self.async_write_ha_state()
        low = self._endpoint.get("pidWindowLow")
        if low is None:
            low = self._endpoint.get("combiSettings", {}).get("pidWindowLow", 0.1)
        result = await self.coordinator.async_set_combi_range(float(low or 0.1), value)
        if not result:
            self._optimistic_value = None
            self.async_write_ha_state()


class CosaOpenWindowDurationNumber(CoordinatorEntity, NumberEntity):
    """Açık Pencere Kapalı Kalma Süresi Number Entity (15 - 90 dk)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 15
    _attr_native_max_value = 90
    _attr_native_step = 15
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_open_window_duration"
        self._attr_name = "Açık Pencere Süresi"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_value: int | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def native_value(self) -> int | None:
        if self._optimistic_value is not None:
            return self._optimistic_value
        val = self._endpoint.get("openWindowDuration")
        return int(val) if val is not None else 15

    @callback
    def _handle_coordinator_update(self) -> None:
        real_value = self._endpoint.get("openWindowDuration")
        if self._optimistic_value is not None and real_value is not None:
            if int(real_value) == self._optimistic_value:
                self._optimistic_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Kapalı kalma süresini ayarla."""
        val = int(value)
        self._optimistic_value = val
        self.async_write_ha_state()
        result = await self.coordinator.async_set_open_window_duration(val)
        if not result:
            self._optimistic_value = None
            self.async_write_ha_state()
