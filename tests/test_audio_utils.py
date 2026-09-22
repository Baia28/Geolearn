"""Regression tests for exclusive playback in the shared audio helper."""

import unittest
from unittest.mock import patch

from flet.core.audio import ReleaseMode

from gui.services import audio as audio_utils


class FakePage:
    def __init__(self):
        self.overlay = []
        self.update_count = 0

    def update(self):
        self.update_count += 1


class FakeAudio:
    def __init__(self, **kwargs):
        self.src = kwargs["src"]
        self.autoplay = kwargs["autoplay"]
        self.release_mode = kwargs["release_mode"]
        self.release_count = 0

    def release(self):
        self.release_count += 1


class PlayAudioFileTests(unittest.TestCase):
    def test_new_clip_replaces_the_active_pronunciation(self):
        page = FakePage()

        with patch.object(audio_utils.ft, "Audio", FakeAudio):
            audio_utils.play_audio_file(page, "audio/first.m4a")
            first_player = page.overlay[0]
            audio_utils.play_audio_file(page, "audio/second.m4a")

        self.assertEqual(
            [player.src for player in page.overlay],
            ["/audio/second.m4a"],
        )
        self.assertTrue(all(player.autoplay for player in page.overlay))
        self.assertTrue(
            all(player.release_mode == ReleaseMode.RELEASE for player in page.overlay)
        )
        self.assertEqual(first_player.release_count, 1)


if __name__ == "__main__":
    unittest.main()
