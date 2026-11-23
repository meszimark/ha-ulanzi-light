"""Constants and packet helpers for the Ulanzi Light integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "ulanzi_light"

WRITE_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

CONF_POLL_INTERVAL = "poll_interval"
# Seconds between state reads; 0 turns the regular read off.
DEFAULT_POLL_INTERVAL = 60
MAX_POLL_INTERVAL = 3600

MIN_KELVIN = 2700
MAX_KELVIN = 6500

# FF A1 01 <x> <x> AA: power, mode and status commands.
CMD_ON = bytes([0xFF, 0xA1, 0x01, 0x00, 0x00, 0xAA])
CMD_OFF = bytes([0xFF, 0xA1, 0x01, 0x01, 0x01, 0xAA])
# Asks the light for its state; it answers with an FF B1 notification.
CMD_QUERY = bytes([0xFF, 0xA1, 0x01, 0x30, 0x30, 0xAA])

# The light reports this mode while it shows plain white light.
MODE_CCT = 0x02

EFFECTS: dict[str, int] = {
    "Flash": 0x04,
    "TV": 0x05,
    "Candle": 0x06,
    "Strobe 1": 0x0C,
    "Strobe 2": 0x0D,
    "Strobe 3": 0x0E,
}
EFFECT_NAMES: dict[int, str] = {code: name for name, code in EFFECTS.items()}

STATUS_HEADER = bytes([0xFF, 0xB1, 0x10])
STATUS_LENGTH = 20


def cmd_brightness(percent: int) -> bytes:
    """Brightness 0-100."""
    level = max(0, min(100, int(percent)))
    return bytes([0xFF, 0xA2, 0x01, level, level, 0xAA])


def cmd_color_temp(kelvin: int) -> bytes:
    """Colour temperature in Kelvin, big-endian, with additive checksum.

    Also takes the light out of an effect, back to plain white.
    """
    kelvin = max(MIN_KELVIN, min(MAX_KELVIN, int(kelvin)))
    hi, lo = kelvin >> 8, kelvin & 0xFF
    return bytes([0xFF, 0xA3, 0x02, hi, lo, (hi + lo) & 0xFF, 0xAA])


def cmd_effect(code: int) -> bytes:
    """Start one of the built-in effects."""
    return bytes([0xFF, 0xA1, 0x01, code, code, 0xAA])


@dataclass(frozen=True)
class UlanziStatus:
    """State reported by the light in answer to CMD_QUERY."""

    is_on: bool
    brightness_pct: int
    kelvin: int
    mode: int
    min_kelvin: int
    max_kelvin: int

    @property
    def effect(self) -> str | None:
        """Name of the running effect, or None for plain white light."""
        return EFFECT_NAMES.get(self.mode)


def parse_status(data: bytes) -> UlanziStatus | None:
    """Decode an FF B1 status notification; None if it is something else.

    FF B1 10 | brightness | kelvin (2) | 4 unused | mode | power |
    min kelvin (2) | max kelvin (2) | 3 unused | checksum of the 16 bytes.
    """
    if len(data) != STATUS_LENGTH or data[:3] != STATUS_HEADER:
        return None
    if sum(data[3:19]) & 0xFF != data[19]:
        return None
    return UlanziStatus(
        is_on=data[11] == 0x01,
        brightness_pct=data[3],
        kelvin=(data[4] << 8) | data[5],
        mode=data[10],
        min_kelvin=(data[12] << 8) | data[13],
        max_kelvin=(data[14] << 8) | data[15],
    )
