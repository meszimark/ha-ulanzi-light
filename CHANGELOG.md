# Changelog

## 0.3.0

- The interval of the regular state read can be set in the options (0 = off).
- Own icon.
- VL-120Bi confirmed as tested.

## 0.2.0

- Effects: Flash, TV, Candle, Strobe 1–3.
- The real state is read back from the light after every command and once a
  minute, so changes made on the light or in the Ulanzi app are picked up.
- The colour temperature range is taken from the light.
- Turning off is a single command now.

## 0.1.2

- First public release: HACS metadata, licence, documentation.

## 0.1.1

- Discovery by manufacturer id, because Home Assistant's passive scan often
  never sees the light's name.
- The Bluetooth address can be typed in when nothing is discovered.

## 0.1.0

- On/off, brightness and colour temperature over Bluetooth LE.
