import zipfile, glob, json, re, sys, gzip, base64
try:
    import tomllib
except Exception:
    tomllib = None
rows = []
names = {}
for j in sorted(glob.glob(sys.argv[1] + '/*.jar')):
    try:
        z = zipfile.ZipFile(j)
    except Exception:
        continue
    nl = z.namelist()
    if 'META-INF/neoforge.mods.toml' in nl:
        t = z.read('META-INF/neoforge.mods.toml').decode('utf-8', 'ignore')
        for m in re.finditer(r'modId\s*=\s*"([^"]+)"[\s\S]*?displayName\s*=\s*"([^"]+)"', t):
            names.setdefault(m.group(1), m.group(2))
    for n in nl:
        m = re.match(r'data/([^/]+)/advancements?/(.+)\.json$', n)
        if not m or '/recipes/' in '/' + m.group(2) + '/' or m.group(2).startswith('recipes'):
            continue
        ns, path = m.group(1), m.group(2)
        try:
            a = json.loads(z.read(n).decode('utf-8', 'ignore'))
        except Exception:
            continue
        d = a.get('display')
        if not d or d.get('hidden'):
            continue
        ic = d.get('icon') or {}
        icon = ic.get('id') or ic.get('item') or 'minecraft:book'
        def key(v):
            if isinstance(v, dict):
                return 'T:' + v['translate'] if 'translate' in v else 'L:' + str(v.get('text', ''))
            if isinstance(v, list) and v:
                return key(v[0])
            return 'L:' + str(v)
        rows.append([f'{ns}:{path}', a.get('parent', ''), icon, d.get('frame', 'task'),
                     key(d.get('title', '')), key(d.get('description', ''))])
out = {'names': names, 'adv': rows}
sys.stdout.write(base64.b64encode(gzip.compress(json.dumps(out, separators=(',', ':')).encode(), 9)).decode())
