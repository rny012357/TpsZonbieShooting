"""
エントリーポイント
SceneManager + AssetManager + SettingsManagerを初期化し、
ホーム画面からゲームを開始する。
"""
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from asset_manager import AssetManager
from settings_manager import SettingsManager
from sound_manager import SoundManager
from scene_manager import SceneManager
from home_scene import HomeScene


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # マネージャー初期化
    settings = SettingsManager()
    assets = AssetManager()
    assets.load_all()
    sound = SoundManager()

    # シーンマネージャー
    scene_mgr = SceneManager()
    scene_mgr.push(HomeScene(scene_mgr))

    # メインループ
    while scene_mgr.running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                scene_mgr.quit()
                break
            if scene_mgr.current_scene:
                scene_mgr.current_scene.handle_event(event)

        if not scene_mgr.running:
            break

        if scene_mgr.current_scene:
            scene_mgr.current_scene.update()
            scene_mgr.current_scene.draw(screen)

        pygame.display.flip()

    # 設定保存
    settings.save()
    pygame.quit()


if __name__ == "__main__":
    main()
