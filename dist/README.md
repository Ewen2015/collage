# Installable skill package

`collage-art.skill` is a ZIP of the complete `skills/collage-art/` folder, with
`SKILL.md` at the archive root. It contains the workflow, five reference
documents, four scripts, `requirements.txt`, `install.sh`, `install.ps1` and
an `assets/` folder. A lone `SKILL.md` is not enough — the scripts are what
render the artwork.

## Install methods

The standard open agent-skills CLI (Node.js 22.20+) installs the whole folder:

```bash
npx skills add Ewen2015/ewen-collage --skill collage-art -g -y
npx skills add https://github.com/Ewen2015/ewen-collage/tree/main/skills/collage-art
npx skills add https://github.com/Ewen2015/ewen-collage/raw/main/dist/collage-art.skill
```

Or unzip manually into any agent's skills directory:

```bash
mkdir -p AGENT_SKILLS/collage-art
unzip -o collage-art.skill -d AGENT_SKILLS/collage-art
cd AGENT_SKILLS/collage-art && bash install.sh
```

On Windows use `powershell -ExecutionPolicy Bypass -File install.ps1`.

`install.sh` / `install.ps1` install Pillow and NumPy and run
`scripts/check_setup.py`, which verifies Python 3.9+, all bundled files,
font resolution and a renderer smoke test. The 16 built-in presets work
offline; only Wikimedia Commons source-image searching needs network access.

## Rebuild after editing the skill

From the repository root:

```bash
python3 - <<'PY'
import zipfile, os
root = 'skills/collage-art'
out = 'dist/collage-art.skill'
files = []
for dp, dn, fns in os.walk(root):
    dn[:] = [d for d in dn if d != '__pycache__']
    for fn in sorted(fns):
        if fn.endswith(('.pyc', '.DS_Store')):
            continue
        p = os.path.join(dp, fn)
        files.append((p, os.path.relpath(p, root)))
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p, arc in sorted(files):
        z.write(p, arc)
print(out, os.path.getsize(out), 'bytes')
PY
```

The `.skill` package is deterministic in content and is checked in so that
GitHub Pages and anyone installing by URL get the same bundle. Rebuild it
whenever a file inside `skills/collage-art/` changes.
