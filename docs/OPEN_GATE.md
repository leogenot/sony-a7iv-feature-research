# Open Gate / full-height movie recording

## Current conclusion

The A7 IV 6.02 application contains a generic full-frame 5K 3:2 imager path,
but the extracted update does not establish a complete Open Gate recording
mode for `PRODUCT_MODEL_LS`, the ILCE-7M4's product class. Earlier revisions
of this note wrongly said `LAX`; see [Product class](PRODUCT_CLASS.md). The
strongest evidence currently supports an internal sensor/input format which
is normally scaled or cropped before encoding.

No tested backup-property change enables Open Gate recording. Do not interpret
the shared scan-mode names as an unlock by themselves.

## Likely reference product: FX5

Sony's published FX5 description uses the same set of scan modes found in the
A7 IV shared application: full-frame 5K 3:2, full-frame 5K 16:9, and
full-frame 5K 17:9. Sony also states that FX5 Open Gate recording is available
only with X-OCN. [Sony FX5 Open Gate description][fx5-open-gate]

The A7 IV `appFw.so` contains generic X-OCN selection names as well:

```text
SELECT_CODEC_X_OCN_LT
SELECT_CODEC_X_OCN_LL1
SELECT_CODEC_X_OCN_LL2
set_select_codec_for_exclusion_x_ocn_lt
set_select_codec_for_exclusion_x_ocn_ll1
set_select_codec_for_exclusion_x_ocn_ll2
```

It also contains more than twenty `PRODUCT_MODEL_*` classes. Taken together,
this strongly suggests that the application packages model-shared cinema
support which is selected by product tables. The A7 IV does not expose X-OCN
as a recording format, and its documented XAVC recorder has no 5K 3:2 mode.
Therefore the exact 5K 3:2 strings are more plausibly part of the FX5 or a
related product path than a hidden A7 IV XAVC setting.

## Positive firmware evidence

`appFw.so` contains the following exact strings:

```text
VIDEO_FORMAT_5016x2824P
VIDEO_FORMAT_5016x3344P
VIDEO_FORMAT_5016x2648P
IMAGER_SCANMODE_FF
IMAGER_SCANMODE_S35
IMAGER_SCANMODE_FF_5K_3_2
IMAGER_SCANMODE_FF_5K_17_9
IMAGER_SCANMODE_FF_5K_16_9
IMAGER_SCANMODE_FF_CROP_4_5K_17_9
IMAGER_SCANMODE_FF_CROP_4_5K_16_9
IMAGER_SCANMODE_FF_CROP_3_8K_16_9
IMAGER_SCANMODE_S35_3_2K_16_9
```

The 5016x3344 dimensions are exactly 3:2. The application also contains:

```text
EVENT_REMOTE_IMAGER_SCANMODE
N5model25setting_imager_scanmode_tE
set_imager_scanmode
set_imager_scanmode_by_assignable_button
BKID_APP_EXTERN_MENU_MOVIE_REC_ASPECT_XAVC
BKID_APP_MR_EXTERN_MENU_MOVIE_REC_ASPECT_XAVC
BKID_APP_EXTERN_MENU_MOVIE_REC_ASPECT_UNBUF_SHS
extern_menu_movie_rec_aspect_xavc
extern_menu_movie_rec_aspect_unbuf_shs
movie_image_aspect
```

This shows that the shared application understands full-height 3:2 imager
scanning and has a movie-aspect model/menu abstraction.

## Evidence missing from the recording side

The same binary has codec/profile strings for AVC and HEVC output at
3840x2160, 4096x2160, and HD sizes. Searching the AVC, HEVC, and VPC profile
names found no encoder profile containing `5016`, `3344`, `5K`, or `3_2`.
The exact 5016x3344 and 5K-3:2 identifiers occur only in `appFw.so`; no
separate configuration file in the extracted root repeats them.

The physical A7 IV protocol-3 snapshot similarly contains no descriptor
default, current value, range, or enumeration equal to 5016 or 3344. There is
therefore no exposed Remote SDK/PTP resolution choice corresponding to the
internal scan mode.

Sony's A7 IV movie table lists 3840x2160 for every 4K recording format and
1920x1080 for HD. It does not list a 3:2 movie size. [Sony A7 IV Movie
Settings][a7-movie-settings]

One useful negative control is DCI 4K. The shared A7 IV application contains
`VIDEO_FORMAT_4096x2160P` and DCI-related user-interface text, even though the
A7 IV's official movie table exposes only 3840x2160 4K. This demonstrates why
a generic format name in this multi-model application is not proof of A7 IV
availability.

## Related backup properties

Name-record decoding maps the movie-aspect objects to these persisted
properties:

| Property | Firmware name | Live/default value |
| --- | --- | --- |
| `0x02cf00d7` | `BKID_APP_EXTERN_MENU_MOVIE_REC_ASPECT_XAVC` | `01` |
| `0x02cf00e2` | `BKID_APP_MR_EXTERN_MENU_MOVIE_REC_ASPECT_XAVC` | ten bytes, all `01` |
| `0x02cf122e` | `BKID_APP_EXTERN_MENU_MOVIE_REC_ASPECT_UNBUF_SHS` | `01` |

All 32 regional A7 IV 6.02 backup profiles inspected use the same values. The
enum meaning of these bytes has not been recovered. The `EXTERN_MENU` names
may represent an externally calculated/menu-facing state rather than an
independent feature switch, so changing them is not currently a justified
experiment.

`0x02cf0199` is `BKID_APP_SETTING_ASPECT_RATIO`, but its value table belongs
to still-image aspect ratios. The English resources describe 3:2 as a still
image setting, so this is not an Open Gate selector.

## What would establish an actual Open Gate path

The remaining work is to resolve the model/product predicate that selects
`IMAGER_SCANMODE_FF_5K_3_2`, then trace its output into the movie-recorder
configuration. A viable recording path needs all of the following:

1. A `PRODUCT_MODEL_LS` route to the 5K 3:2 scan mode.
2. A recorder/encoder configuration accepting a 3:2 frame instead of reducing
   it to 3840x2160.
3. Matching buffer, metadata, thermal, media-rate, and playback definitions.
4. A menu or safely callable setting path selecting the mode.

Until the encoder path is found, the evidence supports dormant shared imager
machinery rather than a usable hidden Open Gate mode.

The current probability of a settings-only unlock is low. Establishing a
usable A7 IV mode would require proving that the `LS` product path can select
the scan mode and that its hardware/recorder can use a non-X-OCN 3:2 output.
Changing an `EXTERN_MENU` byte cannot establish either requirement.

## Reproduction

```bash
A7=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so

strings -a -t x "$A7" | rg \
  'IMAGER_SCANMODE|VIDEO_FORMAT_5016|MOVIE_REC_ASPECT|movie_image_aspect'

strings -a "$A7" | rg -i \
  '^(AVC|HEVC|VPC_).*(5016|3344|5K|3_2)'

python3 scripts/analyze_ptp_snapshot.py \
  ~/Documents/a7iv-ptp-speed-matched.json --find 5016

python3 scripts/analyze_ptp_snapshot.py \
  ~/Documents/a7iv-ptp-speed-matched.json --find 3344
```

[a7-movie-settings]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000640834.html
[fx5-open-gate]: https://electronics.sony.com/imaging/cinema-line-cameras/all-cinema-line-cameras/p/ilmefx5b
