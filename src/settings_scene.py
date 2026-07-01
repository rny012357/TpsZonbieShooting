"""
設定画面シーン
音量スライダー（全体/BGM/SE）と戻るボタン。
"""
import pygame
from scene_manager import Scene, SceneManager
from settings_manager import SettingsManager
from sound_manager import SoundManager
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CENTER_X, COLOR_BLACK
)

# サイバー風カラー
COLOR_CYBER_GREEN = (0, 255, 100)
COLOR_CYBER_DIM = (0, 150, 60)
COLOR_CYBER_BLUE = (80, 200, 255)
COLOR_CYBER_DARK = (0, 40, 20)


class Slider:
    """横向き音量スライダー"""

    def __init__(self, x: int, y: int, width: int, label: str,
                 font: pygame.font.Font, initial_value: int = 100):
        self.x = x
        self.y = y
        self.width = width
        self.height = 8
        self.label = label
        self.font = font
        self.value = initial_value  # 0〜100
        self.dragging = False
        self.knob_radius = 10

    @property
    def knob_x(self) -> int:
        return self.x + int(self.width * self.value / 100)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理。値が変更された場合Trueを返す。"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ノブまたはバー上をクリック
            bar_rect = pygame.Rect(self.x - 5, self.y - 15,
                                   self.width + 10, 30)
            if bar_rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value(event.pos[0])
                return True

        return False

    def _update_value(self, mouse_x: int):
        """マウスX座標から値を更新する"""
        ratio = (mouse_x - self.x) / self.width
        self.value = max(0, min(100, int(ratio * 100)))

    def draw(self, surface: pygame.Surface):
        """スライダーを描画する"""
        # ラベル
        label_surf = self.font.render(self.label, True, COLOR_CYBER_GREEN)
        surface.blit(label_surf, (self.x, self.y - 30))

        # 値テキスト
        val_surf = self.font.render(f"{self.value}%", True, COLOR_CYBER_DIM)
        val_rect = val_surf.get_rect(right=self.x + self.width, top=self.y - 30)
        surface.blit(val_surf, val_rect)

        # バー背景
        bar_rect = pygame.Rect(self.x, self.y - self.height // 2,
                                self.width, self.height)
        pygame.draw.rect(surface, COLOR_CYBER_DARK, bar_rect, border_radius=4)

        # バー値部分
        filled_width = int(self.width * self.value / 100)
        if filled_width > 0:
            filled_rect = pygame.Rect(self.x, self.y - self.height // 2,
                                       filled_width, self.height)
            pygame.draw.rect(surface, COLOR_CYBER_DIM, filled_rect, border_radius=4)

        # 枠
        pygame.draw.rect(surface, (0, 80, 40), bar_rect, 1, border_radius=4)

        # ノブ
        knob_x = self.knob_x
        pygame.draw.circle(surface, COLOR_CYBER_GREEN, (knob_x, self.y), self.knob_radius)
        pygame.draw.circle(surface, (200, 255, 220), (knob_x, self.y), 4)


class SettingsScene(Scene):
    """設定画面シーン"""

    def __init__(self, manager: SceneManager):
        super().__init__(manager)
        self._settings = SettingsManager()
        self._sound = SoundManager()

        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 20)
        self.font_button = pygame.font.SysFont("Arial", 24, bold=True)

        # スライダー
        slider_x = CENTER_X - 150
        slider_w = 300
        self.slider_master = Slider(slider_x, 250, slider_w, "MASTER VOLUME",
                                     self.font_label, self._settings.master_volume)
        self.slider_bgm = Slider(slider_x, 340, slider_w, "BGM VOLUME",
                                  self.font_label, self._settings.bgm_volume)
        self.slider_se = Slider(slider_x, 430, slider_w, "SE VOLUME",
                                 self.font_label, self._settings.se_volume)

        # 戻るボタン
        from home_scene import Button
        self.btn_back = Button(CENTER_X, SCREEN_HEIGHT - 80, 200, 44,
                               "BACK", self.font_button,
                               COLOR_CYBER_DIM, COLOR_CYBER_BLUE)

    def handle_event(self, event: pygame.event.Event):
        changed = False
        if self.slider_master.handle_event(event):
            self._settings.master_volume = self.slider_master.value
            changed = True
        if self.slider_bgm.handle_event(event):
            self._settings.bgm_volume = self.slider_bgm.value
            changed = True
        if self.slider_se.handle_event(event):
            self._settings.se_volume = self.slider_se.value
            changed = True

        if changed:
            self._sound.update_volumes()

        if self.btn_back.is_clicked(event):
            self.manager.pop()

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.check_hover(mouse_pos)

    def draw(self, surface: pygame.Surface):
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))

        # タイトル
        title_surf = self.font_title.render("SETTINGS", True, COLOR_CYBER_GREEN)
        title_rect = title_surf.get_rect(center=(CENTER_X, 120))
        surface.blit(title_surf, title_rect)

        # 区切り線
        pygame.draw.line(surface, COLOR_CYBER_DIM,
                         (CENTER_X - 180, 160), (CENTER_X + 180, 160), 1)

        # スライダー
        self.slider_master.draw(surface)
        self.slider_bgm.draw(surface)
        self.slider_se.draw(surface)

        # ボタン
        self.btn_back.draw(surface)
