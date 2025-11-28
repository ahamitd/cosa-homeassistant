"""API client for COSA integration."""

import logging
from typing import Any, Dict, Optional
import aiohttp

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ENDPOINT_LOGIN,
    ENDPOINT_GET_ENDPOINT,
    ENDPOINT_SET_MODE,
    ENDPOINT_SET_TARGET_TEMPERATURES,
    ENDPOINT_LIST_ENDPOINTS,
    USER_AGENT,
    CONTENT_TYPE,
)

_LOGGER = logging.getLogger(__name__)


class CosaAPIError(Exception):
    """Exception raised for API errors."""

    pass


class CosaAPIClient:
    """Client for COSA API."""

    def __init__(self, username: str, password: str, endpoint_id: Optional[str] = None):
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._endpoint_id = endpoint_id
        self._token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._retry_count = 3  # Retry count for failed requests

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
            )
        return self._session

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def login(self) -> bool:
        """Login and get authentication token."""
        # Try different login endpoints and payload formats
        login_endpoints = [
            "/users/login",
            "/auth/login",
            "/login",
        ]
        
        payload_formats = [
            {"username": self._username, "password": self._password},
            {"email": self._username, "password": self._password},
            {"user": self._username, "password": self._password},
        ]

        session = await self._get_session()
        last_error = None

        for endpoint in login_endpoints:
            for payload in payload_formats:
                try:
                    url = f"{API_BASE_URL}{endpoint}"
                    headers = {
                        "User-Agent": USER_AGENT,
                        "Content-Type": CONTENT_TYPE,
                    }

                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Try to extract token from various response formats
                            # Note: API uses authToken (camelCase) as primary format
                            token = None
                            if "authToken" in data:
                                token = data["authToken"]
                            elif "token" in data:
                                token = data["token"]
                            elif "authtoken" in data:
                                token = data["authtoken"]
                            elif "data" in data:
                                if isinstance(data["data"], dict):
                                    token = (
                                        data["data"].get("authToken") or
                                        data["data"].get("token") or
                                        data["data"].get("authtoken")
                                    )
                                elif isinstance(data["data"], str):
                                    token = data["data"]
                            elif "access_token" in data:
                                token = data["access_token"]
                            elif "accessToken" in data:
                                token = data["accessToken"]

                            # Log response for debugging if token not found
                            if not token:
                                _LOGGER.debug("Response data keys: %s", list(data.keys()) if isinstance(data, dict) else "Not a dict")
                                _LOGGER.debug("Response preview: %s", str(data)[:200] if data else "Empty response")

                            if token:
                                self._token = token
                                
                                # Try to extract endpoint ID from response
                                if not self._endpoint_id:
                                    if "endpoint" in data:
                                        endpoint_data = data["endpoint"]
                                        if isinstance(endpoint_data, list) and len(endpoint_data) > 0:
                                            self._endpoint_id = endpoint_data[0].get("id") or endpoint_data[0].get("_id")
                                        elif isinstance(endpoint_data, dict):
                                            self._endpoint_id = endpoint_data.get("id") or endpoint_data.get("_id")
                                    elif "endpoints" in data:
                                        endpoints = data["endpoints"]
                                        if isinstance(endpoints, list) and len(endpoints) > 0:
                                            self._endpoint_id = endpoints[0].get("id") or endpoints[0].get("_id")
                                    elif "user" in data:
                                        user_data = data["user"]
                                        if "endpoint" in user_data:
                                            endpoint_data = user_data["endpoint"]
                                            if isinstance(endpoint_data, list) and len(endpoint_data) > 0:
                                                self._endpoint_id = endpoint_data[0].get("id") or endpoint_data[0].get("_id")
                                            elif isinstance(endpoint_data, dict):
                                                self._endpoint_id = endpoint_data.get("id") or endpoint_data.get("_id")

                                _LOGGER.info("Successfully logged in to COSA API")
                                return True
                            else:
                                _LOGGER.debug("Token not found in response from %s", endpoint)
                                continue
                        elif response.status == 401:
                            # Invalid credentials, don't try other formats
                            error_text = await response.text()
                            _LOGGER.error("Invalid credentials: %s", error_text)
                            raise CosaAPIError("Invalid username or password")
                        else:
                            error_text = await response.text()
                            _LOGGER.debug(
                                "Login attempt failed with status %s: %s", response.status, error_text
                            )
                            last_error = f"Status {response.status}: {error_text}"
                            continue

                except aiohttp.ClientError as err:
                    _LOGGER.debug("Error connecting to %s: %s", endpoint, err)
                    last_error = f"Connection error: {err}"
                    continue
                except CosaAPIError:
                    # Re-raise authentication errors
                    raise
                except Exception as err:
                    _LOGGER.debug("Unexpected error during login: %s", err)
                    last_error = f"Unexpected error: {err}"
                    continue

        # If we get here, all login attempts failed
        raise CosaAPIError(f"Login failed. Last error: {last_error}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        if not self._token:
            raise CosaAPIError("Not authenticated. Please login first.")

        # API expects authtoken (lowercase) in headers based on working config
        return {
            "authtoken": self._token,
            "User-Agent": USER_AGENT,
            "Content-Type": CONTENT_TYPE,
        }

    async def get_endpoint_status(self, endpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """Get endpoint status."""
        endpoint = endpoint_id or self._endpoint_id
        if not endpoint:
            raise CosaAPIError("Endpoint ID is required")

        for attempt in range(self._retry_count):
            try:
                session = await self._get_session()
                url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINT}"

                payload = {"endpoint": endpoint}
                headers = self._get_headers()

                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 401:
                        # Token expired, try to re-login
                        _LOGGER.warning("Token expired, attempting to re-login")
                        await self.login()
                        if attempt < self._retry_count - 1:
                            continue
                    else:
                        error_text = await response.text()
                        _LOGGER.error(
                            "Get endpoint status failed with status %s: %s",
                            response.status,
                            error_text,
                        )
                        if attempt < self._retry_count - 1:
                            continue
                        raise CosaAPIError(f"Get status failed: {response.status}")

            except aiohttp.ClientError as err:
                _LOGGER.error("Error getting endpoint status (attempt %d): %s", attempt + 1, err)
                if attempt < self._retry_count - 1:
                    continue
                raise CosaAPIError(f"Connection error: {err}") from err

        raise CosaAPIError("Failed to get endpoint status after retries")

    async def set_mode(
        self,
        mode: str,
        option: str,
        endpoint_id: Optional[str] = None,
    ) -> bool:
        """Set endpoint mode."""
        endpoint = endpoint_id or self._endpoint_id
        if not endpoint:
            raise CosaAPIError("Endpoint ID is required")

        try:
            session = await self._get_session()
            url = f"{API_BASE_URL}{ENDPOINT_SET_MODE}"

            payload = {
                "endpoint": endpoint,
                "mode": mode,
                "option": option,
            }

            headers = self._get_headers()
            headers["provider"] = "cosa"
            headers["content-type"] = CONTENT_TYPE  # Ensure content-type is set

            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    _LOGGER.info("Successfully set mode to %s", option)
                    return True
                else:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Set mode failed with status %s: %s", response.status, error_text
                    )
                    raise CosaAPIError(f"Set mode failed: {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting mode: %s", err)
            raise CosaAPIError(f"Connection error: {err}") from err

    async def set_target_temperatures(
        self,
        home_temp: float,
        away_temp: float,
        sleep_temp: float,
        custom_temp: float,
        endpoint_id: Optional[str] = None,
    ) -> bool:
        """Set target temperatures."""
        endpoint = endpoint_id or self._endpoint_id
        if not endpoint:
            raise CosaAPIError("Endpoint ID is required")

        try:
            session = await self._get_session()
            url = f"{API_BASE_URL}{ENDPOINT_SET_TARGET_TEMPERATURES}"

            payload = {
                "endpoint": endpoint,
                "targetTemperatures": {
                    "home": home_temp,
                    "away": away_temp,
                    "sleep": sleep_temp,
                    "custom": custom_temp,
                },
            }

            headers = self._get_headers()

            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    _LOGGER.info("Successfully set target temperatures")
                    return True
                else:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Set target temperatures failed with status %s: %s",
                        response.status,
                        error_text,
                    )
                    raise CosaAPIError(f"Set temperatures failed: {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting target temperatures: %s", err)
            raise CosaAPIError(f"Connection error: {err}") from err

    async def list_endpoints(self) -> list[Dict[str, Any]]:
        """List all endpoints for the user."""
        if not self._token:
            await self.login()

        try:
            session = await self._get_session()
            url = f"{API_BASE_URL}{ENDPOINT_LIST_ENDPOINTS}"
            headers = self._get_headers()
            last_status = None

            # Try GET first (as in other repository), then POST if needed
            for method in ["get", "post"]:
                try:
                    if method == "get":
                        async with session.get(url, headers=headers) as response:
                            last_status = response.status
                            if last_status == 200:
                                data = await response.json()
                            elif last_status == 401:
                                # Token expired, break to handle below
                                break
                            else:
                                # Try POST method for other status codes
                                continue
                    else:
                        async with session.post(url, json={}, headers=headers) as response:
                            last_status = response.status
                            if last_status == 200:
                                data = await response.json()
                            else:
                                error_text = await response.text()
                                raise CosaAPIError(f"List endpoints failed: {last_status} - {error_text}")
                    
                    # Try different response formats
                    if isinstance(data, list):
                        return data
                    elif "endpoints" in data:
                        endpoints = data["endpoints"]
                        return endpoints if isinstance(endpoints, list) else [endpoints]
                    elif "endpoint" in data:
                        endpoint = data["endpoint"]
                        return endpoint if isinstance(endpoint, list) else [endpoint]
                    elif "data" in data:
                        data_list = data["data"]
                        return data_list if isinstance(data_list, list) else [data_list]
                    return []
                    
                except CosaAPIError:
                    raise
                except Exception as e:
                    if method == "get":
                        _LOGGER.debug("GET method failed, trying POST: %s", e)
                        continue
                    raise
            
            # Handle 401 - token expired
            if last_status == 401:
                _LOGGER.warning("Token expired, attempting to re-login")
                await self.login()
                # Retry once with POST
                async with session.post(url, json={}, headers=self._get_headers()) as retry_response:
                    if retry_response.status == 200:
                        data = await retry_response.json()
                        if isinstance(data, list):
                            return data
                        elif "endpoints" in data:
                            return data["endpoints"] if isinstance(data["endpoints"], list) else [data["endpoints"]]
                raise CosaAPIError("Failed to list endpoints after re-login")
            elif last_status:
                raise CosaAPIError(f"List endpoints failed with status {last_status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Error listing endpoints: %s", err)
            raise CosaAPIError(f"Connection error: {err}") from err

