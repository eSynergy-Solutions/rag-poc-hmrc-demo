# 🔧 Auto-generate requirements from your code

## Prerequisite

pip install pipreqs

## PowerShell
# 1) Base (runtime only: app code)
pipreqs .\app `
  --force `
  --ignore tests,infrastructure,docs,scripts `
  --savepath .\requirements\base.txt

# 2) Dev (runtime + tests + scripts)
pipreqs . `
  --force `
  --ignore infrastructure,docs,requirements,.github `
  --savepath .\requirements\dev.txt

# 3) Prod (runtime only + entry-point imports)
pipreqs .\app `
  --force `
  --ignore tests,infrastructure,docs,scripts `
  --savepath .\requirements\prod.txt

## Bash
# 1) Base (runtime only: app code)
pipreqs ./app \
  --force \
  --ignore tests,infrastructure,docs,scripts \
  --savepath requirements/base.txt

# 2) Dev (app + tests + scripts)
pipreqs ./app ./scripts \
  --force \
  --ignore infrastructure,docs \
  --savepath requirements/dev.txt

# 3) Prod (runtime only + entry-point imports)
pipreqs ./app \
  --force \
  --ignore tests,infrastructure,docs,scripts \
  --savepath requirements/prod.txt