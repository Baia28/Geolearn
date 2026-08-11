import os
import flet as ft

# 1. SET YOUR RELATIVE FILE PATH HERE (e.g., "audio/gamarjoba.m4a" or "gamarjoba.m4a")
TEST_AUDIO_FILE = "audio/gamarjoba.m4a" 
ASSETS_DIR_NAME = "assets"

def main(page: ft.Page):
    page.title = "Flet Audio Diagnostic Tool"
    page.window_width = 450
    page.window_height = 450

    # Verification A: Check if Python can find the file directly on disk
    full_disk_path = os.path.abspath(os.path.join(ASSETS_DIR_NAME, TEST_AUDIO_FILE))
    file_exists = os.path.exists(full_disk_path)

    status_text = ft.Text(
        value=f"Disk Check: {'✅ EXISTS' if file_exists else '❌ NOT FOUND'}\n"
              f"Full Path: {full_disk_path}",
        color=ft.Colors.GREEN_700 if file_exists else ft.Colors.RED_700,
        weight=ft.FontWeight.BOLD
    )

    # Verification B: Set up local and remote audio sources
    # Flet requires asset paths to start with a leading slash
    clean_asset_src = f"/{TEST_AUDIO_FILE.lstrip('/')}"
    online_sample_src = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

    local_player = ft.Audio(src=clean_asset_src, autoplay=False)
    online_player = ft.Audio(src=online_sample_src, autoplay=False)

    # Add audio controls to page overlay so Flet attaches media handles
    page.overlay.extend([local_player, online_player])

    log_box = ft.Text("Logs will appear here...", italic=True, color=ft.Colors.GREY_700)

    def play_local(e):
        log_box.value = f"Attempting local playback: {local_player.src}"
        page.update()
        local_player.play()

    def play_online(e):
        log_box.value = f"Attempting online stream playback: {online_player.src}"
        page.update()
        online_player.play()

    page.add(
        ft.Text("Flet Audio Diagnostic Test", size=18, weight=ft.FontWeight.BOLD),
        status_text,
        ft.Divider(),
        ft.ElevatedButton("1. Play Local File", icon=ft.Icons.PLAY_ARROW, on_click=play_local),
        ft.ElevatedButton("2. Play Online Stream (MP3 Test)", icon=ft.Icons.CLOUD_DOWNLOAD, on_click=play_online),
        ft.Divider(),
        log_box
    )

if __name__ == "__main__":
    # CRITICAL: assets_dir MUST be explicitly declared in ft.app() for local assets to work
    ft.app(target=main, assets_dir="assets")