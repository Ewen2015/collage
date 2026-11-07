# Installable skill package

`collage.skill` is a ZIP of the complete skill, with `SKILL.md` at the archive
root. The repository itself is the skill: there is no nested `skills/` folder.
The bundle contains the workflow, five reference documents, five scripts,
`requirements.txt`, `install.sh`, `install.ps1` and an `assets/` folder. A lone
`SKILL.md` is not enough — the scripts are what cut source images by content
and render the artwork.

## Install methods

The standard open agent-skills CLI (Node.js 22.20+) installs the whole folder:

```bash
npx skills add Ewen2015/collage -g -y
npx skills add https://github.com/Ewen2015/collage
npx skills add https://github.com/Ewen2015/collage/raw/main/dist/collage.skill
```

Or unzip manually into any agent's skills directory:

```bash
mkdir -p AGENT_SKILLS/collage
unzip -o collage.skill -d AGENT_SKILLS/collage
cd AGENT_SKILLS/collage && bash install.sh
```

On Windows use `powershell -ExecutionPolicy Bypass -File install.ps1`.

`install.sh` / `install.ps1` install Pillow and NumPy and run
`scripts/check_setup.py`, which verifies Python 3.9+, all bundled files,
font resolution, a renderer smoke test and a content-cutout smoke test. The 16
built-in presets and all local content-aware cuts work offline; only Wikimedia
Commons source-image searching needs network access.

## Rebuild after editing the skill

From the repository root:

```bash
python3 - <<'PY'
import zipfile, os
out = 'dist/collage.skill'
include = {'SKILL.md', 'requirements.txt', 'install.sh', 'install.ps1',
           'references', 'scripts', 'assets'}
files = []
for entry in include:
    if os.path.isfile(entry):
        files.append((entry, entry))
        continue
    for dp, dn, fns in os.walk(entry):
        dn[:] = [d for d in dn if d != '__pycache__']
        for fn in sorted(fns):
            if fn.endswith(('.pyc', '.DS_Store')):
                continue
            p = os.path.join(dp, fn)
            files.append((p, os.path.relpath(p, '.')))
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p, arc in sorted(files):
        z.write(p, arc)
print(out, os.path.getsize(out), 'bytes')
PY
```

The `.skill` package is checked in so that
GitHub Pages and anyone installing by URL get the same bundle. Rebuild it
whenever a file inside the skill changes.
