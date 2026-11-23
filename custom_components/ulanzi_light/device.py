"""BLE transport for Ulanzi lights (service FFF0, write FFF2, notify FFF1)."""

from __future__ import annotations

import asyncio
import logging

from bleak.exc import BleakError
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS,
    BleakClientWithServiceCache,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import NOTIFY_UUID, WRITE_UUID

_LOGGER = logging.getLogger(__name__)

# The light drops an idle link after roughly ten seconds, so every command
# has to be able to reconnect first.
_ERRORS = (BleakError, asyncio.TimeoutError, EOFError, *BLEAK_RETRY_EXCEPTIONS)


class UlanziDevice:
    """One Ulanzi light reached through Home Assistant's Bluetooth stack."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    def _on_disconnect(self, _client) -> None:
        _LOGGER.debug("%s: disconnected", self.name)

    def _on_notify(self, _sender, data: bytearray) -> None:
        _LOGGER.debug("%s: notify %s", self.name, data.hex(" "))

    async def _ensure_connected(self) -> None:
        if self.is_connected:
            return
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise HomeAssistantError(
                f"{self.name} is not in Bluetooth range (or another app holds the connection)"
            )
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self.name,
            disconnected_callback=self._on_disconnect,
            max_attempts=3,
        )
        try:
            await self._client.start_notify(NOTIFY_UUID, self._on_notify)
        except _ERRORS as err:
            _LOGGER.debug("%s: could not subscribe to notifications: %s", self.name, err)

    async def _drop(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.disconnect()
            except _ERRORS:
                pass

    async def send(self, *packets: bytes) -> None:
        """Send packets in order, reconnecting once if the link has gone."""
        async with self._lock:
            last_err: Exception | None = None
            for _attempt in range(2):
                try:
                    await self._ensure_connected()
                    assert self._client is not None
                    for packet in packets:
                        await self._client.write_gatt_char(WRITE_UUID, packet)
                        await asyncio.sleep(0.08)
                    return
                except _ERRORS as err:
                    last_err = err
                    _LOGGER.debug("%s: write failed (%s), reconnecting", self.name, err)
                    await self._drop()
            raise HomeAssistantError(f"Could not reach {self.name}: {last_err}")

    async def disconnect(self) -> None:
        async with self._lock:
            await self._drop()
