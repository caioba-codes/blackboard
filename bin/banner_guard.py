#!/usr/bin/env python3
"""Global banner ownership: same file bytes, source URL, or photo credit cannot be reused."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get('BLACKBOARD_HOME', Path.home() / '.cache/blackboard'))

def frontmatter(path):
    text = Path(path).read_text()
    match = re.match(r'^---\s*\n(.*?)\n---(?:\n|$)', text, re.S)
    return dict((k, v.strip().strip('\"\'')) for k, v in re.findall(r'^([\w-]+):[ \t]*(.*)$', match[1] if match else '', re.M))

def lessons(extra=None):
    spec = importlib.util.spec_from_file_location('banner_bridge', ROOT / 'board/bridge.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    dirs = {Path(w['path']).resolve() / 'lessons' for w in bridge.workspaces().values()}
    if extra: dirs.add(Path(extra).resolve().parent)
    return sorted({p.resolve() for d in dirs for p in d.glob('[0-9][0-9][0-9][0-9]-*.md')})

def credit_key(credit):
    return re.sub(r';?\s*reused from lesson.*$', '', credit).strip().rstrip(')').casefold()

def keys(path, fm=None):
    fm = fm or frontmatter(path)
    photo = fm.get('photo', '')
    if not photo: return set()
    result = set()
    if photo.startswith(('https://', 'http://')): result.add('url:' + photo)
    else:
        local = Path(path).parent / photo
        if local.is_file(): result.add('sha:' + hashlib.sha256(local.read_bytes()).hexdigest())
    if fm.get('photo_source'): result.add('url:' + fm['photo_source'])
    if fm.get('credit'): result.add('credit:' + credit_key(fm['credit']))
    return result

@contextmanager
def locked():
    HOME.mkdir(parents=True, exist_ok=True)
    with (HOME / 'banner-ownership.lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield

def conflicts(owner, candidate, include_reservations=True):
    owner = str(Path(owner).resolve())
    for p in lessons(owner):
        if str(p) != owner and candidate & keys(p): return str(p)
    if include_reservations:
        try: reservations = json.loads((HOME / 'banner-reservations.json').read_text())
        except FileNotFoundError: reservations = {}
        for p, entry in reservations.items():
            # Keep only real owners: removed lessons do not reserve banners forever.
            if p != owner and Path(p).is_file() and candidate.intersection(entry): return p
    return None

def claim(owner, data, source, credit, out, lid):
    """Validate and reserve under one process-wide lock, then atomically save a unique asset."""
    digest = hashlib.sha256(data).hexdigest() if data is not None else None
    candidate = {'url:' + source, 'credit:' + credit_key(credit)}
    if digest: candidate.add('sha:' + digest)
    with locked():
        if conflicts(owner, candidate): return None
        registry = HOME / 'banner-reservations.json'
        try: reservations = json.loads(registry.read_text())
        except FileNotFoundError: reservations = {}
        if data is not None:
            name = f'{lid}-{digest[:16]}.jpg'
            dest = Path(out) / name
            with tempfile.NamedTemporaryFile(dir=out, delete=False) as tmp:
                tmp.write(data); temporary = tmp.name
            os.replace(temporary, dest)
            photo = 'assets/' + name
        else: photo = source
        reservations[str(Path(owner).resolve())] = sorted(candidate)
        with tempfile.NamedTemporaryFile(mode='w', dir=HOME, delete=False) as tmp:
            json.dump(reservations, tmp, indent=2); temporary = tmp.name
        os.replace(temporary, registry)
        return photo

def audit():
    seen, errors = {}, []
    for p in lessons():
        fm = frontmatter(p)
        if fm.get('plain') == 'true': continue
        if not fm.get('photo'):
            errors.append(f'MISSING {p}'); continue
        if not fm['photo'].startswith(('http://', 'https://')) and not (p.parent / fm['photo']).is_file():
            errors.append(f'MISSING ASSET {p}'); continue
        for key in keys(p, fm):
            if key in seen:
                errors.append(f'DUPLICATE {p} == {seen[key]}'); break
        for key in keys(p, fm): seen.setdefault(key, p)
    return sorted(set(errors))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', type=Path)
    args = parser.parse_args()
    if args.lesson:
        fm = frontmatter(args.lesson)
        if fm.get('plain') == 'true' or not fm.get('photo'): raise SystemExit(0)
        with locked(): duplicate = conflicts(args.lesson, keys(args.lesson, fm), False)
        if duplicate:
            print(f'Duplicate banner: {args.lesson} shares a photo with {duplicate}. Reroll with bin/image.sh before rendering.', file=__import__('sys').stderr)
            raise SystemExit(1)
    else:
        errors = audit()
        print('\n'.join(errors) if errors else 'PASS: all lesson banners are present and unique')
        raise SystemExit(bool(errors))
