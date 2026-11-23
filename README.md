# Ulanzi Light for Home Assistant

Control Ulanzi Bluetooth video lights from Home Assistant, locally, without
the Ulanzi Connect app.

[Magyar leírás](README.hu.md)

## What it does

Each light becomes one `light` entity with:

- on / off
- brightness (1–100 %)
- colour temperature, 2700–6500 K

RGB, effects and battery level are not supported yet.

## Supported lights

| Light | Status |
| --- | --- |
| Ulanzi COB light advertising as `Ulanzi light(XXXX)` | Tested |
| VL-200Bi, VL-120Bi, VL-120C, EC65, AL60, AL120, L149 | Untested – same protocol according to [lctl](https://github.com/kevinlouie/lctl) |

If your light works (or does not), please open an issue with the model name.

## Requirements

- Home Assistant 2025.1 or newer (developed and tested on 2026.11)
- A working Bluetooth adapter or an ESPHome Bluetooth proxy **with active
  connections** within range of the light

## Installation

### HACS

1. HACS → ⋮ → **Custom repositories**
2. Repository: `https://github.com/meszimark/ha-ulanzi-light`, type: **Integration**
3. Install **Ulanzi Light**, then restart Home Assistant.

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

## Known limitations

- **Assumed state.** The light does not report its state, so Home Assistant
  shows what it sent last. Changes made on the light itself or in the Ulanzi
  app are not picked up.
- **One connection at a time.** While the Ulanzi app is connected, Home
  Assistant cannot reach the light, and the other way round.
- **Short delay.** The light drops an idle Bluetooth link after about ten
  seconds, so a command after a pause can take 1–3 seconds while the
  integration reconnects.

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
| Off | `FF A1 01 30 30 AA`, then `FF A1 01 01 01 AA` |
| Brightness (0–100) | `FF A2 01 LL LL AA` |
| Colour temperature (K, big-endian) | `FF A3 02 HH LL CS AA`, `CS = (HH + LL) & 0xFF` |

## Credits

The protocol was documented by Kevin Louie's
[lctl](https://github.com/kevinlouie/lctl) (MIT). This integration is an
independent implementation for Home Assistant.

## Disclaimer

This is an unofficial, community project. It is not affiliated with or
endorsed by Ulanzi. "Ulanzi" is a trademark of its owner.

## License

[MIT](LICENSE)
