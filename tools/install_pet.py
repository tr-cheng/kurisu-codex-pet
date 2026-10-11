"""Install (copy) the beige-jacket pet into the local Codex pets folder - user-requested 2026-10-11.

Writes <root>/deliverables/<PET_ID>/{pet.json, spritesheet.webp} (staged copy kept with the
project), then copies that folder to %USERPROFILE%\\.codex\\pets\\<PET_ID>\\. Refuses to overwrite
an existing folder. Does NOT change which pet is selected in Codex.
Verification mirrors the Codex 26.1007.2314.0 loader (app-initial/src JS): pet.json parses with
optional id/displayName, nullable description, spriteVersionNumber in {1,2} (default 1),
spritesheetPath resolved inside the pet folder; image width 1536 and height 1872 for v1.
Usage: python -I install_pet.py <project_root>
"""
import hashlib, json, os, pathlib, shutil, struct, sys

PET_ID = 'kurisu-beige-jacket'
root = pathlib.Path(sys.argv[1]).resolve()
atlas = root / 'final' / 'spritesheet.webp'
manifest = {'id': PET_ID, 'displayName': '牧濑红莉栖 · 米色外套',
            'description': '红莉栖米色外套半身立绘（视觉小说原画），个人本机使用。',
            'spriteVersionNumber': 1, 'spritesheetPath': 'spritesheet.webp'}


def webp_size(b):
    if b[:4] != b'RIFF' or b[8:12] != b'WEBP':
        raise SystemExit('not a WebP file')
    if b[12:16] == b'VP8L':                       # lossless: 14-bit width-1, height-1 after signature byte 0x2f
        bits = struct.unpack('<I', b[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if b[12:16] == b'VP8X':
        return int.from_bytes(b[24:27], 'little') + 1, int.from_bytes(b[27:30], 'little') + 1
    raise SystemExit('unexpected WebP chunk ' + b[12:16].decode('latin1'))


def verify(folder):
    m = json.loads((folder / 'pet.json').read_text(encoding='utf-8'))
    assert isinstance(m.get('displayName', ''), str) and m.get('spriteVersionNumber', 1) in (1, 2)
    sheet = (folder / m.get('spritesheetPath', 'spritesheet.webp')).resolve()
    assert sheet.parent == folder.resolve(), 'spritesheet path escapes the pet folder'
    data = sheet.read_bytes()
    w, h = webp_size(data)
    want_h = 1872 if m.get('spriteVersionNumber', 1) == 1 else 2288
    assert (w, h) == (1536, want_h), f'dimensions {w}x{h}, loader needs 1536x{want_h}'
    return {'pet_json': m, 'sheet_sha256': hashlib.sha256(data).hexdigest(), 'size': [w, h]}


stage = root / 'deliverables' / PET_ID
stage.mkdir(parents=True, exist_ok=True)
(stage / 'pet.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(atlas, stage / 'spritesheet.webp')
staged = verify(stage)

pets = pathlib.Path(os.environ['USERPROFILE']) / '.codex' / 'pets'
target = pets / PET_ID
if target.exists():
    raise SystemExit(f'{target} already exists; not overwriting')
if not pets.is_dir():
    raise SystemExit(f'{pets} does not exist; not creating it')
shutil.copytree(stage, target)
installed = verify(target)
assert installed['sheet_sha256'] == staged['sheet_sha256'] == hashlib.sha256(atlas.read_bytes()).hexdigest()
print(json.dumps({'installed_to': str(target), **installed}, ensure_ascii=False, indent=1))
