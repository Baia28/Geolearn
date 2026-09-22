"""Large Georgian keyboard practice view."""

from collections.abc import Callable

import flet as ft

from gui.services.audio import play_audio_file
from gui.activities.keyboard import GeorgianKeyboard
from gui.components import icon_button, page_header, text_input, tonal_card
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class AlphabetKeyboardView(ft.Column):
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
        self._last_display_value = ""
        self._build_ui()

    def _build_ui(self) -> None:
        tokens = self.tokens
        self.display_field = text_input(
            label="Practice text",
            hint_text="Type or tap a key to write and hear Georgian…",
            width=tokens.dimensions.wide_input_width,
            text_size=tokens.typography.title,
            text_align=ft.TextAlign.CENTER,
            on_change=self._translate_physical_input,
            suffix=icon_button(
                ft.Icons.CLEAR_ROUNDED,
                self._clear_text,
                tooltip="Clear text",
                tokens=tokens,
            ),
            tokens=tokens,
        )
        instructions = tonal_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_ROUNDED, color=tokens.colors.primary),
                            ft.Text(
                                "How the Georgian layout works",
                                size=tokens.typography.body_lg,
                                weight=ft.FontWeight.BOLD,
                                color=tokens.colors.on_primary_container,
                            ),
                        ],
                        spacing=tokens.spacing.sm,
                    ),
                    ft.Text(
                        "• Standard keys map phonetically to Latin counterparts (A → ა, B → ბ, D → დ).\n"
                        "• Shift reveals seven special letters: W → ჭ, R → ღ, T → თ, S → შ, J → ჟ, Z → ძ, C → ჩ.\n"
                        "• Modern Georgian has no uppercase distinction; Shift simply fits all 33 letters on a standard layout.",
                        size=tokens.typography.body_sm,
                        color=tokens.colors.on_primary_container,
                    ),
                ],
                spacing=tokens.spacing.sm,
            ),
            tone="primary",
            tokens=tokens,
        )
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self._handle_key_tap,
            on_backspace=self._handle_backspace,
            size="large",
            tokens=tokens,
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Georgian Keyboard Practice",
                        subtitle="Type with a physical keyboard or tap the keys below",
                        on_back=lambda _event: self.on_back_to_menu(),
                        back_label="Back to alphabet hub",
                        max_width=tokens.dimensions.keyboard_content_width,
                        tokens=tokens,
                    ),
                    instructions,
                    self.display_field,
                    self.keyboard,
                ],
                max_width=tokens.dimensions.keyboard_content_width,
                tokens=tokens,
            )
        ]

    def _handle_key_tap(self, character: str) -> None:
        self.display_field.value = (self.display_field.value or "") + character
        self._last_display_value = self.display_field.value
        self.display_field.update()
        if character != " ":
            self._play_character(character)

    def _handle_backspace(self) -> None:
        self.display_field.value = (self.display_field.value or "")[:-1]
        self._last_display_value = self.display_field.value
        self.display_field.update()

    def _clear_text(self, _event=None) -> None:
        self.display_field.value = ""
        self._last_display_value = ""
        self.display_field.update()

    def _play_character(self, character: str) -> None:
        audio_path = self.audio_map.get(character)
        if audio_path and self.page:
            play_audio_file(self.page, audio_path)

    def _translate_physical_input(self, event) -> None:
        typed = event.control.value or ""
        translated = GeorgianKeyboard.translate_latin_text(typed)
        if translated != typed:
            event.control.value = translated
            event.control.update()
        if len(translated) == len(self._last_display_value) + 1:
            self._play_character(translated[-1])
        self._last_display_value = translated
