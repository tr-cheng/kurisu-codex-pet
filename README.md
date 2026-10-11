# Kurisu (beige jacket) · Codex desktop pet build scripts

Scripts that turn the Makise Kurisu visual-novel sprites from the
[LivePNG](https://github.com/FrancescoCaracciolo/LivePNG) examples into a local
[Codex](https://openai.com/codex) desktop pet: a v1 sprite atlas of 8 × 9 cells, each 192 × 208.

**This repository contains no artwork.**
- The LivePNG repo credits the sprites to the *Steins;Gate* visual novel. They are official game art,
  with no licence stated, and their copyright belongs to the game's rights holders.
- Use the scripts only to build a pet for your own machine, and do not redistribute the results.
- This is an unofficial fan project, not affiliated with the rights holders, LivePNG or OpenAI.

## Build

Requirements: Python 3.11+ with Pillow and numpy.

```powershell
python -I tools/fetch_livepng_casual.py .   # download the 68 'casual' sprites at a pinned commit and
                                            # verify each file against the git tree (personal use)
python -I tools/build_casual.py .           # write final/spritesheet.webp (1536 x 1872, v1)
python -I tools/install_pet.py .            # copy the pet to %USERPROFILE%\.codex\pets\kurisu-beige-jacket\
```

Then select "牧濑红莉栖 · 米色外套" in Codex → Settings → Pets. On a 200 % display, set the pet
size to 192 for an exact 2× scale.

## What the pet does

| Codex state | Pose | Motion |
| --- | --- | --- |
| idle | arms down ↔ arms crossed | breathing, one wink per loop |
| running-right / running-left (dragged) | arms down, annoyed | bounce + 3° lean toward the drag |
| waving (greeting) | hand on chest (mirrored) | closed-eye smile, nod |
| jumping | arms down | crouch → lift → peak → settle |
| failed | arms crossed, angry | complaining mouth, slight sag |
| waiting | hand on chest (mirrored), blush | breathing |
| running (work) | arms crossed, annoyed | muttering mouth |
| review | arms crossed, neutral | small nod |

Design notes:
- Half body down to the thighs, with feathered canvas cuts and a bottom fade.
- The hand-on-chest pose is mirrored and aligned on the face, so every pose faces the same way.
- It is a v1 pet, so it does not follow the cursor: the sprites have no head-turn art.

## Licence

The code and documentation in this repository are released under the MIT licence (see `LICENSE`).
The licence does not cover the sprites or anything generated from them, which are not included.
