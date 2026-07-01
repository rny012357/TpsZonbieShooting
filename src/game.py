"""
ゲームメインクラス
Areaシステム、バフオーブ、スコア、ダメージ表示を統括する。
サイバー空間風デザイン。
"""
import pygame
import random
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    CENTER_X, GROUND_Y, HORIZON_Y,
    COLOR_BLACK, COLOR_SKY, COLOR_GROUND, COLOR_GRID,
    COLOR_HORIZON, COLOR_GRAY,
    HIT_X, HIT_Z,
    PERSPECTIVE_DEPTH, SCALE_FACTOR, MIN_SCALE,
    ZOMBIE_SPEED_MIN, ZOMBIE_SPEED_MAX,
    PLAYER_SPEED, PLAYER_FORWARD_SPEED,
    PLAYER_SCREEN_X,
    WORLD_X_MIN, WORLD_X_MAX,
    GRID_SIZE, GRID_DRAW_RANGE, GRID_DRAW_BEHIND,
    SCORE_ZOMBIE_KILL, SCORE_AREA_CLEAR, SCORE_ZOMBIE_MISS
)
from player import Player
from bullet import Bullet
from zombie import Zombie
from ui import UI
from effects import EffectManager
from game_object import GameObject
from area import AreaManager
from buff_system import load_buff_definitions, roll_buff, get_buff_value, BuffOrb


class Game:
    """ゲームメインクラス"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.buff_defs = load_buff_definitions()
        self.reset()

    def reset(self):
        """ゲーム状態をリセットする"""
        self.player = Player()
        self.bullets: list[Bullet] = []
        self.buff_orbs: list[BuffOrb] = []
        self.kill_count = 0
        self.score = 0
        self.game_over = False
        self.ui = UI()
        self.effects = EffectManager()
        self.area_manager = AreaManager()

    def handle_input(self):
        """入力処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

                if self.game_over and event.key == pygame.K_r:
                    self.reset()
                    return

                if not self.game_over and event.key == pygame.K_r:
                    current_time = pygame.time.get_ticks()
                    self.player.start_reload(current_time)

        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        # SPACE長押し連射
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if self.player.can_shoot(current_time):
                self.player.shoot(current_time)
                bullet = Bullet(self.player.x, self.player.z)
                self.bullets.append(bullet)
                mx, my = self.player.get_muzzle_position()
                self.effects.trigger_muzzle_flash(mx, my)

        # 移動処理（エリア境界制限付き）
        self.move_player(keys)

    def move_player(self, keys):
        """プレイヤーの移動をエリア境界制限付きで行う"""
        move_dx = 0.0
        move_dz = 0.0

        if keys[pygame.K_a]:
            move_dx -= PLAYER_SPEED
        if keys[pygame.K_d]:
            move_dx += PLAYER_SPEED
        if keys[pygame.K_w]:
            move_dz += PLAYER_FORWARD_SPEED

        if move_dx == 0 and move_dz == 0:
            return

        new_x = self.player.x + move_dx
        new_z = self.player.z + move_dz

        # 左右の境界制限（縦グリッド線の範囲内）
        new_x = max(WORLD_X_MIN, min(WORLD_X_MAX, new_x))

        self.player.x = new_x
        self.player.z = new_z

    def check_collisions(self):
        """当たり判定を行う"""
        current_time = pygame.time.get_ticks()

        # 全エリアのアクティブなゾンビを取得
        all_zombies = self.area_manager.get_all_active_zombies()

        # 弾とゾンビの当たり判定
        for bullet in self.bullets[:]:
            if not bullet.alive:
                continue

            for zombie in all_zombies:
                if not zombie.alive:
                    continue
                if (abs(bullet.x - zombie.x) < HIT_X and
                        abs(bullet.z - zombie.z) < HIT_Z):
                    # ダメージ計算
                    damage, is_crit = self.player.calc_damage()
                    killed = zombie.take_hit(damage)

                    # ダメージ数値表示
                    self.effects.spawn_damage_text(
                        zombie.x, zombie.z,
                        self.player.x, self.player.z,
                        damage, is_crit
                    )

                    if killed:
                        self.effects.spawn_kill_particles(
                            zombie.x, zombie.z,
                            self.player.x, self.player.z
                        )
                        self.kill_count += 1
                        self.score += SCORE_ZOMBIE_KILL

                        # バフオーブ生成
                        buff_def, rarity = roll_buff(
                            self.area_manager.current_area_number,
                            self.buff_defs
                        )
                        orb = BuffOrb(
                            zombie.x, zombie.z,
                            self.player.x, self.player.z,
                            buff_def, rarity
                        )
                        self.buff_orbs.append(orb)

                    bullet.alive = False
                    break

        # ゾンビのプレイヤー攻撃判定
        for zombie in all_zombies:
            if zombie.alive:
                old_hp = self.player.hp
                zombie.attack(self.player, current_time)
                if self.player.hp < old_hp:
                    self.effects.trigger_screen_shake()

    def update(self):
        """ゲーム状態を更新する"""
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()

        # リロード更新
        self.player.update_reload(current_time)

        # 弾の更新
        for bullet in self.bullets:
            bullet.update()

        # ゾンビの更新（AI含む）
        all_zombies = self.area_manager.get_all_active_zombies()
        for zombie in all_zombies:
            zombie.check_activation(self.player.x, self.player.z)
            zombie.update()

        # 弾の消滅判定
        self.bullets = [b for b in self.bullets if b.alive]

        # 当たり判定
        self.check_collisions()

        # エリア更新
        self.area_manager.update(self.player.z)

        # エリア制圧時のスコア加算
        current_area = self.area_manager.current_area
        if current_area.cleared and current_area.clear_time == current_time:
            self.score += SCORE_AREA_CLEAR

        # バフオーブ更新
        for orb in self.buff_orbs[:]:
            collected = orb.update()
            if collected:
                # バフ適用
                buff_value = get_buff_value(orb.buff_def, orb.rarity)
                self.player.apply_buff(orb.buff_def["type"], buff_value)
        self.buff_orbs = [o for o in self.buff_orbs if o.alive]

        # エフェクト更新
        self.effects.update()

        # プレイヤー死亡判定
        if self.player.is_dead():
            self.game_over = True

    def draw_background(self, surface: pygame.Surface):
        """サイバー空間風の背景とグリッドを描画する。

        横線はエリア内のみ描画（縦線の範囲内に制限）。
        プレイヤー手前にもグリッドを描画。
        """
        surface.fill(COLOR_SKY)

        # 地面
        ground_rect = pygame.Rect(0, HORIZON_Y, SCREEN_WIDTH, SCREEN_HEIGHT - HORIZON_Y)
        pygame.draw.rect(surface, COLOR_GROUND, ground_rect)

        # 水平線
        pygame.draw.line(surface, COLOR_HORIZON,
                         (0, HORIZON_Y), (SCREEN_WIDTH, HORIZON_Y), 2)
        for glow_offset in range(1, 4):
            alpha = max(0, 60 - glow_offset * 20)
            glow_color = (0, min(255, COLOR_HORIZON[1]),
                          min(255, COLOR_HORIZON[2] + 30))
            glow_surf = pygame.Surface((SCREEN_WIDTH, 2), pygame.SRCALPHA)
            pygame.draw.line(glow_surf, (*glow_color, alpha),
                             (0, 0), (SCREEN_WIDTH, 0), 2)
            surface.blit(glow_surf, (0, HORIZON_Y - glow_offset))
            surface.blit(glow_surf, (0, HORIZON_Y + glow_offset))

        px, pz = self.player.x, self.player.z

        # === 縦線の画面X範囲を計算（横線のクリップに使用） ===
        grid_x_positions = list(range(WORLD_X_MIN, WORLD_X_MAX + 1, GRID_SIZE))
        left_x = WORLD_X_MIN
        right_x = WORLD_X_MAX

        # === 横線（z方向）: エリア内のみ描画、手前も含む ===
        z_start_world = int((pz - GRID_DRAW_BEHIND) / GRID_SIZE) * GRID_SIZE
        z_end_world = pz + GRID_DRAW_RANGE

        z = z_start_world
        while z <= z_end_world:
            relative_z = z - pz
            if relative_z > 0:
                y = GameObject.relative_z_to_screen_y(relative_z)
                if y > HORIZON_Y:
                    t = GameObject.perspective_t(relative_z)
                    brightness = max(0.15, 1.0 - t * 0.85)
                    color = (
                        int(COLOR_GRID[0] * brightness),
                        int(COLOR_GRID[1] * brightness),
                        int(COLOR_GRID[2] * brightness)
                    )
                    # 横線をエリア内（縦線の範囲）に制限
                    scale = 1.0 / (1.0 + relative_z * SCALE_FACTOR)
                    scale = max(scale, MIN_SCALE)
                    screen_left = int(PLAYER_SCREEN_X + (left_x - px) * scale)
                    screen_right = int(PLAYER_SCREEN_X + (right_x - px) * scale)
                    pygame.draw.line(surface, color,
                                     (screen_left, y), (screen_right, y), 1)
            elif relative_z < 0 and relative_z > -GRID_DRAW_BEHIND:
                # 手前のグリッド（プレイヤーの足元より手前）
                abs_rel_z = abs(relative_z)
                # 手前は画面下方向に広がる
                y = int(GROUND_Y + abs_rel_z * 0.8)
                if y < SCREEN_HEIGHT:
                    brightness = max(0.1, 1.0 - abs_rel_z / GRID_DRAW_BEHIND * 0.8)
                    color = (
                        int(COLOR_GRID[0] * brightness),
                        int(COLOR_GRID[1] * brightness),
                        int(COLOR_GRID[2] * brightness)
                    )
                    scale = 1.0 / (1.0 + abs_rel_z * SCALE_FACTOR * 0.3)
                    screen_left = int(PLAYER_SCREEN_X + (left_x - px) * scale)
                    screen_right = int(PLAYER_SCREEN_X + (right_x - px) * scale)
                    pygame.draw.line(surface, color,
                                     (screen_left, y), (screen_right, y), 1)
            z += GRID_SIZE

        # === 縦線（x方向） ===
        for grid_x in grid_x_positions:
            relative_x = grid_x - px

            segments = 20
            prev_sx, prev_sy = None, None
            for seg in range(segments + 1):
                seg_rel_z = 1 + (GRID_DRAW_RANGE - 1) * (seg / segments)
                scale = 1.0 / (1.0 + seg_rel_z * SCALE_FACTOR)
                scale = max(scale, MIN_SCALE)
                sx = int(PLAYER_SCREEN_X + relative_x * scale)
                sy = GameObject.relative_z_to_screen_y(seg_rel_z)

                if sy <= HORIZON_Y:
                    break

                if prev_sx is not None:
                    t = GameObject.perspective_t(seg_rel_z)
                    brightness = max(0.15, 1.0 - t * 0.85)
                    color = (
                        int(COLOR_GRID[0] * brightness),
                        int(COLOR_GRID[1] * brightness),
                        int(COLOR_GRID[2] * brightness)
                    )
                    pygame.draw.line(surface, color,
                                     (prev_sx, prev_sy), (sx, sy), 1)

                prev_sx, prev_sy = sx, sy

            # 手前への縦線延長
            if prev_sx is not None:
                near_scale = 1.0 / (1.0 + 1 * SCALE_FACTOR)
                near_sx = int(PLAYER_SCREEN_X + relative_x * near_scale)
                near_sy = GROUND_Y

                # 足元から下に延長
                behind_scale = 1.0 / (1.0 + GRID_DRAW_BEHIND * SCALE_FACTOR * 0.3)
                behind_sx = int(PLAYER_SCREEN_X + relative_x * behind_scale)
                behind_sy = int(GROUND_Y + GRID_DRAW_BEHIND * 0.8)
                behind_sy = min(behind_sy, SCREEN_HEIGHT)

                color = (
                    int(COLOR_GRID[0] * 0.4),
                    int(COLOR_GRID[1] * 0.4),
                    int(COLOR_GRID[2] * 0.4)
                )
                pygame.draw.line(surface, color,
                                 (near_sx, near_sy), (behind_sx, behind_sy), 1)

    def draw(self):
        """全描画処理"""
        shake_x, shake_y = self.effects.get_shake_offset()

        if shake_x != 0 or shake_y != 0:
            render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            render_surface = self.screen

        # 背景
        self.draw_background(render_surface)

        # エリアゲート描画
        px, pz = self.player.x, self.player.z
        for gate in self.area_manager.get_visible_gates(pz):
            gate.draw(render_surface, px, pz)

        # 全ゾンビを距離でソート（奥から手前）
        all_zombies = self.area_manager.get_all_active_zombies()
        draw_objects = []
        draw_objects.extend(self.bullets)
        draw_objects.extend(all_zombies)
        draw_objects.sort(key=lambda obj: obj.z - pz, reverse=True)

        for obj in draw_objects:
            obj.draw(render_surface, px, pz)

        # プレイヤー
        self.player.draw(render_surface)

        # バフオーブ描画
        for orb in self.buff_orbs:
            orb.draw(render_surface)

        # エフェクト
        self.effects.draw(render_surface)

        # シェイク適用
        if shake_x != 0 or shake_y != 0:
            self.screen.fill(COLOR_BLACK)
            self.screen.blit(render_surface, (shake_x, shake_y))

        # UI描画
        current_time = pygame.time.get_ticks()
        self.ui.draw_hp_bar(self.screen, self.player.hp, self.player.max_hp)
        self.ui.draw_ammo(self.screen, self.player.ammo, self.player.max_ammo,
                          self.player.reloading,
                          self.player.get_reload_progress(current_time))

        # スコア（右上）
        self.ui.draw_score(self.screen, self.score)

        # ステータスUI（左側）
        self.ui.draw_stats(self.screen, self.player)

        # エリアUI（右側）
        self.ui.draw_area_map(self.screen, self.area_manager)

        # AREA CLEAR!
        if self.area_manager.clear_display_active:
            from config import AREA_CLEAR_DISPLAY_TIME
            elapsed = current_time - self.area_manager.clear_display_start
            self.ui.draw_area_clear(self.screen,
                                     self.area_manager.clear_display_area,
                                     elapsed, AREA_CLEAR_DISPLAY_TIME)

        # ゲームオーバー
        if self.game_over:
            self.ui.draw_game_over(self.screen, self.kill_count,
                                    self.area_manager.current_area_number,
                                    self.score)

        pygame.display.flip()

    def run(self):
        """メインループ"""
        while self.running:
            self.clock.tick(FPS)
            self.handle_input()
            self.update()
            self.draw()

        pygame.quit()
