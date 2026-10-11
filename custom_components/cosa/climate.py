"""COSA Climate Platform."""

from __future__ import annotations

import asyncio
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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, MIN_TEMP, MAX_TEMP, TEMP_STEP,
    MODE_MANUAL, MODE_AUTO, MODE_SCHEDULE, MODE_TURBO, MODE_VENTILATION,
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

# Preset İkonları
PRESET_ICONS = {
    PRESET_EVDE: "mdi:home",
    PRESET_UYKU: "mdi:bed",
    PRESET_DISARI: "mdi:walk",
    PRESET_MANUEL: "mdi:tune",
    PRESET_OTOMATIK: "mdi:thermostat-auto",
    PRESET_HAFTALIK: "mdi:calendar-clock",
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
    _attr_translation_key = "cosa_thermostat"
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
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.data.get("endpoint", {}).get("name", "COSA Termostat") if coordinator.data else "COSA Termostat",
            manufacturer="COSA",
            model="Smart Thermostat",
        )
        # Optimistic update için geçici değerler
        self._optimistic_target_temp: float | None = None
        self._optimistic_preset: str | None = None
        self._optimistic_hvac_mode: HVACMode | None = None

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
        # Optimistic değer varsa onu göster
        if self._optimistic_target_temp is not None:
            return self._optimistic_target_temp
        
        # Cihaz ister manual, auto veya schedule modunda olsun,
        # kombinin referans aldığı hedef o anki aktif profilin (option) sıcaklığıdır.
        option = self._endpoint.get("option")
        if option == OPTION_HOME:
            return self._endpoint.get("homeTemperature")
        elif option == OPTION_AWAY:
            return self._endpoint.get("awayTemperature")
        elif option == OPTION_SLEEP:
            return self._endpoint.get("sleepTemperature")
        elif option == OPTION_CUSTOM:
            return self._endpoint.get("customTemperature")
        
        return self._endpoint.get("targetTemperature")

    @property
    def hvac_mode(self) -> HVACMode:
        # Optimistic değer varsa onu göster
        if self._optimistic_hvac_mode is not None:
            return self._optimistic_hvac_mode
        
        mode = self._endpoint.get("mode")
        if mode == MODE_MANUAL:
            option = self._endpoint.get("option")
            if option == OPTION_FROZEN:
                return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        mode = self._endpoint.get("mode")
        combi_state = self._endpoint.get("combiState")
        if mode == MODE_TURBO or combi_state == "on":
            return HVACAction.HEATING
        elif mode == MODE_VENTILATION:
            return HVACAction.OFF
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        # Optimistic değer varsa onu göster
        if self._optimistic_preset is not None:
            return self._optimistic_preset
            
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        # Otomatik veya Haftalık modda dahi olsak, cihaz aktif olarak dışarıda
        # veya uyku profilindeyse durumun arayüze ve otomasyonlara doğru yansıması için
        # aktif profili önceliklendir.
        if option in (OPTION_AWAY, OPTION_SLEEP):
            return OPTION_TO_PRESET.get(option, PRESET_EVDE)
        
        if mode == MODE_SCHEDULE:
            return PRESET_HAFTALIK
        elif mode == MODE_AUTO:
            return PRESET_OTOMATIK
        elif mode == MODE_MANUAL:
            return OPTION_TO_PRESET.get(option, PRESET_EVDE)
        return OPTION_TO_PRESET.get(option, PRESET_EVDE)

    @property
    def icon(self) -> str:
        """Mod ve duruma göre dinamik ikon döndür."""
        combi_state = self._endpoint.get("combiState")
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        # Isıtılıyorsa alev ikonu
        if combi_state == "on":
            return "mdi:fire"
        
        # Kapalıysa (optimistic veya gerçek)
        if self._optimistic_hvac_mode == HVACMode.OFF:
            return "mdi:snowflake"
        if mode == MODE_MANUAL and option == OPTION_FROZEN:
            return "mdi:snowflake"
        
        # Turbo veya havalandırma aktifse öncelikli ikon
        if mode == MODE_TURBO:
            return "mdi:fire"
        elif mode == MODE_VENTILATION:
            return "mdi:window-open-variant"
        
        # Aktif profile göre dinamik ikon
        if option == OPTION_AWAY:
            return "mdi:walk"
        elif option == OPTION_SLEEP:
            return "mdi:bed"
        elif mode == MODE_SCHEDULE:
            return "mdi:calendar-clock"
        elif mode == MODE_AUTO:
            return "mdi:thermostat-auto"
        elif option == OPTION_HOME:
            return "mdi:home"
        
        current_preset = self.preset_mode
        return PRESET_ICONS.get(current_preset, "mdi:thermostat")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator güncellemesini işle ve optimistic değerleri temizle."""
        # API'den gelen gerçek veriyle optimistic değerleri karşılaştır
        real_target = self._endpoint.get("targetTemperature")
        if self._optimistic_target_temp is not None and real_target == self._optimistic_target_temp:
            self._optimistic_target_temp = None
        
        # HVAC mode kontrolü
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        if mode == MODE_MANUAL and option == OPTION_FROZEN:
            real_hvac_mode = HVACMode.OFF
        else:
            real_hvac_mode = HVACMode.HEAT
        
        if self._optimistic_hvac_mode is not None and real_hvac_mode == self._optimistic_hvac_mode:
            self._optimistic_hvac_mode = None
        
        # Preset kontrolü
        real_preset = None
        if mode == MODE_SCHEDULE:
            real_preset = PRESET_HAFTALIK
        elif mode == MODE_AUTO:
            real_preset = PRESET_OTOMATIK
        else:
            real_preset = OPTION_TO_PRESET.get(option, PRESET_EVDE)
        
        if self._optimistic_preset is not None and real_preset == self._optimistic_preset:
            self._optimistic_preset = None
        
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        # Optimistic update
        self._optimistic_hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            self._optimistic_preset = None  # Preset'i temizle
        self.async_write_ha_state()
        
        if hvac_mode == HVACMode.OFF:
            result = await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_FROZEN)
        else:
            result = await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_HOME)
        
        if not result:
            # API başarısız, optimistic değeri temizle
            self._optimistic_hvac_mode = None
            self._optimistic_preset = None
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        # Optimistic update - preset ve sıcaklık
        self._optimistic_preset = preset_mode
        self._optimistic_hvac_mode = HVACMode.HEAT  # Preset seçildiğinde ısıtma açık
        
        # Preset'e göre sıcaklığı da hemen güncelle
        if preset_mode == PRESET_EVDE:
            self._optimistic_target_temp = self._endpoint.get("homeTemperature", 21)
        elif preset_mode == PRESET_UYKU:
            self._optimistic_target_temp = self._endpoint.get("sleepTemperature", 19)
        elif preset_mode == PRESET_DISARI:
            self._optimistic_target_temp = self._endpoint.get("awayTemperature", 15)
        elif preset_mode == PRESET_MANUEL:
            self._optimistic_target_temp = self._endpoint.get("customTemperature", 20)
        elif preset_mode in (PRESET_OTOMATIK, PRESET_HAFTALIK):
            self._optimistic_target_temp = self._endpoint.get("targetTemperature", 21)
        
        self.async_write_ha_state()
        
        if preset_mode == PRESET_HAFTALIK:
            result = await self.coordinator.async_set_mode(MODE_SCHEDULE)
        elif preset_mode == PRESET_OTOMATIK:
            result = await self.coordinator.async_set_mode(MODE_AUTO)
        else:
            option = PRESET_TO_OPTION.get(preset_mode, OPTION_HOME)
            result = await self.coordinator.async_set_mode(MODE_MANUAL, option)
        
        if not result:
            # API başarısız, optimistic değerleri temizle
            self._optimistic_preset = None
            self._optimistic_hvac_mode = None
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # Optimistic update - hemen UI'ı güncelle
        self._optimistic_target_temp = temperature
        self.async_write_ha_state()
        
        self._optimistic_preset = PRESET_MANUEL

        # Kayıtlı mod preset sıcaklıklarını koru (Evdeyim, Uykudayım, Dışarıdayım ezilmez!)
        home = self._endpoint.get("homeTemperature", 21)
        away = self._endpoint.get("awayTemperature", 15)
        sleep = self._endpoint.get("sleepTemperature", 19)
        # Stepper sadece o anlık (custom) sıcaklığı ayarlar
        custom = temperature
        
        try:
            result = await self.coordinator.async_set_temperatures(home, away, sleep, custom)
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_CUSTOM)
            if not result:
                # API başarısız ama timeout değilse temizle
                _LOGGER.warning("Sıcaklık ayarı başarısız, optimistic değer korunuyor")
        except asyncio.TimeoutError:
            # Timeout - optimistic değeri koru, arka planda işlenebilir
            _LOGGER.warning("API timeout - sıcaklık ayarı arka planda işleniyor")
        except Exception as err:
            _LOGGER.error("Sıcaklık ayarı hatası: %s", err)
            self._optimistic_target_temp = None
            self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._endpoint.get("device", {})
        forecast_data = self._forecast.get("hourly", [{}])
        current_weather = forecast_data[0] if forecast_data else {}
        
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        # Preset ikonu bilgisini ekle
        current_preset = self.preset_mode
        preset_icon = PRESET_ICONS.get(current_preset, "mdi:thermostat")
        
        mode_names = {
            MODE_MANUAL: "Manuel",
            MODE_AUTO: "Otomatik",
            MODE_SCHEDULE: "Haftalık Program",
            MODE_TURBO: "Turbo Isıtma",
            MODE_VENTILATION: "Havalandırma",
        }
        
        domain_data = self.hass.data.get(DOMAIN, {})
        timer_duration = getattr(self.coordinator, "last_timer_duration", None) or (domain_data.get("last_timer_duration") if isinstance(domain_data, dict) else None)
        if mode not in (MODE_TURBO, MODE_VENTILATION):
            timer_duration = None
            if isinstance(domain_data, dict):
                domain_data["last_timer_duration"] = None

        return {
            "mode": mode,
            "timer_duration": timer_duration,
            "mode_name": mode_names.get(mode, mode),
            "option": option,
            "option_name": OPTION_TO_PRESET.get(option, option),
            "is_away": option == OPTION_AWAY,
            "is_auto": mode == MODE_AUTO,
            "is_scheduled": mode == MODE_SCHEDULE,
            "is_turbo": mode == MODE_TURBO,
            "is_ventilation": mode == MODE_VENTILATION,
            "rollback_at": self._endpoint.get("rollbackAt"),
            "rollback": self._endpoint.get("rollback"),
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
            "preset_icon": preset_icon,
        }
