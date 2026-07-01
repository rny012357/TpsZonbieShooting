"""
ゲームシーン
Areaシステム、バフオーブ、スコア、ダメージ表示、サウンドを統括する。
ESCでポーズ画面を開く。ポーズ中はゲーム時間が停止する。
サイバー空間風デザイン。
"""
import pygame
import random
import math
from scene_manager import Scene, SceneManager
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
from sound_manager import SoundManager


class GameScene(Scene):
    """ゲームプレイシーン"""

    def __init__(self, manager: SceneManager):
        super().__init__(manager)
        self.buff_defs = load_buff_definitions()
        self.sound = SoundManager()
        self.paused = False
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

    def on_enter(self):
        """シーン開始時にBGMを再生する"""
        self.sound.play_bgm()

    def on_exit(self):
        """シーン終了時にBGMを停止する"""
        self.sound.stop_bgm()

    def handle_event(self, event: pygame.event.Event):
        """入力処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if not self.game_over:
                    # ポーズ画面を開く
                    from pause_scene import PauseScene
                    self.manager.push(PauseScene(self.manager))
                    return

            # ゲームオーバー時のリスタート
            if self.game_over and event.key == pygame.K_r:
                self.reset()
                self.sound.play_bgm()
                return

            # リロード（Rキー）
            if not self.game_over and event.key == pygame.K_r:
                current_time = pygame.time.get_ticks()
                self.player.start_reload(current_time)

    def update(self):
        """ゲーム状態を更新する"""
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # SPACE長押し連射
        if keys[pygame.K_SPACE]:
            if self.player.can_shoot(current_time):
                self.player.shoot(current_time)
                bullet = Bullet(self.player.x, self.player.z)
                self.bullets.append(bullet)
                mx, my = self.player.get_muzzle_position()
                self.effects.trigger_muzzle_flash(mx, my)
                self.sound.play_shoot()

        # 移動処理
        self._move_player(keys)

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
        self._check_collisions(current_time)

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
                buff_value = get_buff_value(orb.buff_def, orb.rarity)
                self.player.apply_buff(orb.buff_def["type"], buff_value)
        self.buff_orbs = [o for o in self.buff_orbs if o.alive]

        # エフェクト更新
        self.effects.update()

        # プレイヤー死亡判定
        if self.player.is_dead():
            self.game_over = True
            self.sound.stop_bgm()

    def _move_player(self, keys):
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
        new_x = max(WORLD_X_MIN, min(WORLD_X_MAX, new_x))

        self.player.x = new_x
        self.player.z = new_z

    def _check_collisions(self, current_time: int):
        """当たり判定を行う"""
        all_zombies = self.area_manager.get_all_active_zombies()

        for bullet in self.bullets[:]:
            if not bullet.alive:
                continue
            for zombie in all_zombies:
                if not zombie.alive:
                    continue
                if (abs(bullet.x - zombie.x) < HIT_X and
                        abs(bullet.z - zombie.z) < HIT_Z):
                    damage, is_crit = self.player.calc_damage()
                    killed = zombie.take_hit(damage)

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
                        self.sound.play_kill()

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

        for zombie in all_zombies:
            if zombie.alive:
                old_hp = self.player.hp
                zombie.attack(self.player, current_time)
                if self.player.hp < old_hp:
                    self.effects.trigger_screen_shake()

    def _draw_background(self, surface: pygame.Surface):
        """サイバー空間風の背景とグリッドを描画する。

        手前グリッド修正: 前方と対称的な透視変換を使用し、
        GROUND_Yで自然に連続する描画を実現。
        """
        surface.fill(COLOR_SKY)

        # 地面（HORIZON_Y以下 + GROUND_Y以下の両方を黒で塗る）
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
        left_x = WORLD_X_MIN
        right_x = WORLD_X_MAX

        # === 前方横線（z方向、relative_z > 0） ===
        z_start_world = int(pz / GRID_SIZE) * GRID_SIZE
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
                    scale = max(MIN_SCALE, 1.0 / (1.0 + relative_z * SCALE_FACTOR))
                    screen_left = int(PLAYER_SCREEN_X + (left_x - px) * scale)
                    screen_right = int(PLAYER_SCREEN_X + (right_x - px) * scale)
                    pygame.draw.line(surface, color,
                                     (screen_left, y), (screen_right, y), 1)
            z += GRID_SIZE

        # === 手前横線（relative_z < 0）: GROUND_Yから下方へ対称的な透視変換 ===
        z_behind_start = int((pz - GRID_DRAW_BEHIND) / GRID_SIZE) * GRID_SIZE
        z = z_behind_start
        while z < pz:
            relative_z = z - pz  # 負の値
            abs_rel_z = abs(relative_z)
            if abs_rel_z > 0:
                # 手前専用の透視変換: GROUND_Y から画面下方へ広がる
                # 前方と対称的に t を計算
                t_behind = 1.0 - PERSPECTIVE_DEPTH / (PERSPECTIVE_DEPTH + abs_rel_z)
                # GROUND_Y から下方へ（前方はGROUND_Y→HORIZON_Y、手前はGROUND_Y→SCREEN_HEIGHT）
                y = int(GROUND_Y + (SCREEN_HEIGHT - GROUND_Y) * t_behind)

                if GROUND_Y < y < SCREEN_HEIGHT:
                    brightness = max(0.1, 1.0 - t_behind * 0.85)
                    color = (
                        int(COLOR_GRID[0] * brightness),
                        int(COLOR_GRID[1] * brightness),
                        int(COLOR_GRID[2] * brightness)
                    )
                    # 手前のスケール: 手前ほど広がる（前方と逆）
                    scale_behind = 1.0 + abs_rel_z * SCALE_FACTOR * 0.5
                    screen_left = int(PLAYER_SCREEN_X + (left_x - px) * scale_behind)
                    screen_right = int(PLAYER_SCREEN_X + (right_x - px) * scale_behind)
                    pygame.draw.line(surface, color,
                                     (screen_left, y), (screen_right, y), 1)
            z += GRID_SIZE

        # === 前方縦線（x方向） ===
        grid_x_positions = list(range(WORLD_X_MIN, WORLD_X_MAX + 1, GRID_SIZE))

        for grid_x in grid_x_positions:
            relative_x = grid_x - px

            # 前方
            segments = 20
            prev_sx, prev_sy = None, None
            for seg in range(segments + 1):
                seg_rel_z = 1 + (GRID_DRAW_RANGE - 1) * (seg / segments)
                scale = max(MIN_SCALE, 1.0 / (1.0 + seg_rel_z * SCALE_FACTOR))
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

            # 手前への縦線延長（GROUND_Yから画面下部へ）
            behind_segments = 8
            prev_bx, prev_by = None, None
            for seg in range(behind_segments + 1):
                seg_behind_z = 1 + (GRID_DRAW_BEHIND - 1) * (seg / behind_segments)
                t_b = 1.0 - PERSPECTIVE_DEPTH / (PERSPECTIVE_DEPTH + seg_behind_z)
                by = int(GROUND_Y + (SCREEN_HEIGHT - GROUND_Y) * t_b)

                # 手前ほどスケールが大きくなる（広がる）
                scale_b = 1.0 + seg_behind_z * SCALE_FACTOR * 0.5
                bx = int(PLAYER_SCREEN_X + relative_x * scale_b)

                if by >= SCREEN_HEIGHT:
                    break

                if prev_bx is not None:
                    brightness = max(0.1, 1.0 - t_b * 0.85)
                    color = (
                        int(COLOR_GRID[0] * brightness),
                        int(COLOR_GRID[1] * brightness),
                        int(COLOR_GRID[2] * brightness)
                    )
                    pygame.draw.line(surface, color,
                                     (prev_bx, prev_by), (bx, by), 1)
                prev_bx, prev_by = bx, by

            # 前方と手前の接続（GROUND_Y付近）
            near_scale = 1.0 / (1.0 + 1 * SCALE_FACTOR)
            near_sx = int(PLAYER_SCREEN_X + relative_x * near_scale)
            # 手前の始点
            behind_start_scale = 1.0 + 1 * SCALE_FACTOR * 0.5
            behind_start_sx = int(PLAYER_SCREEN_X + relative_x * behind_start_scale)

            color_connect = (
                int(COLOR_GRID[0] * 0.5),
                int(COLOR_GRID[1] * 0.5),
                int(COLOR_GRID[2] * 0.5)
            )
            pygame.draw.line(surface, color_connect,
                             (near_sx, GROUND_Y), (behind_start_sx, GROUND_Y + 1), 1)

    def draw(self, surface: pygame.Surface):
        """全描画処理"""
        shake_x, shake_y = self.effects.get_shake_offset()

        if shake_x != 0 or shake_y != 0:
            render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            render_surface = surface

        # 背景
        self._draw_background(render_surface)

        # エリアゲート
        px, pz = self.player.x, self.player.z
        for gate in self.area_manager.get_visible_gates(pz):
            gate.draw(render_surface, px, pz)

        # ゾンビ・弾を距離でソート
        all_zombies = self.area_manager.get_all_active_zombies()
        draw_objects = []
        draw_objects.extend(self.bullets)
        draw_objects.extend(all_zombies)
        draw_objects.sort(key=lambda obj: obj.z - pz, reverse=True)

        for obj in draw_objects:
            obj.draw(render_surface, px, pz)

        # プレイヤー
        self.player.draw(render_surface)

        # バフオーブ
        for orb in self.buff_orbs:
            orb.draw(render_surface)

        # エフェクト
        self.effects.draw(render_surface)

        # シェイク適用
        if shake_x != 0 or shake_y != 0:
            surface.fill(COLOR_BLACK)
            surface.blit(render_surface, (shake_x, shake_y))

        # UI描画
        current_time = pygame.time.get_ticks()
        self.ui.draw_hp_bar(surface, self.player.hp, self.player.max_hp)
        self.ui.draw_ammo(surface, self.player.ammo, self.player.max_ammo,
                          self.player.reloading,
                          self.player.get_reload_progress(current_time))

        self.ui.draw_score(surface, self.score)
        self.ui.draw_stats(surface, self.player)
        self.ui.draw_area_map(surface, self.area_manager)

        # AREA CLEAR!
        if self.area_manager.clear_display_active:
            from config import AREA_CLEAR_DISPLAY_TIME
            elapsed = current_time - self.area_manager.clear_display_start
            self.ui.draw_area_clear(surface,
                                     self.area_manager.clear_display_area,
                                     elapsed, AREA_CLEAR_DISPLAY_TIME)

        # ゲームオーバー
        if self.game_over:
            self.ui.draw_game_over(surface, self.kill_count,
                                    self.area_manager.current_area_number,
                                    self.score)
