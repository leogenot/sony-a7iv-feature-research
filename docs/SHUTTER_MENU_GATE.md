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
answer is that `0x02cf1702=01` bypasses the absent selector page by setting the
backing state directly; the icon is evidence that the runtime state was
accepted, not evidence that the A7 IV menu catalogue contains the FX3 page.

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
compiled into A7 IV 6.02. It does not yet prove the exact branch taken for a
specific dial event. If the angle still cannot be changed in **M**, **S**, or
Flexible Exposure with Tv explicitly set to **Manual**, that result would
indicate a second product/input-dispatch gate. The useful diagnostic would then
be to read `0x02cf1704` before and after several control-wheel steps: a changed
property with a fixed display would identify a UI refresh problem, while an
unchanged property would identify blocked input dispatch.

### Live dial-block diagnosis

The camera later reported the following live backup settings after the angle
remained fixed at `0x02cf1704=10`:

```text
0x02cf024d = 00  setting_movie_exposure_mode_setting = P/A/S/M control
0x02cf0247 = 00  setting_movie_exposure_mode = Intelligent Auto
0x02cf02d9 = 01  setting_shutter_speed_a_m_switching = Manual
0x02cf1549 = 01  shutter_speed_manual_lock_state = Off/unlocked
```

The Tv channel was therefore already manual and unlocked, but the active movie
exposure mode was Intelligent Auto. That combination explains the nonzero
`PRM_HAITA_setting_shutter_speed_a_m_switching_exposure_mode` state checked by
the angle-drive action. With `0x02cf024d=00`, selecting Movie mode plus physical
mode-dial **S** or **M** should change `0x02cf0247` to `03` or `04`, respectively,
and remove this exposure-mode inhibition.

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

## Most useful next reverse-engineering target

The next target is the code/data that constructs the Exposure menu's ordered
item list for `PRODUCT_MODEL_LAX`, then compare it with the
`PRODUCT_MODEL_ALCIN_UUD` path. A sound trace should begin from neighboring
visible entries such as **Auto Slow Shutter** and **Auto/Manual Swt. Set.**,
because those provide known nodes on both products. It should not begin by
patching key ID `0x173`: that ID is already registered and is local to this
specific build.

Until that menu node and its predicate are identified, direct backup-property
selection is the only mechanism demonstrated by the current evidence. It
enables the state but does not reconstruct the FX3 settings page.

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
| A finer product-specific menu catalogue/composition path suppresses the A7 IV page | Medium-high |
| Exact function/table/patch responsible for the omission | Not yet established |

[a7-menu]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1001803623.html
[a7-defaults]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1001803633.html
[fx3-shutter]: https://helpguide.sony.net/ilc/2210/v1/en/contents/TP1001690662.html
[fx3-menu]: https://helpguide.sony.net/ilc/2210/v1/en/contents/TP1000888827.html
[a7-auto-manual]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000657953.html
[a7-exposure]: https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000657954.html
