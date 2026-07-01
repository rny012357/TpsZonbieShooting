"""
サウンド管理
BGMループ再生、効果音再生、音量設定の反映を行う。
"""
import pygame
from asset_manager import AssetManager
from settings_manager import SettingsManager


class SoundManager:
    """サウンドの再生・音量管理クラス（シングルトン）"""

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
        self.bgm_playing = False
        self._assets = AssetManager()
        self._settings = SettingsManager()

    def play_bgm(self):
        """BGMをループ再生する（ゲームプレイ中のみ）"""
        if self.bgm_playing:
            return
        bgm = self._assets.get_sound("BGM")
        if bgm:
            bgm.set_volume(self._settings.get_bgm_effective_volume())
            bgm.play(loops=-1)  # 無限ループ
            self.bgm_playing = True

    def stop_bgm(self):
        """BGMを停止する"""
        bgm = self._assets.get_sound("BGM")
        if bgm:
            bgm.stop()
        self.bgm_playing = False

    def play_shoot(self):
        """発射音を再生する"""
        se = self._assets.get_sound("se_pyun2")
        if se:
            se.set_volume(self._settings.get_se_effective_volume())
            se.play()

    def play_kill(self):
        """撃破音を再生する"""
        se = self._assets.get_sound("A_short_sound_effect_#3-1782831469960")
        if se:
            se.set_volume(self._settings.get_se_effective_volume())
            se.play()

    def update_volumes(self):
        """音量設定をすべての再生中サウンドに反映する"""
        # BGMの音量更新
        bgm = self._assets.get_sound("BGM")
        if bgm and self.bgm_playing:
            bgm.set_volume(self._settings.get_bgm_effective_volume())
