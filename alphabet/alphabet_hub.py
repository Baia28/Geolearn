"""Alphabet feature hub and its local sub-screen navigation."""

from collections.abc import Callable

import flet as ft

from alphabet.alphabet_db import AlphabetDB
from alphabet.alphabet_gallery import AlphabetGalleryView
from alphabet.alphabet_pronunciation import PhoneticsGuideView
from alphabet.alphabet_typing import AlphabetTypingGameView
from alphabet.anban_game import AnbanGameView
from alphabet.keyboard_practice_view import AlphabetKeyboardView
from gui.components import action_card, page_header, primary_button, section_label, tonal_card
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class AlphabetPage(ft.Column):
    """Local controller for alphabet gallery, guides, games, and keyboard practice."""

    def __init__(
        self,
        on_back_home: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.on_back_home = on_back_home
        self.tokens = tokens
        self.db = AlphabetDB()
        self.show_main_menu()

    def show_main_menu(self) -> None:
        tokens = self.tokens
        self.scroll = None
        activities = [
            action_card(
                "Alphabet Gallery",
                "Browse all 33 Mkhedruli letters, sounds, and examples",
                ft.Icons.GRID_VIEW_ROUNDED,
                lambda _event: self.launch_gallery(),
                icon_color=tokens.colors.error,
                tokens=tokens,
            ),
            action_card(
                "Phonetics & Sound Groups",
                "Master ejectives, confusion triads, and sound families",
                ft.Icons.RECORD_VOICE_OVER_ROUNDED,
                lambda _event: self.launch_phonetics_guide(),
                icon_color=tokens.colors.secondary,
                tokens=tokens,
            ),
            action_card(
                "Georgian Keyboard Practice",
                "Explore the keyboard layout with audio and Shift guidance",
                ft.Icons.KEYBOARD_ROUNDED,
                lambda _event: self.launch_keyboard_explorer(),
                icon_color=tokens.colors.primary,
                tokens=tokens,
            ),
            action_card(
                "Anbani Associations",
                "Associate vocabulary images with Georgian letters",
                ft.Icons.SPORTS_ESPORTS_ROUNDED,
                lambda _event: self.launch_game(),
                icon_color=tokens.colors.warning,
                tokens=tokens,
            ),
            action_card(
                "Listen & Type",
                "Practice audio dictation by typing the letter you hear",
                ft.Icons.HEADSET_ROUNDED,
                lambda _event: self.launch_typing_game(),
                icon_color=tokens.colors.success,
                tokens=tokens,
            ),
        ]
        call_to_action = tonal_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, color=tokens.colors.secondary),
                            ft.Text(
                                "Feeling a little more confident?",
                                size=tokens.typography.body_lg,
                                weight=ft.FontWeight.BOLD,
                                color=tokens.colors.on_secondary_container,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=tokens.spacing.sm,
                        wrap=True,
                    ),
                    ft.Text(
                        "Continue your progress from Home, or move on to Phase 0 when you're ready.",
                        size=tokens.typography.body_sm,
                        color=tokens.colors.on_secondary_container,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    primary_button(
                        "Go to Home",
                        lambda _event: self.on_back_home(),
                        icon=ft.Icons.HOME_ROUNDED,
                        tokens=tokens,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.spacing.sm,
            ),
            tone="secondary",
            tokens=tokens,
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Georgian Alphabet Hub (ანბანი)",
                        subtitle="Build confidence with letters, sounds, and typing",
                        on_back=lambda _event: self.on_back_home(),
                        back_label="Back to home",
                        max_width=tokens.dimensions.reading_width,
                        tokens=tokens,
                    ),
                    section_label("Select an activity", tokens=tokens),
                    *activities,
                    call_to_action,
                ],
                max_width=tokens.dimensions.reading_width,
                tokens=tokens,
            )
        ]
        if self.page:
            self.update()

    def _show_child(self, control: ft.Control) -> None:
        self.controls = [control]
        self.update()

    def launch_gallery(self) -> None:
        self._show_child(
            AlphabetGalleryView(
                db=self.db,
                on_back_to_menu=self.show_main_menu,
                tokens=self.tokens,
            )
        )

    def launch_phonetics_guide(self) -> None:
        self._show_child(
            PhoneticsGuideView(
                db=self.db,
                on_back_to_menu=self.show_main_menu,
                tokens=self.tokens,
            )
        )

    def launch_game(self) -> None:
        game = AnbanGameView(
            db=self.db,
            on_back_to_menu=self.show_main_menu,
            tokens=self.tokens,
        )
        self._show_child(game)
        game.start_game()

    def launch_typing_game(self) -> None:
        game = AlphabetTypingGameView(
            db=self.db,
            on_back_to_menu=self.show_main_menu,
            tokens=self.tokens,
        )
        self._show_child(game)
        game.start_game()

    def launch_keyboard_explorer(self) -> None:
        self._show_child(
            AlphabetKeyboardView(
                db=self.db,
                on_back_to_menu=self.show_main_menu,
                tokens=self.tokens,
            )
        )
