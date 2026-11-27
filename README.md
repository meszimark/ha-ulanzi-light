# Ulanzi Light for Home Assistant

Control Ulanzi Bluetooth video lights from Home Assistant, locally, without
the Ulanzi Connect app.

[Magyar leírás](README.hu.md)

## What it does

Each light becomes one `light` entity with:

- on / off
- brightness (1–100 %)
- colour temperature, 2700–6500 K
- effects: Flash, TV, Candle, Strobe 1–3
- real state: the light is asked for its state after every command and once
  a minute, so changes made on the light itself or in the Ulanzi app show up
  in Home Assistant

RGB and battery level are not supported yet.

## Supported lights

| Light | Status |
| --- | --- |
| VL-120Bi (120 W bi-colour COB, advertises as `Ulanzi light(XXXX)`) | Tested |
| VL-200Bi, VL-120C, EC65, AL60, AL120, L149 | Untested – same protocol according to [lctl](https://github.com/kevinlouie/lctl) |

If your light works (or does not), please open an issue with the model name.

## Requirements

- Home Assistant 2025.1 or newer (developed and tested on 2026.11)
- A working Bluetooth adapter or an ESPHome Bluetooth proxy **with active
  connections** within range of the light

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=meszimark&repository=ha-ulanzi-light&category=integration)

Or: HACS → search for **Ulanzi Light** → Download, then restart Home Assistant.

### Manual

Copy `custom_components/ulanzi_light` into your `config/custom_components`
folder and restart Home Assistant.

## Setup

1. Power the light on and **close the Ulanzi Connect app** – the light accepts
   only one Bluetooth connection at a time.
2. The light is normally discovered automatically. Otherwise go to
   **Settings → Devices & services → Add integration → Ulanzi Light**.
3. If no light is listed, type its Bluetooth address (`AA:BB:CC:DD:EE:FF`).
   You can find it under Settings → Devices & services → Bluetooth →
   advertisement monitor.

## Options

**Settings → Devices & services → Ulanzi Light → Configure** sets how often
Home Assistant asks the light for its state (60 seconds by default). `0` turns
the regular read off; the state is then only read after a command.

## Known limitations

- **One connection at a time.** While the Ulanzi app is connected, Home
  Assistant cannot reach the light, and the other way round. Home Assistant
  only holds the link for a few seconds at a time.
- **Short delay after a pause.** The light drops the Bluetooth link about ten
  seconds after connecting, so the first command after a pause takes a second
  or two while the integration reconnects.
- **State can lag** by the read interval (a minute by default) for changes
  made outside Home Assistant.
- **Lights that never answer** the status query keep working, with the state
  Home Assistant sent last (assumed state).

## Troubleshooting

Enable debug logging and attach the log to your issue:

```yaml
logger:
  logs:
    custom_components.ulanzi_light: debug
```

## Protocol

Service `FFF0`, write characteristic `FFF2`, notify characteristic `FFF1`.

| Command | Bytes |
| --- | --- |
| On | `FF A1 01 00 00 AA` |
| Off | `FF A1 01 01 01 AA` |
| Brightness (0–100) | `FF A2 01 LL LL AA` |
| Colour temperature (K, big-endian) | `FF A3 02 HH LL CS AA`, `CS = (HH + LL) & 0xFF` – also ends an effect |
| Effect | `FF A1 01 XX XX AA` – Flash `04`, TV `05`, Candle `06`, Strobe 1–3 `0C` `0D` `0E` |
| Status query | `FF A1 01 30 30 AA` |

The light answers a status query with a 20-byte notification:

`FF B1 10 | brightness | kelvin (2) | 4 unused | mode | power | min kelvin (2) | max kelvin (2) | 3 unused | checksum`

- `mode`: `02` for plain white light, otherwise the effect code
- `power`: `01` on, `00` off
- `checksum`: sum of the 16 bytes after `FF B1 10`, modulo 256

About three seconds after connecting the light also sends `BB B6` + 8 random
bytes + `FF`, and closes the link roughly seven seconds later. The Ulanzi app
presumably answers this; the integration does not, and reconnects instead.

## Credits

The command set was documented by Kevin Louie's
[lctl](https://github.com/kevinlouie/lctl) (MIT). This integration is an
independent implementation for Home Assistant; the status query and its
answer were worked out on a real light.

## Disclaimer

This is an unofficial, community project. It is not affiliated with or
endorsed by Ulanzi. "Ulanzi" is a trademark of its owner.

## License

[MIT](LICENSE)
