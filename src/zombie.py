"""
ゾンビクラス
エリア内にスポーンし、待機状態から追跡状態に遷移する。
エリア番号に応じてHP・攻撃力がスケーリングされる。
"""
import pygame
import random
from game_object import GameObject
from config import (
    ZOMBIE_SPEED_MIN, ZOMBIE_SPEED_MAX,
    ZOMBIE_ATTACK_DISTANCE, ZOMBIE_BASE_ATTACK_DAMAGE,
    ZOMBIE_ATTACK_COOLDOWN, ZOMBIE_ACTIVATION_RANGE,
    COLOR_ZOMBIE_BODY, COLOR_ZOMBIE_HEAD, COLOR_RED,
    WORLD_X_MIN, WORLD_X_MAX
)


class Zombie(GameObject):
    """ゾンビクラス"""

    # AI状態
    STATE_IDLE = "idle"        # 待機（スポーン時のデフォルト）
    STATE_TRACKING = "tracking"  # プレイヤー追跡中

    def __init__(self, x: float = None, z: float = None, hp: int = 1,
                 attack_damage: int = None, idle: bool = True):
        if x is None:
            x = random.uniform(WORLD_X_MIN + 30, WORLD_X_MAX - 30)
        if z is None:
            z = 0
        super().__init__(x, z)
        self.speed = random.uniform(ZOMBIE_SPEED_MIN, ZOMBIE_SPEED_MAX)
        self.hp = hp
        self.max_hp = hp
        self.attack_damage = attack_damage if attack_damage else ZOMBIE_BASE_ATTACK_DAMAGE
        self.last_attack_time = 0

        # AI状態
        self.state = self.STATE_IDLE if idle else self.STATE_TRACKING
        self.activation_range = ZOMBIE_ACTIVATION_RANGE

        # 色バリエーション
        g_variation = random.randint(-20, 20)
        self.body_color = (
            COLOR_ZOMBIE_BODY[0] + random.randint(-10, 10),
            max(80, min(220, COLOR_ZOMBIE_BODY[1] + g_variation)),
            COLOR_ZOMBIE_BODY[2] + random.randint(-10, 10)
        )
        self.head_color = (
            COLOR_ZOMBIE_HEAD[0] + random.randint(-10, 10),
            max(100, min(230, COLOR_ZOMBIE_HEAD[1] + g_variation)),
            COLOR_ZOMBIE_HEAD[2] + random.randint(-10, 10)
        )
        # 歩行揺れ
        self.sway_offset = random.uniform(0, 6.28)
        self.sway_speed = random.uniform(0.02, 0.06)

    def check_activation(self, player_x: float, player_z: float):
        """プレイヤーが一定距離以内に入ったら追跡開始する"""
        if self.state != self.STATE_IDLE:
            return
        dx = self.x - player_x
        dz = self.z - player_z
        dist = (dx * dx + dz * dz) ** 0.5
        if dist <= self.activation_range:
            self.state = self.STATE_TRACKING

    def activate(self):
        """即座に追跡状態にする（被弾時）"""
        self.state = self.STATE_TRACKING

    def update(self):
        """毎フレーム更新。追跡中のみ移動する。"""
        if self.state == self.STATE_IDLE:
            # 待機中は微妙に左右に揺れるだけ
            self.sway_offset += self.sway_speed * 0.3
            return

        # 追跡中: プレイヤー方向（手前）に移動
        self.z -= self.speed

        # 左右に少し揺れる（歩行表現）
        self.sway_offset += self.sway_speed
        sway = 0.3 * pygame.math.Vector2(1, 0).rotate(
            self.sway_offset * 57.3
        ).x
        self.x += sway

    def take_hit(self, damage: int = 1) -> bool:
        """被弾処理。撃破された場合Trueを返す。被弾で即追跡開始。"""
        self.activate()  # 被弾で追跡開始
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def can_attack(self, player_z: float, current_time: int) -> bool:
        """攻撃可能かどうかを判定する"""
        if self.state == self.STATE_IDLE:
            return False
        relative_z = self.z - player_z
        return (relative_z <= ZOMBIE_ATTACK_DISTANCE and
                relative_z >= 0 and
                current_time - self.last_attack_time >= ZOMBIE_ATTACK_COOLDOWN)

    def attack(self, player, current_time: int):
        """プレイヤーを攻撃する（エリアに応じた攻撃力）"""
        if self.can_attack(player.z, current_time):
            player.take_damage(self.attack_damage)
            self.last_attack_time = current_time

    def draw(self, surface: pygame.Surface, player_x: float, player_z: float):
        """ゾンビを人型シルエットで描画する"""
        if not self.alive:
            return

        relative_z = self.z - player_z
        if relative_z < 0:
            return

        sx, sy = self.world_to_screen_relative(player_x, player_z)
        scale = self.get_scale_relative(relative_z)

        # 待機中は少し暗く表示
        if self.state == self.STATE_IDLE:
            body_c = tuple(max(30, c - 30) for c in self.body_color)
            head_c = tuple(max(30, c - 30) for c in self.head_color)
        else:
            body_c = self.body_color
            head_c = self.head_color

        # 各パーツのサイズをスケーリング
        body_w = max(4, int(30 * scale))
        body_h = max(6, int(50 * scale))
        head_r = max(3, int(14 * scale))
        arm_w = max(2, int(8 * scale))
        arm_h = max(4, int(35 * scale))
        leg_w = max(2, int(10 * scale))
        leg_h = max(4, int(30 * scale))

        # 足
        leg_offset = max(2, int(8 * scale))
        pygame.draw.rect(surface, body_c, (
            sx - leg_offset - leg_w // 2, sy - leg_h, leg_w, leg_h
        ))
        pygame.draw.rect(surface, body_c, (
            sx + leg_offset - leg_w // 2, sy - leg_h, leg_w, leg_h
        ))

        # 体
        body_rect = pygame.Rect(
            sx - body_w // 2, sy - leg_h - body_h, body_w, body_h
        )
        pygame.draw.rect(surface, body_c, body_rect,
                         border_radius=max(1, int(4 * scale)))

        # 腕
        arm_y = sy - leg_h - body_h + max(2, int(10 * scale))
        pygame.draw.rect(surface, body_c, (
            sx - body_w // 2 - arm_w, arm_y, arm_w, arm_h
        ))
        pygame.draw.rect(surface, body_c, (
            sx + body_w // 2, arm_y, arm_w, arm_h
        ))

        # 頭
        head_y = sy - leg_h - body_h - head_r
        pygame.draw.circle(surface, head_c, (sx, head_y), head_r)

        # 目（追跡中は赤く光る、待機中は暗い）
        if head_r >= 5:
            eye_offset = max(1, int(4 * scale))
            eye_r = max(1, int(2 * scale))
            eye_color = COLOR_RED if self.state == self.STATE_TRACKING else (60, 40, 40)
            pygame.draw.circle(surface, eye_color,
                               (sx - eye_offset, head_y - max(1, int(2 * scale))), eye_r)
            pygame.draw.circle(surface, eye_color,
                               (sx + eye_offset, head_y - max(1, int(2 * scale))), eye_r)

        # HPバー（HP > 1 のゾンビのみ）
        if self.max_hp > 1 and self.hp > 0:
            bar_w = max(8, int(40 * scale))
            bar_h = max(2, int(4 * scale))
            bar_x = sx - bar_w // 2
            bar_y = head_y - head_r - max(3, int(6 * scale))
            pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
            hp_ratio = self.hp / self.max_hp
            hp_w = int(bar_w * hp_ratio)
            if hp_w > 0:
                hp_color = COLOR_RED if hp_ratio < 0.3 else (200, 200, 50) if hp_ratio < 0.6 else (50, 200, 50)
                pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_w, bar_h))
