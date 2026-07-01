"""
エリアシステム
Area, AreaGate, AreaManagerを提供する。
Waveシステムに代わるゲーム進行の中核。
各エリアは乱数シードを持ち、ゾンビ配置を再現可能にする。
"""
import random
import math
import pygame
from config import (
    AREA_LENGTH, AREA_GATE_OFFSET,
    AREA_BASE_ZOMBIE_COUNT, AREA_ZOMBIE_INCREMENT,
    AREA_ZOMBIE_HP_BASE, AREA_ZOMBIE_HP_INCREMENT,
    AREA_ZOMBIE_DMG_INCREMENT, AREA_CLEAR_DISPLAY_TIME,
    ZOMBIE_BASE_ATTACK_DAMAGE,
    ZOMBIE_SPEED_MIN, ZOMBIE_SPEED_MAX,
    WORLD_X_MIN, WORLD_X_MAX,
    COLOR_GATE_BORDER, COLOR_GATE_FILL,
    SCALE_FACTOR, MIN_SCALE,
    PLAYER_SCREEN_X, GROUND_Y, HORIZON_Y,
    SCREEN_WIDTH
)
from zombie import Zombie
from game_object import GameObject


class AreaGate:
    """エリアゲート: エリアの入口を示す透明な平面オブジェクト（演出専用）"""

    def __init__(self, area_number: int, z_position: float):
        self.area_number = area_number
        self.z = z_position
        self.visible = True

    def draw(self, surface: pygame.Surface, player_x: float, player_z: float):
        """ゲートを半透明の平面として描画する（サイバー風）"""
        if not self.visible:
            return

        relative_z = self.z - player_z
        if relative_z < -50 or relative_z > 1500:
            return

        # z座標が手前でも奥でも描画（通過中も見える）
        abs_rel_z = max(1, abs(relative_z))
        scale = 1.0 / (1.0 + abs_rel_z * SCALE_FACTOR)
        scale = max(scale, MIN_SCALE)

        y = GameObject.relative_z_to_screen_y(abs_rel_z)
        if relative_z < 0:
            # 手前にある場合、画面下部付近に描画
            y = min(GROUND_Y + 20, int(GROUND_Y + abs(relative_z) * 0.5))

        # ゲートの幅と高さ
        gate_width = int((WORLD_X_MAX - WORLD_X_MIN) * scale)
        gate_height = max(10, int(150 * scale))

        # ゲート中心のX座標
        center_x = int(PLAYER_SCREEN_X + (0 - player_x) * scale)

        # 半透明の矩形
        gate_surf = pygame.Surface((gate_width, gate_height), pygame.SRCALPHA)
        # 内部: 薄い色
        gate_surf.fill((*COLOR_GATE_FILL, 40))
        # 枠: ネオン発光線
        pygame.draw.rect(gate_surf, (*COLOR_GATE_BORDER, 120),
                         (0, 0, gate_width, gate_height), 2)

        # エリア番号テキスト
        font = pygame.font.SysFont("Arial", max(12, int(28 * scale)), bold=True)
        text = font.render(f"Area {self.area_number}", True,
                           (*COLOR_GATE_BORDER, 200))
        text_rect = text.get_rect(center=(gate_width // 2, gate_height // 2))
        gate_surf.blit(text, text_rect)

        # 描画位置
        draw_x = center_x - gate_width // 2
        draw_y = y - gate_height

        surface.blit(gate_surf, (draw_x, draw_y))

        # グロー効果（枠の外側）
        glow_surf = pygame.Surface((gate_width + 8, gate_height + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*COLOR_GATE_BORDER, 30),
                         (0, 0, gate_width + 8, gate_height + 8), 4)
        surface.blit(glow_surf, (draw_x - 4, draw_y - 4))


class Area:
    """1つのエリアを表す"""

    def __init__(self, area_number: int):
        self.area_number = area_number
        self.seed = hash(area_number) & 0xFFFFFFFF

        # エリアのz座標範囲
        self.z_start = (area_number - 1) * AREA_LENGTH
        self.z_end = area_number * AREA_LENGTH

        # ゲート
        self.gate = AreaGate(area_number, self.z_start + AREA_GATE_OFFSET)

        # ゾンビ
        self.zombies: list[Zombie] = []
        self.cleared = False
        self.clear_time = 0  # クリア時刻

        # ゾンビを配置
        self._spawn_zombies()

    def _spawn_zombies(self):
        """エリア内にゾンビをランダム配置する（乱数シード使用）"""
        rng = random.Random(self.seed)

        zombie_count = AREA_BASE_ZOMBIE_COUNT + (self.area_number - 1) * AREA_ZOMBIE_INCREMENT
        zombie_hp = AREA_ZOMBIE_HP_BASE + (self.area_number - 1) * AREA_ZOMBIE_HP_INCREMENT
        zombie_dmg = ZOMBIE_BASE_ATTACK_DAMAGE + (self.area_number - 1) * AREA_ZOMBIE_DMG_INCREMENT

        # ゾンビをエリア内のランダム座標に配置
        # ゲートより少し奥から配置開始
        spawn_z_min = self.z_start + AREA_GATE_OFFSET + 100
        spawn_z_max = self.z_end - 100

        for _ in range(zombie_count):
            x = rng.uniform(WORLD_X_MIN + 30, WORLD_X_MAX - 30)
            z = rng.uniform(spawn_z_min, spawn_z_max)
            zombie = Zombie(x=x, z=z, hp=zombie_hp,
                            attack_damage=zombie_dmg, idle=True)
            zombie.speed = rng.uniform(ZOMBIE_SPEED_MIN, ZOMBIE_SPEED_MAX)
            self.zombies.append(zombie)

    def get_remaining_zombies(self) -> int:
        """生存中のゾンビ数を返す"""
        return sum(1 for z in self.zombies if z.alive)

    def check_cleared(self) -> bool:
        """エリア制圧判定"""
        if self.cleared:
            return True
        if self.get_remaining_zombies() == 0:
            self.cleared = True
            self.clear_time = pygame.time.get_ticks()
            return True
        return False


class AreaManager:
    """エリアの生成・管理・遷移を統括する"""

    def __init__(self):
        self.areas: list[Area] = []
        self.current_area_index = 0
        self.clear_display_active = False
        self.clear_display_area = 0
        self.clear_display_start = 0

        # 最初の2エリアを生成
        self.areas.append(Area(1))
        self.areas.append(Area(2))

    @property
    def current_area(self) -> Area:
        return self.areas[self.current_area_index]

    @property
    def current_area_number(self) -> int:
        return self.current_area.area_number

    def get_all_active_zombies(self) -> list[Zombie]:
        """全エリアのアクティブなゾンビを返す"""
        zombies = []
        for area in self.areas:
            zombies.extend([z for z in area.zombies if z.alive])
        return zombies

    def update(self, player_z: float):
        """エリア状態を更新する"""
        current_time = pygame.time.get_ticks()

        # 現在のエリアの制圧判定
        current = self.current_area
        if not current.cleared and current.check_cleared():
            self.clear_display_active = True
            self.clear_display_area = current.area_number
            self.clear_display_start = current_time

        # AREA CLEAR表示の終了判定
        if self.clear_display_active:
            if current_time - self.clear_display_start >= AREA_CLEAR_DISPLAY_TIME:
                self.clear_display_active = False

        # プレイヤーが次エリアに入ったら現在エリアを更新
        if self.current_area_index < len(self.areas) - 1:
            next_area = self.areas[self.current_area_index + 1]
            if player_z >= next_area.z_start:
                self.current_area_index += 1

        # 先のエリアを先読み生成（現在エリア+2まで）
        max_needed = self.current_area_index + 3
        while len(self.areas) < max_needed:
            next_num = len(self.areas) + 1
            self.areas.append(Area(next_num))

    def get_visible_gates(self, player_z: float) -> list[AreaGate]:
        """描画範囲内のゲートを返す"""
        gates = []
        for area in self.areas:
            gate_rel_z = area.gate.z - player_z
            if -100 < gate_rel_z < 1500:
                gates.append(area.gate)
        return gates

    def get_area_at_z(self, z: float) -> Area | None:
        """指定z座標にあるエリアを返す"""
        for area in self.areas:
            if area.z_start <= z < area.z_end:
                return area
        return None
