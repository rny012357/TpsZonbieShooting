"""
ホーム画面シーン
ゲーム起動時の最初の画面。タイトル、スタート/終了/設定ボタン。
"""
import pygame
from scene_manager import Scene, SceneManager
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CENTER_X, COLOR_BLACK
)

# サイバー風カラー
COLOR_CYBER_GREEN = (0, 255, 100)
COLOR_CYBER_DIM = (0, 150, 60)
COLOR_CYBER_DARK = (0, 40, 20)
COLOR_CYBER_BLUE = (80, 200, 255)


class Button:
    """サイバー風ボタン"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, font: pygame.font.Font,
                 color=COLOR_CYBER_GREEN, hover_color=COLOR_CYBER_BLUE):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.hovered = False

    def check_hover(self, mouse_pos: tuple[int, int]):
        """マウスがボタン上にあるか判定"""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """クリックされたか判定"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface):
        """ボタンを描画する"""
        current_color = self.hover_color if self.hovered else self.color

        # 背景
        bg_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 120))
        surface.blit(bg_surf, self.rect.topleft)

        # 枠線
        pygame.draw.rect(surface, current_color, self.rect, 2, border_radius=4)

        # グロー
        if self.hovered:
            glow = pygame.Surface((self.rect.width + 8, self.rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*current_color, 30),
                             (0, 0, self.rect.width + 8, self.rect.height + 8),
                             4, border_radius=6)
            surface.blit(glow, (self.rect.x - 4, self.rect.y - 4))

        # テキスト
        text_surf = self.font.render(self.text, True, current_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class HomeScene(Scene):
    """ホーム画面シーン"""

    def __init__(self, manager: SceneManager):
        super().__init__(manager)
        pygame.font.init()

        self.font_title = pygame.font.SysFont("Arial", 56, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 20)
        self.font_button = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)

        # ボタン
        btn_y = SCREEN_HEIGHT // 2 + 80
        self.btn_start = Button(CENTER_X, btn_y, 240, 50,
                                "START", self.font_button)
        self.btn_quit = Button(CENTER_X, btn_y + 70, 240, 50,
                               "QUIT", self.font_button,
                               COLOR_CYBER_DIM, (220, 50, 50))
        self.btn_settings = Button(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 40,
                                   120, 36, "SETTINGS", self.font_small,
                                   COLOR_CYBER_DIM, COLOR_CYBER_BLUE)

        # グリッドアニメーション用
        self.grid_offset = 0.0

    def handle_event(self, event: pygame.event.Event):
        if self.btn_start.is_clicked(event):
            from game_scene import GameScene
            self.manager.change(GameScene(self.manager))

        elif self.btn_quit.is_clicked(event):
            self.manager.quit()

        elif self.btn_settings.is_clicked(event):
            from settings_scene import SettingsScene
            self.manager.push(SettingsScene(self.manager))

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_start.check_hover(mouse_pos)
        self.btn_quit.check_hover(mouse_pos)
        self.btn_settings.check_hover(mouse_pos)
        self.grid_offset += 0.5

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BLACK)

        # 背景グリッドアニメーション
        self._draw_background_grid(surface)

        # タイトル
        title_text = self.font_title.render("Cyber Zombie Shooting Game",
                                            True, COLOR_CYBER_GREEN)
        title_rect = title_text.get_rect(center=(CENTER_X, 180))
        surface.blit(title_text, title_rect)

        # タイトルグロー
        glow_surf = self.font_title.render("Cyber Zombie Shooting Game",
                                           True, COLOR_CYBER_DIM)
        glow_surf.set_alpha(60)
        glow_rect = glow_surf.get_rect(center=(CENTER_X + 2, 182))
        surface.blit(glow_surf, glow_rect)

        # サブタイトル
        sub_text = self.font_subtitle.render("CYBER ARENA", True, COLOR_CYBER_DIM)
        sub_rect = sub_text.get_rect(center=(CENTER_X, 240))
        surface.blit(sub_text, sub_rect)

        # ボタン
        self.btn_start.draw(surface)
        self.btn_quit.draw(surface)
        self.btn_settings.draw(surface)

    def _draw_background_grid(self, surface: pygame.Surface):
        """背景のアニメーショングリッド"""
        grid_color = (0, 40, 20)
        spacing = 60

        # 縦線
        for x in range(0, SCREEN_WIDTH + spacing, spacing):
            pygame.draw.line(surface, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)

        # 横線（スクロール）
        offset = int(self.grid_offset) % spacing
        for y in range(-spacing + offset, SCREEN_HEIGHT + spacing, spacing):
            pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
