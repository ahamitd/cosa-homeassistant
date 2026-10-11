"""COSA Smart Termostat Entegrasyonu - Stable Polling Version."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CosaAPI, CosaAPIError
from .const import DOMAIN, MODE_AUTO, MODE_SCHEDULE, MODE_TURBO, MODE_VENTILATION, OPTION_HOME

_LOGGER = logging.getLogger(__name__)

# Stabil polling - WebSocket problemi çözülünce eklenecek
UPDATE_INTERVAL = timedelta(seconds=15)  # 15 saniye optimal

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kur."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    # Login
    email = entry.data.get("email")
    password = entry.data.get("password")
    
    login_result = await api.login(email, password)
    if not login_result.get("ok"):
        _LOGGER.error("COSA login başarısız")
        return False
    
    token = login_result.get("token")
    endpoint_id = entry.data.get("endpoint_id")
    
    # Data fetch fonksiyonu
    async def async_update_data():
        """Veriyi API'den al."""
        try:
            endpoint = await api.get_endpoint_detail(endpoint_id, token)
            
            forecast = {}
            reports = {}
            place_id = endpoint.get("place")
            if place_id:
                forecast = await api.get_forecast(place_id, token)
            
            # Rapor verilerini al
            reports = await api.get_reports(endpoint_id, token)
            
            return {"endpoint": endpoint, "forecast": forecast, "reports": reports}
            
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err
    
    # Coordinator oluştur - stabil polling
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="COSA",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    # Coordinator'a yardımcı metodlar ekle
    coordinator.api = api
    coordinator.token = token
    coordinator.endpoint_id = endpoint_id
    
    def _get_current_calibration() -> float:
        """Mevcut kalibrasyon değerini al."""
        if coordinator.data:
            return coordinator.data.get("endpoint", {}).get("calibration", 0.0)
        return 0.0
    
    def _is_open_window_enabled() -> bool:
        """Açık pencere özelliğinin aktif olup olmadığını kontrol et."""
        if coordinator.data:
            return coordinator.data.get("endpoint", {}).get("openWindowEnable", False)
        return False
    
    coordinator._get_current_calibration = _get_current_calibration
    coordinator._is_open_window_enabled = _is_open_window_enabled
    
    async def async_set_mode(
        mode: str, option: Optional[str] = None,
        duration: Optional[int] = None, rollback: Optional[dict[str, Any]] = None
    ) -> bool:
        """Mod değiştir."""
        result = await api.set_mode(endpoint_id, mode, option, duration, rollback, token)
        if result:
            await coordinator.async_request_refresh()
        return result

    async def async_set_turbo(duration: int = 20) -> bool:
        """Turbo ısıtma modunu süreli başlat."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        current_mode = endpoint.get("mode", MODE_AUTO)
        current_option = endpoint.get("option", OPTION_HOME)
        if current_mode in (MODE_TURBO, MODE_VENTILATION):
            rollback = endpoint.get("rollback", {"mode": MODE_AUTO, "option": current_option})
        else:
            rollback = {"mode": current_mode, "option": current_option}
        
        result = await api.set_mode(endpoint_id, MODE_TURBO, duration=duration, rollback=rollback, token=token)
        if result:
            coordinator.last_timer_duration = int(duration)
            coordinator.last_timer_mode = MODE_TURBO
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result

    async def async_set_ventilation(duration: int = 15) -> bool:
        """Havalandırma (kapatma) modunu süreli başlat."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        current_mode = endpoint.get("mode", MODE_AUTO)
        current_option = endpoint.get("option", OPTION_HOME)
        if current_mode in (MODE_TURBO, MODE_VENTILATION):
            rollback = endpoint.get("rollback", {"mode": MODE_AUTO, "option": current_option})
        else:
            rollback = {"mode": current_mode, "option": current_option}
        
        result = await api.set_mode(endpoint_id, MODE_VENTILATION, duration=duration, rollback=rollback, token=token)
        if result:
            coordinator.last_timer_duration = int(duration)
            coordinator.last_timer_mode = MODE_VENTILATION
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result

    async def async_cancel_timer_mode() -> bool:
        """Turbo veya havalandırma modunu iptal edip rollback moduna dön."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        rollback = endpoint.get("rollback", {})
        target_mode = rollback.get("mode", MODE_AUTO)
        target_option = rollback.get("option")
        result = await api.set_mode(endpoint_id, target_mode, option=target_option, token=token)
        if result:
            coordinator.last_timer_duration = None
            coordinator.last_timer_mode = None
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_temperatures(home: float, away: float, sleep: float, custom: float) -> bool:
        """Tüm sıcaklıkları ayarla."""
        _LOGGER.info("🔧 Sıcaklık ayarlanıyor: home=%s, away=%s, sleep=%s, custom=%s", 
                     home, away, sleep, custom)
        
        try:
            result = await api.set_target_temperatures(endpoint_id, home, away, sleep, custom, token)
            _LOGGER.info("API sonuç: %s", result)
            
            if result:
                # Kısa bir bekleme sonrası refresh - API'nin işlemesi için
                await asyncio.sleep(1)
                await coordinator.async_request_refresh()
            
            return result
        except Exception as err:
            _LOGGER.error("Sıcaklık ayarlama hatası: %s", err)
            return False
    
    async def async_set_preset_temperature(preset: str, temperature: float) -> bool:
        """Preset sıcaklığını ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        
        temps = {
            "home": endpoint.get("homeTemperature", 21.0),
            "away": endpoint.get("awayTemperature", 18.0),
            "sleep": endpoint.get("sleepTemperature", 19.0),
            "custom": endpoint.get("customTemperature", 22.0),
        }
        temps[preset] = temperature
        
        result = await api.set_target_temperatures(
            endpoint_id,
            temps["home"], temps["away"], temps["sleep"], temps["custom"],
            token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_open_window(enabled: bool) -> bool:
        """Açık pencere algılama özelliğini ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        calibration = endpoint.get("calibration", 0.0)
        duration = endpoint.get("openWindowDuration", 15)
        result = await api.set_device_settings(
            endpoint_id, 
            calibration=float(calibration), 
            open_window_enable=enabled,
            open_window_duration=int(duration),
            token=token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result

    async def async_set_open_window_duration(duration: int) -> bool:
        """Açık pencere kapalı kalma süresini ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        calibration = endpoint.get("calibration", 0.0)
        enabled = endpoint.get("openWindowEnable", True)
        result = await api.set_device_settings(
            endpoint_id, 
            calibration=float(calibration), 
            open_window_enable=enabled,
            open_window_duration=int(duration),
            token=token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_calibration(value: float) -> bool:
        """Kalibrasyonu ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        enabled = endpoint.get("openWindowEnable", True)
        duration = endpoint.get("openWindowDuration", 15)
        result = await api.set_device_settings(
            endpoint_id, 
            calibration=round(float(value), 1), 
            open_window_enable=enabled,
            open_window_duration=int(duration),
            token=token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result
    
    coordinator.async_set_mode = async_set_mode
    coordinator.async_set_turbo = async_set_turbo
    coordinator.async_set_ventilation = async_set_ventilation
    coordinator.async_cancel_timer_mode = async_cancel_timer_mode
    coordinator.async_set_temperatures = async_set_temperatures
    coordinator.async_set_preset_temperature = async_set_preset_temperature
    async def async_set_combi_range(pid_window_low: float, pid_window_high: float) -> bool:
        """Kombi çalışma ve durma aralıklarını ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        combi_settings = dict(endpoint.get("combiSettings", {}))
        combi_settings["pidWindowLow"] = round(float(pid_window_low), 2)
        combi_settings["pidWindowHigh"] = round(float(pid_window_high), 2)
        if "heating" not in combi_settings:
            combi_settings["heating"] = True
        
        result = await api.set_combi_settings(
            endpoint_id,
            combi_settings=combi_settings,
            token=token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result

    coordinator.async_set_open_window = async_set_open_window
    coordinator.async_set_open_window_duration = async_set_open_window_duration
    coordinator.async_set_calibration = async_set_calibration
    coordinator.async_set_combi_range = async_set_combi_range
    
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "token": token,
    }
    
    
    # Servisleri kaydet (set_turbo, set_ventilation, cancel_timer, set_combi_range)
    if not hass.services.has_service(DOMAIN, "set_turbo"):
        async def handle_set_turbo(call):
            duration = int(call.data.get("duration", 20))
            hass.data[DOMAIN]["last_timer_duration"] = duration
            hass.data[DOMAIN]["last_timer_mode"] = MODE_TURBO
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_set_turbo"):
                        await c.async_set_turbo(duration)
        hass.services.async_register(DOMAIN, "set_turbo", handle_set_turbo)

    if not hass.services.has_service(DOMAIN, "set_ventilation"):
        async def handle_set_ventilation(call):
            duration = int(call.data.get("duration", 15))
            hass.data[DOMAIN]["last_timer_duration"] = duration
            hass.data[DOMAIN]["last_timer_mode"] = MODE_VENTILATION
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_set_ventilation"):
                        await c.async_set_ventilation(duration)
        hass.services.async_register(DOMAIN, "set_ventilation", handle_set_ventilation)

    if not hass.services.has_service(DOMAIN, "cancel_timer"):
        async def handle_cancel_timer(call):
            hass.data[DOMAIN]["last_timer_duration"] = None
            hass.data[DOMAIN]["last_timer_mode"] = None
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_cancel_timer_mode"):
                        await c.async_cancel_timer_mode()
        hass.services.async_register(DOMAIN, "cancel_timer", handle_cancel_timer)

    if not hass.services.has_service(DOMAIN, "set_combi_range"):
        async def handle_set_combi_range(call):
            work_range = call.data.get("work_range")
            stop_range = call.data.get("stop_range")
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_set_combi_range"):
                        endpoint = c.data.get("endpoint", {}) if c.data else {}
                        cur_work = float(work_range) if work_range is not None else float(endpoint.get("pidWindowLow", 0.1))
                        cur_stop = float(stop_range) if stop_range is not None else float(endpoint.get("pidWindowHigh", 0.2))
                        await c.async_set_combi_range(cur_work, cur_stop)
        hass.services.async_register(DOMAIN, "set_combi_range", handle_set_combi_range)

    if not hass.services.has_service(DOMAIN, "set_schedule"):
        async def handle_set_schedule(call):
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_set_mode"):
                        await c.async_set_mode(MODE_SCHEDULE)
        hass.services.async_register(DOMAIN, "set_schedule", handle_set_schedule)

    if not hass.services.has_service(DOMAIN, "set_auto"):
        async def handle_set_auto(call):
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict):
                    c = entry_data.get("coordinator")
                    if c and hasattr(c, "async_set_mode"):
                        await c.async_set_mode(MODE_AUTO)
        hass.services.async_register(DOMAIN, "set_auto", handle_set_auto)

    # Mevcut kayıtlı varlıkların kategorilerini otomatik güncelle (Kontroller, Yapılandırma, Tanılama ayrımı)
    try:
        from homeassistant.helpers import entity_registry as er
        from homeassistant.const import EntityCategory
        ent_reg = er.async_get(hass)
        for reg_entry in list(ent_reg.entities.values()):
            if reg_entry.config_entry_id == entry.entry_id:
                uid = reg_entry.unique_id
                target_cat = None
                if any(k in uid for k in ("calibration", "combi_work_range", "combi_stop_range", "open_window_duration", "open_window_enable")):
                    target_cat = EntityCategory.CONFIG
                elif any(k in uid for k in ("battery", "rssi", "firmware", "connected")):
                    target_cat = EntityCategory.DIAGNOSTIC
                
                if target_cat is not None and reg_entry.entity_category != target_cat:
                    ent_reg.async_update_entity(reg_entry.entity_id, entity_category=target_cat)
    except Exception as err:
        _LOGGER.debug("Entity category migration check: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
