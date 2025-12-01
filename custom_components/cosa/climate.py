"""COSA Smart Thermostat Climate Platform.

Bu modül Home Assistant climate entity'sini oluşturur.
DataUpdateCoordinator kullanarak her 10 saniyede API'den veri çeker.

HVAC Modları:
- off: Kapalı (mode=manual, option=frozen)
- heat: Isıtma açık (mode=manual/auto/schedule)

Preset Modları:
- home: Ev modu (mode=manual, option=home)
- sleep: Uyku modu (mode=manual, option=sleep)
- away: Dışarı modu (mode=manual, option=away)
- custom: Kullanıcı modu (mode=manual, option=custom)
- auto: Otomatik mod (mode=auto)
- schedule: Haftalık program (mode=schedule)

Sıcaklık Ayarı:
- setTargetTemperatures API'si ile tüm preset sıcaklıkları güncellenir
"""

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

from .api import (
    CosaAPI,
    CosaAPIError,
    CosaAuthError,
    extract_endpoint_state,
)
from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    MIN_TEMP,
    MAX_TEMP,
    TEMP_STEP,
    MODE_MANUAL,
    MODE_AUTO,
    MODE_SCHEDULE,
    OPTION_HOME,
    OPTION_SLEEP,
    OPTION_AWAY,
    OPTION_CUSTOM,
    OPTION_FROZEN,
    PRESET_HOME,
    PRESET_SLEEP,
    PRESET_AWAY,
    PRESET_CUSTOM,
    PRESET_AUTO,
    PRESET_SCHEDULE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Climate platformunu kur.
    
    DataUpdateCoordinator oluşturur ve climate entity'yi ekler.
    """
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    # Coordinator oluştur
    coordinator = CosaCoordinator(hass, config_entry, entry_data)
    
    # İlk veri çekimini yap
    await coordinator.async_config_entry_first_refresh()
    
    # Coordinator'ı sakla (sensor platformu da kullanacak)
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    
    # Climate entity oluştur
    async_add_entities([CosaClimate(coordinator, config_entry)])
    
    _LOGGER.info("COSA climate entity oluşturuldu")


class CosaCoordinator(DataUpdateCoordinator):
    """COSA veri güncelleme koordinatörü.
    
    Her SCAN_INTERVAL'da (10 saniye) API'den veri çeker.
    Token süresi dolarsa otomatik yeniler.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        entry_data: dict[str, Any],
    ) -> None:
        """Koordinatörü başlat."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        
        self.config_entry = config_entry
        self._email = entry_data["email"]
        self._password = entry_data["password"]
        self._token = entry_data["token"]
        self._endpoint_id = entry_data["endpoint_id"]
        self._device_name = entry_data.get("device_name", "COSA Termostat")
        
        # API istemcisi
        self._api = CosaAPI(async_get_clientsession(hass))

    async def _async_update_data(self) -> dict[str, Any]:
        """API'den güncel verileri çek.
        
        Her 10 saniyede çağrılır.
        getEndpoints API'sinden sıcaklık, nem, mod, option, targetTemperatures alınır.
        
        Returns:
            Normalize edilmiş endpoint durumu
            
        Raises:
            UpdateFailed: API hatası durumunda
        """
        try:
            # Endpoint'leri al
            endpoints = await self._api.get_endpoints(self._token)
            
            if not endpoints:
                raise UpdateFailed("Endpoint bulunamadı")
            
            # Bizim endpoint'i bul
            endpoint = None
            for ep in endpoints:
                ep_id = ep.get("id") or ep.get("_id")
                if ep_id == self._endpoint_id:
                    endpoint = ep
                    break
            
            if not endpoint:
                # İlk endpoint'i kullan
                endpoint = endpoints[0]
            
            # Durumu çıkar ve döndür
            state = extract_endpoint_state(endpoint)
            _LOGGER.debug("Veri güncellendi: %s", state)
            return state
            
        except CosaAuthError:
            # Token süresi dolmuş, yenile
            _LOGGER.warning("Token süresi doldu, yenileniyor...")
            try:
                self._token = await self._api.login(self._email, self._password)
                
                # Tekrar dene
                endpoints = await self._api.get_endpoints(self._token)
                
                if endpoints:
                    endpoint = endpoints[0]
                    for ep in endpoints:
                        ep_id = ep.get("id") or ep.get("_id")
                        if ep_id == self._endpoint_id:
                            endpoint = ep
                            break
                    return extract_endpoint_state(endpoint)
                    
            except Exception as err:
                raise UpdateFailed(f"Token yenileme hatası: {err}") from err
                
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err
            
        except Exception as err:
            raise UpdateFailed(f"Beklenmeyen hata: {err}") from err

    async def async_set_mode(self, mode: str, option: str | None = None) -> None:
        """Mod değiştir.
        
        Args:
            mode: "manual", "auto", veya "schedule"
            option: Manual için: "home", "sleep", "away", "custom", "frozen"
        """
        try:
            await self._api.set_mode(self._token, self._endpoint_id, mode, option)
            await self.async_request_refresh()
        except CosaAuthError:
            # Token yenile ve tekrar dene
            self._token = await self._api.login(self._email, self._password)
            await self._api.set_mode(self._token, self._endpoint_id, mode, option)
            await self.async_request_refresh()

    async def async_set_temperatures(
        self,
        home: float,
        away: float,
        sleep: float,
        custom: float,
    ) -> None:
        """Hedef sıcaklıkları ayarla.
        
        Args:
            home: Ev modu sıcaklığı
            away: Dışarı modu sıcaklığı
            sleep: Uyku modu sıcaklığı
            custom: Kullanıcı modu sıcaklığı
        """
        try:
            await self._api.set_target_temperatures(
                self._token,
                self._endpoint_id,
                home,
                away,
                sleep,
                custom,
            )
            await self.async_request_refresh()
        except CosaAuthError:
            # Token yenile ve tekrar dene
            self._token = await self._api.login(self._email, self._password)
            await self._api.set_target_temperatures(
                self._token,
                self._endpoint_id,
                home,
                away,
                sleep,
                custom,
            )
            await self.async_request_refresh()


class CosaClimate(CoordinatorEntity[CosaCoordinator], ClimateEntity):
    """COSA Termostat Climate Entity.
    
    Home Assistant'ın climate kartında görünen ana entity.
    HVAC modu, preset modu ve sıcaklık kontrolü sağlar.
    """

    # Entity özellikleri
    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TEMP_STEP
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    
    # Desteklenen HVAC modları
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    
    # Desteklenen özellikler
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    
    # Preset modları
    _attr_preset_modes = [
        PRESET_HOME,
        PRESET_SLEEP,
        PRESET_AWAY,
        PRESET_CUSTOM,
        PRESET_AUTO,
        PRESET_SCHEDULE,
    ]

    def __init__(
        self,
        coordinator: CosaCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Climate entity'yi başlat."""
        super().__init__(coordinator)
        
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        self._attr_name = "Termostat"
        
        # Cihaz bilgisi
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator._device_name,
            manufacturer="COSA",
            model="Smart Thermostat",
        )
        
        # Son bilinen preset (OFF'dan dönüş için)
        self._last_preset = PRESET_HOME

    @property
    def current_temperature(self) -> float | None:
        """Mevcut oda sıcaklığı."""
        if self.coordinator.data:
            return self.coordinator.data.get("temperature")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Hedef sıcaklık."""
        if self.coordinator.data:
            return self.coordinator.data.get("target_temperature")
        return None

    @property
    def current_humidity(self) -> int | None:
        """Mevcut nem oranı."""
        if self.coordinator.data:
            humidity = self.coordinator.data.get("humidity")
            if humidity is not None:
                return int(humidity)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Mevcut HVAC modu.
        
        - OFF: mode=manual, option=frozen
        - HEAT: Diğer tüm durumlar
        """
        if not self.coordinator.data:
            return HVACMode.OFF
        
        mode = self.coordinator.data.get("mode")
        option = self.coordinator.data.get("option")
        
        # Manual + frozen = OFF
        if mode == MODE_MANUAL and option == OPTION_FROZEN:
            return HVACMode.OFF
        
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Mevcut HVAC eylemi.
        
        - OFF: Kapalı
        - HEATING: Kombi çalışıyor
        - IDLE: Beklemede
        """
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        
        if self.coordinator.data:
            combi_state = self.coordinator.data.get("combi_state")
            if combi_state == "on":
                return HVACAction.HEATING
        
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Mevcut preset modu.
        
        API'den gelen mode ve option'a göre belirlenir.
        """
        if not self.coordinator.data:
            return None
        
        mode = self.coordinator.data.get("mode")
        option = self.coordinator.data.get("option")
        
        # Auto mod
        if mode == MODE_AUTO:
            return PRESET_AUTO
        
        # Schedule mod
        if mode == MODE_SCHEDULE:
            return PRESET_SCHEDULE
        
        # Manual mod - option'a göre
        if mode == MODE_MANUAL:
            option_to_preset = {
                OPTION_HOME: PRESET_HOME,
                OPTION_SLEEP: PRESET_SLEEP,
                OPTION_AWAY: PRESET_AWAY,
                OPTION_CUSTOM: PRESET_CUSTOM,
                OPTION_FROZEN: None,  # OFF modunda preset yok
            }
            return option_to_preset.get(option)
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Ekstra durum özellikleri."""
        attrs = {}
        
        if self.coordinator.data:
            attrs["mode"] = self.coordinator.data.get("mode")
            attrs["option"] = self.coordinator.data.get("option")
            attrs["combi_state"] = self.coordinator.data.get("combi_state")
            attrs["is_connected"] = self.coordinator.data.get("is_connected")
            
            target_temps = self.coordinator.data.get("target_temperatures", {})
            attrs["target_temp_home"] = target_temps.get("home")
            attrs["target_temp_away"] = target_temps.get("away")
            attrs["target_temp_sleep"] = target_temps.get("sleep")
            attrs["target_temp_custom"] = target_temps.get("custom")
        
        return attrs

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """HVAC modunu değiştir.
        
        - OFF: mode=manual, option=frozen
        - HEAT: Son bilinen preset'e dön veya home
        """
        if hvac_mode == HVACMode.OFF:
            # Kapalı modu
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_FROZEN)
        else:
            # Isıtmayı aç - son preset'e dön
            preset = self._last_preset or PRESET_HOME
            await self.async_set_preset_mode(preset)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Preset modunu değiştir.
        
        Preset'e göre uygun API çağrısı yapılır.
        """
        # Son preset'i kaydet (OFF'dan dönüş için)
        if preset_mode not in (None, OPTION_FROZEN):
            self._last_preset = preset_mode
        
        if preset_mode == PRESET_AUTO:
            await self.coordinator.async_set_mode(MODE_AUTO)
        elif preset_mode == PRESET_SCHEDULE:
            await self.coordinator.async_set_mode(MODE_SCHEDULE)
        else:
            # Manual modlar
            preset_to_option = {
                PRESET_HOME: OPTION_HOME,
                PRESET_SLEEP: OPTION_SLEEP,
                PRESET_AWAY: OPTION_AWAY,
                PRESET_CUSTOM: OPTION_CUSTOM,
            }
            option = preset_to_option.get(preset_mode, OPTION_HOME)
            await self.coordinator.async_set_mode(MODE_MANUAL, option)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Hedef sıcaklığı ayarla.
        
        Aktif preset'e göre ilgili sıcaklık güncellenir.
        Tüm preset sıcaklıkları tek API çağrısıyla gönderilir.
        """
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # Mevcut sıcaklıkları al
        current_temps = {}
        if self.coordinator.data:
            current_temps = self.coordinator.data.get("target_temperatures", {})
        
        home = current_temps.get("home", 20.0)
        away = current_temps.get("away", 15.0)
        sleep = current_temps.get("sleep", 18.0)
        custom = current_temps.get("custom", 20.0)
        
        # Aktif preset'e göre sıcaklığı güncelle
        preset = self.preset_mode or PRESET_HOME
        
        if preset == PRESET_HOME:
            home = temperature
        elif preset == PRESET_AWAY:
            away = temperature
        elif preset == PRESET_SLEEP:
            sleep = temperature
        elif preset == PRESET_CUSTOM:
            custom = temperature
        elif preset in (PRESET_AUTO, PRESET_SCHEDULE):
            # Auto/schedule modunda home sıcaklığını güncelle
            home = temperature
        
        # Sıcaklıkları API'ye gönder
        await self.coordinator.async_set_temperatures(home, away, sleep, custom)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Koordinatör güncellemelerini işle."""
        # Son preset'i güncelle (OFF değilse)
        if self.preset_mode and self.preset_mode != OPTION_FROZEN:
            self._last_preset = self.preset_mode
        
        self.async_write_ha_state()
