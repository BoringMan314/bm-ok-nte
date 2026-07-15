"""Sync translation assets from i18n branch onto main (upstream -> i18n -> main)."""

from __future__ import annotations



import subprocess

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

I18N_BRANCH = "i18n"

PATHS = [

    "i18n/zh_TW/LC_MESSAGES/ok.po",

    "i18n/zh_CN/LC_MESSAGES/ok.po",

    "i18n/en_US/LC_MESSAGES/ok.po",

    "i18n/ja_JP/LC_MESSAGES/ok.po",

    "i18n/ko_KR/LC_MESSAGES/ok.po",

    "i18n/es_ES/LC_MESSAGES/ok.po",

    "i18n/pt_BR/LC_MESSAGES/ok.po",

    "tools/compile_mo.py",

]





def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:

    print("+", " ".join(cmd))

    return subprocess.run(cmd, cwd=ROOT, check=check, text=True, capture_output=True)





def main() -> int:

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

    if branch != "main":

        print(f"expected branch main, got {branch}", file=sys.stderr)

        return 1



    run(["git", "fetch", "upstream"])

    run(["git", "fetch", "origin", I18N_BRANCH])



    if run(["git", "rev-parse", "--verify", f"refs/heads/{I18N_BRANCH}"], check=False).returncode:

        print(f"missing local branch {I18N_BRANCH}", file=sys.stderr)

        return 1



    behind = run(

        ["git", "rev-list", "--count", f"refs/heads/{I18N_BRANCH}..upstream/main"],

        check=False,

    ).stdout.strip()

    if behind != "0":

        print(f"warning: i18n branch is {behind} commit(s) behind upstream/main")



    run(["git", "checkout", I18N_BRANCH, "--", *PATHS])

    run([sys.executable, str(ROOT / "tools" / "sync_i18n.py")])

    run([sys.executable, str(ROOT / "tools" / "compile_mo.py")])

    print("done: main i18n synced from i18n branch")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

