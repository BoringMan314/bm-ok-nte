"""Merge runtime ok-script notification strings into i18n_catalog.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "tools" / "i18n_catalog.json"
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]

# From upstream ok/gui/i18n/*.ts (app context) + bm pt_BR / missing entries.
RUNTIME_ENTRIES = {
    "Game Exited": {
        "zh_TW": "遊戲已關閉",
        "zh_CN": "游戏已关闭",
        "en_US": "Game Exited",
        "ja_JP": "ゲームが終了しました",
        "ko_KR": "게임이 종료됨",
        "es_ES": "Juego cerrado",
        "pt_BR": "Jogo encerrado",
    },
    "Paused because game window is minimized or out of screen!": {
        "zh_TW": "已暫停：遊戲視窗已最小化或部分超出螢幕範圍！",
        "zh_CN": "已暂停：游戏窗口最小化或者部分在屏幕外！",
        "en_US": "Paused because game window is minimized or out of screen!",
        "ja_JP": "ゲームウィンドウが最小化または画面外のため一時停止しました！",
        "ko_KR": "게임 창이 최소화되었거나 화면 밖에 있어 일시 중지됨!",
        "es_ES": "¡Pausado porque la ventana del juego está minimizada o fuera de la pantalla!",
        "pt_BR": "Pausado porque a janela do jogo está minimizada ou fora da tela!",
    },
    "Auto exit because game exited": {
        "zh_TW": "因遊戲關閉而自動關閉",
        "zh_CN": "由于游戏退出, 自动关闭",
        "en_US": "Auto exit because game exited",
        "ja_JP": "ゲームが終了したため自動終了します",
        "ko_KR": "게임이 종료되어 자동 종료됨",
        "es_ES": "Cierre automático porque el juego se cerró",
        "pt_BR": "Fechamento automático porque o jogo foi encerrado",
    },
    "Paused because game exited": {
        "zh_TW": "已暫停：遊戲已關閉！",
        "zh_CN": "已暂停：游戏已经退出！",
        "en_US": "Paused because game exited",
        "ja_JP": "ゲームが終了したため一時停止しました",
        "ko_KR": "게임이 종료되어 일시 중지됨",
        "es_ES": "Pausado porque el juego se cerró",
        "pt_BR": "Pausado porque o jogo foi encerrado",
    },
    "Stopped": {
        "zh_TW": "已停止",
        "zh_CN": "已停止",
        "en_US": "Stopped",
        "ja_JP": "停止",
        "ko_KR": "중지됨",
        "es_ES": "Detenido",
        "pt_BR": "Parado",
    },
    "Paused because browser exited": {
        "zh_TW": "已暫停：瀏覽器已關閉！",
        "zh_CN": "已暂停：浏览器已关闭！",
        "en_US": "Paused because browser exited",
        "ja_JP": "ブラウザが終了したため一時停止しました",
        "ko_KR": "브라우저가 종료되어 일시 중지됨",
        "es_ES": "Pausado porque el navegador se cerró",
        "pt_BR": "Pausado porque o navegador foi encerrado",
    },
}


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    added = updated = 0
    for msgid, translations in RUNTIME_ENTRIES.items():
        if msgid not in catalog:
            catalog[msgid] = translations
            added += 1
        else:
            for loc in LOCALES:
                if catalog[msgid].get(loc) != translations[loc]:
                    catalog[msgid][loc] = translations[loc]
                    updated += 1
    CATALOG.write_text(
        json.dumps(dict(sorted(catalog.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"catalog: +{added} new, {updated} locale updates, total {len(catalog)}")

    patches = {
        loc: {"app": {msgid: RUNTIME_ENTRIES[msgid][loc] for msgid in RUNTIME_ENTRIES}}
        for loc in LOCALES
    }
    out = ROOT / "i18n" / "gui" / "notification_patches.json"
    out.write_text(json.dumps(patches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(RUNTIME_ENTRIES)} strings × {len(LOCALES)} locales)")


if __name__ == "__main__":
    main()
