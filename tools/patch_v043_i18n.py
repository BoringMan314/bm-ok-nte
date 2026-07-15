"""Complete v0.0.43 DailyTask / AnomalyTask po entries for all locales."""
from __future__ import annotations

import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]

PATCHES: dict[str, dict[str, str]] = {
    "一咖舍任务": {
        "en_US": "Cafe Tasks",
        "zh_CN": "一咖舍任务",
        "zh_TW": "一咖舍任務",
        "ja_JP": "カフェタスク",
        "ko_KR": "카페 작업",
        "es_ES": "Tareas del café",
        "pt_BR": "Tarefas do café",
    },
    "选择日常任务中的一咖舍处理方式": {
        "en_US": "Choose how to handle Cafe daily tasks",
        "zh_CN": "选择日常任务中的一咖舍处理方式",
        "zh_TW": "選擇日常任務中的一咖舍處理方式",
        "ja_JP": "デイリータスクでのカフェ処理方法を選択",
        "ko_KR": "일일 작업에서 카페 처리 방식을 선택",
        "es_ES": "Elige cómo gestionar las tareas diarias del café",
        "pt_BR": "Escolha como lidar com as tarefas diárias do café",
    },
    "不执行": {
        "en_US": "Do not execute",
        "zh_CN": "不执行",
        "zh_TW": "不執行",
        "ja_JP": "実行しない",
        "ko_KR": "실행하지 않음",
        "es_ES": "No ejecutar",
        "pt_BR": "Não executar",
    },
    "第 {} 个项目": {
        "en_US": "Item #{}",
        "zh_CN": "第 {} 个项目",
        "zh_TW": "第 {} 個專案",
        "ja_JP": "第 {} 項目",
        "ko_KR": "제 {}번 항목",
        "es_ES": "Elemento n.º {}",
        "pt_BR": "Item n.º {}",
    },
    "运行一咖舍自动化": {
        "en_US": "Run cafe automation",
        "zh_CN": "运行一咖舍自动化",
        "zh_TW": "執行一咖舍自動化",
        "ja_JP": "カフェ自動化を実行",
        "ko_KR": "카페 자동화 실행",
        "es_ES": "Ejecutar automatización del café",
        "pt_BR": "Executar automação do café",
    },
}


def patch_locale(locale: str) -> int:
    path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
    po = polib.pofile(str(path))
    by_id = {e.msgid: e for e in po if e.msgid and not e.obsolete}
    changed = 0
    for msgid, translations in PATCHES.items():
        msgstr = translations[locale]
        if msgid in by_id:
            entry = by_id[msgid]
            if entry.msgstr != msgstr:
                entry.msgstr = msgstr
                changed += 1
        else:
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            changed += 1
    po.wrapwidth = 999999
    po.save(str(path))
    print(f"{locale}: {changed} update(s)")
    return changed


def main() -> int:
    total = sum(patch_locale(loc) for loc in LOCALES)
    print(f"total updates: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
