#!/usr/bin/env python3
"""Rebuild index.toml and the pack.toml index hash the way `packwiz refresh` does.

Handy when packwiz isn't installed locally. CI still runs the real `packwiz refresh`
and fails if this produced anything different.
Usage: python3 tools/reindex.py [new-version]
"""
import fnmatch, hashlib, os, re, sys

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
ign = [l.strip() for l in open('.packwizignore') if l.strip() and not l.startswith('#')]

def ignored(p):
    for pat in ign:
        if pat.endswith('/') and (p + '/').startswith(pat):
            return True
        if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(os.path.basename(p), pat):
            return True
    return False

files = []
for root, dirs, names in os.walk('.'):
    dirs[:] = [d for d in dirs if d != '.git']
    for n in names:
        p = os.path.relpath(os.path.join(root, n), '.')
        if p in ('pack.toml', 'index.toml', '.packwizignore') or ignored(p):
            continue
        files.append(p)
files.sort()
out = 'hash-format = "sha256"\n\n'
for p in files:
    out += f'[[files]]\nfile = "{p}"\nhash = "{sha(p)}"\n'
    if p.endswith('.pw.toml'):
        out += 'metafile = true\n'
    out += '\n'
open('index.toml', 'w').write(out.rstrip('\n') + '\n')
pk = open('pack.toml').read()
if len(sys.argv) > 1:
    pk = re.sub(r'^version = "[^"]+"', f'version = "{sys.argv[1]}"', pk, flags=re.M)
pk = re.sub(r'(\[index\]\nfile = "index.toml"\nhash-format = "sha256"\nhash = ")[0-9a-f]+(")',
            r'\g<1>' + sha('index.toml') + r'\2', pk)
open('pack.toml', 'w').write(pk)
print(len(files), 'files indexed')
