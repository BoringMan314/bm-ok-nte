"""Convert catalog zh_TW values from simplified to traditional (OpenCC s2twp)."""

from __future__ import annotations



import json

import re

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"

CJK = re.compile(r"[\u4e00-\u9fff]")





def main() -> int:

    from opencc import OpenCC



    cc = OpenCC("s2twp")

    catalog: dict[str, dict[str, str]] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    updated = 0

    for msgid, locs in catalog.items():

        cn = locs.get("zh_CN", msgid)

        tw = locs.get("zh_TW", cn)

        src = tw or cn or msgid

        if not CJK.search(src):

            continue

        if tw != cn:

            continue

        converted = cc.convert(src)

        if converted != tw:

            locs["zh_TW"] = converted

            updated += 1

    CATALOG_PATH.write_text(

        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",

        encoding="utf-8",

    )

    print(f"zh_TW catalog: converted {updated} entries (s2twp)")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

