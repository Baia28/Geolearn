"""Multiple-choice exercise card for receptive learning activities."""

from collections.abc import Callable
import random

import flet as ft

from gui.services.audio import play_audio_file
from gui.components import (
    answer_button,
    audio_button,
    icon_button,
    instruction_banner,
    review_badge,
    set_answer_button_state,
)
from gui.core.theme import TOKENS, DesignTokens


class MultipleChoiceCard(ft.Container):
    def __init__(
        self,
        mode: str,
        target_data: dict,
        distractors: list,
        on_submit: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            padding=ft.padding.only(
                left=tokens.spacing.xl,
                right=tokens.spacing.xl,
                bottom=tokens.spacing.md,
            ),
            alignment=ft.alignment.top_center,
            border_radius=tokens.radius.lg,
        )
        self.mode = mode
        self.target = target_data or {}
        self.distractors = distractors or []
        self.on_submit = on_submit
        self.tokens = tokens
        self.option_buttons: list[ft.ElevatedButton] = []
        self._build_ui()

    def did_mount(self) -> None:
        if "audio_mc" in self.mode:
            self.trigger_audio()

    def _build_ui(self) -> None:
        tokens = self.tokens
        instruction, task_icon = self._instruction()
        prompt_ui, subtitle_ui, correct_answer = self._prompt()

        options = list(self.distractors) + [correct_answer]
        random.shuffle(options)
        self.option_buttons = [
            answer_button(
                str(option),
                lambda _event, answer=option, correct=correct_answer: self._handle_click(
                    answer, correct
                ),
                width=380,
                height=60,
                data=option,
                tokens=tokens,
            )
            for option in options
        ]

        controls: list[ft.Control] = []
        badge = review_badge(self.target, tokens=tokens)
        if badge:
            controls.append(badge)
        controls.extend(
            [
                instruction_banner(task_icon, instruction, tokens=tokens),
                ft.Container(height=tokens.spacing.xs),
                prompt_ui,
                subtitle_ui,
                ft.Column(
                    controls=self.option_buttons,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.spacing.md,
                ),
            ]
        )
        self.content = ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            spacing=tokens.spacing.sm,
        )

    def _instruction(self) -> tuple[str, object]:
        instructions = {
            "audio_mc_to_eng": ("Listen and select the correct English meaning", ft.Icons.HEADPHONES_ROUNDED),
            "audio_mc_to_geo": ("Listen and select the spoken Georgian word", ft.Icons.HEADPHONES_ROUNDED),
            "mc_geo_to_eng": ("Translate to English", ft.Icons.TRANSLATE_ROUNDED),
            "mc_eng_to_geo": ("Translate to Georgian", ft.Icons.LANGUAGE_ROUNDED),
            "mc_geo_pair_geo": ("Choose the most natural response", ft.Icons.FORUM_ROUNDED),
            "dialogue_context_mc": ("What does this quote mean?", ft.Icons.MENU_BOOK_ROUNDED),
            "dialogue_roleplay_mc": ("Complete the conversation", ft.Icons.PERSON_ADD_ROUNDED),
        }
        return instructions.get(self.mode, ("Choose the correct answer", ft.Icons.TOUCH_APP_ROUNDED))

    def _prompt(self) -> tuple[ft.Control, ft.Control, str]:
        tokens = self.tokens
        if "audio_mc" in self.mode:
            correct = (
                self.target.get("eng", "")
                if self.mode == "audio_mc_to_eng"
                else self.target.get("geo", "")
            )
            subtitle_controls: list[ft.Control] = [
                ft.Text(
                    "Tap to listen again",
                    size=tokens.typography.label,
                    color=tokens.colors.text_secondary,
                    italic=True,
                )
            ]
            transliteration = self.target.get("trans", "")
            if transliteration:
                subtitle_controls.append(
                    ft.Text(
                        f"({transliteration})",
                        size=tokens.typography.body_lg,
                        color=tokens.colors.text_secondary,
                        italic=True,
                    )
                )
            return (
                audio_button(lambda _event: self.trigger_audio(), diameter=110, icon_size=48, tokens=tokens),
                ft.Column(
                    subtitle_controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.spacing.xxs,
                ),
                str(correct),
            )

        if self.mode in {"mc_geo_to_eng", "mc_geo_pair_geo", "dialogue_context_mc"}:
            if self.mode == "mc_geo_to_eng":
                prompt = self.target.get("geo", "")
                correct = self.target.get("eng", "")
                transliteration = self.target.get("trans", "")
            elif self.mode == "mc_geo_pair_geo":
                prompt = self.target.get("prompt_geo") or self.target.get("prompt", "")
                correct = self.target.get("correct_geo") or self.target.get("correct", "")
                transliteration = self.target.get("prompt_trans") or self.target.get("trans", "")
            else:
                prompt = self.target.get("quote_geo", "")
                correct = self.target.get("correct_eng", "")
                transliteration = self.target.get("trans", "")

            prompt_ui = ft.Row(
                controls=[
                    ft.Text(
                        prompt,
                        size=tokens.typography.page_title,
                        weight=ft.FontWeight.BOLD,
                        color=tokens.colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    icon_button(
                        ft.Icons.VOLUME_UP_ROUNDED,
                        lambda _event: self.trigger_audio(),
                        tooltip="Listen",
                        tokens=tokens,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
            )
            subtitle = (
                ft.Text(
                    f"({transliteration})",
                    size=tokens.typography.body_lg,
                    color=tokens.colors.text_muted,
                    italic=True,
                )
                if transliteration
                else ft.Container()
            )
            return prompt_ui, subtitle, str(correct)

        if self.mode == "mc_eng_to_geo":
            prompt = self.target.get("eng", "")
            correct = self.target.get("geo", "")
        elif self.mode == "dialogue_roleplay_mc":
            speaker = self.target.get("speaker", "A")
            context = self.target.get("context_eng", "")
            prompt = f"Complete Speaker {speaker}\nHint: {context}"
            correct = self.target.get("correct_geo", "")
        else:
            prompt = self.target.get("prompt", self.target.get("eng", "Missing prompt"))
            correct = self.target.get("correct", self.target.get("geo", "Missing answer"))

        image_source = self.target.get("image")
        image_widget: ft.Control
        if image_source:
            image_widget = ft.Image(
                src=image_source,
                width=160,
                height=110,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(tokens.radius.md),
            )
        else:
            image_widget = ft.Container(
                width=160,
                height=110,
                bgcolor=tokens.colors.subtle_surface,
                border_radius=tokens.radius.lg,
                border=ft.border.all(1, tokens.colors.border),
                alignment=ft.alignment.center,
                content=ft.Icon(
                    ft.Icons.IMAGE_OUTLINED,
                    size=40,
                    color=tokens.colors.text_muted,
                ),
            )
        prompt_ui = ft.Column(
            controls=[
                image_widget,
                ft.Text(
                    prompt,
                    size=tokens.typography.page_title,
                    weight=ft.FontWeight.BOLD,
                    color=tokens.colors.text_primary,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
        )
        return prompt_ui, ft.Container(), str(correct)

    def trigger_audio(self) -> None:
        audio_path = (
            self.target.get("audio")
            or self.target.get("audio_path")
            or self.target.get("audio_file")
            or self.target.get("file")
        )
        if audio_path and self.page:
            play_audio_file(self.page, audio_path)

    def _handle_click(self, selected, correct) -> None:
        is_correct = selected == correct
        for button in self.option_buttons:
            button.disabled = True
            if button.data == correct:
                set_answer_button_state(button, "correct", tokens=self.tokens)
            elif button.data == selected and not is_correct:
                set_answer_button_state(button, "incorrect", tokens=self.tokens)
        self.update()
        self.on_submit(is_correct, user_input=selected)
