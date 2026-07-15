import os

from ok import Box, ConfigOption
from ok.util.GlobalConfig import basic_options

basic_options.default_config["Mute Game while in Background"] = True

from ok.util.config import Config

_bm_config_init = Config.__init__


def _config_init(self, name, default, folder=None, validator=None):
    if name == "_ok":
        default = {**default, "show_overlay_logs": False}
    _bm_config_init(self, name, default, folder=folder, validator=validator)


Config.__init__ = _config_init

from src.interaction.NTEInteraction import NTEInteraction
from src.process_feature import process_feature

if "PATH" not in os.environ:
    os.environ["PATH"] = ""

version = "v1.2.13"
# 不需要修改version, Github Action打包会自动修改

key_config_option = ConfigOption(
    "Game Hotkey Config",
    {  # 全局配置示例
        "Skill Key": "e",
        "Ultimate Key": "q",
        "Arc Key": "r",
        "Use QWERTY Physical Keys": False,
    },
    description="In Game Hotkey for Skills",
    config_description={
        "Use QWERTY Physical Keys": (
            "All letter/number keys, including every hotkey above, are replaced by US QWERTY\n"
            "physical positions, not your current layout's printed keys."
        ),
    },
)

monthly_card_config_option = ConfigOption(
    "Monthly Card Config",
    {"Check Monthly Card": True, "Monthly Card Time": 5},
    description="Turn on to avoid interruption by monthly card when executing tasks",
    config_description={
        "Check Monthly Card": "Check for monthly card to avoid interruption of tasks",
        "Monthly Card Time": "Your computer's local time when the monthly card will popup, hour in (1-24)",
    },
)

# Required by BaseNTETask after upstream v0.0.41; hidden from Settings via patch below.
sound_trigger_config_option = ConfigOption(
    "Sound Trigger Config",
    {
        "Enable Sound Trigger": False,
        "Dodge All Attacks": True,
        "Dodge Threshold": 0.13,
        "Counter Attack Threshold": 0.12,
    },
    description="Sound-based dodge and counter trigger settings",
    config_description={
        "Enable Sound Trigger": "Enable sound recognition for automatic dodge and counter attacks",
        "Dodge All Attacks": "Dodge all attacks without performing counter attacks",
        "Dodge Threshold": "Dodge sound recognition threshold (0.0-1.0, lower is more sensitive)",
        "Counter Attack Threshold": "Counter attack sound recognition threshold (0.0-1.0, lower is more sensitive)",
    },
)


def blur_area(width, height):
    return Box(width * 0, height * 0.9769, to_x=width * 0.0943, to_y=height * 1)


_ABOUT_DISCLAIMER = {
    "zh_CN": [
        "本软件是免费开源的。如果你被收费，请立即退款。请访问 QQ 频道或 GitHub 下载最新的官方版本。",
        "本软件仅供个人使用，用于学习 Python 编程、计算机视觉、UI 自动化等。请勿将其用于任何营利性或商业用途。",
        "使用本软件可能会导致账号被封。请在了解风险后再使用。",
    ],
    "zh_TW": [
        "本軟體是免費開源的。如果你被收費，請立即退款。請造訪 QQ 頻道或 GitHub 下載最新的官方版本。",
        "本軟體僅供個人使用，用於學習 Python 程式設計、電腦視覺、UI 自動化等。請勿將其用於任何營利性或商業用途。",
        "使用本軟體可能會導致帳號被封。請在了解風險後再使用。",
    ],
    "en_US": [
        "This software is free and open-source. If you were charged for it, please request a refund immediately. Visit the QQ channel or GitHub to download the latest official version.",
        "This software is for personal use only, intended for learning Python programming, computer vision, UI automation, and similar purposes. Do not use it for any commercial or profit-seeking activities.",
        "Using this software may result in account bans. Please proceed only if you fully understand the risks.",
    ],
    "es_ES": [
        "Este software es gratuito y de código abierto. Si le cobraron por él, solicite un reembolso de inmediato. Visite el canal de QQ o GitHub para descargar la última versión oficial.",
        "Este software es solo para uso personal, destinado al aprendizaje de programación Python, visión por computadora, automatización de UI, etc. No lo utilice con fines comerciales o de lucro.",
        "El uso de este software puede provocar la suspensión de cuentas. Continúe solo si comprende plenamente los riesgos.",
    ],
    "ja_JP": [
        "本ソフトウェアは無料のオープンソースです。有料で購入した場合は、すぐに返金を請求してください。QQ チャンネルまたは GitHub から最新の公式版をダウンロードしてください。",
        "本ソフトウェアは個人利用のみを目的としており、Python プログラミング、コンピュータビジョン、UI 自動化などの学習用です。営利目的や商用利用には使用しないでください。",
        "本ソフトウェアの使用により、アカウントが停止される可能性があります。リスクを十分理解した上でご利用ください。",
    ],
    "ko_KR": [
        "본 소프트웨어는 무료 오픈소스입니다. 유료로 구매하셨다면 즉시 환불을 요청하세요. QQ 채널 또는 GitHub에서 최신 공식 버전을 다운로드하세요.",
        "본 소프트웨어는 Python 프로그래밍, 컴퓨터 비전, UI 자동화 등을 학습하기 위한 개인 사용만을 목적으로 합니다. 영리 또는 상업적 목적으로 사용하지 마세요.",
        "본 소프트웨어 사용으로 계정 정지가 발생할 수 있습니다. 위험을 충분히 이해한 후 사용하세요.",
    ],
}


def _build_about_html(lang: str) -> str:
    sentences = _ABOUT_DISCLAIMER.get(lang) or _ABOUT_DISCLAIMER["en_US"]
    paragraphs = []
    for sentence in sentences:
        paragraphs.append(f'<p style="color:red;">\n<strong>{sentence}</strong>\n</p>')
    return "\n\n".join(paragraphs)


config = {
    "custom_tasks": False,
    "debug": False,  # Optional, default: False
    "use_gui": True,  # 目前只支持True
    "config_folder": "configs",  # 最好不要修改
    "global_configs": [
        key_config_option,
        monthly_card_config_option,
        sound_trigger_config_option,
    ],
    # "screenshot_processor": make_bottom_left_black,  # 在截图的时候对frame进行修改, 可选
    "blur_area": blur_area,
    "gui_icon": "icons/icon.png",  # 窗口图标, 最好不需要修改文件名
    "wait_until_before_delay": 0,
    "wait_until_check_delay": 0,
    "wait_until_settle_time": 0,  # 调用 wait_until时候, 在第一次满足条件的时候, 会等待再次检测, 以避免某些滑动动画没到预定位置就在动画路径中被检测到
    "ocr": {  # 可选, 使用的OCR库
        "default": {
            "lib": "onnxocr",
            "auto_simplify": True,
            "params": {
                "use_openvino": True,
            },
        },
        # "bg_onnx_ocr": {
        #     "lib": "onnxocr",
        #     "auto_simplify": True,
        #     "params": {
        #         "use_openvino": True,
        #     },
        # },
    },
    "windows": {  # Windows游戏请填写此设置
        "exe": "HTGame.exe",
        "hwnd_class": "UnrealWindow",
        "interaction": [
            NTEInteraction
        ],
        # Genshin:某些操作可以后台, 部分游戏支持 PostMessage:可后台点击, 极少游戏支持 ForegroundPostMessage:前台使用PostMessage Pynput/PyDirect:仅支持前台使用
        "capture_method": [
            "WGC",
            "BitBlt_RenderFull",
        ],  # Windows版本支持的话, 优先使用WGC, 否则使用BitBlt_Full. 支持的capture有 BitBlt, WGC, BitBlt_RenderFull, DXGI
        "check_hdr": False,  # 当用户开启AutoHDR时候提示用户, 但不禁止使用
        "force_no_hdr": False,  # True=当用户开启AutoHDR时候禁止使用
        "require_bg": True,  # 要求使用后台截图
        'start_exe': False,
    },
    # 'adb': {  # Windows游戏请填写此设置, mumu模拟器使用原生截图和input,速度极快. 其他模拟器和真机使用adb,截图速度较慢
    #     'packages': ['com.abc.efg1', 'com.abc.efg1']
    # },
    "start_timeout": 120,  # default 60
    "window_size": {  # ok-script窗口大小
        "width": 850,
        "height": 700,
        "min_width": 850,
        "min_height": 700,
        "fixed": True,
    },
    "supported_resolution": {
        "ratio": "16:9",  # 支持的游戏分辨率
        "min_size": (1920, 1080),  # 支持的最低游戏分辨率
        "resize_to": [(2560, 1440), (1920, 1080)],  # 可选, 如果非16:9自动缩放为 resize_to
    },
    "links": {  # 关于里显示的链接, 可选
        "default": {
            "github": "https://github.com/BoringMan314",
            "discord": "https://discord.gg/vVyCatEBgA",
            "sponsor": "https://ko-fi.com/boringman0314",
            "share": "https://github.com/BoringMan314/bm-ok-nte/releases",
            "faq": "https://github.com/BnanZ0/ok-nte",
            "qq_channel": "https://pd.qq.com/s/djmm6l44y",
        }
    },
    "about": "",
    "screenshots_folder": "screenshots",  # 截图存放目录, 每次重新启动会清空目录
    "gui_title": "bm-ok-nte",  # 窗口名
    "template_matching": {  # 可选, 如使用OpenCV的模板匹配
        "coco_feature_json": os.path.join("assets", "coco_annotations.json"),
        "default_horizontal_variance": 0.002,  # 默认x偏移, 查找不传box的时候, 会根据coco坐标, match偏移box内的
        "default_vertical_variance": 0.002,  # 默认y偏移
        "default_threshold": 0.7,  # 默认threshold
        "feature_processor": process_feature,
    },
    "template_tab": {
        # 默认是否生成标签枚举
        "generate_label_enum": True,
        # 默认标签枚举的相对路径
        "label_enum_relative_path": "src/Labels",
    },
    "version": version,  # 版本
    "my_app": [
        "src.globals",
        "Globals",
    ],  # 可选. 全局单例对象, 可以存放加载的模型, 使用og.my_app调用
    "onetime_tasks": [  # 用户点击触发的任务
        ["src.tasks.FishingTask", "FishingTask"],
    ],
    "trigger_tasks": [],
    "custom_tabs": [
        # ['src.ui.MyTab', 'MyTab'], #可选, 自定义UI, 显示在侧边栏
    ],
    "scene": ["src.scene.NTEScene", "NTEScene"],
    "update_pyappify": {
        "to_version": "1.1.6",
        "zip_url": "https://github.com/BnanZ0/ok-nte/releases/download/v1.1.6/ok-nte-win32.zip",
        "sha256": "fd66db24f9435ae8c4c05e0de4f4f00f0097a0187d677d473dad74800cd988c0",
    },
}


def _patch_about_tab_hide_other_projects():
    from ok.gui.about.AboutTab import AboutTab
    from ok.gui.common.config import cfg

    _orig_init = AboutTab.__init__

    def __init__(self, config, *args, **kwargs):
        lang = cfg.get(cfg.language).value.name()
        _orig_init(self, {**config, "about": _build_about_html(lang)}, *args, **kwargs)
        group = getattr(self, "group", None)
        if group is not None:
            self.vBoxLayout.removeWidget(group)
            group.setParent(None)
            group.deleteLater()
            del self.group

    AboutTab.__init__ = __init__


_patch_about_tab_hide_other_projects()


from src.bm_shell import apply_patches

apply_patches()


def _patch_task_log_i18n():
    from ok import og
    from ok.task.task import BaseTask

    def _tr(text):
        try:
            return og.app.tr(str(text)) if og.app else str(text)
        except Exception:
            return str(text)

    def info_set(self, key, value):
        if key not in ("Log", "Error"):
            self.logger.info(f"info_set {_tr(key)} {_tr(value)}")
        self.info[key] = value

    def log_info(self, message, notify=False):
        self.logger.info(message)
        self.info.pop("Error", None)
        self.info.pop("Warning", None)
        info_set(self, "Log", message)
        if notify:
            self.notification(message, tray=True)

    def log_warning(self, message, notify=False):
        self.logger.warning(message)
        info_set(self, "Warning", message)
        if notify:
            self.notification(message, tray=True)

    def log_error(self, message, exception=None, notify=False):
        self.logger.error(message, exception)
        if exception is not None:
            message += str(exception.args[0] if exception.args else exception)
        info_set(self, "Error", message)
        if notify:
            self.notification(message, error=True, tray=True)

    BaseTask.info_set = info_set
    BaseTask.log_info = log_info
    BaseTask.log_warning = log_warning
    BaseTask.log_error = log_error


_patch_task_log_i18n()


def _patch_start_card_task_name_i18n():
    from ok import og
    from ok.gui.start.StartCard import StartCard

    _orig_update_status = StartCard.update_status

    def update_status(self):
        _orig_update_status(self)
        if (
            not og.executor.paused
            and og.executor.connected()
            and not og.executor.active_trigger_task_count()
        ):
            task = og.executor.current_task
            if task and task.enabled and og.executor.can_capture():
                self.status_bar.setTitle(
                    og.app.tr("Running: {}").format(og.app.tr(task.name))
                )

    StartCard.update_status = update_status


_patch_start_card_task_name_i18n()


def _patch_mute_on_config_reset():
    from ok.device.capture_methods.hwnd_window import HwndWindow, set_mute_state
    from ok.util.config import Config

    _orig_reset = Config.reset_to_default

    def reset_to_default(self):
        old = dict(self)
        _orig_reset(self)
        if self.validator is not None:
            for key, value in self.default.items():
                if old.get(key) != value:
                    self.validator(key, value)

    Config.reset_to_default = reset_to_default

    def handle_mute(self, mute=None):
        if mute is None:
            mute = self.mute_option.get("Mute Game while in Background")
        if self.hwnd and self.to_handle_mute:
            set_mute_state(self.hwnd, 0 if not mute or self.visible else 1)

    HwndWindow.handle_mute = handle_mute


_patch_mute_on_config_reset()


def _patch_hide_sound_trigger_settings():
    from ok.util.GlobalConfig import GlobalConfig

    _HIDDEN_GLOBAL_CONFIGS = {
        "Sound Trigger Config",
        "Game Hotkey Config",
    }

    _orig_get_visible = GlobalConfig.get_all_visible_configs

    def get_all_visible_configs(self):
        return [
            item
            for item in _orig_get_visible(self)
            if item[0] not in _HIDDEN_GLOBAL_CONFIGS
        ]

    GlobalConfig.get_all_visible_configs = get_all_visible_configs


_patch_hide_sound_trigger_settings()
