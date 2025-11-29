import asyncio
import pytest
import json
import os
import sys
import importlib.machinery
import types
from unittest.mock import patch

# Ensure the test package path and fake package modules
tests_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
package_root = os.path.join(tests_root, 'custom_components')

sys.path.insert(0, tests_root)
sys.modules['custom_components'] = types.ModuleType('custom_components')
sys.modules['custom_components.cosa'] = types.ModuleType('custom_components.cosa')

# Create minimal Home Assistant stubs to allow importing integration modules that rely on HA
homeassistant = types.ModuleType('homeassistant')
homeassistant.components = types.ModuleType('homeassistant.components')
homeassistant.components.climate = types.ModuleType('homeassistant.components.climate')

# Minimal ClimateEntity
class ClimateEntity:
    pass

setattr(homeassistant.components.climate, 'ClimateEntity', ClimateEntity)

# Minimal HVACMode and feature flags
class HVACMode:
    HEAT = 'heat'
    OFF = 'off'

class ClimateEntityFeature:
    TARGET_TEMPERATURE = 1
    PRESET_MODE = 2

setattr(homeassistant.components.climate, 'HVACMode', HVACMode)
setattr(homeassistant.components.climate, 'ClimateEntityFeature', ClimateEntityFeature)

homeassistant.components.climate.const = types.ModuleType('homeassistant.components.climate.const')
setattr(homeassistant.components.climate.const, 'PRESET_AWAY', 'away')
setattr(homeassistant.components.climate.const, 'PRESET_HOME', 'home')
setattr(homeassistant.components.climate.const, 'PRESET_SLEEP', 'sleep')

homeassistant.const = types.ModuleType('homeassistant.const')
setattr(homeassistant.const, 'ATTR_TEMPERATURE', 'temperature')
class UnitOfTemperature:
    CELSIUS = 'C'
setattr(homeassistant.const, 'UnitOfTemperature', UnitOfTemperature)

homeassistant.config_entries = types.ModuleType('homeassistant.config_entries')
class ConfigEntry:
    def __init__(self, entry_id, data):
        self.entry_id = entry_id
        self.data = data
setattr(homeassistant.config_entries, 'ConfigEntry', ConfigEntry)

homeassistant.helpers = types.ModuleType('homeassistant.helpers')
homeassistant.helpers.entity = types.ModuleType('homeassistant.helpers.entity')
class DeviceInfo(dict):
    pass
setattr(homeassistant.helpers.entity, 'DeviceInfo', DeviceInfo)

homeassistant.helpers.entity_platform = types.ModuleType('homeassistant.helpers.entity_platform')
from typing import Callable
setattr(homeassistant.helpers.entity_platform, 'AddEntitiesCallback', Callable)
homeassistant.helpers.update_coordinator = types.ModuleType('homeassistant.helpers.update_coordinator')
class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval=None):
        self.hass = hass
        self._logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
    async def async_request_refresh(self):
        return
class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
setattr(homeassistant.helpers.update_coordinator, 'DataUpdateCoordinator', DataUpdateCoordinator)
setattr(homeassistant.helpers.update_coordinator, 'CoordinatorEntity', CoordinatorEntity)

homeassistant.core = types.ModuleType('homeassistant.core')
class HomeAssistant:
    pass
setattr(homeassistant.core, 'HomeAssistant', HomeAssistant)

# Register stubs in sys.modules
sys.modules['homeassistant'] = homeassistant
sys.modules['homeassistant.components'] = homeassistant.components
sys.modules['homeassistant.components.climate'] = homeassistant.components.climate
sys.modules['homeassistant.components.climate.const'] = homeassistant.components.climate.const
sys.modules['homeassistant.const'] = homeassistant.const
sys.modules['homeassistant.config_entries'] = homeassistant.config_entries
sys.modules['homeassistant.helpers'] = homeassistant.helpers
sys.modules['homeassistant.helpers.entity'] = homeassistant.helpers.entity
sys.modules['homeassistant.helpers.entity_platform'] = homeassistant.helpers.entity_platform
sys.modules['homeassistant.helpers.update_coordinator'] = homeassistant.helpers.update_coordinator
sys.modules['homeassistant.core'] = homeassistant.core

# Load const and api (source) modules without executing __init__.py
const_path = os.path.join(package_root, 'cosa', 'const.py')
const_loader = importlib.machinery.SourceFileLoader('custom_components.cosa.const', const_path)
const_mod = const_loader.load_module()
sys.modules['custom_components.cosa.const'] = const_mod

api_path = os.path.join(package_root, 'cosa', 'api.py')
api_loader = importlib.machinery.SourceFileLoader('custom_components.cosa.api', api_path)
api_mod = api_loader.load_module()
sys.modules['custom_components.cosa.api'] = api_mod

climate_path = os.path.join(package_root, 'cosa', 'climate.py')
climate_loader = importlib.machinery.SourceFileLoader('custom_components.cosa.climate', climate_path)
climate_mod = climate_loader.load_module()
sys.modules['custom_components.cosa.climate'] = climate_mod

from custom_components.cosa.api import CosaAPIClient
from custom_components.cosa.climate import CosaClimate


class MockResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    async def json(self):
        return self._payload

    async def text(self):
        return json.dumps(self._payload)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


# Mock responses used by the fake session
def mock_post_success_login(url, json_payload=None, headers=None):
    payload = {
        "success": True,
        "data": {
            "authToken": "SAMPLETOKEN123",
            "endpoints": [{"id": "end_001"}],
        },
    }
    return MockResponse(payload, status=200)


def mock_post_get_endpoint(url, json_payload=None, headers=None):
    endpoint_id = None
    if isinstance(json_payload, dict):
        endpoint_id = json_payload.get('endpoint') or json_payload.get('id')
    endpoint_id = endpoint_id or 'end_001'
    payload = {
        "endpoint": {
            "id": endpoint_id,
            "temperature": 20.5,
            "combiState": "on",
            "option": "home",
            "targetTemperatures": {"home": 21, "away": 16},
            "humidity": 40,
        }
    }
    return MockResponse(payload, status=200)


def mock_post_list_endpoints(url, json_payload=None, headers=None):
    payload = {
        "endpoints": [
            {
                "id": "66e06d3edac55e12009be544",
                "name": "Evim",
                "active": True,
                "device": "65a14f74774cc50932c98980",
                "option": "home",
                "mode": "schedule",
                "operationMode": "heating",
                "relayOption": "off",
                "relayMode": "manual",
                "targetTemperature": 25.8,
                "temperature": 26,
                "humidity": 54.8,
                "createdAt": "2024-09-10T16:01:02.889Z",
                "updatedAt": "2025-11-29T14:05:35.825Z",
                "isConnected": True,
            }
        ],
        "ok": 1,
    }
    return MockResponse(payload, status=200)


def mock_post_get_user_info(url, json_payload=None, headers=None):
    payload = {
        "user": {
            "name": "Abdulhamit",
            "email": "hamitdurmus@gmail.com",
            "provider": "cosa",
            "id": "66e06d24539c431400acb37b",
        },
        "ok": 1,
    }
    return MockResponse(payload, status=200)


@pytest.mark.asyncio
async def test_login_list_get_flow():
    # Basic flow: login -> list_endpoints -> get_endpoint_status
    client = CosaAPIClient(username="test@example.com", password="testpass")

    def fake_session_post(url, *args, **kwargs):
        json_payload = kwargs.get('json') or kwargs.get('json_payload')
        headers = kwargs.get('headers')
        if url.endswith('/users/login') or url.endswith('/auth/login'):
            return mock_post_success_login(url, json_payload=json_payload, headers=headers)
        elif url.endswith('/endpoints/getEndpoint'):
            return mock_post_get_endpoint(url, json_payload=json_payload, headers=headers)
        else:
            return mock_post_get_endpoint(url, json_payload=json_payload, headers=headers)

    def fake_get(*args, **kwargs):
        # For GET calls, json_payload will be None
        return mock_post_get_endpoint(args[0], json_payload=None, headers=kwargs.get('headers'))

    with patch('aiohttp.ClientSession') as MockSession:
        mock_sess_instance = MockSession.return_value
        mock_sess_instance.post = fake_session_post
        mock_sess_instance.get = fake_get

        # perform login
        await client.login()
        print('Token after login:', client._token)
        assert client._token == 'SAMPLETOKEN123'

        # list endpoints
        eps = await client.list_endpoints()
        print('List endpoints:', eps)
        assert isinstance(eps, list) and eps and eps[0]['id'] == 'end_001'

        # get endpoint status
        status = await client.get_endpoint_status('end_001')
        print('Endpoint status:', status)
        assert status and status.get('endpoint') and status['endpoint']['id'] == 'end_001'

        await client.close()

    # Additional realistic sample response test for list_endpoints
    client2 = CosaAPIClient(username="test@example.com", password="testpass")

    def dispatch_realistic_post(url, *args, **kwargs):
        json_payload = kwargs.get('json') or kwargs.get('json_payload')
        headers = kwargs.get('headers')
        if url.endswith('/users/login') or url.endswith('/auth/login'):
            return mock_post_success_login(url, json_payload=json_payload, headers=headers)
        return mock_post_list_endpoints(url, json_payload=json_payload, headers=headers)

    with patch('aiohttp.ClientSession') as MockSession:
        mock_sess_instance = MockSession.return_value
        mock_sess_instance.post = dispatch_realistic_post
        mock_sess_instance.get = lambda *args, **kwargs: mock_post_list_endpoints(args[0], json_payload=None, headers=kwargs.get('headers'))

        await client2.login()
        eps2 = await client2.list_endpoints()
        print('Realistic List endpoints:', eps2)
        assert eps2 and isinstance(eps2, list)
        assert eps2[0]['id'] == '66e06d3edac55e12009be544'
        await client2.close()

    # Token-only flow test
    client3 = CosaAPIClient(token='SAMPLETOKEN123')

    def dispatch_token_post(url, *args, **kwargs):
        json_payload = kwargs.get('json') or kwargs.get('json_payload')
        headers = kwargs.get('headers')
        if url.endswith('/users/getInfo'):
            return mock_post_get_user_info(url, json_payload=json_payload, headers=headers)
        if url.endswith('/endpoints/getEndpoints') or url.endswith('/endpoints/list'):
            return mock_post_list_endpoints(url, json_payload=json_payload, headers=headers)
        return mock_post_get_endpoint(url, json_payload=json_payload, headers=headers)

    with patch('aiohttp.ClientSession') as MockSession:
        mock_sess_instance = MockSession.return_value
        mock_sess_instance.post = dispatch_token_post
        mock_sess_instance.get = lambda *args, **kwargs: mock_post_list_endpoints(args[0], json_payload=None, headers=kwargs.get('headers'))

        await client3.get_user_info()
        eps3 = await client3.list_endpoints()
        print('Token only list endpoints:', eps3)
        assert eps3 and isinstance(eps3, list)
        assert eps3[0]['id'] == '66e06d3edac55e12009be544'

    # Simple coordinator + entity mapping test
    class DummyCoordinator:
        def __init__(self, data):
            self.data = data
            self.client = None
            self.endpoint_id = '66e06d3edac55e12009be544'

    class DummyConfigEntry:
        def __init__(self):
            self.entry_id = 'entry_1'
            self.data = {'username': 'test@example.com', 'device_name': 'Evim'}

    coord_data = {
        'temperature': 26,
        'target_temperature': 25.8,
        'humidity': 54.8,
        'combi_state': 'on',
        'option': 'home',
        'mode': 'schedule',
        'target_temperatures': {'home': 26, 'away': 15, 'sleep': 26.3, 'custom': 20},
        'name': 'Evim',
        'operation_mode': 'heating',
    }

    coord = DummyCoordinator(coord_data)
    entry = DummyConfigEntry()
    entity = CosaClimate(coord, entry)
    # Validate preset mapping without debug prints
    # Basic expectations
    assert entity.current_temperature == 26
    assert entity.target_temperature == 25.8
    assert entity.preset_mode == 'schedule' or entity.preset_mode == 'auto' or entity.preset_mode == 'home'
@pytest.mark.asyncio
async def test_session_close_behavior_new():
    # 1) External (passed) session should NOT be closed by client
    class DummySession:
        def __init__(self):
            self.closed = False
            self.close_called = False

        def post(self, url, *args, **kwargs):
            return mock_post_success_login(url, json_payload=kwargs.get('json') or kwargs.get('json_payload'), headers=kwargs.get('headers'))

        def get(self, url, *args, **kwargs):
            return mock_post_get_endpoint(url, json_payload=kwargs.get('json') or kwargs.get('json_payload'), headers=kwargs.get('headers'))

        async def close(self):
            self.close_called = True
            self.closed = True

    dummy_session = DummySession()
    client = CosaAPIClient(username="test@example.com", password="testpass", session=dummy_session)
    await client.login()
    assert not dummy_session.close_called
    await client.close()
    assert dummy_session.close_called is False

    # 2) Session created by the client (not passed) should be closed by close()
    class OwnedSession:
        def __init__(self):
            self.closed = False
            self.close_called = False

        def post(self, url, *args, **kwargs):
            return mock_post_success_login(url, json_payload=kwargs.get('json') or kwargs.get('json_payload'), headers=kwargs.get('headers'))

        def get(self, url, *args, **kwargs):
            return mock_post_get_endpoint(url, json_payload=kwargs.get('json') or kwargs.get('json_payload'), headers=kwargs.get('headers'))

        async def close(self):
            self.close_called = True
            self.closed = True

    import custom_components.cosa.api as api_module
    original_client_session = api_module.aiohttp.ClientSession
    try:
        api_module.aiohttp.ClientSession = lambda *args, **kwargs: OwnedSession()
        client2 = CosaAPIClient(username="test@example.com", password="testpass")
        s = await client2._get_session()
        assert client2._own_session is True
        await client2.close()
        assert s.closed is True
    finally:
        api_module.aiohttp.ClientSession = original_client_session


# Removed script-style execution; tests should be run via pytest
