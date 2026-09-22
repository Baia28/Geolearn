"""Interactive guide to Georgian phonetics and letter groups."""

from collections.abc import Callable

import flet as ft

from gui.services.audio import play_audio_file
from gui.components import content_card, page_header
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class PhoneticsGuideView(ft.Column):
    def __init__(
        self,
        db,
        on_back_to_menu: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.tokens = tokens
        letters = self.db.get_alphabet_letters()
        self.audio_map = {
            item.get("georgian"): item.get("letter_audio")
            for item in letters
            if item.get("georgian")
        }
        self._build_ui()

    def _build_ui(self) -> None:
        tokens = self.tokens
        triads = [
            ("Labials (B/P sound family)", ["ბ", "ფ", "პ"], "Voiced → Aspirated → Ejective"),
            ("Velars (G/K sound family)", ["გ", "ქ", "კ"], "Voiced → Aspirated → Ejective"),
            ("Dentals (D/T sound family)", ["დ", "თ", "ტ"], "Voiced → Aspirated → Ejective"),
            ("Dental Affricates (DZ/TS)", ["ძ", "ც", "წ"], "Voiced → Aspirated → Ejective"),
            ("Postalveolar Affricates (J/CH)", ["ჯ", "ჩ", "ჭ"], "Voiced → Aspirated → Ejective"),
            ("Gutturals & Throat Sounds", ["ღ", "ხ", "ჰ"], "Deep voiced → Harsh voiceless → Soft H"),
        ]
        sound_types = [
            ("Ejective Sounds", ["ტ", "კ", "პ", "წ", "ჭ", "ყ"], "Sharply popped sounds produced with closed vocal cords.", "error"),
            ("Aspirated Sounds", ["თ", "ფ", "ქ"], "Accompanied by a strong puff of air.", "primary"),
            ("Affricates", ["ც", "ძ", "ჩ", "ჯ", "წ", "ჭ"], "A stop consonant that releases into a fricative.", "secondary"),
            ("Gutturals & Throat Consonants", ["ხ", "ღ", "ყ", "ქ"], "Pronounced deeper in the palate or throat.", "success"),
        ]
        articulation = [
            ("Bilabial (Both Lips)", ["ბ", "პ", "ფ", "მ"]),
            ("Dental / Alveolar", ["დ", "თ", "ტ", "ს", "ზ", "ლ", "რ", "ნ", "ც", "ძ", "წ"]),
            ("Postalveolar", ["შ", "ჟ", "ჩ", "ჯ", "ჭ"]),
            ("Velar (Soft Palate)", ["გ", "კ", "ქ", "ხ"]),
            ("Uvular (Back Throat)", ["ღ", "ყ"]),
            ("Glottal (Vocal Cords)", ["ჰ"]),
        ]
        pairs = [("ბ", "პ"), ("გ", "კ"), ("დ", "ტ"), ("ზ", "ს"), ("ჟ", "შ"), ("ძ", "ც"), ("ჯ", "ჩ"), ("ღ", "ხ")]

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=tokens.motion.normal,
            expand=1,
            scrollable=True,
            tabs=[
                ft.Tab(
                    text="Confusion Groups",
                    icon=ft.Icons.COMPARE_ARROWS_ROUNDED,
                    content=self._card_list(
                        [self._group_card(title, letters, subtitle) for title, letters, subtitle in triads]
                    ),
                ),
                ft.Tab(
                    text="Sound Categories",
                    icon=ft.Icons.RECORD_VOICE_OVER_ROUNDED,
                    content=self._card_list(
                        [self._category_card(title, letters, description, tone) for title, letters, description, tone in sound_types]
                    ),
                ),
                ft.Tab(
                    text="Place of Articulation",
                    icon=ft.Icons.ANALYTICS_ROUNDED,
                    content=self._card_list(
                        [self._simple_card(title, letters) for title, letters in articulation]
                    ),
                ),
                ft.Tab(
                    text="Voiced vs. Voiceless",
                    icon=ft.Icons.SWAP_HORIZ_ROUNDED,
                    content=self._card_list([self._pairs_card(pairs)]),
                ),
            ],
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Phonetics & Sound Groups",
                        subtitle="Tap a letter to hear its exact sound",
                        on_back=lambda _event: self.on_back_to_menu(),
                        back_label="Back to alphabet hub",
                        max_width=tokens.dimensions.reading_width,
                        tokens=tokens,
                    ),
                    tabs,
                ],
                max_width=tokens.dimensions.reading_width,
                scroll=False,
                tokens=tokens,
            )
        ]

    def _card_list(self, cards: list[ft.Control]) -> ft.ListView:
        return ft.ListView(
            controls=cards,
            spacing=self.tokens.spacing.md,
            padding=ft.padding.only(top=self.tokens.spacing.md, bottom=self.tokens.spacing.xl),
        )

    def _play_sound(self, character: str) -> None:
        path = self.audio_map.get(character)
        if path and self.page:
            play_audio_file(self.page, path)

    def _letter_chip(self, character: str, tone: str = "primary") -> ft.Card:
        tokens = self.tokens
        backgrounds = {
            "primary": tokens.colors.primary_container,
            "secondary": tokens.colors.secondary_container,
            "success": tokens.colors.success_container,
            "error": tokens.colors.error_container,
        }
        foregrounds = {
            "primary": tokens.colors.on_primary_container,
            "secondary": tokens.colors.on_secondary_container,
            "success": tokens.colors.on_success_container,
            "error": tokens.colors.on_error_container,
        }
        return content_card(
            ft.Text(
                character,
                size=tokens.typography.title,
                weight=ft.FontWeight.BOLD,
                color=foregrounds[tone],
            ),
            on_click=lambda _event: self._play_sound(character),
            width=52,
            height=52,
            padding=0,
            bgcolor=backgrounds[tone],
            tooltip=f"Hear {character}",
            alignment=ft.alignment.center,
            tokens=tokens,
        )

    def _group_card(self, title: str, letters: list, subtitle: str) -> ft.Card:
        return self._base_card(
            title,
            subtitle,
            [self._letter_chip(character) for character in letters],
        )

    def _category_card(self, title: str, letters: list, description: str, tone: str) -> ft.Card:
        return self._base_card(
            title,
            description,
            [self._letter_chip(character, tone) for character in letters],
        )

    def _simple_card(self, title: str, letters: list) -> ft.Card:
        return self._base_card(title, None, [self._letter_chip(character) for character in letters])

    def _base_card(
        self,
        title: str,
        subtitle: str | None,
        chips: list[ft.Control],
    ) -> ft.Card:
        tokens = self.tokens
        controls: list[ft.Control] = [
            ft.Text(
                title,
                size=tokens.typography.body_lg,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.text_primary,
            )
        ]
        if subtitle:
            controls.append(
                ft.Text(
                    subtitle,
                    size=tokens.typography.body_sm,
                    color=tokens.colors.text_secondary,
                    italic=True,
                )
            )
        controls.append(ft.Row(chips, wrap=True, spacing=tokens.spacing.sm, run_spacing=tokens.spacing.sm))
        return content_card(
            ft.Column(controls, spacing=tokens.spacing.sm),
            padding=tokens.spacing.lg,
            tokens=tokens,
        )

    def _pairs_card(self, pairs: list) -> ft.Card:
        tokens = self.tokens
        pair_boxes = [
            content_card(
                ft.Row(
                    controls=[
                        self._letter_chip(voiced, "secondary"),
                        ft.Text("vs", weight=ft.FontWeight.BOLD, color=tokens.colors.text_muted),
                        self._letter_chip(voiceless, "primary"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=tokens.spacing.sm,
                ),
                padding=tokens.spacing.sm,
                elevation=tokens.elevation.flat,
                tokens=tokens,
            )
            for voiced, voiceless in pairs
        ]
        return content_card(
            ft.Column(
                controls=[
                    ft.Text(
                        "Voiced vs. Voiceless Pairs",
                        size=tokens.typography.title_sm,
                        weight=ft.FontWeight.BOLD,
                        color=tokens.colors.text_primary,
                    ),
                    ft.Text(
                        "Teal = voiced • Blue = voiceless",
                        size=tokens.typography.label,
                        color=tokens.colors.text_secondary,
                        italic=True,
                    ),
                    ft.Row(
                        controls=pair_boxes,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=tokens.spacing.md,
                        run_spacing=tokens.spacing.md,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.spacing.sm,
            ),
            padding=tokens.spacing.lg,
            tokens=tokens,
        )
