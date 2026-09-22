"""Main curriculum dashboard composed from the shared design system."""

from collections.abc import Callable

import flet as ft

from gui.components import action_card, progress_card, section_label
from gui.core.layout import page_shell, responsive_split
from gui.core.theme import TOKENS, DesignTokens


class HomeView(ft.Column):
    def __init__(
        self,
        phases_summary: list,
        on_select_phase: Callable,
        on_select_alphabet: Callable,
        on_quick_review: Callable,
        on_open_fun_facts: Callable | None = None,
        on_global_passive_review: Callable | None = None,
        theme_action: ft.Control | None = None,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.phases_summary = phases_summary
        self.on_select_phase = on_select_phase
        self.on_select_alphabet = on_select_alphabet
        self.on_quick_review = on_quick_review
        self.on_open_fun_facts = on_open_fun_facts
        self.on_global_passive_review = on_global_passive_review
        self.theme_action = theme_action
        self.tokens = tokens
        self._build_ui()

    def _build_ui(self) -> None:
        tokens = self.tokens
        header = ft.Row(
            controls=[
                ft.Container(width=tokens.dimensions.touch_target),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("🇬🇪", size=tokens.typography.display),
                                ft.Text(
                                    "GeoLearn",
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                    color=tokens.colors.on_primary_container,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=tokens.spacing.md,
                        ),
                        ft.Text(
                            "Master the Georgian language step by step",
                            size=tokens.typography.body,
                            color=tokens.colors.text_secondary,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.spacing.xs,
                    expand=True,
                ),
                self.theme_action or ft.Container(width=tokens.dimensions.touch_target),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        curriculum_controls: list[ft.Control] = [
            section_label("Curriculum", tokens=tokens),
            action_card(
                "Georgian Alphabet Resources (ანბანი)",
                "Master Mkhedruli letters, sounds, and visual mnemonics",
                ft.Icons.SORT_BY_ALPHA_ROUNDED,
                lambda _event: self.on_select_alphabet(),
                icon_color=tokens.colors.error,
                compact=True,
                tokens=tokens,
            ),
            ft.Container(height=tokens.spacing.xs),
        ]
        curriculum_controls.extend(
            progress_card(
                eyebrow=f"Phase {phase['phase_num']}",
                title=phase["title"],
                progress=phase["progress"],
                progress_label=(
                    f"{phase['completed_lessons']}/{phase['total_lessons']} lessons"
                ),
                on_click=lambda _event, number=phase["phase_num"]: self.on_select_phase(number),
                tokens=tokens,
            )
            for phase in self.phases_summary
        )
        curriculum_column = ft.Column(controls=curriculum_controls, spacing=tokens.spacing.md)

        quick_column = ft.Column(
            controls=[
                section_label("Quick practice", tokens=tokens),
                action_card(
                    "Active Review",
                    "Test your memory with an adaptive quiz of past lessons.",
                    ft.Icons.PSYCHOLOGY_ROUNDED,
                    lambda _event: self.on_quick_review(),
                    icon_color=tokens.colors.warning,
                    compact=True,
                    tokens=tokens,
                ),
                action_card(
                    "Memory Library",
                    "Review unlocked material and see what to complete next.",
                    ft.Icons.LOCAL_LIBRARY_ROUNDED,
                    lambda _event: (
                        self.on_global_passive_review()
                        if self.on_global_passive_review
                        else None
                    ),
                    icon_color=tokens.colors.primary,
                    compact=True,
                    tokens=tokens,
                ),
                action_card(
                    "Culture & Fun Facts",
                    "Discover Georgian history, food, and traditions.",
                    ft.Icons.LIGHTBULB_OUTLINE_ROUNDED,
                    self.on_open_fun_facts or (lambda _event: None),
                    icon_color=tokens.colors.sunny,
                    icon_foreground=tokens.colors.on_sunny,
                    compact=True,
                    tokens=tokens,
                ),
            ],
            spacing=tokens.spacing.md,
        )

        self.controls = [
            page_shell(
                [
                    header,
                    ft.Container(height=tokens.spacing.sm),
                    responsive_split(
                        curriculum_column,
                        quick_column,
                        primary_columns=8,
                        secondary_columns=4,
                        tokens=tokens,
                    ),
                ],
                max_width=tokens.dimensions.wide_content_width,
                tokens=tokens,
            )
        ]
