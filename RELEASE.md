# Releasing FetchTune v0.3.3

Unzip `fetchtune-v0.3.3-FULL.zip` on top of the repo. Full tree.

## GitHub

```bash
cd /path/to/fetchtune
git add -A
git commit -m "release: v0.3.3"
git push origin main
git tag v0.3.3
git push origin v0.3.3
```

## PyPI

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U build twine
rm -rf dist build
python -m build
twine check dist/*
python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob('dist/*.whl')[0]); print('\\n'.join(sorted(z.namelist())))"
twine upload dist/*
```

Do not re-upload 0.3.2. Username in `~/.pypirc` is `__token__`.
