"""
エフェクトシステム
パーティクル、マズルフラッシュ、画面シェイク、ダメージ数値表示を管理する。
撃破エフェクトは「0」「1」のみで構成されるサイバー風パーティクル。
"""
import pygame
import random
import math
from config import (
    PARTICLE_LIFETIME, PARTICLE_COUNT_KILL,
    MUZZLE_FLASH_DURATION,
    SCREEN_SHAKE_DURATION, SCREEN_SHAKE_INTENSITY,
    DAMAGE_TEXT_LIFETIME,
    COLOR_BLOOD, COLOR_MUZZLE_FLASH, COLOR_YELLOW,
    CENTER_X, GROUND_Y, HORIZON_Y, PERSPECTIVE_DEPTH,
    SCALE_FACTOR, MIN_SCALE,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_SCREEN_X
)
from game_object import GameObject


class BinaryParticle:
    """0/1のバイナリ文字パーティクル（サイバー風撃破エフェクト）"""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 char: str, color: tuple, size: int, lifetime: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.char = char  # "0" or "1"
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.spawn_time = pygame.time.get_ticks()
        self.alive = True
        self.font = pygame.font.SysFont("Courier", max(10, size), bold=True)

    def update(self):
        """パーティクルを更新する"""
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.alive = False
            return
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12  # 重力

    def draw(self, surface: pygame.Surface):
        """0/1文字を描画する"""
        if not self.alive:
            return
        elapsed = pygame.time.get_ticks() - self.spawn_time
        life_ratio = 1.0 - (elapsed / self.max_lifetime)
        alpha = max(0, int(255 * life_ratio))

        text_surf = self.font.render(self.char, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (int(self.x), int(self.y)))


class DamageText:
    """ダメージ数値表示（放物線、重力、透明化）"""

    def __init__(self, x: float, y: float, damage: int, is_crit: bool = False):
        self.x = x
        self.y = y
        self.damage = damage
        self.is_crit = is_crit
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-5, -3)  # 上方向に飛ぶ
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = DAMAGE_TEXT_LIFETIME
        self.alive = True

        if is_crit:
            self.color = (255, 220, 50)  # 金色
            self.font_size = 24
        else:
            self.color = (255, 255, 255)  # 白
            self.font_size = 18

        self.font = pygame.font.SysFont("Arial", self.font_size, bold=True)

    def update(self):
        """更新（放物線+重力）"""
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.alive = False
            return
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # 重力

    def draw(self, surface: pygame.Surface):
        """ダメージ数値を描画する"""
        if not self.alive:
            return
        elapsed = pygame.time.get_ticks() - self.spawn_time
        life_ratio = 1.0 - (elapsed / self.lifetime)
        alpha = max(0, int(255 * life_ratio))

        text = f"{self.damage}"
        if self.is_crit:
            text = f"CRIT! {self.damage}"

        text_surf = self.font.render(text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (int(self.x), int(self.y)))


class EffectManager:
    """エフェクト管理クラス"""

    def __init__(self):
        self.particles: list[BinaryParticle] = []
        self.damage_texts: list[DamageText] = []
        self.muzzle_flash_time = 0
        self.muzzle_flash_active = False
        self.muzzle_flash_pos = (0, 0)
        self.shake_time = 0
        self.shake_active = False

    def spawn_kill_particles(self, world_x: float, world_z: float,
                              player_x: float, player_z: float):
        """ゾンビ撃破時の0/1パーティクルを生成する"""
        relative_x = world_x - player_x
        relative_z = world_z - player_z

        if relative_z < 0:
            return

        scale = 1.0 / (1.0 + relative_z * SCALE_FACTOR)
        scale = max(scale, MIN_SCALE)

        screen_x = int(PLAYER_SCREEN_X + relative_x * scale)
        screen_y = GameObject.relative_z_to_screen_y(relative_z)

        for _ in range(PARTICLE_COUNT_KILL):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(1, 4)

            char = random.choice(["0", "1"])
            # サイバー風: 緑〜シアン系
            g = random.randint(180, 255)
            b = random.randint(100, 220)
            color = (0, g, b)

            font_size = max(10, int(random.randint(14, 22) * scale))
            lifetime = random.randint(400, PARTICLE_LIFETIME + 200)

            self.particles.append(
                BinaryParticle(screen_x, screen_y, vx, vy,
                               char, color, font_size, lifetime)
            )

    def spawn_damage_text(self, world_x: float, world_z: float,
                           player_x: float, player_z: float,
                           damage: int, is_crit: bool = False):
        """ダメージ数値テキストを生成する"""
        relative_x = world_x - player_x
        relative_z = world_z - player_z

        if relative_z < 0:
            return

        scale = 1.0 / (1.0 + relative_z * SCALE_FACTOR)
        scale = max(scale, MIN_SCALE)

        screen_x = int(PLAYER_SCREEN_X + relative_x * scale)
        screen_y = GameObject.relative_z_to_screen_y(relative_z) - 30

        self.damage_texts.append(DamageText(screen_x, screen_y, damage, is_crit))

    def trigger_muzzle_flash(self, screen_x: int, screen_y: int):
        """マズルフラッシュを発生させる"""
        self.muzzle_flash_active = True
        self.muzzle_flash_time = pygame.time.get_ticks()
        self.muzzle_flash_pos = (screen_x, screen_y)

    def trigger_screen_shake(self):
        """画面シェイクを発生させる"""
        self.shake_active = True
        self.shake_time = pygame.time.get_ticks()

    def get_shake_offset(self) -> tuple[int, int]:
        """画面シェイクのオフセットを取得する"""
        if not self.shake_active:
            return 0, 0
        elapsed = pygame.time.get_ticks() - self.shake_time
        if elapsed >= SCREEN_SHAKE_DURATION:
            self.shake_active = False
            return 0, 0
        decay = 1.0 - (elapsed / SCREEN_SHAKE_DURATION)
        intensity = int(SCREEN_SHAKE_INTENSITY * decay)
        offset_x = random.randint(-intensity, intensity)
        offset_y = random.randint(-intensity, intensity)
        return offset_x, offset_y

    def update(self):
        """全エフェクトを更新する"""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for dt in self.damage_texts:
            dt.update()
        self.damage_texts = [dt for dt in self.damage_texts if dt.alive]

        if self.muzzle_flash_active:
            elapsed = pygame.time.get_ticks() - self.muzzle_flash_time
            if elapsed >= MUZZLE_FLASH_DURATION:
                self.muzzle_flash_active = False

    def draw(self, surface: pygame.Surface):
        """全エフェクトを描画する"""
        for p in self.particles:
            p.draw(surface)

        for dt in self.damage_texts:
            dt.draw(surface)

        if self.muzzle_flash_active:
            elapsed = pygame.time.get_ticks() - self.muzzle_flash_time
            flash_ratio = 1.0 - (elapsed / MUZZLE_FLASH_DURATION)
            flash_size = int(30 * flash_ratio)

            if flash_size > 0:
                fx, fy = self.muzzle_flash_pos
                glow_surf = pygame.Surface((flash_size * 4, flash_size * 4), pygame.SRCALPHA)
                alpha = int(120 * flash_ratio)
                pygame.draw.circle(glow_surf, (100, 255, 200, alpha),
                                   (flash_size * 2, flash_size * 2), flash_size * 2)
                surface.blit(glow_surf,
                             (fx - flash_size * 2, fy - flash_size * 2))
                pygame.draw.circle(surface, (200, 255, 240),
                                   (fx, fy), max(2, flash_size // 2))
