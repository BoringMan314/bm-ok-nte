"""Sync gettext ok.po entries across all locales (full i18n catalog)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"

# Fishing UI / stage labels (msgid -> per-locale msgstr)
FISHING_UI_ENTRIES: dict[str, dict[str, str]] = {
    "轮次": {
        "zh_TW": "輪次",
        "zh_CN": "轮次",
        "en_US": "Round",
        "ja_JP": "ラウンド",
        "ko_KR": "회차",
        "es_ES": "Ronda",
        "pt_BR": "Rodada",
    },
    "成功次数": {
        "zh_TW": "成功次數",
        "zh_CN": "成功次数",
        "en_US": "Success count",
        "ja_JP": "成功回数",
        "ko_KR": "성공 횟수",
        "es_ES": "Éxitos",
        "pt_BR": "Sucessos",
    },
    "失败次数": {
        "zh_TW": "失敗次數",
        "zh_CN": "失败次数",
        "en_US": "Failure count",
        "ja_JP": "失敗回数",
        "ko_KR": "실패 횟수",
        "es_ES": "Fallos",
        "pt_BR": "Falhas",
    },
    "当前阶段": {
        "zh_TW": "當前階段",
        "zh_CN": "当前阶段",
        "en_US": "Current stage",
        "ja_JP": "現在の段階",
        "ko_KR": "현재 단계",
        "es_ES": "Fase actual",
        "pt_BR": "Estágio atual",
    },
    "失败原因": {
        "zh_TW": "失敗原因",
        "zh_CN": "失败原因",
        "en_US": "Failure reason",
        "ja_JP": "失敗理由",
        "ko_KR": "실패 원인",
        "es_ES": "Motivo del fallo",
        "pt_BR": "Motivo da falha",
    },
    "开启": {
        "zh_TW": "開啟",
        "zh_CN": "开启",
        "en_US": "On",
        "ja_JP": "オン",
        "ko_KR": "켜짐",
        "es_ES": "Activado",
        "pt_BR": "Ativado",
    },
    "关闭": {
        "zh_TW": "關閉",
        "zh_CN": "关闭",
        "en_US": "Off",
        "ja_JP": "オフ",
        "ko_KR": "꺼짐",
        "es_ES": "Desactivado",
        "pt_BR": "Desativado",
    },
    "Running: {}": {
        "zh_TW": "執行中：{}",
        "zh_CN": "执行中：{}",
        "en_US": "Running: {}",
        "ja_JP": "実行中：{}",
        "ko_KR": "실행 중: {}",
        "es_ES": "En ejecución: {}",
        "pt_BR": "Em execução: {}",
    },
    "cast rod": {
        "zh_TW": "拋竿",
        "zh_CN": "抛竿",
        "en_US": "Cast rod",
        "ja_JP": "キャスト",
        "ko_KR": "낚시대 던지기",
        "es_ES": "Lanzar caña",
        "pt_BR": "Arremessar vara",
    },
    "check monthly card": {
        "zh_TW": "檢查月卡",
        "zh_CN": "检查月卡",
        "en_US": "Check monthly card",
        "ja_JP": "月パス確認",
        "ko_KR": "월정액 확인",
        "es_ES": "Comprobar pase mensual",
        "pt_BR": "Verificar passe mensal",
    },
    "is success": {
        "zh_TW": "釣魚成功",
        "zh_CN": "钓鱼成功",
        "en_US": "Fishing success",
        "ja_JP": "釣り成功",
        "ko_KR": "낚시 성공",
        "es_ES": "Pesca exitosa",
        "pt_BR": "Pesca bem-sucedida",
    },
    "is bite": {
        "zh_TW": "魚兒咬鉤",
        "zh_CN": "鱼儿咬钩",
        "en_US": "Fish biting",
        "ja_JP": "魚がかかりました",
        "ko_KR": "물고기 입질",
        "es_ES": "Pez mordiendo",
        "pt_BR": "Peixe mordendo",
    },
    "control bar": {
        "zh_TW": "溜魚控條",
        "zh_CN": "溜鱼控条",
        "en_US": "Fish control bar",
        "ja_JP": "溜めゲージ",
        "ko_KR": "힘 조절 게이지",
        "es_ES": "Barra de tensión",
        "pt_BR": "Barra de tensão",
    },
    "buy bait": {
        "zh_TW": "購買魚餌",
        "zh_CN": "购买鱼饵",
        "en_US": "Buy bait",
        "ja_JP": "餌を購入",
        "ko_KR": "미끼 구매",
        "es_ES": "Comprar cebo",
        "pt_BR": "Comprar isca",
    },
    "sell fish": {
        "zh_TW": "出售魚獲",
        "zh_CN": "出售鱼获",
        "en_US": "Sell fish",
        "ja_JP": "魚を売却",
        "ko_KR": "어획물 판매",
        "es_ES": "Vender capturas",
        "pt_BR": "Vender peixes",
    },
    "任务结束": {
        "zh_TW": "任務結束",
        "zh_CN": "任务结束",
        "en_US": "Task finished",
        "ja_JP": "タスク終了",
        "ko_KR": "작업 종료",
        "es_ES": "Tarea finalizada",
        "pt_BR": "Tarefa concluída",
    },
    "恢复钓鱼界面": {
        "zh_TW": "恢復釣魚介面",
        "zh_CN": "恢复钓鱼界面",
        "en_US": "Restore fishing screen",
        "ja_JP": "釣り画面を復帰",
        "ko_KR": "낚시 화면 복구",
        "es_ES": "Restaurar pantalla de pesca",
        "pt_BR": "Restaurar tela de pesca",
    },
    "等待钓鱼准备界面": {
        "zh_TW": "等待釣魚準備介面",
        "zh_CN": "等待钓鱼准备界面",
        "en_US": "Waiting for fishing ready screen",
        "ja_JP": "釣り準備画面を待機",
        "ko_KR": "낚시 준비 화면 대기",
        "es_ES": "Esperando pantalla de preparación",
        "pt_BR": "Aguardando tela de preparação",
    },
    "寻找钓鱼交互点": {
        "zh_TW": "尋找釣魚互動點",
        "zh_CN": "寻找钓鱼交互点",
        "en_US": "Find fishing interaction point",
        "ja_JP": "釣り交互ポイントを探索",
        "ko_KR": "낚시 상호작용 지점 탐색",
        "es_ES": "Buscar punto de interacción",
        "pt_BR": "Procurar ponto de interação",
    },
    "下一轮咬钩前未检测到成功面板": {
        "zh_TW": "下一輪咬鉤前未偵測到成功面板",
        "zh_CN": "下一轮咬钩前未检测到成功面板",
        "en_US": "Success panel not detected before next bite",
        "ja_JP": "次のラウンド前に成功パネル未検出",
        "ko_KR": "다음 입질 전 성공 패널 미감지",
        "es_ES": "Panel de éxito no detectado antes de la siguiente mordida",
        "pt_BR": "Painel de sucesso não detectado antes da próxima mordida",
    },
    "状态轮询连续失败": {
        "zh_TW": "狀態輪詢連續失敗",
        "zh_CN": "状态轮询连续失败",
        "en_US": "State polling failed repeatedly",
        "ja_JP": "状態ポーリングが連続失敗",
        "ko_KR": "상태 폴링 연속 실패",
        "es_ES": "Sondeo de estado falló repetidamente",
        "pt_BR": "Polling de estado falhou repetidamente",
    },
    "钓鱼状态轮询失败": {
        "zh_TW": "釣魚狀態輪詢失敗",
        "zh_CN": "钓鱼状态轮询失败",
        "en_US": "Fishing state polling failed",
        "ja_JP": "釣り状態ポーリング失敗",
        "ko_KR": "낚시 상태 폴링 실패",
        "es_ES": "Fallo en sondeo de estado de pesca",
        "pt_BR": "Falha no polling de estado de pesca",
    },
    "Start Game": {
        "zh_TW": "啟動遊戲",
        "zh_CN": "启动游戏",
        "en_US": "Start Game",
        "ja_JP": "ゲームを起動",
        "ko_KR": "게임 시작",
        "es_ES": "Iniciar juego",
        "pt_BR": "Iniciar jogo",
    },
    "Launcher Path": {
        "zh_TW": "啟動器路徑",
        "zh_CN": "启动器路径",
        "en_US": "Launcher Path",
        "ja_JP": "ランチャーパス",
        "ko_KR": "런처 경로",
        "es_ES": "Ruta del lanzador",
        "pt_BR": "Caminho do launcher",
    },
    "FishingTask error": {
        "zh_TW": "釣魚任務錯誤",
        "zh_CN": "钓鱼任务错误",
        "en_US": "Fishing task error",
        "ja_JP": "釣りタスクエラー",
        "ko_KR": "낚시 작업 오류",
        "es_ES": "Error en tarea de pesca",
        "pt_BR": "Erro na tarefa de pesca",
    },
    "RhythmTask error": {
        "zh_TW": "音遊任務錯誤",
        "zh_CN": "音游任务错误",
        "en_US": "Rhythm task error",
        "ja_JP": "リズムタスクエラー",
        "ko_KR": "리듬 작업 오류",
        "es_ES": "Error en tarea de ritmo",
        "pt_BR": "Erro na tarefa de ritmo",
    },
    "记录新特征": {
        "zh_TW": "記錄新特徵",
        "zh_CN": "记录新特征",
        "en_US": "Record New Feature",
        "ja_JP": "新しい特徴を記録",
        "ko_KR": "새 특징 기록",
        "es_ES": "Registrar nueva característica",
        "pt_BR": "Registrar nova característica",
    },
    "输入或选择绑定的{combo} (可选)": {
        "zh_TW": "輸入或選擇綁定的{combo}（可選）",
        "zh_CN": "输入或选择绑定的{combo} (可选)",
        "en_US": "Enter or select the bound {combo} (optional)",
        "ja_JP": "紐付け{combo}を入力または選択（任意）",
        "ko_KR": "연결된 {combo} 입력 또는 선택(선택)",
        "es_ES": "Introduce o selecciona el {combo} vinculado (opcional)",
        "pt_BR": "Digite ou selecione o {combo} vinculado (opcional)",
    },
    "输入或选择关联的角色名称": {
        "zh_TW": "輸入或選擇關聯的角色名稱",
        "zh_CN": "输入或选择关联的角色名称",
        "en_US": "Enter or select the associated character name",
        "ja_JP": "関連キャラクター名を入力または選択",
        "ko_KR": "연결된 캐릭터 이름 입력 또는 선택",
        "es_ES": "Introduce o selecciona el nombre del personaje asociado",
        "pt_BR": "Digite ou selecione o nome do personagem associado",
    },
    "自动钓鱼": {
        "zh_TW": "自動釣魚",
        "zh_CN": "自动钓鱼",
        "en_US": "Auto Fishing",
        "ja_JP": "自動釣り",
        "ko_KR": "자동 낚시",
        "es_ES": "Pesca automática",
        "pt_BR": "Pesca automática",
    },
    "自动完成一轮或多轮钓鱼": {
        "zh_TW": "自動完成一輪或多輪釣魚",
        "zh_CN": "自动完成一轮或多轮钓鱼",
        "en_US": "Automatically complete one or more rounds of fishing",
        "ja_JP": "1回以上の釣りを自動で完了",
        "ko_KR": "한 번 이상의 낚시를 자동으로 완료",
        "es_ES": "Completar automáticamente una o más rondas de pesca",
        "pt_BR": "Concluir automaticamente uma ou mais rodadas de pesca",
    },
    "循环次数": {
        "zh_TW": "循環次數",
        "zh_CN": "循环次数",
        "en_US": "Loop count",
        "ja_JP": "ループ回数",
        "ko_KR": "반복 횟수",
        "es_ES": "Número de rondas",
        "pt_BR": "Número de rodadas",
    },
    "控条模式": {
        "zh_TW": "控條模式",
        "zh_CN": "控条模式",
        "en_US": "Control Bar Mode",
        "ja_JP": "ゲージ制御モード",
        "ko_KR": "게이지 제어 모드",
        "es_ES": "Modo de barra de control",
        "pt_BR": "Modo Barra de Controle",
    },
    "点按时长倍率": {
        "zh_TW": "點按時長倍率",
        "zh_CN": "点按时长倍率",
        "en_US": "Tap Duration Multiplier",
        "ja_JP": "タップ時間倍率",
        "ko_KR": "탭 지속 시간 배율",
        "es_ES": "Multiplicador de duración de pulsación",
        "pt_BR": "Multiplicador de duração do toque",
    },
    "自动补饵卖鱼": {
        "zh_TW": "自動補餌賣魚",
        "zh_CN": "自动补饵卖鱼",
        "en_US": "Auto-Refill Bait & Sell Fish",
        "ja_JP": "自動餌補充・魚売却",
        "ko_KR": "자동 미끼 보충 및 물고기 판매",
        "es_ES": "Auto-recarga cebo y vende pescado",
        "pt_BR": "Recarga Automática de Isca e Venda de Peixes",
    },
    "长按": {
        "zh_TW": "長按",
        "zh_CN": "长按",
        "en_US": "Long Press",
        "ja_JP": "長押し",
        "ko_KR": "길게 누르기",
        "es_ES": "Mantener pulsado",
        "pt_BR": "Pressionar e segurar",
    },
    "点按": {
        "zh_TW": "點按",
        "zh_CN": "点按",
        "en_US": "Tap",
        "ja_JP": "タップ",
        "ko_KR": "탭",
        "es_ES": "Pulsación",
        "pt_BR": "Toque",
    },
    "点按模式专用。用于微调每次按键的持续时间": {
        "zh_TW": "點按模式專用。用於微調每次按鍵的持續時間",
        "zh_CN": "点按模式专用。用于微调每次按键的持续时间",
        "en_US": "For Tap mode only. Used to fine-tune the duration of each key press.",
        "ja_JP": "タップモード専用。各キー入力の持続時間を微調整するために使用します",
        "ko_KR": "탭 모드 전용. 각 키 입력 지속 시간을 미세 조정합니다",
        "es_ES": "Solo para modo pulsación. Ajusta la duración de cada pulsación.",
        "pt_BR": "Somente para o modo toque. Ajusta fino a duração de cada pressionamento.",
    },
    "保存成功": {
        "zh_TW": "儲存成功",
        "zh_CN": "保存成功",
        "en_US": "Saved successfully",
        "ja_JP": "保存しました",
        "ko_KR": "저장 성공",
        "es_ES": "Guardado con éxito",
        "pt_BR": "Salvo com sucesso",
    },
    "更新": {
        "zh_TW": "更新",
        "zh_CN": "更新",
        "en_US": "Update",
        "ja_JP": "アップデート",
        "ko_KR": "업데이트",
        "es_ES": "Actualizar",
        "pt_BR": "Atualizar",
    },
}


def _load_catalog() -> dict[str, dict[str, str]]:
    if CATALOG_PATH.is_file():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    import polib

    catalog: dict[str, dict[str, str]] = {}
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        if not po_path.is_file():
            continue
        for entry in polib.pofile(str(po_path)):
            if entry.obsolete or not entry.msgid:
                continue
            catalog.setdefault(entry.msgid, {})[locale] = (
                entry.msgstr if entry.msgstr else entry.msgid
            )
    return catalog


def _load_entries() -> dict[str, dict[str, str]]:
    from sync_fishing_i18n import ENTRIES as fishing_log_entries

    merged = _load_catalog()
    for source in (fishing_log_entries, FISHING_UI_ENTRIES):
        for msgid, translations in source.items():
            bucket = merged.setdefault(msgid, {})
            bucket.update(translations)
    return merged


def merge_po(po_path: Path, locale: str, reference_ids: set[str], entries: dict[str, dict[str, str]]) -> tuple[int, list[str]]:
    import polib

    po = polib.pofile(str(po_path))
    existing = {e.msgid: e for e in po}
    added = 0
    still_missing: list[str] = []
    for msgid in sorted(reference_ids):
        if msgid not in entries:
            continue
        expected = entries[msgid].get(locale, msgid)
        if msgid in existing:
            entry = existing[msgid]
            if msgid in entries and entry.msgstr != expected:
                entry.msgstr = expected
                added += 1
            continue
        po.append(polib.POEntry(msgid=msgid, msgstr=expected))
        added += 1
    po.wrapwidth = 999999
    po.save(str(po_path))
    for msgid in sorted(reference_ids):
        if msgid not in {e.msgid for e in polib.pofile(str(po_path))}:
            still_missing.append(msgid)
    return added, still_missing


def main() -> None:
    import polib

    entries = _load_entries()
    reference_ids: set[str] = set()
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        if po_path.is_file():
            po = polib.pofile(str(po_path))
            reference_ids.update(e.msgid for e in po if e.msgid)
    reference_ids.update(entries.keys())

    print(f"reference union: {len(reference_ids)} msgids")
    total = 0
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        if not po_path.is_file():
            print(f"skip missing {po_path}")
            continue
        n, missing = merge_po(po_path, locale, reference_ids, entries)
        count = len({e.msgid for e in polib.pofile(str(po_path)) if e.msgid})
        print(f"{locale}: +{n} updates, total {count} msgids")
        if missing:
            print(f"  still missing: {missing}")
        total += n
    print(f"done: {total} entry updates")


if __name__ == "__main__":
    main()
