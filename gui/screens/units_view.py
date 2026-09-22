"""Unit selection screen."""

from collections.abc import Callable

import flet as ft

from gui.components import icon_button, message_state, page_header, progress_card
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class UnitsView(ft.Column):
    def __init__(
        self,
        phase_num: int,
        phase_title: str,
        units_summary: list,
        on_select_unit: Callable,
        on_back: Callable,
        on_home: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.phase_num = phase_num
        self.phase_title = phase_title
        self.units_summary = units_summary
        self.on_select_unit = on_select_unit
        self.on_back = on_back
        self.on_home = on_home
        self.tokens = tokens
        self._build_ui()

    def _build_ui(self) -> None:
        tokens = self.tokens
        header = page_header(
            self.phase_title,
            eyebrow=f"Phase {self.phase_num}",
            on_back=lambda _event: self.on_back(),
            back_label="Back to phases",
            trailing=icon_button(
                ft.Icons.HOME_ROUNDED,
                lambda _event: self.on_home(),
                tooltip="Home",
                tokens=tokens,
            ),
            max_width=tokens.dimensions.reading_width,
            tokens=tokens,
        )

        unit_cards = [
            progress_card(
                eyebrow=f"Unit {unit['unit_num']}",
                title=unit["title"],
                progress=unit["progress"],
                progress_label=f"{unit['completed_lessons']}/{unit['total_lessons']} completed",
                on_click=lambda _event, number=unit["unit_num"]: self.on_select_unit(
                    self.phase_num, number
                ),
                tokens=tokens,
            )
            for unit in self.units_summary
        ]
        content: ft.Control = (
            ft.Column(controls=unit_cards, spacing=tokens.spacing.md)
            if unit_cards
            else message_state(
                "No units yet",
                "Units for this phase will appear here when content is available.",
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                tokens=tokens,
            )
        )

        self.controls = [
            page_shell(
                [header, content],
                max_width=tokens.dimensions.reading_width,
                tokens=tokens,
            )
        ]
