"""
シーン管理
画面遷移をSceneManagerが管理する。
各シーンは独立したupdate(), draw(), handle_event()を持つ。
"""
import pygame


class Scene:
    """シーン基底クラス"""

    def __init__(self, manager: "SceneManager"):
        self.manager = manager

    def handle_event(self, event: pygame.event.Event):
        """イベント処理（サブクラスでオーバーライド）"""
        pass

    def update(self):
        """毎フレーム更新（サブクラスでオーバーライド）"""
        pass

    def draw(self, surface: pygame.Surface):
        """描画（サブクラスでオーバーライド）"""
        pass

    def on_enter(self):
        """シーンがアクティブになった時に呼ばれる"""
        pass

    def on_exit(self):
        """シーンが非アクティブになった時に呼ばれる"""
        pass


class SceneManager:
    """画面遷移を管理するクラス"""

    def __init__(self):
        self._scenes: list[Scene] = []
        self.running = True

    @property
    def current_scene(self) -> Scene | None:
        if self._scenes:
            return self._scenes[-1]
        return None

    def push(self, scene: Scene):
        """シーンをスタックに積む（オーバーレイ的に表示）"""
        if self._scenes:
            self._scenes[-1].on_exit()
        self._scenes.append(scene)
        scene.on_enter()

    def pop(self):
        """現在のシーンをスタックから取り除く"""
        if self._scenes:
            self._scenes[-1].on_exit()
            self._scenes.pop()
            if self._scenes:
                self._scenes[-1].on_enter()

    def change(self, scene: Scene):
        """現在のシーンを置き換える（スタックは維持しない）"""
        if self._scenes:
            self._scenes[-1].on_exit()
            self._scenes.pop()
        self._scenes.append(scene)
        scene.on_enter()

    def clear_and_set(self, scene: Scene):
        """全シーンをクリアして新しいシーンをセットする"""
        while self._scenes:
            self._scenes[-1].on_exit()
            self._scenes.pop()
        self._scenes.append(scene)
        scene.on_enter()

    def quit(self):
        """ゲームを終了する"""
        self.running = False
