"""Visual alphabet-association quiz with pronunciation feedback."""

from collections.abc import Callable
import random

import flet as ft

from gui.services.audio import play_audio_file
from gui.components import (
    answer_button,
    completion_state,
    exercise_action_button,
    feedback_panel,
    icon_button,
    page_header,
    set_answer_button_state,
)
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class AnbanGameView(ft.Column):
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
        self.all_alphabet_letters: list[str] = []
        self.letter_audio_by_geo: dict[str, str | None] = {}
        self.score = 0
        self.total_questions = 0

    def start_game(self) -> None:
        self.questions = self.db.get_anban_game_questions()
        self.remaining_questions = list(self.questions)
        self.all_alphabet_letters = [question["correct_geo"] for question in self.questions]
        self.letter_audio_by_geo = {
            question["correct_geo"]: question.get("letter_audio")
            for question in self.questions
        }
        self.score = 0
        self.total_questions = len(self.questions)
        self.play_round()

    def play_round(self) -> None:
        if not self.remaining_questions:
            self.show_game_over()
            return
        tokens = self.tokens
        target = random.choice(self.remaining_questions)
        self.remaining_questions.remove(target)
        correct = target["correct_geo"]
        correct_audio = target.get("letter_audio")
        choices = [correct] + random.sample(
            [letter for letter in self.all_alphabet_letters if letter != correct],
            min(3, max(0, len(self.all_alphabet_letters) - 1)),
        )
        random.shuffle(choices)

        score_text = ft.Text(
            f"Score: {self.score}",
            size=tokens.typography.body_lg,
            weight=ft.FontWeight.BOLD,
            color=tokens.colors.primary,
        )
        feedback_container = ft.Container(visible=False)
        next_button = exercise_action_button(
            "continue",
            lambda _event: self.play_round(),
            tokens=tokens,
        )
        next_button.visible = False
        option_buttons: list[ft.ElevatedButton] = []

        def check_answer(selected: str) -> None:
            is_correct = selected == correct
            for button in option_buttons:
                button.disabled = True
                if button.data == correct:
                    set_answer_button_state(button, "correct", tokens=tokens)
                elif button.data == selected and not is_correct:
                    set_answer_button_state(button, "incorrect", tokens=tokens)
            if is_correct:
                self.score += 1
                score_text.value = f"Score: {self.score}"

            body: list[ft.Control] = []
            if not is_correct:
                selected_audio = self.letter_audio_by_geo.get(selected)
                body.extend(
                    [
                        self._answer_audio_row(
                            f"You chose {selected}",
                            selected_audio,
                            f"Hear {selected}",
                            tokens.colors.on_error_container,
                        ),
                        self._answer_audio_row(
                            f"Correct answer: {correct}",
                            correct_audio,
                            f"Hear {correct}",
                            tokens.colors.on_success_container,
                        ),
                    ]
                )
            panel = feedback_panel(
                success=is_correct,
                title="Correct!" if is_correct else "Not quite…",
                body=body,
                width=tokens.dimensions.form_width,
                tokens=tokens,
            )
            feedback_container.content = panel.content
            feedback_container.bgcolor = panel.bgcolor
            feedback_container.border = panel.border
            feedback_container.border_radius = panel.border_radius
            feedback_container.padding = panel.padding
            feedback_container.width = panel.width
            feedback_container.visible = True
            next_button.visible = True
            self.update()
            if correct_audio and self.page:
                play_audio_file(self.page, correct_audio)

        option_buttons.extend(
            answer_button(
                choice,
                lambda _event, selected=choice: check_answer(selected),
                width=76,
                height=76,
                text_size=tokens.typography.page_title,
                data=choice,
                tokens=tokens,
            )
            for choice in choices
        )
        question_number = self.total_questions - len(self.remaining_questions)
        image_source = target.get("example_image")
        image = (
            ft.Image(
                src=image_source,
                width=tokens.dimensions.illustration_size,
                height=tokens.dimensions.illustration_size,
                fit=ft.ImageFit.CONTAIN,
            )
            if image_source
            else ft.Container(
                width=tokens.dimensions.illustration_size,
                height=tokens.dimensions.illustration_size,
                alignment=ft.alignment.center,
                bgcolor=tokens.colors.subtle_surface,
                border_radius=tokens.radius.lg,
                content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, color=tokens.colors.text_muted),
            )
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Anbani Associations",
                        on_back=lambda _event: self.on_back_to_menu(),
                        back_label="Back to alphabet hub",
                        trailing=score_text,
                        max_width=tokens.dimensions.reading_width,
                        tokens=tokens,
                    ),
                    ft.Text(
                        f"Question {question_number} of {self.total_questions}",
                        size=tokens.typography.body,
                        color=tokens.colors.text_secondary,
                    ),
                    ft.Text(
                        "Which letter goes with this image?",
                        size=tokens.typography.title_sm,
                        weight=ft.FontWeight.W_500,
                        color=tokens.colors.text_primary,
                    ),
                    image,
                    ft.Row(
                        option_buttons,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=tokens.spacing.lg,
                        run_spacing=tokens.spacing.lg,
                    ),
                    feedback_container,
                    next_button,
                ],
                max_width=tokens.dimensions.reading_width,
                tokens=tokens,
            )
        ]
        if self.page:
            self.update()

    def _answer_audio_row(
        self,
        label: str,
        audio_path: str | None,
        tooltip: str,
        color: str,
    ) -> ft.Row:
        controls: list[ft.Control] = [
            ft.Text(
                label,
                size=self.tokens.typography.body_lg,
                weight=ft.FontWeight.BOLD,
                color=color,
            )
        ]
        if audio_path:
            controls.append(
                icon_button(
                    ft.Icons.VOLUME_UP_ROUNDED,
                    lambda _event: play_audio_file(self.page, audio_path),
                    tooltip=tooltip,
                    tokens=self.tokens,
                )
            )
        return ft.Row(controls, alignment=ft.MainAxisAlignment.CENTER, spacing=self.tokens.spacing.xs)

    def show_game_over(self) -> None:
        percent = int((self.score / self.total_questions) * 100) if self.total_questions else 0
        self.controls = [
            completion_state(
                title="Quiz complete!",
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
