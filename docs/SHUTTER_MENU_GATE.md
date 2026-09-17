# Why the shutter-angle icon appears but the Shutter Mode menu does not

## Conclusion

On ILCE-7M4 firmware 6.02, backup property `0x02cf1702` changes the live
shutter representation between speed and angle, but it does not add a menu
item. The camera can therefore enter angle mode and render its angle control
while still omitting **MENU → Exposure/Color → Exposure → Shutter Mode**.

The evidence points to a product-specific menu catalogue or UI composition
decision, rather than an exposure-mode restriction or a second, obvious backup
flag:

1. Sony's own A7 IV menu inventory omits **Shutter Mode** from the Exposure
   group. It lists **Auto Slow Shutter** as the first movie-only item instead.
   The A7 IV default-settings inventory also omits Shutter Mode. [Sony A7 IV
   menu inventory][a7-menu] [Sony A7 IV default settings][a7-defaults]
2. Sony's FX3 documentation explicitly puts **Shutter Mode** at that location,
   says that it requires FX3 firmware 6.00 or later, and defines **Speed** and
   **Angle** as its choices. [Sony FX3 Shutter Mode][fx3-shutter] [Sony FX3
   menu inventory][fx3-menu]
3. The A7 IV application nevertheless contains the same underlying shutter
   mode parameter, angle values, next/previous-angle actions, UI action key,
   and English label/help text found in the FX3 firmware.
4. The broad `FEATURE_MANAGER_menu_item` value is the same for the A7 IV's
   `LAX` product class and the FX3's `ALCIN_UUD` product class. That broad
   switch therefore does not explain this one missing page.
5. No `PRM_HAITA_setting_mode_shutter...` exclusion rule is present in the A7
   IV binary. In this firmware, temporary enable/disable conditions normally
   leave `PRM_HAITA_...`/`VAL_HAITA_...` names. Their absence does not prove
   that no condition exists, but it makes a normal mode-dependent inhibit less
   likely.

The exact menu-node table or predicate has not yet been identified. It would
be unsafe to name a patch address from the current evidence. The practical
answer is that `0x02cf1702=01` changes the backing display state directly; the
icon is evidence that the formatter accepted angle mode, not evidence that the
A7 IV enabled the FX3 control route or menu page.

## Why the angle can appear but remain fixed when a dial is turned

Changing `0x02cf1702` selects angle representation. It does not force the
shutter exposure channel from Auto to Manual, and it does not change which
physical control is assigned to shutter.

Sony documents a separate activation condition for the FX3: **Angle** is
active only in Shutter Priority, Manual Exposure, or Flexible Exposure when
the shutter is set to Manual. [Sony FX3 Shutter Mode][fx3-shutter] The A7 IV
already has the corresponding exposure controls. In Flexible Exposure, Sony
documents **Tv Auto/Manual Switch** under **Auto/Manual Swt. Set.** and assigns
shutter adjustment to the **control wheel**, rather than the front or rear
dial. [Sony A7 IV Auto/Manual Swt. Set.][a7-auto-manual] Sony also documents
that Flexible Exposure treats aperture, shutter, and ISO as independently
automatic or manual channels. [Sony A7 IV Exposure Ctrl Type][a7-exposure]

The first in-camera test should therefore be one of these:

1. Set the Still/Movie/S&Q selector to Movie, set **Exposure Ctrl Type** to
   **P/A/S/M Mode**, choose **M** or **S**, and turn the control assigned to
   shutter/Tv.
2. Set **Exposure Ctrl Type** to **Flexible Exp. Mode**, open **Exposure/Color
   → Exposure → Auto/Manual Swt. Set.**, change **Tv Auto/Manual Switch** to
   **Manual**, and turn the **control wheel**. On the documented default movie
   assignments, C4 toggles Tv Auto/Manual.

The A7 IV binary supports this interpretation. It contains separate generated
actions for ordinary shutter drive and angle drive:

```text
0x4c5db05  FUNC_set_shut_drive_seq
0x4c5db1d  FUNC_set_shut_drive_seq_angle
0x4c5db3b  FUNC_shutter_angle_next_seq
0x4c5db57  FUNC_shutter_angle_prev_seq
```

Its internal action-name block additionally contains
`set_shut_drive_seq_angle_value`,
`set_is_shutter_speed_min_max_for_angle`, `shutter_angle_next_seq`, and
`shutter_angle_prev_seq` at `0x4fb2b77`–`0x4fb2bd4`. A dedicated model class,
`sequence_set_shut_drive_for_shutter_angle`, is present at `0x4be91a0`; its
vtable is at `0x59d83c0` and reaches the shared drive runner at `0x35436ac`.
The FX3 comparison build also has the four generated actions, at
`0x39c6671`–`0x39c66c3`.

The A7 IV also contains the manual/automatic shutter parameter and its
exposure-mode exclusion data:

```text
0x4c44309  PRM_setting_shutter_speed_a_m_switching
0x4c44355  PRM_HAITA_setting_shutter_speed_a_m_switching_exposure_mode
0x4d9c9db  ...SHUTTER_SPEED_A_M_SWITCHING_AUTO
0x4d9ca24  ...SHUTTER_SPEED_A_M_SWITCHING_MANUAL
0x4d9cca6  ...AUTO_FLEXIBLE_EXPOSURE_MODE
0x4d9cd1a  ...MANUAL_FLEXIBLE_EXPOSURE_MODE
```

This proves that the angle-drive actions and the Auto/Manual exposure gate are
compiled into A7 IV 6.02. The subsequent camera tests covered Movie **M** and
Flexible Exposure with Tv explicitly set to **Manual**. Neither the dial nor
the control wheel changed `0x02cf1704`, identifying blocked input dispatch
rather than a display-refresh problem.

### Service-backup readback limitation

The camera later reported the following backup settings after the angle
remained fixed at `0x02cf1704=10`:

```text
0x02cf024d = 00  setting_movie_exposure_mode_setting = P/A/S/M control
0x02cf0247 = 00  saved setting_movie_exposure_mode value
0x02cf02d9 = 01  setting_shutter_speed_a_m_switching = Manual
0x02cf1549 = 01  shutter_speed_manual_lock_state = Off/unlocked
```

The user confirmed that the camera was actually in Movie **M** while the dial
remained ineffective. Entering service mode changes the operating context, and
`bk r` reads a persisted backup property rather than the live derived
`exposure_mode` object used by the shooting input controller. The ordered enum
names also do not, by themselves, prove the numeric encoding. Consequently,
`0x02cf0247=00` must not be interpreted as proof that the shooting session was
in Intelligent Auto. The reliable part of this observation is that the stored
Tv channel is Manual, its manual lock is Off, and `0x02cf1704` did not change.
The camera owner subsequently verified that `0x02cf0247` remains `00` across
physical mode-dial selections, confirming that this backup property is not a
live mode-dial indicator on the A7 IV.

Flexible Exposure with Tv explicitly Manual and the control wheel was then
tested and also failed. The shared angle action therefore remains inhibited
after only setting `BKID_APP_SETTING_MODE_SHUTTER`.

### Touch-editor result: formatter and editor are split

The Flexible Exposure/control-wheel test also left the displayed value fixed
at `180°`. Tapping that value opened the ordinary shutter-speed editor, with
entries such as `1/30` and `1/50`. Choosing a speed closed the editor while the
footer continued to show `180°`; `0x02cf1704` remained unchanged.

This separates two pieces of the implementation:

- `BKID_APP_SETTING_MODE_SHUTTER=01` reaches the footer formatter, which renders
  the stored angle value and angle icon.
- The A7 IV touch target remains bound to the ordinary shutter-speed editor,
  and dial events likewise do not reach the angle next/previous actions.

The binary contains all three nearby UI action keys:

```text
UIBIZ_KEY_TACT_SHUTTER_SPEED
UIBIZ_KEY_TACT_SHUTTER_MODE
UIBIZ_KEY_TACT_SHUTTER_SELECT
```

It also contains `model::model_extern::extern_BKID_APP_EXTERN_SHUTTER_MODE()`.
That bridge reads the shutter-mode model value, accepts both `0` and `1`, and
publishes event `0x1d5a`. However, there is no separately named
`BKID_APP_*SHUTTER_SELECT` backup property to switch the footer touch target.
The evidence therefore no longer supports a complete in-camera activation by
changing only `0x02cf1702`; a product-specific UI/action binding or executable
patch remains to be identified.

### The full angle-adjustment route is present, but guarded

A more detailed control-flow trace confirms that the firmware contains more
than angle labels and formatting. The A7 IV has a complete dial action for
changing the angle:

```text
dial dispatcher 0x1baf328
  reads shutter mode at 0x28f6e38
  mode 0 (speed) -> ordinary shutter drive 0x27b4fa4
  mode 1 (angle) -> test HAITA getter 0x293d634
                    clear: angle drive 0x26e8b08
                    set:   unavailable-action feedback 0x26e898c

angle drive 0x26e8b08
  emits event 0x3fb8 with a signed step
  positive step -> angle-next worker 0x2593d20
  negative step -> angle-previous worker 0x2593de4
```

There are also direct positive and negative call sites at `0x23648b8`,
`0x2364a34`, `0x2365b20`, and `0x2365c9c`. This makes absence of the angle
arithmetic or increment/decrement sequence an unlikely explanation for the
fixed `180°` display.

The guard read at `0x293d634` is generated model state. Cross-references and
the parallel generated parameter maps identify it as:

```text
PRM_HAITA_setting_shutter_speed_a_m_switching_exposure_mode
```

`HAITA` is Sony's generated availability/inhibit layer. It is runtime state,
not a persisted backup byte with the same name. That explains why setting the
stored Tv channel to Manual and changing `0x02cf1702` can still leave the dial
route blocked. The same broad branch structure exists in the FX3 build; the
important product difference may therefore be how this generated state is
initialized or refreshed, rather than missing angle code.

The two values published through `UIBIZ_KEY_TACT_SHUTTER_SELECT` were also
previously easy to misread. Disassembly of handlers `0x26e7130` and
`0x26e7250` shows that values `1` and `0` select **next** and **previous**
angle actions. They are direction values, not a second speed/angle selector.
There is consequently no evidence that writing a hypothetical
`SHUTTER_SELECT=1` would unlock the mode.

The observed touch behavior adds one independent constraint: the A7 IV footer
still launches the speed editor. Even if the generated HAITA state were made
available, that touch target may still require the product's angle editor
binding. The likely missing pieces are now narrowly defined as runtime
availability initialization and product UI binding, rather than the angle
implementation itself.

### Read-only PC Remote inventory

Sony's Camera Remote SDK models shutter mode, shutter angle, shutter mode
setting, and shutter mode status as distinct live properties. The local
firmware contains matching remote-event names. A useful next check is whether
the A7 IV actually advertises any corresponding vendor property while the
angle flag is active.

The repository includes a read-only inventory tool. Reboot the camera out of
service mode, choose **USB Connection Mode → PC Remote**, close Imaging Edge
and Photos, then run:

```bash
cd ~/Documents/sony-a7iv-feature-research
sudo ~/Documents/Sony-PMCA-RE/venv/bin/python \
  scripts/a7iv_ptp_snapshot.py \
  --output ~/Documents/a7iv-ptp-angle-on.json
```

The script requests Sony protocol 3.00 (`0x012c, 1`), performs the PC Remote
handshake, records the advertised property/control codes, and saves the
aggregate property information returned by read operation `0x9209`. Requesting
legacy protocol 2.00 (`0x00c8`) would deliberately expose only the small
pre-2020 compatibility surface even on an A7 IV. The script does not invoke
the set-property commands (`0x9205` or `0x9207`) and does not alter camera
state. The resulting JSON lets us compare the live USB model with the compiled
`ptp_shutter_*` strings without guessing property numbers.

#### A7 IV 6.02 protocol-3 speed-mode baseline

The first physical A7 IV protocol-3 capture was made with shutter-angle mode
**off** (`0x02cf1702=00`). It is therefore the speed-mode baseline, not an
angle-enabled result. The camera accepted protocol 3.00 and returned:

```text
advertised properties       404
advertised controls          57
aggregate descriptor count  361
aggregate bytes             9054
```

`scripts/analyze_ptp_snapshot.py` decoded all 361 descriptors and consumed
exactly all 9,054 bytes. As expected for this baseline, no default, current,
range, primary enumeration, or secondary enumeration contained `180000`, the
Remote SDK representation of 180 degrees. The result is reproducible with:

```bash
python3 scripts/analyze_ptp_snapshot.py \
  ~/Documents/a7iv-ptp-speed.json \
  --output ~/Documents/a7iv-ptp-speed-decoded.json
```

This baseline cannot establish whether the PC Remote surface changes when the
internal angle formatter is active. The required comparison is an otherwise
identical capture after setting `0x02cf1702=01`, verifying `180°` on screen,
and rebooting into PC Remote mode. A descriptor-level diff will then show
whether angle mode exposes a new property, changes a current value or enable
flag, or leaves the entire remote surface unchanged.

#### A7 IV 6.02 angle-mode comparison

The physical angle-enabled capture also negotiated protocol 3.00 and returned
the same 404 advertised properties, 57 controls, and 361 aggregate
descriptors. Its aggregate data was 8,139 bytes and decoded exactly. No
descriptor contained `180000`.

Two changes are specific to shutter control:

| Property | Speed-mode capture | Angle-enabled capture |
| --- | --- | --- |
| `0xd20d` (`PTP_DPC_SONY_ShutterSpeed`) | enabled, current `0x00010032` (1/50), 37 values | disabled, current `0xffffffff`, no values |
| `0xd19f` (newer 64-bit shutter-speed value) | enabled, current `0x0000000100000032` (1/50), 37 values | disabled, current `0xffffffffffffffff`, no values |

No property was added or removed. In particular, the angle-enabled capture did
not expose a replacement descriptor containing the current 180-degree value.
This is direct evidence that the backup change reaches a distinct shutter
state while the A7 IV's PC Remote surface withholds the angle-value control.

Sony's [Camera Remote SDK device matrix][sdk-property-list] agrees with that observation. It marks
`Shutter Mode Setting` as supported on ILCE-7M4, but marks `Shutter Angle`,
`Shutter Mode`, `Shutter Mode Status`, `Shutter Speed Value`, and `Shutter
Speed Current Value` unsupported on that model. The latter properties are
listed for cinema bodies including ILME-FX3.

The first two captures also differed in aperture, ISO, and groups of other
shooting properties. A second speed-mode capture was therefore made with the
camera otherwise left in the same Movie/Manual configuration. That controlled
comparison returned 8,955 bytes and again decoded all 361 descriptors exactly.

Only `0xd19f` and `0xd20d` changed enablement in the controlled comparison.
The matched speed capture reported 1/125 second in both encodings and 34
settable speed values; angle mode disabled both descriptors, replaced their
current values with all-ones sentinels, and removed both value lists. No
property was added, removed, or enabled as an angle replacement. Three other
descriptors changed only their transient current values: `0xd1b5` moved from
`-7000` to `-6000`, while `0xd204` and Sony battery-level property
[`0xd218`][libgphoto-ptp]
moved from `90` to `88`.

The input evidence hashes are:

```text
6a38324c2145aeff95f02e9a8293862f1f9486b72947c96c72c7f49b822a6ce1  a7iv-ptp-speed-matched.json
d7250328d0d3c3ab76f9b38f5653e1c3b3424dc6424b5880010dfb056a0d68d5  a7iv-ptp-angle-on.json
```

The repository comparison command is:

```bash
python3 scripts/compare_ptp_snapshots.py \
  ~/Documents/a7iv-ptp-speed.json \
  ~/Documents/a7iv-ptp-angle-on.json \
  --enablement-only
```

## Official behavior is product-specific

Sony documents the A7 IV and FX3 differently even when the shooting-mode dial
is already set to Movie or S&Q:

| Camera | Sony's Exposure-group menu inventory |
| --- | --- |
| ILCE-7M4 | Starts with **Auto Slow Shutter**; no **Shutter Mode** entry |
| ILME-FX3 | **Shutter Mode**, then **Auto Slow Shutter** |

The FX3 page says the menu item itself is available for movie/S&Q shooting.
Only the **Angle** choice has the additional exposure-mode conditions: Shutter
Priority, Manual Exposure, or Flexible Exposure with shutter control set to
Manual. [Sony FX3 Shutter Mode][fx3-shutter]

This distinction matters. If the A7 IV page merely became unavailable because
of the current exposure mode, Sony's menu catalogue would still list it and
the UI would normally show a disabled item. Sony's A7 IV inventory contains no
such item at all.

## Binary evidence

The two comparison applications were:

| Image | Local extracted file | SHA-256 |
| --- | --- | --- |
| A7 IV 6.02 | `unpacked/.../nflasha15_unpacked/lib/appFw.so` | `1e1b9202eaa69198f20df03dbfdab2f103b206cc4ebcd2e7bd817e6a710018a2` |
| FX3 7.02 | `comparison/FX3-7.02-unpacked/.../nflasha15_unpacked/lib/appFw.so` | `545c5053a74e04ffbf2bbaaf80f558092dd545ed2298b2395ca547dbba58290f` |

Both are AArch64 ELF shared objects. `strings -a -t x` finds the following
file/virtual addresses (the relevant sections have matching file and virtual
offsets):

| Symbolic name | A7 IV 6.02 | FX3 7.02 | Meaning |
| --- | ---: | ---: | --- |
| `PRM_setting_mode_shutter` | `0x4c4456c` | `0x39b498c` | Speed/angle backing parameter |
| `PRM_setting_shutter_angle` | `0x4c57b46` | `0x39b5516` | Selected angle parameter |
| `VAL_setting_mode_shutter_MODE_SHUTTER_SPEED` | `0x4d9dd0c` | `0x3ab8819` | Speed enum name |
| `VAL_setting_mode_shutter_MODE_SHUTTER_ANGLE` | `0x4d9dd38` | `0x3ab8845` | Angle enum name |
| `FUNC_shutter_angle_next_seq` | `0x4c5db3b` | `0x39c66a7` | Advance angle action |
| `FUNC_shutter_angle_prev_seq` | `0x4c5db57` | `0x39c66c3` | Decrease angle action |
| `UIBIZ_KEY_TACT_SHUTTER_MODE` | `0x4f98129` | `0x3bb18dc` | Shutter-mode UI action key |

### The UIBIZ key is registered in both builds

The dynamic relocation for the A7 IV name points to a key record at
`0x5834580`. The record has key ID `0x173` and name length 30. Its neighbors
are:

```text
0x5834570  id 0x172  UIBIZ_KEY_TACT_IRIS_SPEED
0x5834580  id 0x173  UIBIZ_KEY_TACT_SHUTTER_MODE
0x5834590  id 0x174  UIBIZ_KEY_TACT_SHUTTER_SELECT
```

The FX3 relocation points to the corresponding record at `0x41664b0`, with
key ID `0x170`:

```text
0x41664a0  id 0x16f  UIBIZ_KEY_TACT_IRIS_SPEED
0x41664b0  id 0x170  UIBIZ_KEY_TACT_SHUTTER_MODE
0x41664c0  id 0x171  UIBIZ_KEY_TACT_SHUTTER_SELECT
```

The three-position shift is caused by changes elsewhere in the generated key
table. These numeric UIBIZ IDs are build-local and must not be copied between
firmware versions.

In the A7 IV, code at `0x21867c0` registers key `0x173` in the same generated
run as its neighboring keys:

```asm
21867c0: ldr  x0, [x19, #0x268]
21867c4: mov  w2, #0x173
21867c8: mov  w1, #0x1c
21867cc: bl   0x2184098
21867d0: ldr  x0, [x19, #0x268]
21867d4: mov  w2, #0x174
```

This confirms that the A7 IV has a live shutter-mode UI/action key. The
`TACT` key belongs to the operating-screen/action layer; its existence does
not create a Settings menu node. That distinction matches the observed result:
the movie display reacts, while the Settings catalogue remains unchanged.

### The broad menu feature flag is not the discriminator

The A7 IV's product-name table identifies:

```text
PRODUCT_MODEL_LAX        enum 4
PRODUCT_MODEL_ALCIN_UUD  enum 5
```

`feature_manager::update_product_model()` begins at `0x183ecc0`. Its jump
table at `0x37b7910` maps product enum 4 (`LAX`) to internal feature-table
index 24 and enum 5 (`ALCIN_UUD`) to index 21. The
`FEATURE_MANAGER_menu_item` getter at `0x183f0f4` loads from table
`0x37b9548`. Both relevant entries are `1`:

```text
table[24]  LAX        = 1
table[21]  ALCIN_UUD  = 1
```

Therefore changing the broad `FEATURE_MANAGER_menu_item` value is not a
supported explanation or a useful next experiment. The missing page must be
selected at a finer level.

### Shared resources do not imply a shared menu catalogue

The generic layout files are byte-identical between these two extracted
updates:

| Resource | SHA-256 in both updates |
| --- | --- |
| `master_camera.uxc` | `3c57ae846d37ba95e41cddbdfbe3cad5c3ccf1b68ff434a09641b59f70774017` |
| `LayoutMaster_Menu.uxc` | `281ea2348ba605ceb4807c013382b0c408155b31316fdad36e8e229b8a35ed44` |

Those files provide common screen/layout machinery. They cannot, by
themselves, explain why one product lists the page and the other does not.

The English resources package the same wording in different feature bundles:

| Build | File containing exact `Shutter Mode` label | Label offset |
| --- | --- | ---: |
| A7 IV 6.02 | `string_english_func_j.uxc` | `0x23404` |
| FX3 7.02 | `string_english_f.uxc` | `0x58c78` |

The A7 IV file also contains `Speed`, `Angle`, “Sets the shutter speed when
shooting movies,” and the angle-specific help sentence around offsets
`0x233bc`–`0x23488`. This is strong evidence of shared resource generation,
but not proof that the A7 IV menu tree references those strings. The different
resource-bundle placement is consistent with product UI composition, though
it is not sufficient to identify the responsible predicate.

## What the missing menu is not

- It is not evidence that angle calculations are absent. The camera accepts
  angle state, shows the icon, and the binary contains the angle parameter and
  increment/decrement actions.
- It is not explained by the current P/A/S/M or Flexible Exposure selection.
  Those conditions govern whether the FX3's **Angle** choice is active; Sony
  documents the **Shutter Mode** menu item itself for movie/S&Q.
- It is not controlled by the broad feature-manager `menu_item` value; that
  value is identical for the two product classes in the A7 IV shared build.
- The present analysis found no evidence for a second backup property whose
  sole purpose is to reveal this page.

## Most useful next reverse-engineering targets

There are now two concrete targets:

1. Trace the A7 IV product filter that omits the angle-value and angle-status
   properties from the protocol-3 descriptor generator. The controlled USB
   comparison establishes that no alternate property replaces shutter speed.
2. Trace the writers feeding HAITA getter `0x293d634`, then compare their
   product-model inputs for `PRODUCT_MODEL_LAX` and `PRODUCT_MODEL_ALCIN_UUD`.
   This is more direct than patching angle arithmetic, which already exists.

The Exposure menu's ordered item list remains a separate target for restoring
the FX3-style settings page. A sound trace should begin from neighboring
visible entries such as **Auto Slow Shutter** and **Auto/Manual Swt. Set.**.
It should not begin by patching key ID `0x173`: that key is already registered
and its number is local to this build.

Until the runtime HAITA input and menu predicate are identified, the backup
property changes the displayed state but does not provide a working in-camera
angle control.

## Reproduction commands

With `A7` and `FX3` set to the two extracted `appFw.so` paths:

```bash
shasum -a 256 "$A7" "$FX3"

strings -a -t x "$A7" | rg \
  'PRM_setting_(mode_shutter|shutter_angle)|FUNC_shutter_angle_(next|prev)_seq|UIBIZ_KEY_TACT_SHUTTER_MODE'

strings -a -t x "$FX3" | rg \
  'PRM_setting_(mode_shutter|shutter_angle)|FUNC_shutter_angle_(next|prev)_seq|UIBIZ_KEY_TACT_SHUTTER_MODE'

objdump -d --start-address=0x183ecc0 --stop-address=0x183f120 "$A7"
objdump -d --start-address=0x21867c0 --stop-address=0x21867e0 "$A7"
```

The UIBIZ record addresses above were obtained by parsing `.rela.dyn`
`R_AARCH64_RELATIVE` entries whose addends equal the name-string addresses,
then reading the generated 16-byte records as pointer, 32-bit ID, and 32-bit
name length.

## Confidence

| Finding | Confidence |
| --- | --- |
| The A7 IV menu item is absent by product design, not merely hidden by the current exposure mode | High |
| `0x02cf1702` changes the backing shutter mode without adding a menu node | High, based on the observed camera result plus matching firmware parameters |
| The runtime/action implementation for shutter angle exists in A7 IV 6.02 | High |
| The angle-mode dial path contains a generated HAITA availability guard before the setter | High |
| Angle mode disables both exposed speed descriptors without exposing an angle replacement | High, from the controlled protocol-3 A/B capture |
| The exact input which keeps that HAITA state asserted on the A7 IV | Not yet established |
| A finer product-specific menu catalogue/composition path suppresses the A7 IV page | Medium-high |
| Exact function/table/patch responsible for the omission | Not yet established |

[a7-menu]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1001803623.html
[a7-defaults]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1001803633.html
[fx3-shutter]: https://helpguide.sony.net/ilc/2210/v1/en/contents/TP1001690662.html
[fx3-menu]: https://helpguide.sony.net/ilc/2210/v1/en/contents/TP1000888827.html
[a7-auto-manual]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000657953.html
[a7-exposure]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000657954.html
[sdk-property-list]: https://amarburg.github.io/sony_remote_camera_sdk/function_list/device_property_list.html
[libgphoto-ptp]: https://github.com/gphoto/libgphoto2/blob/master/camlibs/ptp2/ptp.h
