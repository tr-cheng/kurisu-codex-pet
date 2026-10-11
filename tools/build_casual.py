"""Build the v1 Codex pet atlas for Makise Kurisu (beige jacket) from the LivePNG 'casual' sprites.

Input : sources/livepng_casual/  (fetched by tools/fetch_livepng_casual.py; official Steins;Gate
        visual-novel art - personal local use only, never redistribute)
Output: final/spritesheet.webp   (1536x1872 = 8 cols x 9 rows of 192x208, lossless, transparent)

Codex v1 rows: idle 6, running-right 8, running-left 8, waving 4, jumping 5, failed 8, waiting 6,
running 6, review 6 frames; unused cells stay transparent. (Codex plays idle durations x6 and
other rows 3x before returning to idle.)
Design: half body down to the thighs, one fixed transform for every frame. Poses: ASA arms down,
ASB arms crossed, ASC hand on chest. ASA and ASB share an identical face; every ASC image is
mirrored left-right and translated so its face centre lands on the ASA/ASB face centre, so all
poses face the same way. Continuous rows are sampled at q = i/n (no repeated seam frame).
Frame pipeline: source -> (ASC: mirror) -> edge feathering of the canvas cuts -> Lanczos to 4x the
cell scale -> place on a 768x832 canvas at integer offsets (dy in cell px; lean = rotation about
the cell bottom centre in premultiplied RGBa) -> Lanczos to 192x208 -> bottom alpha fade -> RGB of
fully transparent pixels set to 0.
Usage: python -I build_casual.py <project_root>
"""
import math, pathlib, sys
import numpy as np
from PIL import Image, ImageOps

root = pathlib.Path(sys.argv[1]).resolve()
SRC = root / 'sources' / 'livepng_casual'
CW, CH, K, COLS = 192, 208, 4, 8                   # cell size, hi-res factor, atlas columns
SRC_W, SRC_H, HAIR_TOP = 686, 992, 24              # sprite canvas; first row of hair
SCALE = (CH - 14) / (SRC_H - HAIR_TOP)             # hair top at cell y=14, canvas bottom at cell bottom
FADE, CLEAR = 30, 2                                # bottom fade rows, then fully clear rows
FEATHER, ASA_CUT_TOP = 40, 773                     # source px; ASA is cut by the right edge from row 773
# Face centres (source px) = centre of the region where expressions differ within a pose:
# ASA/ASB box (251,152)-(441,314); ASC box (280,165)-(467,317), mirrored -> (219,165)-(406,317).
FACE_AB, FACE_C_MIRRORED = (346.0, 233.0), (312.5, 241.0)
SHIFT_C = (FACE_AB[0] - FACE_C_MIRRORED[0], FACE_AB[1] - FACE_C_MIRRORED[1])   # (+33.5, -8.0)
FILES = {('ASA', '01'): 'idle/4/CRS_ASA_400001{m}.png', ('ASA', '02'): 'blink/1/CRS_ASA_400002{m}.png',
         ('ASA', '04'): 'annoyed/4/CRS_ASA_400004{m}.png', ('ASA', '06'): 'happy/2/CRS_ASA_400006{m}.png',
         ('ASB', '01'): 'idle/3/CRS_ASB_400001{m}.png', ('ASB', '04'): 'annoyed/1/CRS_ASB_400004{m}.png',
         ('ASB', '07'): 'angry/1/CRS_ASB_400007{m}.png',
         ('ASC', '01'): 'idle/2/CRS_ASC_400001{m}.png', ('ASC', '02'): 'blush/0/CRS_ASC_400002{m}.png',
         ('ASC', '03'): 'happy/0/CRS_ASC_400003{m}.png'}     # expr 01 neutral, 02 wink/blush, 03/06 closed-eye smile ...
_cache = {}


def feather(im, pose):
    """Fade alpha toward the canvas cuts (moves with the sprite): bottom edge for every pose,
    right edge for ASA only, switched on over FEATHER rows above its first cut row."""
    a = np.array(im).astype(np.float32)
    h, w = a.shape[:2]
    smooth = lambda t: t * t * (3 - 2 * t)
    y = np.arange(h, dtype=np.float32)[:, None]; x = np.arange(w, dtype=np.float32)[None, :]
    f = smooth(np.clip((h - 1 - y) / FEATHER, 0, 1)) * np.ones((1, w), np.float32)
    if pose == 'ASA':
        wy = smooth(np.clip((y - (ASA_CUT_TOP - FEATHER)) / FEATHER, 0, 1))
        fx = smooth(np.clip((w - 1 - x) / FEATHER, 0, 1))
        f = f * (1 - wy * (1 - fx))
    a[:, :, 3] *= f
    return Image.fromarray(np.rint(a).astype(np.uint8))


def hires(pose, expr, mouth):
    key = (pose, expr, mouth)
    if key not in _cache:
        im = Image.open(SRC / FILES[(pose, expr)].format(m=mouth)).convert('RGBA')
        if pose == 'ASC':
            im = ImageOps.mirror(im)
        im = feather(im, pose)
        _cache[key] = im.resize((round(SRC_W * SCALE * K), round(SRC_H * SCALE * K)), Image.Resampling.LANCZOS)
    return _cache[key]


def frame(pose, expr, mouth, dy=0.0, lean=0.0):
    """One 192x208 cell. dy: cell px, + = down. lean: degrees, + = top toward screen right."""
    sx, sy = SHIFT_C if pose == 'ASC' else (0.0, 0.0)
    left = round((CW / 2 - SRC_W / 2 * SCALE + sx * SCALE) * K)
    top = round((14 - HAIR_TOP * SCALE + sy * SCALE + dy) * K)
    canvas = Image.new('RGBa', (CW * K, CH * K), (0, 0, 0, 0))
    canvas.paste(hires(pose, expr, mouth).convert('RGBa'), (left, top))
    if lean:
        canvas = canvas.rotate(-lean, resample=Image.Resampling.BICUBIC, center=(CW * K / 2, CH * K))
    cell = canvas.convert('RGBA').resize((CW, CH), Image.Resampling.LANCZOS)
    a = np.array(cell).astype(np.float32)
    end = CH - CLEAR; ramp = np.ones(CH, np.float32)
    ramp[end - FADE:end] = (end - np.arange(end - FADE, end)) / (FADE + 1); ramp[end:] = 0
    a[:, :, 3] *= ramp[:, None]
    a = np.rint(a).astype(np.uint8); a[a[:, :, 3] == 0, :3] = 0
    return Image.fromarray(a)


breath = lambda q: -0.5 * (1 - math.cos(2 * math.pi * q))          # 0 .. -1 px (up)
dip = lambda q, amp: amp * 0.5 * (1 - math.cos(2 * math.pi * q))    # 0 .. +amp px (down)
lean = lambda i: 3 + 0.5 * math.sin(2 * math.pi * i / 8)            # degrees, toward the drag
MOUTH4, BOUNCE4 = ['00', '01', '02', '01'], [0, -2, -3, -1]
ROWS = [  # (state, [(pose, expression, mouth, dy, lean), ...]) in Codex row order
    ('idle', [('ASA', '02' if i == 2 else '01', '00', breath(i / 6)) if i < 3 else ('ASB', '01', '00', breath(i / 6)) for i in range(6)]),
    ('running-right', [('ASA', '04', MOUTH4[i % 4], BOUNCE4[i % 4], lean(i)) for i in range(8)]),
    ('running-left', [('ASA', '04', MOUTH4[i % 4], BOUNCE4[i % 4], -lean(i)) for i in range(8)]),
    ('waving', [('ASC', '01', '00', 0), ('ASC', '03', '02', 1.5), ('ASC', '03', '01', 0.75), ('ASC', '01', '00', 0)]),
    ('jumping', [('ASA', '01', '00', 1.5), ('ASA', '06', '01', -5), ('ASA', '06', '02', -9), ('ASA', '06', '01', -4), ('ASA', '01', '00', 0)]),
    ('failed', [('ASB', '07', ['00', '01', '02', '01', '00', '01', '00', '00'][i], dip(i / 8, 1.5)) for i in range(8)]),
    ('waiting', [('ASC', '02', ['00', '01', '01', '00', '00', '01'][i], breath(i / 6)) for i in range(6)]),
    ('running', [('ASB', '04', ['00', '01', '00', '01', '02', '01'][i], 0.5 * breath(i / 6)) for i in range(6)]),
    ('review', [('ASB', '01', ['00', '00', '00', '01', '00', '00'][i], dip(i / 6, 1.5)) for i in range(6)]),
]
assert [len(s) for _, s in ROWS] == [6, 8, 8, 4, 5, 8, 6, 6, 6]

atlas = Image.new('RGBA', (COLS * CW, len(ROWS) * CH), (0, 0, 0, 0))
for r, (state, spec) in enumerate(ROWS):
    for i, f in enumerate(spec):
        atlas.paste(frame(*f), (i * CW, r * CH))
a = np.array(atlas); a[a[:, :, 3] == 0, :3] = 0
(root / 'final').mkdir(exist_ok=True)
out = root / 'final' / 'spritesheet.webp'
Image.fromarray(a).save(out, format='WEBP', lossless=True, quality=100, method=6, exact=True)
print('wrote', out)
