import asyncio
import pytest
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

# Create minimal homeassistant stub modules to allow importing the climate module
ha_module = types.ModuleType("homeassistant")
sys.modules["homeassistant"] = ha_module

ha_components = types.ModuleType("homeassistant.components")
sys.modules["homeassistant.components"] = ha_components

climate_mod = types.ModuleType("homeassistant.components.climate")
class ClimateEntity:
    pass
class ClimateEntityFeature:
    TARGET_TEMPERATURE = 1
    PRESET_MODE = 2
class HVACMode:
    OFF = "off"
    HEAT = "heat"
climate_mod.ClimateEntity = ClimateEntity
climate_mod.ClimateEntityFeature = ClimateEntityFeature
climate_mod.HVACMode = HVACMode
sys.modules["homeassistant.components.climate"] = climate_mod

climate_const = types.ModuleType("homeassistant.components.climate.const")
climate_const.PRESET_AWAY = "away"
climate_const.PRESET_HOME = "home"
climate_const.PRESET_SLEEP = "sleep"
sys.modules["homeassistant.components.climate.const"] = climate_const

homeassistant_config = types.ModuleType("homeassistant.config_entries")
class ConfigEntry:
    pass
homeassistant_config.ConfigEntry = ConfigEntry
sys.modules["homeassistant.config_entries"] = homeassistant_config

homeassistant_const = types.ModuleType("homeassistant.const")
homeassistant_const.ATTR_TEMPERATURE = "temperature"
class UnitOfTemperature:
    CELSIUS = "C"
homeassistant_const.UnitOfTemperature = UnitOfTemperature
class Platform:
    CLIMATE = "climate"
    SENSOR = "sensor"
homeassistant_const.Platform = Platform
sys.modules["homeassistant.const"] = homeassistant_const

homeassistant_core = types.ModuleType("homeassistant.core")
class HomeAssistant:
    pass
homeassistant_core.HomeAssistant = HomeAssistant
sys.modules["homeassistant.core"] = homeassistant_core

helpers_entity = types.ModuleType("homeassistant.helpers.entity")
class DeviceInfo(dict):
    pass
helpers_entity.DeviceInfo = DeviceInfo
sys.modules["homeassistant.helpers.entity"] = helpers_entity

helpers_entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
class AddEntitiesCallback:
    pass
helpers_entity_platform.AddEntitiesCallback = AddEntitiesCallback
sys.modules["homeassistant.helpers.entity_platform"] = helpers_entity_platform

helpers_update = types.ModuleType("homeassistant.helpers.update_coordinator")
class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
    async def async_config_entry_first_refresh(self):
        return None

helpers_update.CoordinatorEntity = CoordinatorEntity
helpers_update.DataUpdateCoordinator = DataUpdateCoordinator
sys.modules["homeassistant.helpers.update_coordinator"] = helpers_update

from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.cosa.climate import CosaClimate
from custom_components.cosa.const import PRESET_HOME


@pytest.mark.asyncio
async def test_climate_sync_wrappers_do_not_raise():
    """Ensure sync wrappers for climate methods are available and don't raise NotImplementedError."""

    # Setup fake hass loop
    hass = SimpleNamespace(loop=asyncio.get_event_loop())

    # Setup fake client with async methods
    async def fake_set_mode(**kwargs):
        return True

    async def fake_set_target_temperatures(**kwargs):
        return True

    client = SimpleNamespace(
        set_mode=AsyncMock(side_effect=fake_set_mode),
        set_target_temperatures=AsyncMock(side_effect=fake_set_target_temperatures),
        login=AsyncMock(return_value=None),
        _token="fake_token",
    )

    # Coordinator minimal implementation
    coordinator = SimpleNamespace(
        data={
            "temperature": 19.5,
            "target_temperature": 21.0,
            "humidity": 45,
            "combi_state": "on",
            "option": "home",
            "mode": "manual",
            "target_temperatures": {"home": 21, "away": 16, "sleep": 18, "custom": 20},
        },
        client=client,
        endpoint_id="end_001",
        async_request_refresh=AsyncMock(return_value=None),
    )

    # config_entry used only for ids
    config_entry = SimpleNamespace(entry_id="abc123", data={"device_name": "unit1", "username": "user"})

    # Create entity
    e = CosaClimate(coordinator, config_entry)
    e.hass = hass

    # Call async methods to ensure the async API path works correctly
    await e.async_set_temperature(**{ATTR_TEMPERATURE: 22})
    await e.async_set_hvac_mode(HVACMode.HEAT)
    await e.async_set_preset_mode(PRESET_HOME)

    # Allow pending async operations to finish
    await asyncio.sleep(0)

    # Verify async client calls were invoked
    assert client.set_mode.called

    # Call synchronous wrappers (should not raise and should call underlying client)
    e.set_temperature(**{ATTR_TEMPERATURE: 22})
    e.set_hvac_mode(HVACMode.HEAT)
    e.set_preset_mode(PRESET_HOME)
    await asyncio.sleep(0)
    assert client.set_mode.called


def test_climate_properties_guard_none():
    """Ensure properties return None when coordinator.data is None (no crash)."""
    coordinator = SimpleNamespace(data=None, client=None, endpoint_id=None)
    config_entry = SimpleNamespace(entry_id="abc123", data={})
    e = CosaClimate(coordinator, config_entry)
    assert e.current_temperature is None
    assert e.target_temperature is None
    assert e.hvac_mode is None
    assert e.preset_mode is None


@pytest.mark.asyncio
async def test_coordinator_client_is_created_if_none(monkeypatch):
    """If coordinator.client is None a new client should be created and used for set operations."""
    hass = SimpleNamespace(loop=asyncio.get_event_loop())

    # Fake client with AsyncMock methods
    async def fake_set_mode(**kwargs):
        return True

    async def fake_set_target_temperatures(**kwargs):
        return True

    fake_client = SimpleNamespace(
        set_mode=AsyncMock(side_effect=fake_set_mode),
        set_target_temperatures=AsyncMock(side_effect=fake_set_target_temperatures),
        list_endpoints=AsyncMock(return_value=[{"id": "end_001"}]),
        login=AsyncMock(return_value=None),
        _token="fake_token",
        _endpoint_id=None,
    )

    # Monkeypatch constructor of CosaAPIClient in the climate module to return our fake_client
    monkeypatch.setattr(
        "custom_components.cosa.climate.CosaAPIClient",
        lambda username=None, password=None, endpoint_id=None, token=None, session=None: fake_client,
    )

    coordinator = SimpleNamespace(
        data={
            "temperature": 19.5,
            "target_temperature": 21.0,
            "humidity": 45,
            "combi_state": "on",
            "option": "home",
            "mode": "manual",
            "target_temperatures": {"home": 21, "away": 16, "sleep": 18, "custom": 20},
        },
        client=None,
        endpoint_id=None,
        async_request_refresh=AsyncMock(return_value=None),
    )

    config_entry = SimpleNamespace(entry_id="def456", data={"username": "user", "password": "pass"})
    e = CosaClimate(coordinator, config_entry)
    e.hass = hass

    # Call async methods and verify they used the fake client
    await e.async_set_temperature(**{ATTR_TEMPERATURE: 22})
    await e.async_set_hvac_mode(HVACMode.HEAT)
    await e.async_set_preset_mode(PRESET_HOME)

    assert fake_client.set_mode.called
