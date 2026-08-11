import asyncio
import base64
import json
import logging
import ssl
from typing import Any, Optional
from urllib.parse import urlparse

import aiohttp


logger = logging.getLogger(__name__)


class RemnawaveAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


def _positive_int_or_none(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isascii() and stripped.isdigit():
            candidate = int(stripped)
            return candidate if candidate > 0 else None
    return None


class RemnawaveAPI:
    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        secret_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        caddy_token: str | None = None,
        auth_type: str = "api_key",
    ):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.api_key = (api_key or "").strip()
        self.secret_key = (secret_key or "").strip() or None
        self.username = (username or "").strip() or None
        self.password = (password or "").strip() or None
        self.caddy_token = (caddy_token or "").strip() or None
        self.auth_type = (auth_type or "api_key").strip().lower()
        self.session: Optional[aiohttp.ClientSession] = None

    def _detect_connection_type(self) -> str:
        parsed = urlparse(self.base_url)
        local_hosts = {"localhost", "127.0.0.1", "remnawave", "remnawave-backend", "app", "api"}
        host = parsed.hostname or ""
        if host in local_hosts:
            return "local"
        if host.startswith(("192.168.", "10.", "172.")) or host.endswith(".local"):
            return "local"
        return "external"

    def _prepare_auth_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
        }
        if self.auth_type == "basic" and self.username and self.password:
            creds = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["X-Api-Key"] = f"Basic {creds}"
        elif self.auth_type == "caddy":
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            if self.caddy_token:
                headers["X-Api-Key"] = self.caddy_token
        else:
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _prepare_cookies(self) -> dict[str, str] | None:
        if not self.secret_key:
            return None
        if ":" in self.secret_key:
            key_name, key_value = self.secret_key.split(":", 1)
            return {key_name: key_value}
        return {self.secret_key: self.secret_key}

    async def __aenter__(self):
        headers = self._prepare_auth_headers()
        cookies = self._prepare_cookies()
        connector_kwargs = {}
        if self._detect_connection_type() == "local" and self.base_url.startswith("https://"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector_kwargs["ssl"] = ssl_context
            headers.update({"X-Forwarded-Host": "localhost", "Host": "localhost"})
        connector = aiohttp.TCPConnector(**connector_kwargs)
        session_kwargs = {
            "timeout": aiohttp.ClientTimeout(total=60, connect=10),
            "headers": headers,
            "connector": connector,
        }
        if cookies:
            session_kwargs["cookies"] = cookies
        self.session = aiohttp.ClientSession(**session_kwargs)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        allow_raw_text: bool = False,
    ) -> dict | str:
        if not self.session:
            raise RemnawaveAPIError("Session not initialized")
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        base_delay = 1.0
        for attempt in range(max_retries + 1):
            try:
                kwargs = {"params": params}
                if data is not None:
                    kwargs["json"] = data
                async with self.session.request(method, url, **kwargs) as response:
                    response_text = await response.text()
                    if allow_raw_text and response.status < 400:
                        return response_text
                    try:
                        response_data = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        response_data = {"raw_response": response_text}
                    if response.status == 429 and attempt < max_retries:
                        retry_after = float(response.headers.get("Retry-After", base_delay * (2**attempt)))
                        await asyncio.sleep(retry_after)
                        continue
                    if response.status >= 400:
                        raise RemnawaveAPIError(
                            str(response_data.get("message") or f"HTTP {response.status}"),
                            status_code=response.status,
                            response_data=response_data if isinstance(response_data, dict) else None,
                        )
                    return response_data if isinstance(response_data, dict) else {"response": response_data}
            except aiohttp.ClientError as e:
                if attempt < max_retries:
                    await asyncio.sleep(base_delay * (2**attempt))
                    continue
                raise RemnawaveAPIError(f"Request failed: {e!s}")
        raise RemnawaveAPIError(f"Max retries exceeded for {method} {endpoint}")

    async def _resolve_user_id(self, identifier: Any) -> int | None:
        numeric_id = _positive_int_or_none(identifier)
        if numeric_id is not None:
            return numeric_id
        lookup = str(identifier or "").strip()
        if not lookup:
            return None
        for payload in ({"shortUuid": lookup}, {"username": lookup}):
            try:
                response = await self._make_request("POST", "/api/users/resolve", payload)
                data = response.get("response") or {}
                resolved_id = _positive_int_or_none(data.get("id"))
                if resolved_id is not None:
                    return resolved_id
            except RemnawaveAPIError as e:
                if e.status_code in (400, 404):
                    continue
                raise
        return None

    async def _user_endpoint_identifier(self, identifier: Any) -> str:
        resolved = await self._resolve_user_id(identifier)
        return str(resolved if resolved is not None else str(identifier).strip())

    async def get_user_by_telegram_id(self, telegram_id: int) -> list[dict[str, Any]]:
        try:
            response = await self._make_request("GET", f"/api/users/by-telegram-id/{telegram_id}")
            users = response.get("response") or []
            if isinstance(users, dict):
                users = [users]
            return users
        except RemnawaveAPIError as e:
            if e.status_code not in (400, 404):
                raise
        response = await self._make_request("GET", "/api/users/stream", params={"size": 1000, "telegramId": telegram_id})
        return (response.get("response") or {}).get("users", []) or []

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        try:
            response = await self._make_request("GET", f"/api/users/by-username/{username}")
            return response.get("response")
        except RemnawaveAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_user_by_short_uuid(self, short_uuid: str) -> dict[str, Any] | None:
        try:
            response = await self._make_request("GET", f"/api/users/by-short-uuid/{short_uuid}")
            return response.get("response")
        except RemnawaveAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_subscription_info(self, short_uuid: str) -> dict[str, Any]:
        response = await self._make_request("GET", f"/api/sub/{short_uuid}/info")
        return response.get("response") or {}

    async def get_subscription_links(self, short_uuid: str) -> dict[str, str]:
        base_url = f"{self.base_url}/api/sub/{short_uuid}"
        return {
            "base": base_url,
            "stash": f"{base_url}/stash",
            "singbox": f"{base_url}/singbox",
            "singbox_legacy": f"{base_url}/singbox-legacy",
            "mihomo": f"{base_url}/mihomo",
            "json": f"{base_url}/json",
            "v2ray_json": f"{base_url}/v2ray-json",
            "clash": f"{base_url}/clash",
        }

    async def get_user_accessible_nodes(self, identifier: str) -> list[dict[str, Any]]:
        endpoint_id = await self._user_endpoint_identifier(identifier)
        response = await self._make_request("GET", f"/api/users/{endpoint_id}/accessible-nodes")
        return (response.get("response") or {}).get("activeNodes", []) or []

    async def get_user_devices_all(self, identifier: str) -> dict[str, Any]:
        endpoint_id = await self._user_endpoint_identifier(identifier)
        devices: list[dict[str, Any]] = []
        start = 0
        page_size = 1000
        while True:
            try:
                response = await self._make_request(
                    "GET",
                    f"/api/hwid/devices/{endpoint_id}",
                    params={"start": start, "size": page_size},
                )
            except RemnawaveAPIError as e:
                if e.status_code == 404:
                    return {"devices": [], "total": 0}
                raise
            data = response.get("response") or {}
            page_devices = data.get("devices") or []
            total = int(data.get("total") or 0)
            devices.extend(page_devices)
            if len(devices) >= total or not page_devices:
                return {"devices": devices, "total": len(devices)}
            start += len(page_devices)

    async def reset_user_devices(self, identifier: str) -> bool:
        resolved_id = await self._resolve_user_id(identifier)
        if resolved_id is not None:
            response = await self._make_request("POST", "/api/hwid/devices/delete-all", data={"userId": resolved_id})
            payload = response.get("response") if isinstance(response, dict) else None
            if isinstance(payload, dict):
                remaining = int(payload.get("total") or len(payload.get("devices") or []))
                return remaining == 0
            return True
        devices_info = await self.get_user_devices_all(str(identifier))
        devices = devices_info.get("devices") or []
        failed = 0
        for device in devices:
            hwid = str(device.get("hwid") or "").strip()
            if not hwid:
                continue
            if not await self.remove_device(str(identifier), hwid):
                failed += 1
        return failed < max(1, len(devices) / 2)

    async def remove_device(self, identifier: str, device_hwid: str) -> bool:
        resolved_id = await self._resolve_user_id(identifier)
        payload = {"hwid": device_hwid}
        if resolved_id is not None:
            payload["userId"] = resolved_id
        else:
            payload["userUuid"] = str(identifier)
        try:
            response = await self._make_request("POST", "/api/hwid/devices/delete", data=payload)
            payload_response = response.get("response") if isinstance(response, dict) else None
            if isinstance(payload_response, dict) and isinstance(payload_response.get("devices"), list):
                return all(str(item.get("hwid") or "") != str(device_hwid) for item in payload_response["devices"])
            devices_info = await self.get_user_devices_all(str(identifier))
            devices = devices_info.get("devices") or []
            return all(str(item.get("hwid") or "") != str(device_hwid) for item in devices)
        except RemnawaveAPIError:
            return False

    async def revoke_user_subscription(
        self,
        identifier: str,
        new_short_uuid: str | None = None,
        revoke_only_passwords: bool = False,
    ) -> dict[str, Any]:
        endpoint_id = await self._user_endpoint_identifier(identifier)
        payload = {}
        if new_short_uuid:
            payload["shortUuid"] = new_short_uuid
        if revoke_only_passwords:
            payload["revokeOnlyPasswords"] = True
        response = await self._make_request("POST", f"/api/users/{endpoint_id}/actions/revoke", data=payload)
        return response.get("response") or {}
