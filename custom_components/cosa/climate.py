"""Climate platform for COSA integration."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_HOME,
    PRESET_SLEEP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import CosaAPIClient, CosaAPIError
from .const import (
    DOMAIN,
    MODE_AWAY,
    MODE_AUTO,
    MODE_CUSTOM,
    MODE_FROZEN,
    MODE_HOME,
    MODE_SCHEDULE,
    MODE_SLEEP,
    PRESET_AUTO,
    PRESET_CUSTOM,
    PRESET_SCHEDULE,
    SCAN_INTERVAL,
    MIN_TEMP,
    MAX_TEMP,
    TEMP_STEP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up COSA climate platform."""
    # Get coordinator from hass.data (created in __init__.py)
    coordinator: CosaDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]

    # Create entity
    entity = CosaClimate(coordinator, config_entry)
    async_add_entities([entity])
    _LOGGER.info("COSA climate entity created: %s", entity.unique_id)

    # Try to refresh data if not already done
    if not coordinator.data:
        try:
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.info("COSA coordinator refresh successful")
        except Exception as err:
            _LOGGER.error(
                "Failed to refresh coordinator during setup: %s", err, exc_info=True
            )
            # Entity is still created, it will retry on next update


class CosaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching COSA data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.config_entry = config_entry
        self.client: Optional[CosaAPIClient] = None
        self.endpoint_id: Optional[str] = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from COSA API."""
        if self.client is None:
            self.client = CosaAPIClient(
                username=self.config_entry.data["username"],
                password=self.config_entry.data["password"],
                endpoint_id=self.config_entry.data.get("endpoint_id"),
            )
            self.endpoint_id = self.config_entry.data.get("endpoint_id")
            await self.client.login()

        # If endpoint_id is not set, try to get it from API
        if not self.endpoint_id:
            try:
                endpoints = await self.client.list_endpoints()
                if endpoints and len(endpoints) > 0:
                    first_endpoint = endpoints[0]
                    self.endpoint_id = (
                        first_endpoint.get("id") or
                        first_endpoint.get("_id") or
                        first_endpoint.get("endpoint")
                    )
                    _LOGGER.info("Auto-detected endpoint ID: %s", self.endpoint_id)
                else:
                    _LOGGER.error("No endpoints found for user")
                    raise CosaAPIError("No endpoints found")
            except Exception as err:
                _LOGGER.error("Failed to get endpoint ID: %s", err)
                raise CosaAPIError(f"Failed to get endpoint ID: {err}") from err

        if not self.endpoint_id:
            raise CosaAPIError("Endpoint ID is required but not available")

        try:
            status = await self.client.get_endpoint_status(self.endpoint_id)
            
            # Handle different response formats
            endpoint_data = {}
            if isinstance(status, dict):
                endpoint_data = status.get("endpoint", {})
                # If endpoint is not in response, maybe the response itself is the endpoint data
                if not endpoint_data and "temperature" in status:
                    endpoint_data = status
            elif isinstance(status, list) and len(status) > 0:
                endpoint_data = status[0]
            
            _LOGGER.debug("Endpoint data received: %s", endpoint_data)
            
            if not endpoint_data:
                _LOGGER.warning("Empty endpoint data received. Full response: %s", status)
                # Return default values to prevent entity creation failure
                return {
                    "temperature": None,
                    "target_temperature": None,
                    "humidity": None,
                    "combi_state": "off",
                    "option": None,
                    "mode": None,
                    "target_temperatures": {
                        "home": None,
                        "away": None,
                        "sleep": None,
                        "custom": None,
                    },
                }

            return {
                "temperature": endpoint_data.get("temperature"),
                "target_temperature": endpoint_data.get("targetTemperature"),
                "humidity": endpoint_data.get("humidity"),
                "combi_state": endpoint_data.get("combiState"),
                "option": endpoint_data.get("option"),
                "mode": endpoint_data.get("mode"),
                "target_temperatures": {
                    "home": endpoint_data.get("targetTemperatures", {}).get("home"),
                    "away": endpoint_data.get("targetTemperatures", {}).get("away"),
                    "sleep": endpoint_data.get("targetTemperatures", {}).get("sleep"),
                    "custom": endpoint_data.get("targetTemperatures", {}).get("custom"),
                },
            }
        except CosaAPIError as err:
            _LOGGER.error("Error fetching COSA data: %s", err)
            # Check if it's an authentication error
            if "401" in str(err) or "expired" in str(err).lower() or "authentication" in str(err).lower():
                _LOGGER.info("Authentication error detected, attempting to re-login")
                try:
                    await self.client.login()
                    # Retry once after re-login
                    status = await self.client.get_endpoint_status(self.endpoint_id)
                    endpoint_data = status.get("endpoint", {})
                    return {
                        "temperature": endpoint_data.get("temperature"),
                        "target_temperature": endpoint_data.get("targetTemperature"),
                        "humidity": endpoint_data.get("humidity"),
                        "combi_state": endpoint_data.get("combiState"),
                        "option": endpoint_data.get("option"),
                        "mode": endpoint_data.get("mode"),
                        "target_temperatures": {
                            "home": endpoint_data.get("targetTemperatures", {}).get("home"),
                            "away": endpoint_data.get("targetTemperatures", {}).get("away"),
                            "sleep": endpoint_data.get("targetTemperatures", {}).get("sleep"),
                            "custom": endpoint_data.get("targetTemperatures", {}).get("custom"),
                        },
                    }
                except Exception as retry_err:
                    _LOGGER.error("Re-login failed: %s", retry_err)
                    raise
            raise


class CosaClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a COSA climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [
        PRESET_HOME,
        PRESET_AWAY,
        PRESET_SLEEP,
        PRESET_CUSTOM,
        PRESET_AUTO,
        PRESET_SCHEDULE,
    ]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP

    def __init__(
        self, coordinator: CosaDataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = "COSA Termostat"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        
        # Set device info for proper device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"COSA Termostat ({config_entry.data.get('username', 'Unknown')})",
            manufacturer="COSA",
            model="Smart Thermostat",
        )

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self.coordinator.data.get("temperature")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        return self.coordinator.data.get("target_temperature")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        combi_state = self.coordinator.data.get("combi_state")
        if combi_state == "off":
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode."""
        option = self.coordinator.data.get("option")
        mode = self.coordinator.data.get("mode")
        
        # Check mode first (auto, schedule, manual)
        if mode == "auto":
            return PRESET_AUTO
        elif mode == "schedule":
            return PRESET_SCHEDULE
        
        # Then check option (for manual mode)
        if option == MODE_HOME:
            return PRESET_HOME
        elif option == MODE_AWAY:
            return PRESET_AWAY
        elif option == MODE_SLEEP:
            return PRESET_SLEEP
        elif option == MODE_CUSTOM:
            return PRESET_CUSTOM
        elif option == MODE_AUTO:
            return PRESET_AUTO
        elif option == MODE_SCHEDULE:
            return PRESET_SCHEDULE
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {
            "humidity": self.coordinator.data.get("humidity"),
            "combi_state": self.coordinator.data.get("combi_state"),
            "option": self.coordinator.data.get("option"),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Get current preset mode to determine which temperature to update
        current_preset = self.preset_mode
        target_temps = self.coordinator.data.get("target_temperatures", {})

        # Update the temperature for current preset
        if current_preset == PRESET_HOME:
            target_temps["home"] = temperature
        elif current_preset == PRESET_AWAY:
            target_temps["away"] = temperature
        elif current_preset == PRESET_SLEEP:
            target_temps["sleep"] = temperature
        elif current_preset == PRESET_CUSTOM:
            target_temps["custom"] = temperature
        else:
            # Default to home if no preset
            target_temps["home"] = temperature

        try:
            await self.coordinator.client.set_target_temperatures(
                home_temp=target_temps.get("home", 20),
                away_temp=target_temps.get("away", 15),
                sleep_temp=target_temps.get("sleep", 18),
                custom_temp=target_temps.get("custom", 20),
                endpoint_id=self.coordinator.endpoint_id,
            )
            await self.coordinator.async_request_refresh()
        except CosaAPIError as err:
            _LOGGER.error("Error setting temperature: %s", err)
            raise

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        try:
            if hvac_mode == HVACMode.OFF:
                await self.coordinator.client.set_mode(
                    mode="manual",
                    option=MODE_FROZEN,
                    endpoint_id=self.coordinator.endpoint_id,
                )
            elif hvac_mode == HVACMode.HEAT:
                # Turn on with current preset or default to home
                current_preset = self.preset_mode or PRESET_HOME
                option_map = {
                    PRESET_HOME: MODE_HOME,
                    PRESET_AWAY: MODE_AWAY,
                    PRESET_SLEEP: MODE_SLEEP,
                    PRESET_CUSTOM: MODE_CUSTOM,
                }
                option = option_map.get(current_preset, MODE_HOME)
                await self.coordinator.client.set_mode(
                    mode="manual",
                    option=option,
                    endpoint_id=self.coordinator.endpoint_id,
                )
            await self.coordinator.async_request_refresh()
        except CosaAPIError as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
            raise

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        option_map = {
            PRESET_HOME: MODE_HOME,
            PRESET_AWAY: MODE_AWAY,
            PRESET_SLEEP: MODE_SLEEP,
            PRESET_CUSTOM: MODE_CUSTOM,
            PRESET_AUTO: MODE_AUTO,
            PRESET_SCHEDULE: MODE_SCHEDULE,
        }

        option = option_map.get(preset_mode)
        if not option:
            _LOGGER.error("Invalid preset mode: %s", preset_mode)
            return

        try:
            # Determine mode based on preset
            if preset_mode in [PRESET_AUTO, PRESET_SCHEDULE]:
                # For auto and schedule, mode should be the preset name
                await self.coordinator.client.set_mode(
                    mode=preset_mode,
                    option=option,
                    endpoint_id=self.coordinator.endpoint_id,
                )
            else:
                # For manual presets (home, away, sleep, custom)
                await self.coordinator.client.set_mode(
                    mode="manual",
                    option=option,
                    endpoint_id=self.coordinator.endpoint_id,
                )
            await self.coordinator.async_request_refresh()
        except CosaAPIError as err:
            _LOGGER.error("Error setting preset mode: %s", err)
            raise

