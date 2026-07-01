"""
設定管理
settings.jsonの読み書きを行う。
起動時に読み込み、変更時・終了時に保存する。
"""
import json
import os

# 設定ファイルパス（srcディレクトリと同じ階層）
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

# デフォルト設定値
DEFAULT_SETTINGS = {
    "master_volume": 100,
    "bgm_volume": 100,
    "se_volume": 100,
}


class SettingsManager:
    """設定の読み書きを管理するシングルトン風クラス"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings: dict = {}
        self.load()

    def load(self):
        """設定を読み込む。ファイルが存在しない場合はデフォルト値で生成する。"""
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                # 不足キーをデフォルトで補完
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except (json.JSONDecodeError, IOError):
                self.settings = DEFAULT_SETTINGS.copy()
                self.save()
        else:
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

    def save(self):
        """設定をファイルに保存する。"""
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except IOError:
            pass

    @property
    def master_volume(self) -> int:
        return self.settings.get("master_volume", 100)

    @master_volume.setter
    def master_volume(self, value: int):
        self.settings["master_volume"] = max(0, min(100, value))
        self.save()

    @property
    def bgm_volume(self) -> int:
        return self.settings.get("bgm_volume", 100)

    @bgm_volume.setter
    def bgm_volume(self, value: int):
        self.settings["bgm_volume"] = max(0, min(100, value))
        self.save()

    @property
    def se_volume(self) -> int:
        return self.settings.get("se_volume", 100)

    @se_volume.setter
    def se_volume(self, value: int):
        self.settings["se_volume"] = max(0, min(100, value))
        self.save()

    def get_bgm_effective_volume(self) -> float:
        """BGMの実効音量（0.0〜1.0）: master × bgm"""
        return (self.master_volume / 100.0) * (self.bgm_volume / 100.0)

    def get_se_effective_volume(self) -> float:
        """SEの実効音量（0.0〜1.0）: master × se"""
        return (self.master_volume / 100.0) * (self.se_volume / 100.0)
