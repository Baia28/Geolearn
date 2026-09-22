"""Lesson selection and unit-tool screen."""

from collections.abc import Callable

import flet as ft

from gui.components import (
    action_card,
    content_card,
    icon_button,
    message_state,
    page_header,
    primary_button,
    section_label,
)
from gui.core.layout import page_shell, responsive_split
from gui.core.theme import TOKENS, DesignTokens


class LessonsView(ft.Column):
    def __init__(
        self,
        phase_num: int,
        unit_num: int,
        unit_title: str,
        lessons_list: list,
        on_select_lesson: Callable,
        on_passive_read: Callable,
        on_unit_review: Callable,
        on_back: Callable,
        on_home: Callable,
        has_review_material: bool = True,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.phase_num = phase_num
        self.unit_num = unit_num
        self.unit_title = unit_title
        self.lessons_list = lessons_list
        self.on_select_lesson = on_select_lesson
        self.on_passive_read = on_passive_read
        self.on_unit_review = on_unit_review
        self.on_back = on_back
        self.on_home = on_home
        self.has_review_material = has_review_material
        self.tokens = tokens
        self._build_ui()

    def _build_lesson_card(self, lesson: dict) -> ft.Card:
        tokens = self.tokens
        lesson_num = int(lesson["lesson_num"])
        title = str(lesson.get("title", "")).strip()
        is_complete = bool(lesson.get("is_completed", False))
        generic_title = not title or title.lower() == f"lesson {lesson_num}".lower()
        display_title = f"Lesson {lesson_num}" if generic_title else title

        def start_lesson(_event) -> None:
            self.on_select_lesson(self.phase_num, self.unit_num, lesson_num)

        title_controls: list[ft.Control] = []
        if not generic_title:
            title_controls.append(
                ft.Text(
                    f"Lesson {lesson_num}",
                    size=tokens.typography.caption,
                    color=tokens.colors.text_secondary,
                    weight=ft.FontWeight.BOLD,
                )
            )
        title_controls.append(
            ft.Text(
                display_title,
                size=tokens.typography.body_lg,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.text_primary,
            )
        )
        return content_card(
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_ROUNDED if is_complete else ft.Icons.PLAY_CIRCLE_ROUNDED,
                        color=tokens.colors.success if is_complete else tokens.colors.primary,
                        size=tokens.dimensions.icon_lg,
                    ),
                    ft.Column(title_controls, spacing=tokens.spacing.xxs, expand=True),
                    primary_button(
                        "Review" if is_complete else "Start",
                        start_lesson,
                        height=tokens.dimensions.compact_button_height,
                        tokens=tokens,
                    ),
                ],
                spacing=tokens.spacing.md,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=start_lesson,
            bgcolor=(tokens.colors.success_container if is_complete else tokens.colors.surface),
            tokens=tokens,
        )

    def _build_ui(self) -> None:
        tokens = self.tokens
        header = page_header(
            self.unit_title,
            eyebrow=f"Phase {self.phase_num} • Unit {self.unit_num}",
            on_back=lambda _event: self.on_back(),
            back_label="Back to units",
            trailing=icon_button(
                ft.Icons.HOME_ROUNDED,
                lambda _event: self.on_home(),
                tooltip="Home",
                tokens=tokens,
            ),
            max_width=tokens.dimensions.wide_content_width,
            tokens=tokens,
        )

        lesson_cards = [self._build_lesson_card(lesson) for lesson in self.lessons_list]
        lessons_content: ft.Control = (
            ft.Column(
                controls=[section_label("Lessons", tokens=tokens), *lesson_cards],
                spacing=tokens.spacing.md,
            )
            if lesson_cards
            else message_state(
                "No lessons yet",
                "Lessons for this unit will appear here when content is available.",
                icon=ft.Icons.SCHOOL_OUTLINED,
                tokens=tokens,
            )
        )

        tools = ft.Column(
            controls=[
                section_label("Unit tools", tokens=tokens),
                action_card(
                    "Practice Review",
                    (
                        "Test your memory with an adaptive review of this unit."
                        if self.has_review_material
                        else "Start a lesson to unlock this unit's review material."
                    ),
                    ft.Icons.REPLAY_ROUNDED,
                    lambda _event: self.on_unit_review(self.phase_num, self.unit_num),
                    icon_color=tokens.colors.warning,
                    compact=True,
                    disabled=not self.has_review_material,
                    tokens=tokens,
                ),
                action_card(
                    "Reference Materials",
                    "Browse vocabulary, phrases, and dialogues at your own pace.",
                    ft.Icons.MENU_BOOK_ROUNDED,
                    lambda _event: self.on_passive_read(self.phase_num, self.unit_num),
                    icon_color=tokens.colors.primary,
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
                    responsive_split(
                        lessons_content,
                        tools,
                        primary_columns=8,
                        secondary_columns=4,
                        tokens=tokens,
                    ),
                ],
                max_width=tokens.dimensions.wide_content_width,
                tokens=tokens,
            )
        ]
