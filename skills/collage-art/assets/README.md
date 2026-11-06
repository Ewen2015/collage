# Local source assets

Drop user-supplied images here when working offline or with the user's own
photographs. Reference them by path in a recipe's `source` field, and record
their origin in the job's `SOURCES.json` with `"license": "user-provided"`.

Autonomous sourcing (`scripts/source_assets.py`) writes to the job's assets
directory instead; this folder is for checked-in assets only.
