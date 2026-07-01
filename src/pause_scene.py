"""
ポーズ画面シーン
ESCキーで開閉。ゲーム時間を停止する。
続ける/ホームに戻る/設定ボタン。
"""
import pygame
from scene_manager import Scene, SceneManager
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CENTER_X, COLOR_BLACK
)

# サイバー風カラー
COLOR_CYBER_GREEN = (0, 255, 100)
COLOR_CYBER_DIM = (0, 150, 60)
COLOR_CYBER_BLUE = (80, 200, 255)


class PauseScene(Scene):
    """ポーズ画面シーン"""

    def __init__(self, manager: SceneManager):
        super().__init__(manager)
        pygame.font.init()

        self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 26, bold=True)

        from home_scene import Button
        btn_y = SCREEN_HEIGHT // 2 - 10
        self.btn_resume = Button(CENTER_X, btn_y, 260, 48,
                                 "RESUME", self.font_button,
                                 COLOR_CYBER_GREEN, COLOR_CYBER_BLUE)
        self.btn_home = Button(CENTER_X, btn_y + 65, 260, 48,
                               "HOME", self.font_button,
                               COLOR_CYBER_DIM, COLOR_CYBER_BLUE)
        self.btn_settings = Button(CENTER_X, btn_y + 130, 260, 48,
                                   "SETTINGS", self.font_button,
                                   COLOR_CYBER_DIM, COLOR_CYBER_BLUE)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ポーズ解除
                self.manager.pop()
                return

        if self.btn_resume.is_clicked(event):
            self.manager.pop()

        elif self.btn_home.is_clicked(event):
            from home_scene import HomeScene
            from sound_manager import SoundManager
            SoundManager().stop_bgm()
            self.manager.clear_and_set(HomeScene(self.manager))

        elif self.btn_settings.is_clicked(event):
            from settings_scene import SettingsScene
            self.manager.push(SettingsScene(self.manager))

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_resume.check_hover(mouse_pos)
        self.btn_home.check_hover(mouse_pos)
        self.btn_settings.check_hover(mouse_pos)

    def draw(self, surface: pygame.Surface):
        # 半透明黒オーバーレイ（仕様: RGBA(0,0,0,160)）
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # PAUSED テキスト
        title_surf = self.font_title.render("PAUSED", True, COLOR_CYBER_GREEN)
        title_rect = title_surf.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 - 120))
        surface.blit(title_surf, title_rect)

        # 区切り線
        pygame.draw.line(surface, COLOR_CYBER_DIM,
                         (CENTER_X - 140, SCREEN_HEIGHT // 2 - 75),
                         (CENTER_X + 140, SCREEN_HEIGHT // 2 - 75), 1)

        # ボタン
        self.btn_resume.draw(surface)
        self.btn_home.draw(surface)
        self.btn_settings.draw(surface)
