# Known differences

Dumps where PPSSPP's hardware renderers (Vulkan, OpenGL) still differ from the PSP references for a known
reason that's been left for later, grouped by cause. The software renderer matches the PSP on nearly all
of them. Numbers are differing pixels from `tools/compare.py` at the time of writing.

## 16-bit framebuffer precision

The PSP stores 5551, 565 and 4444 framebuffers with 5 (or 6, or 4) bits per channel and truncates every
blend result to that. The hardware renderers keep 8 bits, so small increments that the PSP loses survive.
A blend adds in 8 bits and then truncates: the stored value goes up a level only when the expanded
destination's low bits plus the increment reach the next level, so how much is lost depends on how bright
the destination already is. This shows up mostly as frames that come out a little too bright, worst with
many additive passes.

Not emulated on purpose for now. Options looked at (2026-10-09):

- Flooring the source term to whole levels in the shader: exact on dark destinations (Fate/Extra's glow
  88k -> 0.8k px) but too dark on bright ones (Gundam Assault Survive 7k -> 46k).
- Exact blending with the destination read (framebuffer copy or fetch), limited to through-mode draws,
  which are mostly full screen composites: would cover Peace Walker and Shin Sangoku Musou, not Fate/Extra.

| Dumps | Where |
|---|---|
| 11774 ULES01372 Metal Gear Solid Peace Walker (12 dumps, 15-20k) | Through-mode FIXA adds of 5 to green and blue in the 5551 frame: the PSP averages +3.6 and +1.3 |
| 15716 ULJM05637 Shin Sangoku Musou Multi Raid 2 (109k) | Bloom composite, four additive through-mode passes into the 5551 frame |
| 6273, 11397, 15015 ULUS10576 Fate/Extra (1-91k) | Glow built from 12 additive passes into a 5551 buffer |
| 13950, 17033 God Eater Burst / God Eater 2 | Bloom feeds back on itself; the scene is about 4 levels bright before it |
| 6963 UCES01242_0001, 15071 UCUS98649 SOCOM | Faint fog layers and a CLUT8 glow on a 5551 frame |
| 6371, 16131 NPUG80221 Super Stardust (21-24k) | Purple cast after the 2x bloom composite, from the 565 copy of the scene |
| 16131 UCUS98668 Resistance: Retribution (44-66k), 15923 UCES01184 (51k), 16131 UCUS98641 and 10415 UCES00710 Syphon Filter: Logan's Shadow (1-54k) | Bright pass in a 128x128 5551 buffer: a reverse-subtract threshold that the PSP's truncation takes to 0, then MAX and blur passes, then the high bytes read as CLUT8. Shows as a glowing rectangle over fires |
| 10421 Harvest Moon, 12964 Ys Seven, 15896 Kurohyou 2, 13782 NPJH50625 Nayuta | Same mechanism, seen in the flooring experiment |

## Filtering precision

The GE filters with 4-bit weights and truncates twice. GPUs filter more finely.

| Dumps | Where |
|---|---|
| 9572 ULUS10345 Star Wars The Force Unleashed (28k) | A CLUT8 overlay that the PSP filters bilinearly; the shader depal path samples nearest |

## Depth precision

| Dumps | Where |
|---|---|
| 8481 UCES00786_0003 ATV Offroad Fury Pro, OpenGL only (+1k) | OpenGL without clip control stores depth as 0.5..1, losing a bit near 0 (float depth on Apple) |

## Dumps not to trust

| Dumps | Why |
|---|---|
| 19318 ULUS10285 Silent Hill Origins | Depth buffer garbage on the left side |
| 18879 NPJH50443 FF Type-0 | Looks suspicious |
| 8390 NPJH50333 Kurohyou 2 | Looks suspicious, might be right |
| 11100, 15923 (removed), 21641 (removed) Burnout Dominator | Old captures with state the game doesn't have; use ULES00703_0004 |
