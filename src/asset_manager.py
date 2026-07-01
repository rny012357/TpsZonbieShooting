"""
アセット管理
画像・音声を起動時に一括ロードし、シーン間で共有する。
同じアセットを複数回読み込まない。
"""
import os
import pygame

# アセットディレクトリ
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")


class AssetManager:
    """アセットの一括管理クラス（シングルトン）"""

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
        self._images: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._loaded = False

    def load_all(self):
        """全アセットを一括ロードする（起動時に1回だけ呼ぶ）"""
        if self._loaded:
            return

        # 画像ロード
        if os.path.exists(IMAGES_DIR):
            for filename in os.listdir(IMAGES_DIR):
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    name = os.path.splitext(filename)[0]
                    filepath = os.path.join(IMAGES_DIR, filename)
                    try:
                        image = pygame.image.load(filepath).convert_alpha()
                        self._images[name] = image
                    except pygame.error:
                        print(f"警告: 画像の読み込みに失敗: {filepath}")

        # 音声ロード
        if os.path.exists(SOUNDS_DIR):
            for filename in os.listdir(SOUNDS_DIR):
                if filename.lower().endswith((".mp3", ".wav", ".ogg")):
                    name = os.path.splitext(filename)[0]
                    filepath = os.path.join(SOUNDS_DIR, filename)
                    try:
                        sound = pygame.mixer.Sound(filepath)
                        self._sounds[name] = sound
                    except pygame.error:
                        print(f"警告: 音声の読み込みに失敗: {filepath}")

        self._loaded = True

    def get_image(self, name: str) -> pygame.Surface | None:
        """画像を取得する（拡張子なしの名前で指定）"""
        return self._images.get(name)

    def get_sound(self, name: str) -> pygame.mixer.Sound | None:
        """音声を取得する（拡張子なしの名前で指定）"""
        return self._sounds.get(name)

    def get_image_scaled(self, name: str, width: int, height: int) -> pygame.Surface | None:
        """画像をスケーリングして取得する"""
        image = self._images.get(name)
        if image is None:
            return None
        return pygame.transform.scale(image, (width, height))
