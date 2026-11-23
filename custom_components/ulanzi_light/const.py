"""Constants for the Ulanzi Light integration."""

DOMAIN = "ulanzi_light"

WRITE_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

MIN_KELVIN = 2700
MAX_KELVIN = 6500

CMD_ON = bytes([0xFF, 0xA1, 0x01, 0x00, 0x00, 0xAA])
CMD_OFF_1 = bytes([0xFF, 0xA1, 0x01, 0x30, 0x30, 0xAA])
CMD_OFF_2 = bytes([0xFF, 0xA1, 0x01, 0x01, 0x01, 0xAA])


def cmd_brightness(percent: int) -> bytes:
    """Brightness 0-100."""
    level = max(0, min(100, int(percent)))
    return bytes([0xFF, 0xA2, 0x01, level, level, 0xAA])


def cmd_color_temp(kelvin: int) -> bytes:
    """Colour temperature in Kelvin, big-endian, with additive checksum."""
    kelvin = max(MIN_KELVIN, min(MAX_KELVIN, int(kelvin)))
    hi, lo = kelvin >> 8, kelvin & 0xFF
    return bytes([0xFF, 0xA3, 0x02, hi, lo, (hi + lo) & 0xFF, 0xAA])
