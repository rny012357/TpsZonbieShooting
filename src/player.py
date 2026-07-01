"""
プレイヤークラス
HP管理、移動、射撃、リロード、ステータス管理を担当する。
バフによるステータス変動に対応。
character.pngスプライトを使用して描画。
"""
import pygame
import random
from game_object import GameObject
from config import (
    PLAYER_HP, PLAYER_SPEED, PLAYER_FORWARD_SPEED,
    COLOR_PLAYER_BODY, COLOR_PLAYER_GUN, COLOR_WHITE,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_SCREEN_X, PLAYER_SCREEN_Y,
    BASE_FIRE_INTERVAL,
    PLAYER_INIT_ATTACK, PLAYER_INIT_CRIT_RATE, PLAYER_INIT_CRIT_DMG,
    PLAYER_INIT_RELOAD_TIME, PLAYER_INIT_FIRE_SPEED, PLAYER_INIT_MAGAZINE
)
from asset_manager import AssetManager


class Player(GameObject):
    """プレイヤークラス"""

    def __init__(self):
        super().__init__(x=0, z=0)
        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP

        # === ステータス（バフで変動する） ===
        self.attack = PLAYER_INIT_ATTACK
        self.attack_mult = 1.0
        self.crit_rate = PLAYER_INIT_CRIT_RATE
        self.crit_dmg = PLAYER_INIT_CRIT_DMG
        self.reload_time = PLAYER_INIT_RELOAD_TIME
        self.fire_speed = PLAYER_INIT_FIRE_SPEED
        self.magazine_size = PLAYER_INIT_MAGAZINE

        # 射撃
        self.last_shot_time = -self.get_fire_interval()

        # リロードシステム
        self.ammo = self.magazine_size
        self.max_ammo = self.magazine_size
        self.reloading = False
        self.reload_start_time = 0

        # スプライト読み込み
        self._sprite = None
        self._load_sprite()

    def _load_sprite(self):
        """AssetManagerからスプライトを読み込む"""
        assets = AssetManager()
        img = assets.get_image("character")
        if img:
            # スプライトをゲームに適したサイズにスケーリング
            # 元画像のアスペクト比を維持
            orig_w, orig_h = img.get_size()
            target_h = 120  # 画面下部に表示するサイズ
            scale_ratio = target_h / orig_h
            target_w = int(orig_w * scale_ratio)
            self._sprite = pygame.transform.scale(img, (target_w, target_h))

    def get_fire_interval(self) -> int:
        """攻撃速度を考慮した連射間隔（ミリ秒）"""
        return max(50, int(BASE_FIRE_INTERVAL * (100 / max(50, self.fire_speed))))

    def get_effective_attack(self) -> int:
        """実効攻撃力を計算する（固定値 × 倍率）"""
        return int(self.attack * self.attack_mult)

    def calc_damage(self) -> tuple[int, bool]:
        """ダメージ計算（クリティカル判定込み）"""
        base_dmg = self.get_effective_attack()
        is_crit = random.random() < self.crit_rate
        if is_crit:
            dmg = int(base_dmg * (1.0 + self.crit_dmg))
        else:
            dmg = base_dmg
        return dmg, is_crit

    def apply_buff(self, buff_type: str, value):
        """バフを適用する"""
        if buff_type == "attack":
            self.attack += value
        elif buff_type == "attack_mult":
            self.attack_mult += value
        elif buff_type == "crit_rate":
            self.crit_rate = min(1.0, self.crit_rate + value)
        elif buff_type == "crit_dmg":
            self.crit_dmg += value
        elif buff_type == "reload_time":
            self.reload_time = max(500, self.reload_time + value)
        elif buff_type == "fire_speed":
            self.fire_speed += value
        elif buff_type == "magazine":
            self.magazine_size += value
            self.max_ammo = self.magazine_size
            self.ammo = min(self.ammo + value, self.max_ammo)
        elif buff_type == "hp_heal":
            self.hp = min(self.max_hp, self.hp + value)

    def move(self, keys):
        """キー入力に応じてワールド内を移動する"""
        if keys[pygame.K_a]:
            self.x -= PLAYER_SPEED
        if keys[pygame.K_d]:
            self.x += PLAYER_SPEED
        if keys[pygame.K_w]:
            self.z += PLAYER_FORWARD_SPEED

    def can_shoot(self, current_time: int) -> bool:
        """射撃可能かどうかを判定する"""
        if self.reloading:
            return False
        if self.ammo <= 0:
            return False
        return current_time - self.last_shot_time >= self.get_fire_interval()

    def shoot(self, current_time: int):
        """射撃時刻を記録し、弾を消費する"""
        self.last_shot_time = current_time
        self.ammo -= 1
        if self.ammo <= 0:
            self.start_reload(current_time)

    def start_reload(self, current_time: int):
        """リロードを開始する"""
        if self.reloading or self.ammo >= self.max_ammo:
            return
        self.reloading = True
        self.reload_start_time = current_time

    def update_reload(self, current_time: int):
        """リロード状態を更新する"""
        if self.reloading:
            if current_time - self.reload_start_time >= self.reload_time:
                self.ammo = self.max_ammo
                self.reloading = False

    def get_reload_progress(self, current_time: int) -> float:
        """リロード進捗を取得する（0.0〜1.0）"""
        if not self.reloading:
            return 1.0
        elapsed = current_time - self.reload_start_time
        return min(1.0, elapsed / self.reload_time)

    def take_damage(self, damage: int):
        """ダメージを受ける"""
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def is_dead(self) -> bool:
        """死亡判定"""
        return self.hp <= 0

    def draw(self, surface: pygame.Surface, player_x: float = None, player_z: float = None):
        """プレイヤーを画面下部固定位置に描画する（character.png使用）"""
        sx = PLAYER_SCREEN_X

        if self._sprite:
            # スプライト描画
            sprite_rect = self._sprite.get_rect()
            sprite_rect.centerx = sx
            sprite_rect.bottom = SCREEN_HEIGHT - 10
            surface.blit(self._sprite, sprite_rect)
        else:
            # フォールバック: 矩形シルエット（スプライトが読み込めない場合）
            body_width = 60
            body_height = 80
            body_rect = pygame.Rect(
                sx - body_width // 2,
                SCREEN_HEIGHT - body_height - 10,
                body_width, body_height
            )
            pygame.draw.rect(surface, COLOR_PLAYER_BODY, body_rect, border_radius=8)

            gun_width = 12
            gun_height = 50
            gun_rect = pygame.Rect(
                sx - gun_width // 2,
                SCREEN_HEIGHT - body_height - 10 - gun_height + 20,
                gun_width, gun_height
            )
            pygame.draw.rect(surface, COLOR_PLAYER_GUN, gun_rect, border_radius=3)

            muzzle_y = SCREEN_HEIGHT - body_height - 10 - gun_height + 20
            pygame.draw.circle(surface, COLOR_WHITE, (sx, muzzle_y), 3)

    def get_muzzle_position(self) -> tuple[int, int]:
        """銃口の画面座標を返す"""
        sx = PLAYER_SCREEN_X
        if self._sprite:
            # スプライトの上端付近（銃口位置）
            sprite_h = self._sprite.get_height()
            muzzle_y = SCREEN_HEIGHT - 10 - sprite_h + 10
        else:
            body_height = 80
            gun_height = 50
            muzzle_y = SCREEN_HEIGHT - body_height - 10 - gun_height + 20
        return sx, muzzle_y
