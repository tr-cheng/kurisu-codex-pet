"""Step 1: fetch the LivePNG 'kurisu / casual' sprite set at a pinned commit and verify it.

Source (download approved by the user on 2026-10-11):
  https://github.com/FrancescoCaracciolo/LivePNG
  path examples/models/kurisu/assets/casual/**  (68 PNG, about 46 MB at approval time)
  The repo's examples/README.md credits the Kurisu model to the Steins;Gate visual novel and
  gives no licence for the images (the repo's GPL-3.0 covers its code). Personal local use only;
  do not redistribute, upload or publish these files or frames derived from them.

Integrity (per file, against the git tree of the pinned commit):
  len(data) == tree 'size'  and  sha1(b"blob <size>\\0" + data) == tree 'sha'  (the git object id)
  plus the 8-byte PNG signature. SHA-256 is recorded for later checks.
Nothing downloaded is executed or decoded here. The script refuses a non-empty destination and
stops BEFORE downloading if the file count or total size differs from what the user approved.

Usage: python -I fetch_livepng_casual.py <project_root> [commit_sha]   (default: the pinned commit)
Writes: <root>/sources/livepng_casual/<expression>/<variant>/<file>.png
        <root>/sources/livepng_casual_manifest.json
"""
import datetime, hashlib, json, pathlib, sys, urllib.parse, urllib.request

OWNER, REPO = 'FrancescoCaracciolo', 'LivePNG'
PREFIX = 'examples/models/kurisu/assets/casual/'
APPROVED_COUNT, APPROVED_BYTES = 68, 46_320_681      # from the tree listing shown to the user
root = pathlib.Path(sys.argv[1]).resolve()
dest = root / 'sources' / 'livepng_casual'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'kurisu-pet-fetch/1.0', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


PINNED = 'b9df5f821ebfd1d58ff9a42399924e6f058908b4'   # LivePNG commit of 2024-10-13 used to build the pet
commit = sys.argv[2] if len(sys.argv) > 2 else PINNED
cinfo = json.loads(get(f'https://api.github.com/repos/{OWNER}/{REPO}/commits/{commit}'))
tree = json.loads(get(f'https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{commit}?recursive=1'))
if tree.get('truncated'):
    raise SystemExit('git tree listing is truncated; stop')
entries = sorted((e for e in tree['tree'] if e['type'] == 'blob' and e['path'].startswith(PREFIX)
                  and e['path'].lower().endswith('.png')), key=lambda e: e['path'])
total = sum(e['size'] for e in entries)
if len(entries) != APPROVED_COUNT or abs(total - APPROVED_BYTES) > APPROVED_BYTES * 0.01:
    raise SystemExit(f'listing differs from the approved set: {len(entries)} files, {total} bytes; nothing downloaded')
if dest.exists() and any(dest.iterdir()):
    raise SystemExit(f'destination not empty: {dest}')

records = []
for e in entries:
    rel = e['path'][len(PREFIX):]
    parts = rel.split('/')
    if any(p in ('', '.', '..') or '\\' in p or ':' in p for p in parts):
        raise SystemExit(f'unsafe path in listing: {rel}')
    url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit}/' + urllib.parse.quote(e['path'])
    data = get(url)
    git_sha = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
    if len(data) != e['size'] or git_sha != e['sha'] or data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit(f'verification failed for {rel}: size {len(data)}/{e["size"]}, sha1 {git_sha}/{e["sha"]}')
    out = dest.joinpath(*parts)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    records.append({'path': rel, 'bytes': len(data), 'git_blob_sha1': git_sha,
                    'sha256': hashlib.sha256(data).hexdigest(), 'url': url})

manifest = {
    'source_repo': f'https://github.com/{OWNER}/{REPO}', 'path': PREFIX, 'commit': commit,
    'commit_date': cinfo['commit']['committer']['date'], 'commit_message': cinfo['commit']['message'][:200],
    'credit_in_repo': 'examples/README.md credits the kurisu model to the Steins;Gate visual novel',
    'image_licence': 'none stated (repo GPL-3.0 covers code only); personal local use only, no redistribution',
    'downloaded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'verification': 'size + git blob sha1 against the pinned git tree + PNG signature',
    'file_count': len(records), 'total_bytes': sum(r['bytes'] for r in records), 'files': records,
}
(root / 'sources' / 'livepng_casual_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: manifest[k] for k in ('commit', 'commit_date', 'file_count', 'total_bytes')}, ensure_ascii=False))
