# A7 IV cinema features: web research

Date: 2026-11-25

Scope: public web sources only (Sony help guides, Sony support/press, lab tests, GitHub). Claims found only in forums, Reddit, single reviews or search-engine summaries are marked **unverified**. Inferences are marked **inference**.

## 1. Sensor readout / rolling shutter per mode

### Measured numbers

| Mode | Readout | Source |
|---|---|---|
| FF 4K 24p | 26.76 ms | Horshack table, https://horshack-dpreview.github.io/RollingShutter/ |
| FF 4K 25p | 26.8 ms | CineD lab test, https://www.cined.com/sony-a7-iv-lab-test-rolling-shutter-dynamic-range-and-latitude/ and https://www.cined.com/camera-database/?camera=Alpha-a7-IV |
| FF 4K 30p | 26.71 ms (Horshack); ~27.4 ms (DPReview) | https://horshack-dpreview.github.io/RollingShutter/ ; https://www.dpreview.com/reviews/sony-a7-iv-review |
| S35/APS-C 4K 25p | 13 ms | CineD camera database (link above) |
| S35/APS-C 4K 60p | 13.00 ms (Horshack); ~12.8 ms (DPReview) | links above |
| FF HD 24/30/60p | 8.86 / 8.91 / 8.86 ms | Horshack table |
| FF HD 120p | 6.50 ms | Horshack table |
| Stills, e-shutter (14-bit) | 67.63 ms (Horshack); ~1/15 s (DPReview) | links above |

Horshack's method: photograph a 500 Hz flicker source and count bands (described on the page). CineD's 26.8 ms and DPReview's 27.4 ms agree within about 3%. I found no CineD number for any HD mode.

How the modes are produced, per reviewers and Sony:
- FF 4K is downsampled from the 7K sensor (CineD, citing Sony, link above). DPReview guesses the readout is 12-bit (DPReview link, **inference by the reviewer**).
- 4K 60p is an S35 crop "from a 4.6K region" with "a tiny bit of oversampling" (DPReview). Camera Labs calls it a 1.5x crop (https://www.cameralabs.com/sony-a7-iv-review/3/).
- FF HD 60/120p: I found no reviewer who documents the method (skipping vs binning). **Inference:** the HD readout is about 1/3 of the FF 4K readout over the same full-width field (8.86 vs 26.7 ms), so it reads about one row in three. That points to 3:1 vertical subsampling. On the related a6700, community reverse engineering documents 3x3 pixel skipping for 1080p 60 (1984x1116 read) (https://github.com/Himpq/FireHydrant/tree/main/1080p_binning). That is a different body, so treat it as an analogy, not proof. The usual reports of soft, aliased 1080p on Sony full-frame bodies are forum-level (**unverified**).

### Check against our readout table

Dividing the measured times by our line-period counts gives:

| Mode | Line periods (ours) | Measured | Time per line period |
|---|---|---|---|
| FF 4K 30p | 2011 | 26.71 ms | 13.28 us |
| S35 4K 60p | 1356 | 13.00 ms | 9.59 us |
| FF HD 60p | 682 | 8.86 ms | 12.99 us |
| FF HD 120p | 682 | 6.50 ms | 9.53 us |

**Inference:** the table matches the measurements well. Two line clocks show up, about 13.0–13.3 us and about 9.53–9.59 us. The 682-period HD mode uses both, depending on frame rate.

**Verdict: the measurements support "FF 4K60 from the 7K readout is impossible", with one correction to the margin:**
- At FF's own line period (13.28 us), the readout takes 26.7 ms against a 16.68 ms frame. That is 1.6x too slow, close to our "~1.5x".
- Even at the fastest line period measured anywhere on the camera (9.53 us), 2011 periods take ≈19.2 ms. That is still 1.15x over 16.68 ms. So the margin is thinner than 1.5x, but 60p still does not fit. Note that 19.2 ms would fit a 50p frame (20.0 ms) or a 48p frame (20.85 ms) if the FF line could run on the fast clock.
- FF lines appear to be bandwidth-bound. FF 4K moves about 7008 px x ~3942 rows in 26.7 ms, about 1.03 Gpx/s. S35 4K60 moves about 0.95 Gpx/s. FF on the fast clock would need about 1.44 Gpx/s, roughly 40% more than any measured mode. CineD also measured S35 at 13 ms even at 25p, so Sony runs S35 on the fast clock at every frame rate but never runs FF 4K on it. That fits a hardware limit (**inference**, unproven).
- The a7 V needed a new partially stacked sensor to get FF 4K60 (14.7 ms, and 13 ms with AoVP) (https://www.cined.com/sony-a7-v-lab-test-rolling-shutter-dynamic-range-and-exposure-latitude/ ; https://nofilmschool.com/sony-a7-v). That is circumstantial support.

**Caveat (contradicts a blanket "no FF 60p"):** full-height, full-width subsampled readout is fast. HD 120p reads in 6.5 ms. So a binned or skipped FF 60p mode below 4K is physically plausible. Erlla says he is working on a "3.5K 60p in 2x2 pixel binning mode" (https://github.com/Erlla/sony-a7m4-custom-firmware/issues/20, maintainer comment, **unverified**, no release).

**Open gate (inference):** the same model gives a 4688-row readout of ≈26.7 x 4688/3942 ≈ 31.8 ms. That fits 24/25/30p (30p is tight) and not 50/60p. Rolling shutter in open gate would be about 32 ms, worse than FF 4K.

## 2. Hidden-feature candidates: shipped by Sony?

**A7 IV:** none of the candidates has ever shipped in-camera, up to 6.02. Sources:
- The A7 IV MENU list has no de-squeeze, shutter angle, Log shooting, time-lapse movie, waveform or RAW output item (https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1001803623.html).
- Firmware history: 1.10 added a serial number in movie metadata. 3.00 added Network Streaming, C2PA and a paid Custom Grid license. 4.00 added Shot Marks, focus bracketing and Monitor & Control app support. 5.00 added digital signatures for stills. 6.00/6.01 added clip flags, a dual-card capacity display, an always-on audio meter, signatures for movies, Spot XL/Custom AF areas and FTP features. 6.02 fixed focus bracketing and stability. Sources: https://www.alphashooters.com/cameras/sony-a7iv/firmware/ (aggregator), https://www.newsshooter.com/2025/11/25/sony-a7r-v-ver-4-00-a7-iv-ver-6-00-firmware-updates/ , https://fstoppers.com/gear/sony-releases-major-firmware-updates-a1-a7s-iii-a7-iv-and-a9-iii-662312 , https://www.newsshooter.com/2026/05/29/sony-a7s-iii-a7-iv-firmware-updates/ .
- Sony's own support pages (sony.ca, sony.co.in) returned 403 to the fetcher, so the version lists above come from secondary sources.

**Off-camera exception:** the Sony Monitor & Control phone app lists the ILCE-7M4 as supporting waveform, vectorscope, histogram, false color, EL Zone and de-squeeze. It does not support LUTs or [Shutter mode] (angle) on the ILCE-7M4. Source: https://helpguide.sony.net/promobile/mc/v1/en/contents/supported_camera.html . A7 IV 4.00 added Monitor & Control support (alphashooters link above).

| Feature | Bodies that got it (version) | Sources |
|---|---|---|
| Anamorphic de-squeeze display | FX3 3.00 / FX30 2.00 (Apr 2023): 1.3x, 2.0x. FX3 7.00 / FX30 6.00 / FX3A 2.00 (Aug 2025): + 1.5x and "1.6x" (the FX30 guide says 1.65-fold correction). FX2 at launch: 1.3x, 2.0x. FX5 has a De-Squeeze page. Not found on a7S III, a7 V, a7C II, a7CR, a6700, a9 III, a1 II | https://www.videomaker.com/news/sony-releases-firmware-update-for-fx3-and-fx30/ ; https://helpguide.sony.net/ilc/2220/v1/en/contents/TP1001106329.html ; https://www.imaging-resource.com/news/2025/08/27/sony-releases-new-firmware-for-fx3-fx3a-and-fx30-cinema-cameras ; https://amateurphotographer.com/latest/photo-news/new-sony-fx2-cinema-camera-with-tilting-viewfinder-and-a7c-ii-tech/ ; https://helpguide.sony.net/ilc/2630/v1/en/contents/shooting.html ; help-guide indexes 2320/2360/2370/2380/2440/2540 under https://helpguide.sony.net/ilc/ |
| Shutter angle | FX3 6.00 / FX30 5.00 (Sep 2024; pulled 13 Sep, re-released 9 Oct 2024). FX5: [Mode] Speed/Angle, continuous 360.0° to 4.2°. The Monitor & Control table marks shutter mode as available in the ILCE/FX2 group only on the FX2. Not on any Alpha body | https://digitalcameraworld.com/news/finally-firmware-update-brings-shutter-angle-to-sony-fx3-and-fx30 ; https://helpguide.sony.net/ilc/2630/v1/en/contents/shooting.html ; Monitor & Control table above |
| DCI 4K 4096x2160 | FX3 3.00 / FX30 2.00: XAVC S-I DCI 4K. a7S III 3.00 (28 Mar 2024) plus a free "DCI 4K / 24.00p Upgrade License" via Creators' Cloud (24.00p only; no proxy; reboots on switch). Not A7 IV, not a7 V | Videomaker link above ; https://creatorscloud.sony.net/catalog/en-us/cameraupgrade/index.html ; https://www.newsshooter.com/2024/02/20/sony-%ce%b17s-iii-dci-4k-24-00p-upgrade-license-available-in-march/ |
| Time-lapse movie (S&Q dial > Time-lapse) | At launch on a6700, a7C II, a7CR, a9 III, ILX-LR1, ZV-E10 II, a1 II, a7 V, a7R VI. Interval 1–60 s; 4K limited to <6 s intervals; HD/4K XAVC S; no audio. Never added by firmware to A7 IV, a7S III, a7R V or a1 (not found) | https://helpguide.sony.net/ilc/2540/v1/en/contents/221h_timelapse_movie_settings.html ; sibling pages for 2320, 2360, 2370, 2380, 2390, 2430, 2440, 2620 |
| Log shooting mode / Flexible ISO / Cine EI | FX3 2.00 (Jul 2022): Cine EI, Cine EI Quick, Flexible ISO, user LUTs (16), S-Log2 removed. FX2 and FX3A: Off / Flexible ISO / Cine EI Quick / Cine EI. a7S III 4.00 (Apr 2025): Log shooting mode with LUT preview, S-Log2 dropped. a7C II and a7 V: Off / On (Flexible ISO) only. a6700, a7CR, a9 III, a1 II and ILX-LR1 have a Log Shooting Setting page | https://www.newsshooter.com/2022/07/13/sony-fx3-version-2-00-firmware-update/ ; https://helpguide.sony.net/ilc/2530/v1/en/contents/211h_log_shoot_setting.html ; https://helpguide.sony.net/ilc/2510/v1/en/contents/211h_s_log_shooting.html ; https://www.cined.com/sony-a7s-iii-firmware-update-version-4-00-released-adds-in-camera-luts-and-more/ ; https://helpguide.sony.net/ilc/2360/v1/en/contents/211h_log_shoot_setting.html ; https://helpguide.sony.net/ilc/2540/v1/en/contents/211h_log_shoot_setting.html |
| Base ISO switch | FX3 (800/12800, Cine EI since 2.00). FX5: Base ISO 12800 / 4000 / 800 / 800 (Dual Gain). a7 V has dual native 800/8000 but no Cine EI menu | Newsshooter FX3 2.00 link ; FX5 shooting menu link ; CineD a7 V lab link |
| Waveform / false color | In-camera only on the FX5 ("Video Signal Monitor", "False Color" pages). FX3/FX30 and the A7 IV get them through the Monitor & Control phone app. DPReview says the a7 V has no in-camera waveform or false color (search snippet, **unverified**) | FX5 shooting menu link ; Monitor & Control table ; https://dpreview.com/reviews/sony-a7-v-review |
| BIG6 home screen | FX3 7.00 / FX30 6.00 / FX3A 2.00 (Aug 2025). The FX2 UI is "based on VENICE"; BIG6 on FX2 not confirmed | https://www.videomaker.com/news/sony-fx3-gets-big6-home-menu-and-braw-recording-with-firmware-update/ ; Imaging Resource link above |
| RAW over HDMI | FX3 7.00 / FX30 6.00 (Blackmagic RAW on BMD recorders). FX2 "16-bit RAW output" (retailer). FX2 guide: HDMI RAW needs Log Shooting not Off. A7 IV: none | Imaging Resource link ; https://www.wexphotovideo.com/sony-fx2-launch ; https://helpguide.sony.net/ilc/2530/v1/en/contents/211h_log_shoot_setting.html ; Camera Labs link above |
| Variable ND | Hardware filter. Absent on the FX30 and A7 IV (community survey: "hardware absent") | https://github.com/OlliV/fx30_fw (updates/menu_survey) |
| Auto Framing | a6700, a7C II, a7CR, a9 III, a1 II, a7 V, a7R VI. Sony ties it to the AI processing unit (a7C II, a6700), which the A7 IV lacks | https://www.sony-asia.com/interchangeable-lens-cameras/products/ilce-7cm2/feature3 ; https://www.sony.co.th/en/interchangeable-lens-cameras/products/ilce-6700/feature-list ; help-guide indexes above |
| True 24.00p | FX3 3.00 / FX30 2.00. a7S III 3.00 (via the license, with 1/24, 1/48, 1/96 shutter steps) | Videomaker FX3 link ; Creators' Cloud link |

Notes on the help-guide checks:
- "Not found" for Alpha bodies means no page title matched in the help-guide index. The FX5 keeps shutter angle inside its [Shutter] page, so a title search could miss a feature. The Monitor & Control table independently says shutter mode is FX-only.
- 1.6x vs 1.65x: Sony markets it as 1.6x, but the FX30 help guide text says "1.65-fold horizontal correction".

## 3. A7 IV hardware facts

- **Sensor:** 35 mm full frame, 35.9 x 23.9 mm, Exmor R CMOS. About 33.0 MP effective and 34.1 MP total, 3:2 (https://store.sony.co.th/blogs/6646505275435_39568395829291/6646505275435_specifications). DXOMARK calls it "a completely new ... 33 MP BSI-CMOS" (https://www.dxomark.com/sony-a7-iv-sensor-test/).
- **Readout:** a Sony feature page (fetch blocked, text from a search snippet) says 4K 60p uses full pixel readout without binning. FF 4K is 7K oversampled (CineD, citing Sony). Numbers are in section 1.
- **Dual base ISO in S-Log3:** Sony does not claim one. Sony lists S-Log native at ISO 800, lowerable to 200–640 (search snippet of the Sony feature page, **unverified** text).
  - Measured, stills only: DXOMARK places the second conversion-gain step at ISO 400 (the A7 III's was at 800) (DXOMARK link).
  - No lab has measured an S-Log3 second gain point. Videomaker saw "dual-native-like" behaviour from ISO 3200 (https://www.videomaker.com/reviews/sony-a7-iv-review-sonys-mirrorless-jack-of-all-trades/, subjective, **unverified**).
  - **Inference:** a stills DCG at ~ISO 400 plus the usual ~3-stop S-Log3 ISO offset lands near S-Log3 ISO 3200, which agrees with Videomaker. A sibling data point: the a6700 community found a dormant Cine EI with a HIGH base aligned to 2500 (https://github.com/Himpq/FireHydrant/tree/main/cine_ei).
- **Dynamic range:** CineD measured FF 4K S-Log3 ISO 800 at 12.9 stops (SNR=2) and 14 stops (SNR=1), with about 7 stops of latitude. In-camera NR cannot be turned off (CineD lab link).
- **HDMI:** Type A port. Output resolution Auto/2160p/1080p/1080i. 4K output 60p/50p/30p/25p/24p, all 10-bit. Simultaneous card + HDMI recording or HDMI only. Timecode output and REC control. No 4-channel audio over HDMI (https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000657988.html). No RAW video output (Camera Labs link above).
- **Codecs and max bitrates:** Sony spec sheet (store.sony.co.th link):

  | Codec | Mode | Max bitrate |
  |---|---|---|
  | XAVC S-I 4K 4:2:2 10-bit | 60p / 30p / 24p | 600 / 300 / 240 Mbps |
  | XAVC S-I HD | 60p | 222 Mbps |
  | XAVC HS 4K (H.265) | 4:2:2 10-bit 60p | 200 Mbps |
  | XAVC HS 4K (H.265) | 4:2:0 60p | 150 Mbps |
  | XAVC S 4K 4:2:2 10-bit | 60p / 30p / 24p | 200 / 140 / 100 Mbps |
  | XAVC S HD 8-bit 4:2:0 | 120p | 100 Mbps |

  S&Q goes up to 120 fps. USB streaming goes up to 4K 15p.
- **Heat and recording time:** Sony help guide, [Auto Pwr OFF Temp.] = High. At 25 °C: about 120 min for both HD and 4K. At 40 °C: about 120 min HD and about 30 min 4K. Conditions: XAVC S 4K 30p 60M, monitor open, no Wi-Fi (https://helpguide.sony.net/ilc/2110/v1/en/contents/TP1000653559.html). Camera Labs recorded past 30 min without overheating.

## 4. Community firmware projects (BIONZ XR era)

| Project | Body | What it does | Relevance |
|---|---|---|---|
| https://github.com/Erlla/sony-a7m4-custom-firmware | A7 IV 6.02 | Install without Fastboot over plain USB. Fastboot via RP2040. Custom update signing, FL2/FL3 port from FX2, third-party battery, custom sounds, custom stills aspect ratios, 16-slot custom LUT (stills looks), shell/SSH, AWB tweak | Base of our build. Issue #20/#40 ask for FF 60p; maintainer: "working on 3.5K60 in 2x2 binning" (**unverified**). Issue #21 asks for false color. Issue #38 is open gate |
| https://github.com/ArcaneLantern/a7iv-open-gate-test | A7 IV 6.02 | RAM-only open gate 4K 3:2 3840x2560 and 5.7K 3:2 5760x3840. 5.7K at 300 Mbps XAVC HS 24p NTSC. Includes a "C3 de-squeeze preview cycle". 5.7K does not play back in camera | Already ships a de-squeeze preview on the A7 IV. Issue #4 asks for Cine EI and preview LUTs |
| https://github.com/DavidBuchanan314/ILCE-7M4-RE | A7 IV | Bootrom serial boot, fastboot payload, eMMC AES-XTS keys, "no signature verification" on eMMC partitions | Low-level enabler |
| https://github.com/16480000/sony-a7iv-qemu | A7 IV 6.02 | QEMU runs the stock UI/menus. The ISP/AF/capture chain is not emulated | Offline UI testing |
| https://github.com/snowfoxyz/sony-a7m4-pplut-research | A7 IV 6.02 | Static analysis: PPLUT1–4 labels and PP-LUT display code exist. The model-gate path is not yet tied to the menu; no patch | Log/LUT gate lead |
| https://github.com/Hearts-Ace/sony-a7r5-custom-firmware | A7R V 4.00 | FL2/FL3, filters, sounds, aspect ratios (port of Erlla/ILCE-7M4-RE) | Shows the patches carry across bodies |
| https://github.com/Himpq/FireHydrant | a6700 2.00 | Done: 6K30, Cine EI / Cine EI Quick (dormant in stock code, unlocked via 3 gates), 1080p oversampled from 6K full readout (replaces 3x3 skipping), card-speed bypass, 2K open gate, FL2/FL3 | Strongest precedent for product-gated Log/Cine EI and HD oversampling on BIONZ XR |
| https://github.com/OlliV/fx30_fw | FX30 6.01 | Decrypt plus a survey of disabled menus. Menu visibility = product menu type + 771 derived `PRM_HAITA_*` availability props + stored values; writing a stored value cannot add a menu item. No open gate or 4:4:4 strings on the FX30 | Explains why gated menus need code patches, not settings writes |
| https://github.com/QAQLeonard/a7c2-tools , https://github.com/YuuLuo/a7c2-service-preload , https://github.com/soralis0912/sony-a7cii-feature-research , https://github.com/soralis0912/sony-a7cii-open-gate-test , https://github.com/jpaulrez/sony-a7c2-hacks | a7C II 2.01 | FL2/FL3, looks, sounds, vertical UI, service-preload code execution. Shutter-angle and open-gate work is WIP with "no verified design". The FF 4K60 hack is only an aim | No verified FF 4K60 or shutter angle on a7C II |
| https://github.com/ma1co/Sony-PMCA-RE , https://github.com/ma1co/OpenMemories-Tweak | Pre-BIONZ-XR (PMCA app bodies) | USB service mode; app install only on PMCA bodies (last push 2024) | Used by ArcaneLantern for the MSC-to-service switch |

Press coverage of the A7 IV open gate hack: https://www.sonyalpharumors.com/sony-a7-iv-open-gate-vibe-coded-firmware-is-now-downloadable/ , https://cameradecision.com/blog/Sony-A7-IV-Gets-Open-Gate-From-a-Fan-Made-Tool-Read-the-Risks-First .

Not found anywhere (as of today): a verified FF 4K60 mode, 1080p open gate, or shutter angle on any A7 IV or a7C II community build. The only 1080p-class open gate is the a6700's "2K OpenGate" (FireHydrant).

## 5. Other software-only cinema features worth porting

Ranked by likely effort and value. The reasons are **inference** unless a source is given.

1. **Shutter angle (FX3 6.00 / FX30 5.00 / FX5).** This is a UI mapping: exposure time = angle / 360 / fps. The A7 IV already sets arbitrary shutter times. Sony added it by firmware to bodies with the same BIONZ XR generation and no hardware change (DCW link in section 2).
2. **De-squeeze 1.3/1.5/1.6(5)/2.0x in-camera.** This is display scaling only. The A7 IV already does it on the phone (Monitor & Control), and ArcaneLantern already does a de-squeeze preview in camera.
3. **BIG6 home screen and Fixed/Variable fps (FX3 7.00).** UI and menu routing over existing settings and S&Q rates (Videomaker BIG6 link).
4. **Log shooting mode with Flexible ISO, Cine EI/EI Quick and monitor LUT (FX3 2.00, a7S III 4.00).** The a7S III got it by firmware. The a6700 community found Cine EI compiled in and only menu-gated (FireHydrant). The monitor LUT depends on a display LUT path; PPLUT display code exists on the A7 IV (snowfoxyz).
5. **True 24.00p and the 1/24, 1/48, 1/96 shutter steps (a7S III 3.00 license, FX3 3.00).** Sony shipped them by firmware or license on the same generation. A timing table change, but the encoder/audio clock must follow (**unverified** for the A7 IV).
6. **DCI 4K 4096x2160.** The FF readout is about 7K wide, so the scaler only needs a different output width. Sony enabled it by license on the a7S III, whose sensor is 4240 px wide. ArcaneLantern already encodes 5760-wide XAVC HS, so the encoder width is not the limit.
7. **Clip-level metadata such as embedded LUT and EI (FX3 2.00).** Metadata only.
8. **Focus Magnifier with Bright Monitoring (FX3 7.00).** UI combination of existing functions.
9. **In-camera waveform and false color (FX5).** False color is a display LUT over luma, so it is likely cheap if the display LUT path is reachable. A waveform needs per-frame histogramming. The A7 IV already sends live view to Monitor & Control, which computes these on the phone. In-camera feasibility is uncertain.
10. **Time-lapse movie (a7C II and later).** Reuses the S&Q encoder at a low capture rate. Sony never back-ported it, so it may depend on newer firmware architecture (**inference**).
11. **HD oversampled from full readout (a6700 community).** The FireHydrant patch routes 1080p60 through the 4K60 readout. On the A7 IV that gives an S35-cropped oversampled HD 60p (the 4K60 readout is S35), or FF HD at ≤30p from the 7K readout.

Not software-only (skip): variable ND (filter hardware), Auto Framing (AI processing unit, per Sony), RAW over HDMI (needs a RAW path to the HDMI transmitter; unproven on the A7 IV), and "true" FF 4K60 from the 7K readout (section 1).

## Confidence and gaps

- **High:**
  - FF 4K readout ≈26.7–27.4 ms and S35 4K60 ≈13 ms: two labs plus Horshack agree.
  - Our line-period table converts to two consistent line clocks.
  - Sony's FX3/FX30/a7S III feature and version history: multiple outlets and Sony help guides.
  - No candidate feature ever shipped on the A7 IV: help-guide menu list plus firmware history.
- **Medium:**
  - HD 60/120 readout numbers: one community source (Horshack). It is methodical but has no second lab.
  - The HD method (3:1 subsampling) is inferred.
  - The throughput explanation for why FF cannot use the fast clock is inferred.
  - Time-lapse and Log-mode body lists come from help-guide page titles, not every menu.
- **Low / unverified:**
  - The S-Log3 second gain point (no lab measurement; ISO ~3200 is inferred).
  - Erlla's 3.5K60 binning work (one issue comment).
  - DPReview's claim that the a7 V has no waveform (snippet only).
  - Whether FX2 has BIG6.
  - FX2 16-bit RAW out (retailer page).
- **Gaps:**
  - Sony's own A7 IV release-notes pages returned 403, so the version list comes from aggregators.
  - No measured readout exists for A7 IV FF 4K in 12-bit vs 14-bit modes, or for stills in 12-bit mode.
  - No public lab test of A7 IV HD 120p image quality (skipping vs binning).
  - It is unknown whether the A7 IV sensor exposes a 2x2-binned FF mode.
