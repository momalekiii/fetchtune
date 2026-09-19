# Releasing FetchTune v0.3.2

Complete tree (every core module in the wheel). Do **not** overlay a
partial zip — that is how 0.3.0 lost `models.py` / `spotify.py`.

PyPI already has 0.3.0 and 0.3.1. This release **must** be `0.3.2`.

## GitHub

```bash
cd /path/to/fetchtune
# unzip fetchtune-v0.3.2-FULL.zip here (overwrite)

ls src/fetchtune/models.py \
   src/fetchtune/resolver.py \
   src/fetchtune/exceptions.py \
   src/fetchtune/providers/spotify.py \
   src/fetchtune/providers/base.py

git add -A
git status
git commit -m "release: v0.3.2"
git push origin main
git tag v0.3.2
git push origin v0.3.2
```

## PyPI

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U build twine
rm -rf dist build
python -m build
twine check dist/*

python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob('dist/*.whl')[0]); print('\n'.join(sorted(z.namelist())))"
# MUST include: models.py resolver.py exceptions.py providers/spotify.py

twine upload dist/*
```

`~/.pypirc` username is `__token__` (not your PyPI name).

A 400 "File already exists" means that version is already on PyPI —
do not re-upload; bump the version instead.

## After upload

```bash
pip uninstall -y fetchtune
pip install -U 'fetchtune[downloader]==0.3.2'
fetchtune --version    # fetchtune 0.3.2
```
