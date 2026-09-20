"""Shared Flet audio playback helpers."""

import flet as ft
from flet.core.audio import ReleaseMode

# Flet renders each Audio control in page.overlay. Keep the overlay bounded while
# still allowing learners to compare several pronunciations at once.
MAX_SIMULTANEOUS_PLAYERS = 3
_PAGE_PLAYER_REGISTRY = "_geolearn_audio_players"


def _get_active_players(page: ft.Page) -> list:
    """Return this page's active players, discarding controls removed elsewhere."""
    players = getattr(page, _PAGE_PLAYER_REGISTRY, None)
    if players is None:
        players = []
        setattr(page, _PAGE_PLAYER_REGISTRY, players)

    players[:] = [player for player in players if player in page.overlay]
    return players


def _remove_player(page: ft.Page, player: ft.Audio) -> None:
    """Release a player and remove its non-visual overlay control."""
    if player in page.overlay:
        player.release()
        page.overlay.remove(player)


def play_audio_file(page: ft.Page, raw_audio_path: str):
    """Play an audio asset, mixing up to three clips at a time."""
    print(f"DEBUG - Attempting to play audio from path: '{raw_audio_path}'")

    if not raw_audio_path or not page:
        print("DEBUG - Audio skipped: raw_audio_path or page context is missing/None")
        return

    # Flet resolves audio assets from a slash-prefixed path.
    clean_relative = str(raw_audio_path).replace("\\", "/").lstrip("/")
    asset_src = f"/{clean_relative}"

    active_players = _get_active_players(page)
    while len(active_players) >= MAX_SIMULTANEOUS_PLAYERS:
        # Bound page.overlay to avoid Flet freezes caused by accumulated controls.
        _remove_player(page, active_players.pop(0))

    # Separate players allow the currently active clips to overlap.
    audio_player = ft.Audio(
        src=asset_src,
        autoplay=True,
        release_mode=ReleaseMode.RELEASE,
    )
    page.overlay.append(audio_player)
    active_players.append(audio_player)
    page.update()
