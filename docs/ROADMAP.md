# Cinema-feature roadmap

Last updated 2026-11-25. Features for the A7 IV custom firmware
([sony-a7m4-custom-firmware-open-gate](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate)), with where
each one stands and what decides the next step. Evidence grades (A–E) are the
[feature inventory](FEATURE_INVENTORY.md)'s.

## Shipped

| Feature | Release | Notes |
| --- | --- | --- |
| Open gate 4K 3:2 (3840x2560) and 5.7K 3:2 (5760x3840), NTSC and PAL | [`beta-0.1`](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate/releases/tag/beta-0.1) | Camera-tested. Chosen with the switch on stills. |

## Test builds waiting for a camera run

| Feature | Release | What the test decides |
| --- | --- | --- |
| English Custom LUT screens | [`alpha-0.1`](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate/releases/tag/alpha-0.1) | Whether long English labels fit on screen |
| Open gate chosen and applied on movie | [`alpha-movie-0.1`](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate/releases/tag/alpha-movie-0.1) | Whether a movie-mode apply takes effect after the menu closes, needs a pipeline restart, or freezes |
| Shutter angle on the dial | [`alpha-angle-0.1`](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate/releases/tag/alpha-angle-0.1) | Whether lifting the availability gate `0x293d634` is enough, and whether the exposure follows the angle. Also the pilot for unlocking other FX3-only code. |
| 1080p 3:2 open gate (1920x1280) and HD 60p: read-only probe | [`alpha-hd-probe-0.1`](https://github.com/leogenot/sony-a7m4-custom-firmware-open-gate/releases/tag/alpha-hd-probe-0.1) | Which sensor readout HD 24/30/60p uses: route A (the 4K readout, scaled) or route B (binned, new sensor work) |

## Candidates

There are two routes. **Unlock** means making Sony's own compiled code reachable, where an availability rule or the
A7 IV's menu catalogue leaves it out (the shutter-angle pattern). **Build** means our own implementation from parts
the A7 IV already has, as Erlla did for Custom LUTs.

| Feature | Grade | Route | What's missing | Next step |
| --- | --- | --- | --- | --- |
| Anamorphic de-squeeze display (1.3x, 2.0x) | B | Unlock | Proof that the A7 IV display honours `0x02cf1bf2` | One-byte camera test ([De-Squeeze](DE_SQUEEZE.md)); then a menu item. Pairs with open gate. |
| Shutter Mode menu (Speed / Angle) | A (display) | Unlock + build | The live setter for the shutter mode | After `alpha-angle-0.1` passes |
| 1080p 3:2 open gate, 24/25/30p | — | Build | HD size, encoder and MP4 changes (route A) | After `alpha-hd-probe-0.1` |
| Monitoring-only User LUT (`.cube` on screen while recording S-Log3) | D (Sony's), build possible | Build | A user table in Gamma Display Assist's display-only path | Find that path's table |
| Cine EI (sensor at base ISO, exposure index on the monitor only, EI in metadata) | D | Unlock, else build | Sony's code runs only for 14 other product classes; otherwise the same display path as the monitoring LUT | After the shutter-angle pilot |
| Log shooting mode and Flexible ISO | D | Unlock, else build (mostly UI) | A7 IV already changes ISO freely in S-Log3 | After the shutter-angle pilot |
| DCI 4K, XAVC S-I (4096x2160) | C | Unlock + build | The file-format enum and the encoder path; the readout fits (4K is already from 7K) | Decode the per-slot file-format enum |
| In-camera time-lapse movie | open lead | Unlock | Whether the A7 IV can reach `timelapse_movie_4k` | Trace its consumers |
| Big6-style main screen, waveform, false colour | — | Build | New screens drawn with Sony's internal drawing system | Large; after the cheaper items |

## Not possible on this body

| Feature | Why |
| --- | --- |
| Full-frame 4K 60p | The 7K full readout is about 2011 line periods; Super 35 4K 60p fits 1356. So the full readout is about 1.5x too slow for 16.7 ms, about twice the processing rate the camera ever runs, and there's no fast readout wide enough for 4K. Check with a flicker test (readout time of FF 4K 24p against S35 4K 60p). |
| RAW over HDMI | Needs the hardware route; Sony enables it only on other product classes |
| Built-in variable ND | Needs ND hardware |
| Base ISO Low/High switch | Depends on the sensor's gain hardware (open question) |

## Web research

Pending: an agent is collecting measured readout times, Sony firmware history for these features on BIONZ XR bodies,
A7 IV hardware facts and community hacks. Results go to `CINEMA_FEATURES_WEB_RESEARCH.md`, and this page will be
updated from them.
