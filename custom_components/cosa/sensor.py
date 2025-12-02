"""COSA Sensor Platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BATTERY_LEVELS, WEATHER_ICONS, WEATHER_TRANSLATIONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor platformunu kur."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        CosaTemperatureSensor(coordinator, config_entry),
        CosaHumiditySensor(coordinator, config_entry),
        CosaTargetTemperatureSensor(coordinator, config_entry),
        CosaBatteryVoltageSensor(coordinator, config_entry),
        CosaBatteryPercentSensor(coordinator, config_entry),
        CosaRssiSensor(coordinator, config_entry),
        CosaCombiStateSensor(coordinator, config_entry),
        CosaModeSensor(coordinator, config_entry),
        CosaOptionSensor(coordinator, config_entry),
        CosaOutdoorTemperatureSensor(coordinator, config_entry),
        CosaOutdoorHumiditySensor(coordinator, config_entry),
        CosaWeatherSensor(coordinator, config_entry),
        CosaFirmwareVersionSensor(coordinator, config_entry),
        # Rapor Sensörleri
        CosaTotalRuntimeSensor(coordinator, config_entry),
        CosaHomeRuntimeSensor(coordinator, config_entry),
        CosaSleepRuntimeSensor(coordinator, config_entry),
        CosaAverageTemperatureSensor(coordinator, config_entry),
        CosaMaxTemperatureSensor(coordinator, config_entry),
        CosaMinTemperatureSensor(coordinator, config_entry),
        CosaMaxHumiditySensor(coordinator, config_entry),
        CosaMinHumiditySensor(coordinator, config_entry),
        CosaOutdoorAverageTemperatureSensor(coordinator, config_entry),
        CosaNetworkQualitySensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class CosaBaseSensor(CoordinatorEntity, SensorEntity):
    """COSA Base Sensor."""

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

    @property
    def _forecast(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("forecast", {})
        return {}


class CosaTemperatureSensor(CosaBaseSensor):
    """Oda Sıcaklığı Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "temperature", "Oda Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("temperature")


class CosaHumiditySensor(CosaBaseSensor):
    """Nem Sensörü."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "humidity", "Nem")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("humidity")


class CosaTargetTemperatureSensor(CosaBaseSensor):
    """Hedef Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "target_temperature", "Hedef Sıcaklık")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("targetTemperature")


class CosaBatteryVoltageSensor(CosaBaseSensor):
    """Pil Voltajı Sensörü."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "battery_voltage", "Pil Voltajı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("batteryVoltage")


class CosaBatteryPercentSensor(CosaBaseSensor):
    """Pil Yüzdesi Sensörü."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "battery_percent", "Pil Seviyesi")

    @property
    def native_value(self) -> int | None:
        power_state = self._endpoint.get("powerState", "")
        return BATTERY_LEVELS.get(power_state, 0)


class CosaRssiSensor(CosaBaseSensor):
    """Sinyal Gücü Sensörü."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "rssi", "Sinyal Gücü")

    @property
    def native_value(self) -> int | None:
        return self._endpoint.get("rssi")


class CosaCombiStateSensor(CosaBaseSensor):
    """Kombi Durumu Sensörü."""

    _attr_icon = "mdi:fire"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "combi_state", "Kombi Durumu")

    @property
    def native_value(self) -> str | None:
        state = self._endpoint.get("combiState")
        if state == "on":
            return "Açık"
        elif state == "off":
            return "Kapalı"
        return state


class CosaModeSensor(CosaBaseSensor):
    """Mod Sensörü."""

    _attr_icon = "mdi:thermostat"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "mode", "Mod")

    @property
    def native_value(self) -> str | None:
        mode = self._endpoint.get("mode")
        mode_names = {
            "manual": "Manuel",
            "auto": "Otomatik",
            "schedule": "Haftalık Program",
        }
        return mode_names.get(mode, mode)


class CosaOptionSensor(CosaBaseSensor):
    """Seçenek Sensörü."""

    _attr_icon = "mdi:home-thermometer"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "option", "Seçenek")

    @property
    def native_value(self) -> str | None:
        option = self._endpoint.get("option")
        option_names = {
            "home": "Evde",
            "away": "Dışarı",
            "sleep": "Uyku",
            "custom": "Manuel",
            "frozen": "Donma Koruma",
        }
        return option_names.get(option, option)


class CosaOutdoorTemperatureSensor(CosaBaseSensor):
    """Dış Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "outdoor_temperature", "Dış Sıcaklık")

    @property
    def native_value(self) -> float | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            return hourly[0].get("temperature")
        return None


class CosaOutdoorHumiditySensor(CosaBaseSensor):
    """Dış Nem Sensörü."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "outdoor_humidity", "Dış Nem")

    @property
    def native_value(self) -> float | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            return hourly[0].get("humidity")
        return None


class CosaWeatherSensor(CosaBaseSensor):
    """Hava Durumu Sensörü."""

    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "weather", "Hava Durumu")

    @property
    def native_value(self) -> str | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            icon = hourly[0].get("icon", "")
            # Türkçe çeviri döndür
            return WEATHER_TRANSLATIONS.get(icon, icon)
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Ekstra özellikler."""
        hourly = self._forecast.get("hourly", [])
        if hourly:
            icon = hourly[0].get("icon", "")
            return {
                "icon_key": icon,
                "ha_icon": WEATHER_ICONS.get(icon, icon),
            }
        return {}


class CosaFirmwareVersionSensor(CosaBaseSensor):
    """Firmware Versiyonu Sensörü."""

    _attr_icon = "mdi:chip"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "firmware", "Firmware Versiyonu")

    @property
    def native_value(self) -> str | None:
        device = self._endpoint.get("device", {})
        return device.get("version")


# ===== RAPOR SENSÖRLERİ =====

class CosaReportBaseSensor(CosaBaseSensor):
    """COSA Rapor Base Sensor."""

    @property
    def _reports(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("reports", {})
        return {}

    @property
    def _stats(self) -> dict:
        return self._reports.get("stats", {})

    @property
    def _summary(self) -> dict:
        return self._reports.get("summary", {})


class CosaTotalRuntimeSensor(CosaReportBaseSensor):
    """Toplam Çalışma Süresi Sensörü (Son 24 Saat)."""

    _attr_icon = "mdi:clock-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "h"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "total_runtime", "Toplam Çalışma Süresi (24s)")

    @property
    def native_value(self) -> float | None:
        runtimes = self._summary.get("runtimes", {})
        total_seconds = runtimes.get("total")
        if total_seconds is None:
            return None
        return round(total_seconds / 3600, 2)

    @property
    def extra_state_attributes(self) -> dict:
        runtimes = self._summary.get("runtimes", {})
        return {
            "evde_saat": round(runtimes.get("home", 0) / 3600, 2),
            "uyku_saat": round(runtimes.get("sleep", 0) / 3600, 2),
            "disari_saat": round(runtimes.get("away", 0) / 3600, 2),
            "manuel_saat": round(runtimes.get("custom", 0) / 3600, 2),
            "donma_koruma_saat": round(runtimes.get("frozen", 0) / 3600, 2),
            "toplam_saniye": runtimes.get("total", 0),
        }


class CosaHomeRuntimeSensor(CosaReportBaseSensor):
    """Evde Modu Çalışma Süresi (Son 24 Saat)."""

    _attr_icon = "mdi:home-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "h"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "home_runtime", "Evde Çalışma Süresi (24s)")

    @property
    def native_value(self) -> float | None:
        runtimes = self._summary.get("runtimes", {})
        seconds = runtimes.get("home")
        if seconds is None:
            return None
        return round(seconds / 3600, 2)


class CosaSleepRuntimeSensor(CosaReportBaseSensor):
    """Uyku Modu Çalışma Süresi (Son 24 Saat)."""

    _attr_icon = "mdi:bed-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "h"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "sleep_runtime", "Uyku Çalışma Süresi (24s)")

    @property
    def native_value(self) -> float | None:
        runtimes = self._summary.get("runtimes", {})
        seconds = runtimes.get("sleep")
        if seconds is None:
            return None
        return round(seconds / 3600, 2)


class CosaAverageTemperatureSensor(CosaReportBaseSensor):
    """Ortalama Sıcaklık Sensörü (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-lines"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "avg_temperature", "Ortalama Sıcaklık (24s)")

    @property
    def native_value(self) -> float | None:
        avg_temps = self._summary.get("averageTemperatures", {})
        return avg_temps.get("total")

    @property
    def extra_state_attributes(self) -> dict:
        avg_temps = self._summary.get("averageTemperatures", {})
        return {
            "evde_ortalama": avg_temps.get("home"),
            "uyku_ortalama": avg_temps.get("sleep"),
            "disari_ortalama": avg_temps.get("away"),
            "manuel_ortalama": avg_temps.get("custom"),
        }


class CosaMaxTemperatureSensor(CosaReportBaseSensor):
    """Maksimum Sıcaklık Sensörü (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "max_temperature", "Maksimum Sıcaklık (24s)")

    @property
    def native_value(self) -> float | None:
        return self._stats.get("maxTemperature")


class CosaMinTemperatureSensor(CosaReportBaseSensor):
    """Minimum Sıcaklık Sensörü (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "min_temperature", "Minimum Sıcaklık (24s)")

    @property
    def native_value(self) -> float | None:
        return self._stats.get("minTemperature")


class CosaMaxHumiditySensor(CosaReportBaseSensor):
    """Maksimum Nem Sensörü (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "max_humidity", "Maksimum Nem (24s)")

    @property
    def native_value(self) -> float | None:
        return self._stats.get("maxHumidity")


class CosaMinHumiditySensor(CosaReportBaseSensor):
    """Minimum Nem Sensörü (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "min_humidity", "Minimum Nem (24s)")

    @property
    def native_value(self) -> float | None:
        return self._stats.get("minHumidity")


class CosaOutdoorAverageTemperatureSensor(CosaReportBaseSensor):
    """Dış Ortam Ortalama Sıcaklık (Son 24 Saat)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:home-thermometer-outline"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "outdoor_avg_temp", "Dış Ortalama Sıcaklık (24s)")

    @property
    def native_value(self) -> float | None:
        avg = self._stats.get("placeAverageTemperature")
        return round(avg, 1) if avg else None


class CosaNetworkQualitySensor(CosaReportBaseSensor):
    """Ağ Kalitesi Sensörü."""

    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "network_quality", "Ağ Kalitesi")

    @property
    def native_value(self) -> str | None:
        quality = self._stats.get("networkQuality")
        if quality is None:
            return None
        quality_names = {
            0: "Çok Zayıf",
            1: "Zayıf", 
            2: "Orta",
            3: "İyi",
            4: "Çok İyi",
        }
        return quality_names.get(quality, f"Seviye {quality}")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "quality_level": self._stats.get("networkQuality"),
            "offline_seconds": self._stats.get("offlineFor", 0),
        }
