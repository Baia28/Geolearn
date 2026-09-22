"""Audio dictation game for Georgian letters."""

from collections.abc import Callable
import random

import flet as ft

from gui.services.audio import play_audio_file
from gui.activities.georgian_input import GeorgianInput
from gui.components import (
    audio_button,
    completion_state,
    exercise_action_button,
    feedback_panel,
    icon_button,
    instruction_banner,
    page_header,
)
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


VOWELS = {"ა", "ე", "ი", "ო", "უ"}


class AlphabetTypingGameView(ft.Column):
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
        self.questions: list[dict] = []
        self.remaining_questions: list[dict] = []
        self.current_target: dict | None = None
        self.score = 0
        self.total_questions = 0
        self.evaluated = False

    def start_game(self) -> None:
        self.questions = [
            item for item in self.db.get_alphabet_letters() if item.get("letter_audio")
        ]
        random.shuffle(self.questions)
        self.remaining_questions = list(self.questions)
        self.score = 0
        self.total_questions = len(self.questions)
        self.play_round()

    def play_round(self) -> None:
        if not self.remaining_questions:
            self.show_game_over()
            return
        tokens = self.tokens
        self.evaluated = False
        self.current_target = self.remaining_questions.pop(0)
        progress = self.total_questions - len(self.remaining_questions)
        score_text = ft.Text(
            f"Score: {self.score}",
            size=tokens.typography.body_lg,
            weight=ft.FontWeight.BOLD,
            color=tokens.colors.primary,
        )
        self.answer_input = GeorgianInput(
            on_submit=self._validate,
            width=tokens.dimensions.form_width,
            tokens=tokens,
        )
        self.feedback_container = ft.Container(visible=False)
        self.submit_btn = ft.Container(
            content=exercise_action_button(
                "check_answer",
                self._validate,
                tokens=tokens,
            )
        )
        self.next_btn = exercise_action_button(
            "continue",
            lambda _event: self.play_round(),
            tokens=tokens,
        )
        self.next_btn.visible = False
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Listen & Type",
                        on_back=lambda _event: self.on_back_to_menu(),
                        back_label="Back to alphabet hub",
                        trailing=score_text,
                        max_width=tokens.dimensions.reading_width,
                        tokens=tokens,
                    ),
                    ft.Text(
                        f"Question {progress} of {self.total_questions}",
                        size=tokens.typography.body,
                        color=tokens.colors.text_secondary,
                    ),
                    instruction_banner(
                        ft.Icons.HEADSET_ROUNDED,
                        "Listen and type what you hear",
                        tokens=tokens,
                    ),
                    audio_button(lambda _event: self.trigger_audio(), tokens=tokens),
                    ft.Text(
                        "Tap to listen again",
                        size=tokens.typography.label,
                        color=tokens.colors.text_secondary,
                        italic=True,
                    ),
                    self.answer_input,
                    self.feedback_container,
                    self.submit_btn,
                    self.next_btn,
                ],
                max_width=tokens.dimensions.reading_width,
                tokens=tokens,
            )
        ]
        if self.page:
            self.update()
        self.trigger_audio()

    def trigger_audio(self) -> None:
        if self.current_target and self.page:
            audio_path = self.current_target.get("letter_audio")
            if audio_path:
                play_audio_file(self.page, audio_path)

    def _validate(self, _event=None) -> None:
        if self.evaluated or not self.current_target:
            return
        tokens = self.tokens
        user_text = self.answer_input.value
        correct = self.current_target.get("georgian", "").strip()
        description = self.current_target.get("linguistic_desc") or self.current_target.get(
            "transliteration", ""
        )
        is_correct = user_text == correct
        self.evaluated = True
        if is_correct:
            self.score += 1
        self.answer_input.lock()
        self.submit_btn.visible = False
        self.next_btn.visible = True

        body: list[ft.Control] = [
            ft.Text(
                "Correct answer:" if is_correct else "Expected answer:",
                size=tokens.typography.label,
                weight=ft.FontWeight.W_500,
                color=(
                    tokens.colors.on_success_container
                    if is_correct
                    else tokens.colors.on_error_container
                ),
            ),
            ft.Text(
                correct,
                size=44,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.error if correct in VOWELS else tokens.colors.text_primary,
            ),
            icon_button(
                ft.Icons.VOLUME_UP_ROUNDED,
                lambda _event: self.trigger_audio(),
                tooltip="Listen again",
                tokens=tokens,
            ),
        ]
        if description:
            body.append(
                ft.Text(
                    f"Pronunciation: {description}",
                    size=tokens.typography.body,
                    color=tokens.colors.text_secondary,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        panel = feedback_panel(
            success=is_correct,
            title="Correct! 🎉" if is_correct else "Not quite…",
            body=body,
            width=tokens.dimensions.form_width,
            tokens=tokens,
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

    def show_game_over(self) -> None:
        percent = int((self.score / self.total_questions) * 100) if self.total_questions else 0
        self.controls = [
            completion_state(
                title="Typing quiz complete!",
                subtitle=f"Final score: {self.score} / {self.total_questions}",
                score=f"{percent}%",
                primary_label="Play again",
                on_primary=lambda _event: self.start_game(),
                secondary_label="Alphabet hub",
                on_secondary=lambda _event: self.on_back_to_menu(),
                tokens=self.tokens,
            )
        ]
        if self.page:
            self.update()
