"""BLE transport for Ulanzi lights (service FFF0, write FFF2, notify FFF1)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
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

from .const import CMD_QUERY, NOTIFY_UUID, WRITE_UUID, UlanziStatus, parse_status

_LOGGER = logging.getLogger(__name__)

# The light drops the link about ten seconds after connecting, so every
# command has to be able to reconnect first.
_ERRORS = (BleakError, asyncio.TimeoutError, EOFError, *BLEAK_RETRY_EXCEPTIONS)

# Pause between packets, and how long to wait for the answer to a query.
_WRITE_GAP = 0.08
_STATUS_TIMEOUT = 1.5


class UlanziDevice:
    """One Ulanzi light reached through Home Assistant's Bluetooth stack."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self.status: UlanziStatus | None = None
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._status_event = asyncio.Event()
        self._listeners: list[Callable[[UlanziStatus], None]] = []

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    def add_listener(self, listener: Callable[[UlanziStatus], None]) -> Callable[[], None]:
        """Call listener for every status the light sends; returns a remover."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _on_disconnect(self, _client) -> None:
        _LOGGER.debug("%s: disconnected", self.name)

    def _on_notify(self, _sender, data: bytearray) -> None:
        _LOGGER.debug("%s: notify %s", self.name, data.hex(" "))
        status = parse_status(bytes(data))
        if status is None:
            return
        self.status = status
        self._status_event.set()
        for listener in list(self._listeners):
            listener(status)

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

    async def send(
        self, *packets: bytes, query: bool = True, release: bool = False
    ) -> UlanziStatus | None:
        """Send packets in order, reconnecting once if the link has gone.

        With query the light is asked for its state afterwards and the answer
        is returned (None if it sent none). With release the link is closed
        again straight away, leaving the light free for other apps.
        """
        async with self._lock:
            last_err: Exception | None = None
            for _attempt in range(2):
                try:
                    await self._ensure_connected()
                    assert self._client is not None
                    for packet in packets:
                        _LOGGER.debug("%s: write %s", self.name, packet.hex(" "))
                        await self._client.write_gatt_char(WRITE_UUID, packet)
                        await asyncio.sleep(_WRITE_GAP)
                    status = await self._query() if query else None
                    if release:
                        await self._drop()
                    return status
                except _ERRORS as err:
                    last_err = err
                    _LOGGER.debug("%s: write failed (%s), reconnecting", self.name, err)
                    await self._drop()
            raise HomeAssistantError(f"Could not reach {self.name}: {last_err}")

    async def _query(self) -> UlanziStatus | None:
        assert self._client is not None
        self._status_event.clear()
        await self._client.write_gatt_char(WRITE_UUID, CMD_QUERY)
        try:
            async with asyncio.timeout(_STATUS_TIMEOUT):
                await self._status_event.wait()
        except TimeoutError:
            _LOGGER.debug("%s: no answer to the status query", self.name)
            return None
        return self.status

    async def disconnect(self) -> None:
        async with self._lock:
            await self._drop()
