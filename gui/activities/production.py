"""Production activities: pair matching and Georgian typing."""

from collections.abc import Callable
import math
import random

import flet as ft

from gui.services.audio import play_audio_file
from gui.activities.georgian_input import GeorgianInput
from gui.components import (
    answer_button,
    audio_button,
    exercise_action_button,
    feedback_panel,
    icon_button,
    instruction_banner,
    review_badge,
    set_answer_button_state,
)
from gui.core.theme import TOKENS, DesignTokens


class MatchMatrix3x3(ft.Container):
    def __init__(
        self,
        targets: list,
        on_submit: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(padding=tokens.spacing.xl)
        self.targets = targets
        self.on_submit = on_submit
        self.tokens = tokens
        self.selected_btn: ft.ElevatedButton | None = None
        self.matches_found = 0
        self._build_grid()

    def _build_grid(self) -> None:
        tokens = self.tokens
        georgian = [
            {"type": "geo", "text": target["geo"], "id": target["id"]}
            for target in self.targets
        ]
        english = [
            {"type": "eng", "text": target["eng"], "id": target["id"]}
            for target in self.targets
        ]
        random.shuffle(georgian)
        random.shuffle(english)
        button_width = 160
        grid = ft.Row(
            controls=[
                ft.Column(
                    [self._create_button(item, button_width) for item in georgian],
                    width=button_width,
                    spacing=tokens.spacing.sm,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    [self._create_button(item, button_width) for item in english],
                    width=button_width,
                    spacing=tokens.spacing.sm,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=tokens.spacing.sm,
            tight=True,
        )
        self.content = ft.Column(
            controls=[
                instruction_banner(
                    ft.Icons.JOIN_INNER_ROUNDED,
                    "Match the corresponding pairs",
                    tokens=tokens,
                ),
                ft.Container(height=tokens.spacing.sm),
                grid,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

    def _create_button(self, data: dict, width: int = 160) -> ft.ElevatedButton:
        label = str(data["text"])
        estimated_lines = max(1, math.ceil(len(label) / 18))
        if len(label) <= 18:
            text_size = self.tokens.typography.body_lg
        elif len(label) <= 36:
            text_size = self.tokens.typography.body
        else:
            text_size = self.tokens.typography.body_sm
        height = max(60, self.tokens.spacing.xxl + estimated_lines * (text_size + 4))
        return answer_button(
            label,
            self._handle_tap,
            width=width,
            height=height,
            text_size=text_size,
            data=data,
            tokens=self.tokens,
        )

    def _handle_tap(self, event) -> None:
        clicked = event.control
        if clicked.disabled:
            return
        if self.selected_btn is None:
            self.selected_btn = clicked
            set_answer_button_state(clicked, "selected", tokens=self.tokens)
            self.update()
            return
        if self.selected_btn == clicked:
            set_answer_button_state(clicked, "default", tokens=self.tokens)
            self.selected_btn = None
            self.update()
            return

        first = self.selected_btn
        is_match = (
            first.data["id"] == clicked.data["id"]
            and first.data["type"] != clicked.data["type"]
        )
        if is_match:
            for button in (first, clicked):
                set_answer_button_state(button, "matched", tokens=self.tokens)
                button.opacity = 0.45
                button.disabled = True
            self.matches_found += 1
            self.selected_btn = None
            self.update()
            if self.matches_found == len(self.targets):
                self.on_submit(True)
        else:
            set_answer_button_state(first, "default", tokens=self.tokens)
            self.selected_btn = None
            self.update()


class TypeGeorgian(ft.Column):
    def __init__(
        self,
        mode: str = "type_georgian",
        target_data: dict | None = None,
        on_submit: Callable | None = None,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            spacing=tokens.spacing.lg,
        )
        self.mode = mode
        self.target = target_data or {}
        self.on_submit = on_submit
        self.tokens = tokens
        self.evaluated = False
        self._build_ui()

    def did_mount(self) -> None:
        if self.mode == "audio_dictation":
            self.trigger_audio()

    def _build_ui(self) -> None:
        tokens = self.tokens
        is_dictation = self.mode == "audio_dictation"
        task_icon = ft.Icons.HEADSET_ROUNDED if is_dictation else ft.Icons.KEYBOARD_ROUNDED
        task_text = "Listen and type what you hear" if is_dictation else "Translate and type in Georgian"
        if is_dictation:
            prompt: ft.Control = ft.Column(
                controls=[
                    audio_button(lambda _event: self.trigger_audio(), tokens=tokens),
                    ft.Text(
                        "Tap to listen again",
                        size=tokens.typography.label,
                        color=tokens.colors.text_secondary,
                        italic=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.spacing.xs,
            )
        else:
            prompt = ft.Text(
                self.target.get("eng", ""),
                size=tokens.typography.page_title,
                weight=ft.FontWeight.W_500,
                color=tokens.colors.text_primary,
                text_align=ft.TextAlign.CENTER,
            )

        self.answer_input = GeorgianInput(
            on_submit=self._validate,
            width=tokens.dimensions.form_width,
            tokens=tokens,
        )
        self.input_field = self.answer_input.field
        self.keyboard = self.answer_input.keyboard
        self.feedback_container = ft.Container(visible=False)
        self.submit_btn = ft.Container(
            content=exercise_action_button(
                "check_answer",
                self._validate,
                tokens=tokens,
            )
        )
        controls: list[ft.Control] = []
        badge = review_badge(self.target, tokens=tokens)
        if badge:
            controls.append(badge)
        controls.extend(
            [
                instruction_banner(task_icon, task_text, tokens=tokens),
                ft.Container(height=tokens.spacing.xs),
                prompt,
                self.answer_input,
                self.feedback_container,
                self.submit_btn,
            ]
        )
        self.controls = controls

    def trigger_audio(self) -> None:
        audio_path = self.target.get("audio") or self.target.get("audio_path")
        if self.page and audio_path:
            play_audio_file(self.page, audio_path)

    @staticmethod
    def _normalize_answer(value: str) -> str:
        punctuation = "!?.,;:'\""
        return value.translate(str.maketrans("", "", punctuation)).strip().lower()

    def _validate(self, _event=None) -> None:
        if self.evaluated:
            return
        user_text = self.input_field.value or ""
        target_text = self.target.get("geo", "")
        is_correct = self._normalize_answer(user_text) == self._normalize_answer(target_text)
        self.evaluated = True
        self.answer_input.lock()
        self.submit_btn.visible = False

        body: list[ft.Control] = [
            ft.Text(
                "Correct answer:" if is_correct else "Expected answer:",
                size=self.tokens.typography.label,
                color=(
                    self.tokens.colors.on_success_container
                    if is_correct
                    else self.tokens.colors.on_error_container
                ),
                weight=ft.FontWeight.W_500,
            ),
            ft.Text(
                target_text,
                size=self.tokens.typography.title,
                weight=ft.FontWeight.BOLD,
                color=self.tokens.colors.text_primary,
                text_align=ft.TextAlign.CENTER,
            ),
            icon_button(
                ft.Icons.VOLUME_UP_ROUNDED,
                lambda _event: self.trigger_audio(),
                tooltip="Listen to the correct answer",
                tokens=self.tokens,
            ),
        ]
        transliteration = self.target.get("trans", "")
        if transliteration:
            body.append(
                ft.Text(
                    f"Pronunciation: {transliteration}",
                    size=self.tokens.typography.body_sm,
                    color=self.tokens.colors.text_secondary,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        panel = feedback_panel(
            success=is_correct,
            title="Correct! 🎉" if is_correct else "Not quite…",
            body=body,
            width=self.tokens.dimensions.form_width,
            tokens=self.tokens,
        )
        self.feedback_container.content = panel.content
        self.feedback_container.bgcolor = panel.bgcolor
        self.feedback_container.border = panel.border
        self.feedback_container.border_radius = panel.border_radius
        self.feedback_container.padding = panel.padding
        self.feedback_container.width = panel.width
        self.feedback_container.visible = True
        if not is_correct:
            self.trigger_audio()
        self.update()
        if self.on_submit:
            self.on_submit(is_correct, user_input=user_text.strip())
