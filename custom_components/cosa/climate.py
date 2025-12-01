"""COSA Climate Platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, MIN_TEMP, MAX_TEMP, TEMP_STEP,
    MODE_MANUAL, MODE_AUTO, MODE_SCHEDULE,
    OPTION_HOME, OPTION_SLEEP, OPTION_AWAY, OPTION_CUSTOM, OPTION_FROZEN,
)

_LOGGER = logging.getLogger(__name__)

# Türkçe Preset İsimleri
PRESET_EVDE = "Evde"
PRESET_UYKU = "Uyku"
PRESET_DISARI = "Dışarı"
PRESET_MANUEL = "Manuel"
PRESET_OTOMATIK = "Otomatik"
PRESET_HAFTALIK = "Haftalık"

# API değerlerinden Türkçe preset'e dönüşüm
OPTION_TO_PRESET = {
    OPTION_HOME: PRESET_EVDE,
    OPTION_SLEEP: PRESET_UYKU,
    OPTION_AWAY: PRESET_DISARI,
    OPTION_CUSTOM: PRESET_MANUEL,
}

# Türkçe preset'ten API değerine dönüşüm
PRESET_TO_OPTION = {
    PRESET_EVDE: OPTION_HOME,
    PRESET_UYKU: OPTION_SLEEP,
    PRESET_DISARI: OPTION_AWAY,
    PRESET_MANUEL: OPTION_CUSTOM,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Climate platformunu kur."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([CosaClimate(coordinator, config_entry)])


class CosaClimate(CoordinatorEntity, ClimateEntity):
    """COSA Climate Entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = [PRESET_EVDE, PRESET_UYKU, PRESET_DISARI, PRESET_MANUEL, PRESET_OTOMATIK, PRESET_HAFTALIK]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer="COSA",
            model="Smart Thermostat",
        )

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def _forecast(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("forecast", {})
        return {}

    @property
    def current_temperature(self) -> float | None:
        return self._endpoint.get("temperature")

    @property
    def current_humidity(self) -> int | None:
        humidity = self._endpoint.get("humidity")
        return round(humidity) if humidity else None

    @property
    def target_temperature(self) -> float | None:
        return self._endpoint.get("targetTemperature")

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self._endpoint.get("mode")
        if mode == MODE_MANUAL:
            option = self._endpoint.get("option")
            if option == OPTION_FROZEN:
                return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        combi_state = self._endpoint.get("combiState")
        if combi_state == "on":
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        if mode == MODE_SCHEDULE:
            return PRESET_HAFTALIK
        elif mode == MODE_AUTO:
            return PRESET_OTOMATIK
        elif mode == MODE_MANUAL:
            return OPTION_TO_PRESET.get(option, PRESET_EVDE)
        return OPTION_TO_PRESET.get(option, PRESET_EVDE)

    @property
    def icon(self) -> str:
        """Mod ve duruma göre ikon döndür."""
        combi_state = self._endpoint.get("combiState")
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        # Isıtılıyorsa alev ikonu
        if combi_state == "on":
            return "mdi:fire"
        
        # Kapalıysa
        if mode == MODE_MANUAL and option == OPTION_FROZEN:
            return "mdi:snowflake"
        
        # Preset'e göre ikon
        if mode == MODE_SCHEDULE:
            return "mdi:calendar-clock"  # Haftalık - takvim
        elif mode == MODE_AUTO:
            return "mdi:thermostat-auto"  # Otomatik
        elif mode == MODE_MANUAL:
            if option == OPTION_HOME:
                return "mdi:home-thermometer"  # Evde
            elif option == OPTION_SLEEP:
                return "mdi:bed"  # Uyku
            elif option == OPTION_AWAY:
                return "mdi:exit-run"  # Dışarı
            elif option == OPTION_CUSTOM:
                return "mdi:tune"  # Manuel (ayar)
        
        return "mdi:thermostat"

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_FROZEN)
        else:
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_HOME)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_HAFTALIK:
            await self.coordinator.async_set_mode(MODE_SCHEDULE)
        elif preset_mode == PRESET_OTOMATIK:
            await self.coordinator.async_set_mode(MODE_AUTO)
        else:
            option = PRESET_TO_OPTION.get(preset_mode, OPTION_HOME)
            await self.coordinator.async_set_mode(MODE_MANUAL, option)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        option = self._endpoint.get("option", OPTION_HOME)
        
        home = self._endpoint.get("homeTemperature", 21)
        away = self._endpoint.get("awayTemperature", 15)
        sleep = self._endpoint.get("sleepTemperature", 19)
        custom = self._endpoint.get("customTemperature", 20)
        
        if option == OPTION_HOME:
            home = temperature
        elif option == OPTION_AWAY:
            away = temperature
        elif option == OPTION_SLEEP:
            sleep = temperature
        elif option == OPTION_CUSTOM:
            custom = temperature
        else:
            home = temperature
        
        await self.coordinator.async_set_temperatures(home, away, sleep, custom)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._endpoint.get("device", {})
        forecast_data = self._forecast.get("hourly", [{}])
        current_weather = forecast_data[0] if forecast_data else {}
        
        return {
            "mode": self._endpoint.get("mode"),
            "option": self._endpoint.get("option"),
            "combi_state": self._endpoint.get("combiState"),
            "home_temperature": self._endpoint.get("homeTemperature"),
            "away_temperature": self._endpoint.get("awayTemperature"),
            "sleep_temperature": self._endpoint.get("sleepTemperature"),
            "custom_temperature": self._endpoint.get("customTemperature"),
            "firmware_version": device.get("version"),
            "battery_voltage": self._endpoint.get("batteryVoltage"),
            "power_state": self._endpoint.get("powerState"),
            "rssi": self._endpoint.get("rssi"),
            "child_lock": self._endpoint.get("childLock"),
            "open_window_state": self._endpoint.get("openWindowState"),
            "outdoor_temperature": current_weather.get("temperature"),
            "outdoor_humidity": current_weather.get("humidity"),
            "weather_icon": current_weather.get("icon"),
        }
