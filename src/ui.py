"""
UI描画クラス
HPバー、残弾数、スコア、ステータスUI、エリアUI、
AREA CLEAR表示、ゲームオーバー表示を担当する。
サイバー空間風デザイン。
"""
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CENTER_X,
    COLOR_WHITE, COLOR_RED, COLOR_HP_BG, COLOR_HP_BAR, COLOR_HP_BAR_HIGH,
    COLOR_BLACK, COLOR_YELLOW, COLOR_GRAY
)

# サイバー風UIカラー
COLOR_CYBER_GREEN = (0, 255, 100)
COLOR_CYBER_BLUE = (80, 200, 255)
COLOR_CYBER_DIM = (0, 150, 60)
COLOR_CYBER_DARK = (0, 60, 30)


class UI:
    """UI描画クラス"""

    def __init__(self):
        pygame.font.init()
        self.font_large = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
        self.font_area = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_stat = pygame.font.SysFont("Courier", 14)
        self.font_area_map = pygame.font.SysFont("Arial", 18, bold=True)

    def draw_hp_bar(self, surface: pygame.Surface, current_hp: int, max_hp: int):
        """HPバーを左下に描画する"""
        bar_x = 30
        bar_y = SCREEN_HEIGHT - 50
        bar_width = 200
        bar_height = 20

        hp_ratio = max(0, current_hp / max_hp)

        if hp_ratio > 0.5:
            bar_color = COLOR_HP_BAR_HIGH
        elif hp_ratio > 0.25:
            bar_color = COLOR_YELLOW
        else:
            bar_color = COLOR_HP_BAR

        bg_rect = pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4)
        pygame.draw.rect(surface, COLOR_HP_BG, bg_rect, border_radius=4)

        hp_width = int(bar_width * hp_ratio)
        if hp_width > 0:
            hp_rect = pygame.Rect(bar_x, bar_y, hp_width, bar_height)
            pygame.draw.rect(surface, bar_color, hp_rect, border_radius=3)

        pygame.draw.rect(surface, COLOR_CYBER_DIM,
                         pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4),
                         2, border_radius=4)

        hp_text = self.font_tiny.render(f"HP {current_hp}/{max_hp}", True, COLOR_CYBER_GREEN)
        surface.blit(hp_text, (bar_x + 5, bar_y + 2))

    def draw_ammo(self, surface: pygame.Surface, ammo: int, max_ammo: int,
                  reloading: bool, reload_progress: float):
        """残弾数とリロード状態を描画する"""
        bar_x = 30
        bar_y = SCREEN_HEIGHT - 80

        if reloading:
            bar_width = 150
            bar_height = 14
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(surface, (10, 30, 20), bg_rect, border_radius=3)

            progress_width = int(bar_width * reload_progress)
            if progress_width > 0:
                progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
                pygame.draw.rect(surface, COLOR_CYBER_BLUE, progress_rect, border_radius=3)

            pygame.draw.rect(surface, COLOR_CYBER_DIM, bg_rect, 1, border_radius=3)

            reload_text = self.font_tiny.render("RELOADING...", True, COLOR_CYBER_BLUE)
            surface.blit(reload_text, (bar_x + bar_width + 10, bar_y - 1))
        else:
            if ammo <= 3:
                ammo_color = COLOR_RED
            elif ammo <= 5:
                ammo_color = COLOR_YELLOW
            else:
                ammo_color = COLOR_CYBER_GREEN

            ammo_text = self.font_small.render(f"AMMO: {ammo}/{max_ammo}", True, ammo_color)
            surface.blit(ammo_text, (bar_x, bar_y))

    def draw_score(self, surface: pygame.Surface, score: int):
        """スコアを右上に描画する"""
        score_label = self.font_tiny.render("SCORE", True, COLOR_CYBER_DIM)
        score_rect = score_label.get_rect(topright=(SCREEN_WIDTH - 30, 15))
        surface.blit(score_label, score_rect)

        score_text = self.font_medium.render(f"{score:,}", True, COLOR_CYBER_GREEN)
        score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 30, 32))
        surface.blit(score_text, score_rect)

    def draw_stats(self, surface: pygame.Surface, player):
        """ステータスUIを左側に縦表示する"""
        stat_x = 30
        stat_y = 20
        line_height = 18

        stats = [
            ("ATK", f"{player.get_effective_attack()}"),
            ("CRIT", f"{player.crit_rate * 100:.0f}%"),
            ("CRIT DMG", f"{player.crit_dmg * 100:.0f}%"),
            ("RELOAD", f"{player.reload_time / 1000:.1f}s"),
            ("FIRE SPD", f"{player.fire_speed}"),
            ("MAGAZINE", f"{player.magazine_size}"),
        ]

        # 背景パネル
        panel_w = 160
        panel_h = len(stats) * line_height + 10
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 80))
        pygame.draw.rect(panel_surf, (*COLOR_CYBER_DIM, 100),
                         (0, 0, panel_w, panel_h), 1)
        surface.blit(panel_surf, (stat_x - 5, stat_y - 5))

        for i, (label, value) in enumerate(stats):
            y = stat_y + i * line_height
            label_surf = self.font_stat.render(f"{label:>9s}", True, COLOR_CYBER_DIM)
            value_surf = self.font_stat.render(f" {value}", True, COLOR_CYBER_GREEN)
            surface.blit(label_surf, (stat_x, y))
            surface.blit(value_surf, (stat_x + label_surf.get_width(), y))

    def draw_area_map(self, surface: pygame.Surface, area_manager):
        """エリアUIを右側に縦表示する（下から上へ番号が増える）"""
        map_x = SCREEN_WIDTH - 50
        map_y_bottom = SCREEN_HEIGHT - 120
        item_spacing = 40

        current_num = area_manager.current_area_number

        # 表示するエリア範囲（現在エリアの前後を表示）
        display_start = max(1, current_num - 1)
        display_end = current_num + 3

        for area_num in range(display_start, display_end + 1):
            # 下から上に配置（area_numが大きいほど上）
            idx = area_num - display_start
            y = map_y_bottom - idx * item_spacing

            if y < 100:
                break

            is_current = (area_num == current_num)
            is_cleared = any(a.area_number == area_num and a.cleared
                            for a in area_manager.areas)

            # 丸（ノード）
            if is_current:
                # 現在エリア: 発光
                pygame.draw.circle(surface, COLOR_CYBER_GREEN, (map_x, y), 12)
                pygame.draw.circle(surface, COLOR_WHITE, (map_x, y), 8)
            elif is_cleared:
                pygame.draw.circle(surface, COLOR_CYBER_DIM, (map_x, y), 10)
                pygame.draw.circle(surface, (0, 80, 40), (map_x, y), 7)
            else:
                pygame.draw.circle(surface, (40, 40, 40), (map_x, y), 10)
                pygame.draw.circle(surface, (20, 20, 20), (map_x, y), 7)

            # エリア番号
            num_color = COLOR_WHITE if is_current else COLOR_CYBER_DIM if is_cleared else COLOR_GRAY
            num_text = self.font_area_map.render(str(area_num), True, num_color)
            num_rect = num_text.get_rect(center=(map_x, y))
            surface.blit(num_text, num_rect)

            # 接続線（次のノードへ）
            if idx > 0:
                next_y = map_y_bottom - (idx - 1) * item_spacing
                line_color = COLOR_CYBER_DIM if is_cleared else (30, 30, 30)
                pygame.draw.line(surface, line_color,
                                 (map_x, y + 12), (map_x, next_y - 12), 1)

    def draw_area_clear(self, surface: pygame.Surface, area_number: int,
                        elapsed_ms: int, duration_ms: int):
        """AREA CLEAR! を画面上部中央に表示する"""
        ratio = elapsed_ms / duration_ms
        if ratio < 0.15:
            alpha = int(255 * (ratio / 0.15))
        elif ratio > 0.7:
            alpha = int(255 * ((1.0 - ratio) / 0.3))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        text = self.font_area.render(f"AREA {area_number} CLEAR!", True, COLOR_CYBER_GREEN)
        text.set_alpha(alpha)
        text_rect = text.get_rect(center=(CENTER_X, 120))
        surface.blit(text, text_rect)

    def draw_game_over(self, surface: pygame.Surface, kill_count: int,
                       area_number: int, score: int):
        """ゲームオーバー画面を描画する"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # SYSTEM FAILURE
        go_text = self.font_large.render("SYSTEM FAILURE", True, COLOR_RED)
        go_rect = go_text.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 - 60))
        surface.blit(go_text, go_rect)

        # Area到達
        area_text = self.font_medium.render(f"Area: {area_number}", True, COLOR_CYBER_BLUE)
        area_rect = area_text.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 - 5))
        surface.blit(area_text, area_rect)

        # 撃破数
        kills_text = self.font_medium.render(f"Kills: {kill_count}", True, COLOR_CYBER_GREEN)
        kills_rect = kills_text.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 + 35))
        surface.blit(kills_text, kills_rect)

        # スコア
        score_text = self.font_medium.render(f"Score: {score:,}", True, COLOR_YELLOW)
        score_rect = score_text.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 + 75))
        surface.blit(score_text, score_rect)

        # リスタート
        restart_text = self.font_small.render(
            "Press R to Restart / ESC to Quit", True, COLOR_CYBER_DIM
        )
        restart_rect = restart_text.get_rect(center=(CENTER_X, SCREEN_HEIGHT // 2 + 120))
        surface.blit(restart_text, restart_rect)
