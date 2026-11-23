# Ulanzi Light – Home Assistant integráció

Ulanzi Bluetooth-os videólámpák vezérlése Home Assistantból, helyben, az
Ulanzi Connect app nélkül.

[English](README.md)

## Mit tud

Minden lámpa egy `light` entitás lesz:

- be / ki
- fényerő (1–100 %)
- színhőmérséklet, 2700–6500 K

RGB, effektek és akkuszint egyelőre nincs.

## Támogatott lámpák

| Lámpa | Állapot |
| --- | --- |
| `Ulanzi light(XXXX)` néven hirdető Ulanzi COB lámpa | Tesztelve |
| VL-200Bi, VL-120Bi, VL-120C, EC65, AL60, AL120, L149 | Nem tesztelt – az [lctl](https://github.com/kevinlouie/lctl) szerint azonos protokoll |

Ha a te lámpáddal megy (vagy nem megy), nyiss egy issue-t a típus nevével.

## Követelmények

- Home Assistant 2025.1 vagy újabb (2026.11-en fejlesztve és tesztelve)
- Működő Bluetooth adapter vagy **aktív kapcsolatot** engedő ESPHome
  Bluetooth proxy a lámpa hatótávolságában

## Telepítés

### HACS

1. HACS → ⋮ → **Egyéni tárolók**
2. Tároló: `https://github.com/meszimark/ha-ulanzi-light`, típus: **Integráció**
3. Telepítsd az **Ulanzi Light** integrációt, majd indítsd újra a Home Assistantot.

### Kézi

Másold a `custom_components/ulanzi_light` mappát a `config/custom_components`
alá, és indítsd újra a Home Assistantot.

## Beállítás

1. Kapcsold be a lámpát, és **zárd be az Ulanzi Connect appot** – a lámpa
   egyszerre csak egy Bluetooth-kapcsolatot fogad.
2. A lámpát a rendszer általában magától felfedezi. Ha nem:
   **Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása → Ulanzi Light**.
3. Ha nem jelenik meg lámpa, írd be a Bluetooth-címét (`AA:BB:CC:DD:EE:FF`).

## Ismert korlátok

- **Feltételezett állapot.** A lámpa nem jelzi vissza az állapotát, a Home
  Assistant azt mutatja, amit utoljára küldött. A lámpán vagy az Ulanzi
  appban végzett állítást nem látja.
- **Egyszerre egy kapcsolat.** Amíg az Ulanzi app csatlakozik, a Home
  Assistant nem éri el a lámpát, és fordítva.
- **Rövid késés.** A lámpa kb. tíz másodperc tétlenség után bontja a
  kapcsolatot, ezért szünet után egy parancs 1–3 másodpercet késhet.

## Hibakeresés

```yaml
logger:
  logs:
    custom_components.ulanzi_light: debug
```

## Köszönet

A protokollt Kevin Louie [lctl](https://github.com/kevinlouie/lctl) projektje
(MIT) dokumentálta. Ez az integráció attól független megvalósítás.

## Jogi megjegyzés

Nem hivatalos, közösségi projekt, nem áll kapcsolatban az Ulanzival.

## Licenc

[MIT](LICENSE)
