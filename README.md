# PPSSPP frame dumps

GE frame dumps (`.ppdmp`) of PSP games, together with what a real PSP renders for each of them. Most were
attached to [PPSSPP](https://github.com/hrydgard/ppsspp) GitHub issues over the years; more are recorded
directly. Use it to check PPSSPP's renderers against the
hardware, compare one backend with another, or find out whether a change makes any game look different.

PPSSPP doesn't include this repository (it's about 1.2 GB). Clone it next to your PPSSPP checkout:

```bash
git clone https://github.com/hrydgard/ppsspp-framedumps.git
```

## What's here

```
dumps/<name>.ppdmp           1007 frame dumps
ref/<name>-psp.png           what a PSP displays for that dump (480x272), for 978 of them
ref/<name>-psp-depth.bin     the PSP's depth buffer after the frame, for 958 of them
manifest.json                one entry per dump (see below)
renames.json                 the original file name of each dump -> its name here
frametests.json              a config for PPSSPP's frametests.py, comparing against ref/
KNOWN_DIFFERENCES.md         differences left for later, grouped by cause
tools/render.py              renders every dump with PPSSPPHeadless
tools/compare.py             compares renders with the PSP references, or with each other
```

The PSP references were made by replaying each dump on a PSP with pspautotests' `utils/ppdmp-playback`
(see "Replaying a dump on a real PSP" in PPSSPP's `docs/frametest.md`). The depth files are a u32 width, a
u32 height, then a u16 depth per pixel, row by row.

### Names

A dump's name is PPSSPP's own name for it, with the GitHub issue number in front when it came from an issue,
and optionally a short description after it:

```
ULES00262_0001 OutRun 2006 water reflections.ppdmp            recorded directly
11928 ULUS10064_0001 OutRun 2006 Coast 2 Coast USA missing water.ppdmp      from issue 11928
```

So a dump PPSSPP records (`ULES00262_0001.ppdmp`) gets its place here by adding a description, and by
prefixing `<issue> ` if it belongs to an issue. Its references are named the same with `-psp.png` and
`-psp-depth.bin` instead of `.ppdmp`.

- The game ID (disc ID, such as `ULES00262`) matters: PPSSPPHeadless applies the game's compatibility
  settings (`assets/compat.ini`) by it, and without them a dump can render differently from the game. Dumps
  from version 4 on store the ID themselves; for older ones headless reads it from the file name. (Older
  PPSSPP builds don't skip the issue number, so they need the change "Read a frame dump's game ID after a
  leading issue number in its name".)
- `_NNNN` is the number PPSSPP gave the dump. For the old issue dumps, whose original numbers were lost, it
  counts `0001`, `0002`, ... per issue and game.
- Descriptions are ASCII, without quotes or other characters that trip up shell scripts, and at most about
  64 characters. For issue dumps it's the issue title, or the name the dump was attached with.
- A few old issue dumps have no known game ID. They're named `<issue> <description>` (with `_2`, `_3` for
  several), until someone identifies the game.

### manifest.json

```json
{"name": "11928 ULUS10064_0001 OutRun 2006 Coast 2 Coast USA missing water", "source": "issue", "issue": 11928,
 "ppssppName": "ULUS10064_0001", "gameId": "ULUS10064", "gameIdSource": "title match", "dumpVersion": 3,
 "pspReference": true, "pspDepth": true, "notes": []}
{"name": "ULES00262_0001 OutRun 2006 water reflections", "source": "recorded", "issue": null,
 "ppssppName": "ULES00262_0001", "origin": "recorded in-game, stage 1 coast", "gameId": "ULES00262",
 "gameIdSource": "header", "dumpVersion": 6,
 "pspReference": true, "pspDepth": true, "notes": []}
```

`source` is `issue` for dumps from a GitHub issue (with `issue` set) and `recorded` for the others, which have
`issue: null` and may say in `origin` where they came from (who recorded them, and where in the game).
`ppssppName` is the `<game ID>_<NNNN>` part of the name (null for the few dumps without a game ID).

`gameIdSource` says how much to trust the ID:

| Source | Meaning |
|---|---|
| `header` | stored in the dump itself (dump version 4 and up; every recorded dump) |
| `file name` | was in the file name the dump was attached with |
| `same issue` | taken from another dump of the same issue |
| `issue` | written in the GitHub issue |
| `title match` | the game named in the issue title, looked up in PPSSPP's `assets/redump.csv` (Europe preferred, then USA, then Japan when the title doesn't say) - a guess |
| `null` | unknown; the name has no ID |

`notes` lists anything unusual: dumps that hang the PSP replayer and so have no reference, and references that
were recaptured.

## Using it

The examples assume this repository and PPSSPP are next to each other, and a built PPSSPPHeadless.

```bash
export PPSSPP_HEADLESS=~/ppsspp/build/PPSSPPHeadless
```

### Check a renderer against the PSP

Render every dump, then compare with the references:

```bash
python3 tools/render.py --graphics vulkan            # out/vulkan/<name>.png
python3 tools/compare.py out/vulkan --sort            # most different first
```

`compare.py` uses PPSSPP's `Tools/image_compare.py` (found through `$PPSSPP` or `../ppsspp`). It ignores the
pixel-or-two differences any two rasterizers have, and counts only areas that really differ, plus broad
color shifts. It prints the differing pixels per dump and a total, so two builds can be compared by their
totals and by which dumps moved. `--heatmaps DIR` writes each differing dump next to its reference with the
differences marked.

The software renderer should match the references exactly for most dumps, so for it any change in the
list is worth a look. The hardware backends never match exactly; compare their totals before and after a
change instead.

### Compare two renderers, or two builds

```bash
python3 tools/render.py --graphics vulkan
python3 tools/render.py --graphics opengl
python3 tools/compare.py out/vulkan out/opengl --sort
```

Where two backends disagree, the reference usually says which one is right. To compare builds, render
with each into different directories (`--out`) and compare those.

### With frametests.py

PPSSPP's `frametests.py` can run the set directly; `frametests.json` compares the software, Vulkan and OpenGL
renderers with the PSP references and writes an HTML report to `out/frametests/`:

```bash
python3 ~/ppsspp/frametests.py frametests.json --filter="Pursuit Force"
```

It uses a plain MSE limit, which suits the software renderer; for the hardware backends `tools/compare.py`
says more.

### Look at one dump

```bash
$PPSSPP_HEADLESS "dumps/<name>.ppdmp" --graphics=software --screenshot-save=out.png
$PPSSPP_HEADLESS "dumps/<name>.ppdmp" --graphics=software --replay-end=120 --screenshot-save=out.png --depth-save=out.d
```

`--replay-end=N` stops after the Nth draw, which helps narrow down which draw goes wrong; `--depth-save`
writes the depth buffer in the same format as the `-psp-depth.bin` references. The dumps also open in
PPSSPP's GE debugger.

## Adding dumps

1. Keep the name PPSSPP gave the dump, add a short description of what it shows, put `<issue> ` in front if it
   came from an issue (with a `_NNNN` not yet used for that issue and game), and put it in `dumps/`.
2. If you have a PSP, replay it there with `utils/ppdmp-playback` and save the screenshot as
   `ref/<name>-psp.png` (and the depth as `ref/<name>-psp-depth.bin`).
3. Add an entry to `manifest.json`, with `source` `issue` or `recorded`.
4. Check that it isn't a duplicate: a dump that renders the same frame as one already here adds nothing.

## Things to know

- A dump records the GE commands of one frame and the memory they used, including what was in VRAM when
  the frame started. An old dump made by a PPSSPP build with a rendering bug carries that bug's leftovers
  into VRAM, so a dump can differ from the game itself.
- Dumps older than version 4 don't store the game ID; their names carry it where it could be found.
- Some GE state outlives a frame on real hardware (how a zero normal is lit depends on the last Bezier patch
  drawn, even by an earlier program); the PSP replayer resets what is known, so the references start from
  the same state as PPSSPP.
- `renames.json` maps the original names, which earlier notes and scripts may still use.
