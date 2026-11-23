"""Light platform for Ulanzi lights."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components import bluetooth
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    EFFECT_OFF,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CMD_OFF,
    CMD_ON,
    DOMAIN,
    EFFECTS,
    MAX_KELVIN,
    MIN_KELVIN,
    UlanziStatus,
    cmd_brightness,
    cmd_color_temp,
    cmd_effect,
)
from .device import UlanziDevice

_LOGGER = logging.getLogger(__name__)

# How often the light is asked for its state, to pick up changes made on the
# light itself or in the Ulanzi app. Home Assistant's own polling is not used:
# it would also poll after every command and close the link each time.
POLL_INTERVAL = timedelta(seconds=60)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([UlanziLight(entry.runtime_data)])


class UlanziLight(LightEntity, RestoreEntity):
    """An Ulanzi light.

    The state shown is what the light reports. Until it has answered once
    (or on a model that never answers) it is what was last sent.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_assumed_state = True
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = [EFFECT_OFF, *EFFECTS]
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    def __init__(self, device: UlanziDevice) -> None:
        self._device = device
        self._attr_unique_id = device.address
        self._attr_is_on = False
        self._attr_brightness = 128
        self._attr_color_temp_kelvin = 5600
        self._attr_effect = EFFECT_OFF
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
            manufacturer="Ulanzi",
            name=device.name,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == STATE_ON
            if (b := last.attributes.get(ATTR_BRIGHTNESS)) is not None:
                self._attr_brightness = int(b)
            if (k := last.attributes.get(ATTR_COLOR_TEMP_KELVIN)) is not None:
                self._attr_color_temp_kelvin = int(k)
            if (e := last.attributes.get(ATTR_EFFECT)) in self._attr_effect_list:
                self._attr_effect = e

        address = self._device.address
        self._attr_available = bluetooth.async_address_present(
            self.hass, address, connectable=True
        )
        self.async_on_remove(self._device.add_listener(self._on_status))
        self.async_on_remove(
            async_track_time_interval(self.hass, self._poll, POLL_INTERVAL)
        )
        self.hass.async_create_background_task(
            self._poll(), f"{DOMAIN} first state read"
        )
        self.async_on_remove(
            bluetooth.async_register_callback(
                self.hass,
                self._seen,
                {"address": address, "connectable": True},
                bluetooth.BluetoothScanningMode.ACTIVE,
            )
        )
        self.async_on_remove(
            bluetooth.async_track_unavailable(
                self.hass, self._gone, address, connectable=True
            )
        )

    @callback
    def _seen(self, _info, _change) -> None:
        if not self._attr_available:
            self._attr_available = True
            self.async_write_ha_state()

    @callback
    def _gone(self, _info) -> None:
        # A connected light stops advertising; that is not the same as gone.
        if self._device.is_connected:
            return
        self._attr_available = False
        self.async_write_ha_state()

    def _apply(self, status: UlanziStatus) -> None:
        self._attr_assumed_state = False
        self._attr_is_on = status.is_on
        if status.brightness_pct > 0:
            self._attr_brightness = max(1, round(status.brightness_pct * 255 / 100))
        if status.min_kelvin < status.max_kelvin:
            self._attr_min_color_temp_kelvin = status.min_kelvin
            self._attr_max_color_temp_kelvin = status.max_kelvin
        if status.kelvin:
            self._attr_color_temp_kelvin = status.kelvin
        self._attr_effect = status.effect or EFFECT_OFF

    @callback
    def _on_status(self, status: UlanziStatus) -> None:
        self._apply(status)
        self.async_write_ha_state()

    async def _poll(self, _now=None) -> None:
        """Ask the light for its state; the answer arrives in _on_status.

        A link opened just for this is closed again straight away, so the
        light stays free for the Ulanzi app. One already open is left alone.
        """
        if not self._attr_available:
            return
        try:
            await self._device.send(release=not self._device.is_connected)
        except HomeAssistantError as err:
            # Busy with another app, or just out of reach: keep what we have.
            _LOGGER.debug("%s: state not read: %s", self._device.name, err)

    async def async_turn_on(self, **kwargs: Any) -> None:
        packets: list[bytes] = []
        if not self._attr_is_on:
            packets.append(CMD_ON)

        effect = kwargs.get(ATTR_EFFECT)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            # Setting a colour temperature also ends a running effect.
            self._attr_color_temp_kelvin = int(kwargs[ATTR_COLOR_TEMP_KELVIN])
            self._attr_effect = EFFECT_OFF
            packets.append(cmd_color_temp(self._attr_color_temp_kelvin))
        elif effect == EFFECT_OFF:
            self._attr_effect = EFFECT_OFF
            packets.append(cmd_color_temp(self._attr_color_temp_kelvin or 5600))
        elif effect in EFFECTS:
            self._attr_effect = effect
            packets.append(cmd_effect(EFFECTS[effect]))

        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = int(kwargs[ATTR_BRIGHTNESS])
        if ATTR_BRIGHTNESS in kwargs or not self._attr_is_on:
            percent = max(1, round((self._attr_brightness or 1) * 100 / 255))
            packets.append(cmd_brightness(percent))

        status = await self._device.send(*packets)
        if status is None:
            self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        status = await self._device.send(CMD_OFF)
        if status is None:
            self._attr_is_on = False
        self.async_write_ha_state()
