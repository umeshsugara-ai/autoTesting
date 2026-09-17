cd /d/autoTesting/.work/wt-at229
git status --porcelain --ignored --untracked-files=all > ../at229-before.txt
uv run pytest -p no:cacheprovider > ../at229-suite.log 2>&1
git status --porcelain --ignored --untracked-files=all > ../at229-after.txt
echo DONE > ../at229-done.txt
