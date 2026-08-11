import flet as ft

def play_audio_file(page: ft.Page, raw_audio_path: str):
    """
    Safely plays audio in Flet using relative asset paths or system paths.
    Ensures leading slash for asset resolution.
    """
    print(f"DEBUG - Attempting to play audio from path: '{raw_audio_path}'")

    if not raw_audio_path or not page:
        print("DEBUG - Audio skipped: raw_audio_path or page context is missing/None")
        return

    # Normalize path: ensure leading slash for Flet assets (e.g. "/audio/gamarjoba.m4a")
    clean_relative = str(raw_audio_path).replace("\\", "/").lstrip("/")
    asset_src = f"/{clean_relative}"

    # Mutate page.overlay in-place using slice assignment (page.overlay is read-only and lacks a setter)
    page.overlay[:] = [c for c in page.overlay if not isinstance(c, ft.Audio)]

    # Create and append a new Audio instance
    audio_player = ft.Audio(src=asset_src, autoplay=True)
    page.overlay.append(audio_player)
    page.update()
    audio_player.play()