"""Add missing fishing-task gettext entries to all locale ok.po files."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]

# msgid (Simplified Chinese source) -> per-locale msgstr
ENTRIES: dict[str, dict[str, str]] = {
    "抛竿失败时，补充默认鱼饵并出售鱼获后重试": {
        "zh_TW": "拋竿失敗時，補充預設魚餌並出售魚獲後重試",
        "zh_CN": "抛竿失败时，补充默认鱼饵并出售鱼获后重试",
        "en_US": "When casting fails, refill default bait, sell catch, and retry",
        "ja_JP": "キャスト失敗時、デフォルト餌を補充して魚を売却し、再試行します",
        "ko_KR": "낚시대 던지기 실패 시 기본 미끼를 보충하고 어획물을 판매한 뒤 재시도합니다",
        "es_ES": "Si falla el lanzamiento, reponer cebo predeterminado, vender capturas y reintentar",
        "pt_BR": "Se a arremessada falhar, reabastece a isca padrão, vende a captura e tenta novamente",
    },
    "进入溜鱼状态": {
        "zh_TW": "進入溜魚狀態",
        "zh_CN": "进入溜鱼状态",
        "en_US": "Entering fish-playing state",
        "ja_JP": "溜め状態に入りました",
        "ko_KR": "힘 조절 상태로 진입",
        "es_ES": "Entrando en fase de tensión",
        "pt_BR": "Entrando no estado de tensionar o peixe",
    },
    "鱼儿咬钩": {
        "zh_TW": "魚兒咬鉤",
        "zh_CN": "鱼儿咬钩",
        "en_US": "Fish is biting",
        "ja_JP": "魚がかかりました",
        "ko_KR": "물고기가 입질했습니다",
        "es_ES": "El pez ha mordido",
        "pt_BR": "O peixe mordeu a isca",
    },
    "开始自动钓鱼，共 {} 轮": {
        "zh_TW": "開始自動釣魚，共 {} 輪",
        "zh_CN": "开始自动钓鱼，共 {} 轮",
        "en_US": "Starting auto fishing, {} round(s) total",
        "ja_JP": "自動釣りを開始、全 {} 回",
        "ko_KR": "자동 낚시 시작, 총 {}회",
        "es_ES": "Iniciando pesca automática, {} ronda(s) en total",
        "pt_BR": "Iniciando pesca automática, {} rodada(s) no total",
    },
    "开始自动钓鱼，无限循环": {
        "zh_TW": "開始自動釣魚，無限循環",
        "zh_CN": "开始自动钓鱼，无限循环",
        "en_US": "Starting auto fishing, infinite loop",
        "ja_JP": "自動釣りを開始、無限ループ",
        "ko_KR": "자동 낚시 시작, 무한 반복",
        "es_ES": "Iniciando pesca automática, bucle infinito",
        "pt_BR": "Iniciando pesca automática, loop infinito",
    },
    "第 {} 轮钓鱼成功": {
        "zh_TW": "第 {} 輪釣魚成功",
        "zh_CN": "第 {} 轮钓鱼成功",
        "en_US": "Round {} fishing succeeded",
        "ja_JP": "第 {} 回の釣り成功",
        "ko_KR": "제 {}회 낚시 성공",
        "es_ES": "Ronda {} de pesca completada",
        "pt_BR": "Rodada {} de pesca concluída com sucesso",
    },
    "第 {} 轮钓鱼失败：未检测到成功面板": {
        "zh_TW": "第 {} 輪釣魚失敗：未偵測到成功面板",
        "zh_CN": "第 {} 轮钓鱼失败：未检测到成功面板",
        "en_US": "Round {} fishing failed: success panel not detected",
        "ja_JP": "第 {} 回の釣り失敗：成功パネルが検出されませんでした",
        "ko_KR": "제 {}회 낚시 실패: 성공 패널 미감지",
        "es_ES": "Ronda {} fallida: no se detectó el panel de éxito",
        "pt_BR": "Rodada {} falhou: painel de sucesso não detectado",
    },
    "第 {} 轮钓鱼失败：状态轮询连续失败": {
        "zh_TW": "第 {} 輪釣魚失敗：狀態輪詢連續失敗",
        "zh_CN": "第 {} 轮钓鱼失败：状态轮询连续失败",
        "en_US": "Round {} fishing failed: state polling failed repeatedly",
        "ja_JP": "第 {} 回の釣り失敗：状態ポーリングが連続失敗",
        "ko_KR": "제 {}회 낚시 실패: 상태 폴링 연속 실패",
        "es_ES": "Ronda {} fallida: sondeo de estado falló repetidamente",
        "pt_BR": "Rodada {} falhou: polling de estado falhou repetidamente",
    },
    "自动钓鱼结束，成功 {}/{}": {
        "zh_TW": "自動釣魚結束，成功 {}/{}",
        "zh_CN": "自动钓鱼结束，成功 {}/{}",
        "en_US": "Auto fishing finished, succeeded {}/{}",
        "ja_JP": "自動釣り終了、成功 {}/{}",
        "ko_KR": "자동 낚시 종료, 성공 {}/{}",
        "es_ES": "Pesca automática finalizada, éxito {}/{}",
        "pt_BR": "Pesca automática concluída, sucesso {}/{}",
    },
    "自动钓鱼结束，成功 {}": {
        "zh_TW": "自動釣魚結束，成功 {}",
        "zh_CN": "自动钓鱼结束，成功 {}",
        "en_US": "Auto fishing finished, succeeded {}",
        "ja_JP": "自動釣り終了、成功 {}",
        "ko_KR": "자동 낚시 종료, 성공 {}",
        "es_ES": "Pesca automática finalizada, éxito {}",
        "pt_BR": "Pesca automática concluída, sucesso {}",
    },
    "未检测到进入抛竿状态": {
        "zh_TW": "未偵測到進入拋竿狀態",
        "zh_CN": "未检测到进入抛竿状态",
        "en_US": "Casting state not detected",
        "ja_JP": "キャスト状態に入っていません",
        "ko_KR": "낚시대 던지기 상태 미감지",
        "es_ES": "No se detectó el estado de lanzamiento",
        "pt_BR": "Estado de arremesso não detectado",
    },
    "未检测到可用鱼饵，开始买饵补货": {
        "zh_TW": "未偵測到可用魚餌，開始買餌補貨",
        "zh_CN": "未检测到可用鱼饵，开始买饵补货",
        "en_US": "No usable bait detected, starting bait restock",
        "ja_JP": "使用可能な餌が見つかりません。餌の補充を開始します",
        "ko_KR": "사용 가능한 미끼 없음, 미끼 보충 시작",
        "es_ES": "No hay cebo disponible, iniciando reposición",
        "pt_BR": "Sem isca disponível, iniciando reabastecimento",
    },
    "等待鱼儿咬钩超时": {
        "zh_TW": "等待魚兒咬鉤逾時",
        "zh_CN": "等待鱼儿咬钩超时",
        "en_US": "Timed out waiting for a bite",
        "ja_JP": "魚のかかり待ちがタイムアウト",
        "ko_KR": "입질 대기 시간 초과",
        "es_ES": "Tiempo de espera de mordida agotado",
        "pt_BR": "Tempo esgotado aguardando mordida",
    },
    "状态机运行超时": {
        "zh_TW": "狀態機執行逾時",
        "zh_CN": "状态机运行超时",
        "en_US": "State machine timed out",
        "ja_JP": "ステートマシンがタイムアウト",
        "ko_KR": "상태 머신 실행 시간 초과",
        "es_ES": "La máquina de estados agotó el tiempo",
        "pt_BR": "Máquina de estados expirou",
    },
    "溜鱼状态超时": {
        "zh_TW": "溜魚狀態逾時",
        "zh_CN": "溜鱼状态超时",
        "en_US": "Fish-playing state timed out",
        "ja_JP": "溜め状態がタイムアウト",
        "ko_KR": "힘 조절 상태 시간 초과",
        "es_ES": "Fase de tensión agotó el tiempo",
        "pt_BR": "Estado de tensionar expirou",
    },
    "默认鱼饵可用": {
        "zh_TW": "預設魚餌可用",
        "zh_CN": "默认鱼饵可用",
        "en_US": "Default bait is available",
        "ja_JP": "デフォルト餌が使用可能",
        "ko_KR": "기본 미끼 사용 가능",
        "es_ES": "Cebo predeterminado disponible",
        "pt_BR": "Isca padrão disponível",
    },
    "未进入购买鱼饵页面": {
        "zh_TW": "未進入購買魚餌頁面",
        "zh_CN": "未进入购买鱼饵页面",
        "en_US": "Did not enter bait purchase screen",
        "ja_JP": "餌購入画面に入れませんでした",
        "ko_KR": "미끼 구매 화면 진입 실패",
        "es_ES": "No se entró a la pantalla de compra de cebo",
        "pt_BR": "Não entrou na tela de compra de isca",
    },
    "一键出售未完成，可能当前鱼获不可出售，跳过出售": {
        "zh_TW": "一鍵出售未完成，可能目前魚獲不可出售，跳過出售",
        "zh_CN": "一键出售未完成，可能当前鱼获不可出售，跳过出售",
        "en_US": "Quick sell incomplete; catch may not be sellable, skipping",
        "ja_JP": "一括売却未完了。売却不可の可能性があるためスキップ",
        "ko_KR": "일괄 판매 미완료, 판매 불가능할 수 있어 건너뜀",
        "es_ES": "Venta rápida incompleta; puede no ser vendible, omitiendo",
        "pt_BR": "Venda rápida incompleta; captura pode ser invendável, ignorando",
    },
    "鱼舱内没有可出售鱼获，跳过出售": {
        "zh_TW": "魚艙內沒有可出售魚獲，跳過出售",
        "zh_CN": "鱼舱内没有可出售鱼获，跳过出售",
        "en_US": "No sellable fish in hold, skipping sell",
        "ja_JP": "魚倉に売却可能な魚がないためスキップ",
        "ko_KR": "어획함에 판매 가능한 물고기 없음, 판매 건너뜀",
        "es_ES": "No hay capturas vendibles, omitiendo venta",
        "pt_BR": "Sem peixes vendáveis no compartimento, ignorando venda",
    },
    "[{}]流程等待超时，执行恢复操作": {
        "zh_TW": "[{}]流程等待逾時，執行恢復操作",
        "zh_CN": "[{}]流程等待超时，执行恢复操作",
        "en_US": "[{}] workflow timed out, running recovery",
        "ja_JP": "[{}] フロー待機タイムアウト、復旧処理を実行",
        "ko_KR": "[{}] 워크플로 대기 시간 초과, 복구 실행",
        "es_ES": "[{}] flujo agotó el tiempo, ejecutando recuperación",
        "pt_BR": "[{}] fluxo expirou, executando recuperação",
    },
    "已回到钓鱼准备界面": {
        "zh_TW": "已回到釣魚準備介面",
        "zh_CN": "已回到钓鱼准备界面",
        "en_US": "Returned to fishing ready screen",
        "ja_JP": "釣り準備画面に戻りました",
        "ko_KR": "낚시 준비 화면으로 복귀",
        "es_ES": "Regresó a la pantalla de preparación de pesca",
        "pt_BR": "Retornou à tela de preparação de pesca",
    },
    "恢复钓鱼准备界面超时": {
        "zh_TW": "恢復釣魚準備介面逾時",
        "zh_CN": "恢复钓鱼准备界面超时",
        "en_US": "Timed out restoring fishing ready screen",
        "ja_JP": "釣り準備画面の復帰がタイムアウト",
        "ko_KR": "낚시 준비 화면 복구 시간 초과",
        "es_ES": "Tiempo agotado al restaurar pantalla de preparación",
        "pt_BR": "Tempo esgotado ao restaurar tela de preparação",
    },
    "成功进入钓鱼场景": {
        "zh_TW": "成功進入釣魚場景",
        "zh_CN": "成功进入钓鱼场景",
        "en_US": "Entered fishing scene successfully",
        "ja_JP": "釣りシーンに入りました",
        "ko_KR": "낚시 장면 진입 성공",
        "es_ES": "Entró a la escena de pesca con éxito",
        "pt_BR": "Entrou na cena de pesca com sucesso",
    },
    "检测到文字: {}": {
        "zh_TW": "偵測到文字: {}",
        "zh_CN": "检测到文字: {}",
        "en_US": "Detected text: {}",
        "ja_JP": "文字を検出: {}",
        "ko_KR": "텍스트 감지: {}",
        "es_ES": "Texto detectado: {}",
        "pt_BR": "Texto detectado: {}",
    },
    "买饵补货": {
        "zh_TW": "買餌補貨",
        "zh_CN": "买饵补货",
        "en_US": "bait restock",
        "ja_JP": "餌補充",
        "ko_KR": "미끼 보충",
        "es_ES": "reposición de cebo",
        "pt_BR": "reabastecimento de isca",
    },
    "钓鱼": {
        "zh_TW": "釣魚",
        "zh_CN": "钓鱼",
        "en_US": "fishing",
        "ja_JP": "釣り",
        "ko_KR": "낚시",
        "es_ES": "pesca",
        "pt_BR": "pesca",
    },
    "monthly_card found click": {
        "zh_TW": "發現月卡，點擊關閉",
        "zh_CN": "发现月卡，点击关闭",
        "en_US": "Monthly card found, clicking to close",
        "ja_JP": "月パスを検出、クリックして閉じます",
        "ko_KR": "월정액 감지, 클릭하여 닫기",
        "es_ES": "Pase mensual detectado, haciendo clic para cerrar",
        "pt_BR": "Passe mensal detectado, clicando para fechar",
    },
    "monthly_card close failed": {
        "zh_TW": "月卡關閉失敗",
        "zh_CN": "月卡关闭失败",
        "en_US": "Failed to close monthly card popup",
        "ja_JP": "月パスの閉じる操作に失敗",
        "ko_KR": "월정액 팝업 닫기 실패",
        "es_ES": "No se pudo cerrar el pase mensual",
        "pt_BR": "Falha ao fechar o passe mensal",
    },
}


def merge_entries(po_path: Path, locale: str) -> int:
    import polib

    po = polib.pofile(str(po_path))
    existing = {e.msgid: e for e in po}
    added = 0
    for msgid, translations in ENTRIES.items():
        msgstr = translations.get(locale, msgid)
        if msgid in existing:
            entry = existing[msgid]
            if entry.msgstr != msgstr:
                entry.msgstr = msgstr
                added += 1
        else:
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            added += 1
    po.wrapwidth = 999999
    po.save(str(po_path))
    return added


def main() -> None:
    total = 0
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        if not po_path.is_file():
            print(f"skip missing {po_path}")
            continue
        n = merge_entries(po_path, locale)
        print(f"{locale}: updated {n} entries")
        total += n
    print(f"done: {total} entry updates")


if __name__ == "__main__":
    main()
