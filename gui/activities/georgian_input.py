"""Reusable Georgian text-entry control with physical and on-screen keyboards."""

from collections.abc import Callable

import flet as ft

from gui.activities.keyboard import GeorgianKeyboard
from gui.components import text_input
from gui.core.theme import TOKENS, DesignTokens


class GeorgianInput(ft.Column):
    def __init__(
        self,
        *,
        on_submit: Callable,
        label: str = "Type in Georgian",
        width: int | None = None,
        keyboard_size: str = "compact",
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.md,
        )
        self.tokens = tokens
        self.locked = False
        self.field = text_input(
            label=label,
            width=width or tokens.dimensions.form_width,
            text_align=ft.TextAlign.CENTER,
            on_change=self._translate_physical_input,
            on_submit=on_submit,
            tokens=tokens,
        )
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self.append,
            on_backspace=self.backspace,
            size=keyboard_size,
            tokens=tokens,
        )
        self.controls = [self.field, self.keyboard]

    @property
    def value(self) -> str:
        return (self.field.value or "").strip()

    def append(self, character: str) -> None:
        if self.locked:
            return
        self.field.value = (self.field.value or "") + character
        self.field.update()

    def backspace(self) -> None:
        if self.locked:
            return
        self.field.value = (self.field.value or "")[:-1]
        self.field.update()

    def lock(self, *, hide_keyboard: bool = True) -> None:
        self.locked = True
        self.field.disabled = True
        self.keyboard.visible = not hide_keyboard

    def _translate_physical_input(self, event) -> None:
        typed = event.control.value or ""
        translated = GeorgianKeyboard.translate_latin_text(typed)
        if translated != typed:
            event.control.value = translated
            event.control.update()
