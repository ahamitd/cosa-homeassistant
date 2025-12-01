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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CosaAPI, CosaAPIError, CosaAuthError
from .const import (
    DOMAIN, SCAN_INTERVAL, MIN_TEMP, MAX_TEMP, TEMP_STEP,
    MODE_MANUAL, MODE_AUTO, MODE_SCHEDULE,
    OPTION_HOME, OPTION_SLEEP, OPTION_AWAY, OPTION_CUSTOM, OPTION_FROZEN,
    PRESET_HOME, PRESET_SLEEP, PRESET_AWAY, PRESET_CUSTOM, PRESET_AUTO, PRESET_SCHEDULE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Climate platformunu kur."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    coordinator = CosaCoordinator(hass, config_entry, entry_data)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    
    async_add_entities([CosaClimate(coordinator, config_entry)])


class CosaCoordinator(DataUpdateCoordinator):
    """COSA Koordinatör."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, entry_data: dict) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        
        self.config_entry = config_entry
        self._email = entry_data["email"]
        self._password = entry_data["password"]
        self._token = entry_data["token"]
        self._endpoint_id = entry_data["endpoint_id"]
        self._device_name = entry_data.get("device_name", "COSA Termostat")
        self._place_id = entry_data.get("place_id")
        
        self._api = CosaAPI(async_get_clientsession(hass))

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            detail = await self._api.get_endpoint_detail(self._endpoint_id, self._token)
            
            # Hava durumu
            forecast = {}
            if self._place_id:
                forecast = await self._api.get_forecast(self._place_id, self._token)
            
            return {
                "endpoint": detail,
                "forecast": forecast,
            }
            
        except CosaAuthError:
            login_result = await self._api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                detail = await self._api.get_endpoint_detail(self._endpoint_id, self._token)
                return {"endpoint": detail, "forecast": {}}
            raise UpdateFailed("Giriş başarısız")
            
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err

    async def async_set_mode(self, mode: str, option: str | None = None) -> None:
        try:
            await self._api.set_mode(self._endpoint_id, mode, option, self._token)
            await self.async_request_refresh()
        except CosaAuthError:
            login_result = await self._api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                await self._api.set_mode(self._endpoint_id, mode, option, self._token)
                await self.async_request_refresh()

    async def async_set_temperatures(self, home: float, away: float, sleep: float, custom: float) -> None:
        try:
            await self._api.set_target_temperatures(self._endpoint_id, home, away, sleep, custom, self._token)
            await self.async_request_refresh()
        except CosaAuthError:
            login_result = await self._api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                await self._api.set_target_temperatures(self._endpoint_id, home, away, sleep, custom, self._token)
                await self.async_request_refresh()


class CosaClimate(CoordinatorEntity, ClimateEntity):
    """COSA Climate Entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = [PRESET_HOME, PRESET_SLEEP, PRESET_AWAY, PRESET_CUSTOM, PRESET_AUTO, PRESET_SCHEDULE]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP

    def __init__(self, coordinator: CosaCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator._device_name,
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
            return PRESET_SCHEDULE
        elif mode == MODE_AUTO:
            return PRESET_AUTO
        elif mode == MODE_MANUAL:
            return option
        return option

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_FROZEN)
        else:
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_HOME)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_SCHEDULE:
            await self.coordinator.async_set_mode(MODE_SCHEDULE)
        elif preset_mode == PRESET_AUTO:
            await self.coordinator.async_set_mode(MODE_AUTO)
        else:
            await self.coordinator.async_set_mode(MODE_MANUAL, preset_mode)

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
