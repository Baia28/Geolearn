"""Interactive and passive dialogue activity components."""

from collections.abc import Callable
import random

import flet as ft

from gui.services.audio import play_audio_file
from gui.components import (
    answer_button,
    feedback_panel,
    primary_button,
    set_answer_button_state,
)
from gui.core.theme import TOKENS, DesignTokens


def audio_replay_hint(tokens: DesignTokens) -> ft.Text:
    return ft.Text(
        "Click a message to hear it again",
        size=tokens.typography.caption,
        color=tokens.colors.text_muted,
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )


def dialogue_avatar(
    speaker: str,
    is_speaker_a: bool,
    tokens: DesignTokens = TOKENS,
) -> ft.CircleAvatar:
    """Shared speaker marker for interactive and reference dialogues."""
    return ft.CircleAvatar(
        content=ft.Text(
            speaker,
            weight=ft.FontWeight.BOLD,
            color=tokens.colors.text_primary,
        ),
        radius=16,
        bgcolor=(
            tokens.colors.subtle_surface
            if is_speaker_a
            else tokens.colors.primary_container
        ),
    )


class ChatBubble(ft.Container):
    def __init__(
        self,
        text: str,
        is_speaker_a: bool,
        subtext: str | None = None,
        audio_path: str | None = None,
        page_ref: ft.Page | None = None,
        on_play: Callable[[str], None] | None = None,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            padding=ft.padding.symmetric(
                horizontal=tokens.spacing.lg,
                vertical=tokens.spacing.md,
            ),
            border_radius=ft.border_radius.only(
                top_left=tokens.radius.lg,
                top_right=tokens.radius.lg,
                bottom_left=tokens.radius.sm if is_speaker_a else tokens.radius.lg,
                bottom_right=tokens.radius.lg if is_speaker_a else tokens.radius.sm,
            ),
            bgcolor=(
                tokens.colors.subtle_surface
                if is_speaker_a
                else tokens.colors.primary_container
            ),
            border=ft.border.all(1, tokens.colors.border),
            ink=bool(audio_path),
            tooltip="Play this line" if audio_path else None,
        )
        controls: list[ft.Control] = [
            ft.Text(
                text,
                color=tokens.colors.text_primary,
                size=tokens.typography.body_lg,
                weight=ft.FontWeight.W_500,
            )
        ]
        if subtext:
            controls.append(
                ft.Text(
                    subtext,
                    color=tokens.colors.text_secondary,
                    size=tokens.typography.label,
                    italic=True,
                )
            )
        self.content = ft.Column(controls, spacing=tokens.spacing.xxs, tight=True)
        if audio_path:
            self.on_click = lambda _event: (
                on_play(audio_path)
                if on_play
                else play_audio_file(page_ref or self.page, audio_path)
            )


class LiveDialogueView(ft.Column):
    def __init__(
        self,
        steps: list,
        on_submit: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        self.steps = steps
        self.on_submit = on_submit
        self.tokens = tokens
        self.current_step_idx = 0
        self.chat_column = ft.Column(
            spacing=tokens.spacing.md,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.chat_container = ft.Container(
            content=ft.Column(
                controls=[audio_replay_hint(tokens), self.chat_column],
                spacing=tokens.spacing.sm,
            ),
            height=240,
            width=tokens.dimensions.dialogue_width,
            padding=tokens.spacing.md,
            border=ft.border.all(1, tokens.colors.border),
            border_radius=tokens.radius.lg,
            bgcolor=tokens.colors.surface,
        )
        self.options_container = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
        )
        self.option_buttons: list[tuple[ft.ElevatedButton, dict]] = []
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text(
                        "Roleplay Practice",
                        size=tokens.typography.title_sm,
                        weight=ft.FontWeight.BOLD,
                        color=tokens.colors.text_primary,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "You: Speaker B",
                            size=tokens.typography.label,
                            color=tokens.colors.on_primary,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=tokens.colors.primary,
                        padding=ft.padding.symmetric(
                            horizontal=tokens.spacing.sm,
                            vertical=tokens.spacing.xs,
                        ),
                        border_radius=tokens.radius.pill,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=tokens.spacing.md,
                wrap=True,
            ),
            self.chat_container,
            self.options_container,
        ]

    def did_mount(self) -> None:
        self._advance_dialogue()

    def _add_bubble(
        self,
        text: str,
        is_speaker_a: bool,
        subtext: str | None = None,
        audio_path: str | None = None,
    ) -> None:
        bubble = ChatBubble(
            text=text,
            is_speaker_a=is_speaker_a,
            subtext=subtext,
            audio_path=audio_path,
            page_ref=self.page,
            tokens=self.tokens,
        )
        avatar = dialogue_avatar(
            "A" if is_speaker_a else "B",
            is_speaker_a,
            self.tokens,
        )
        self.chat_column.controls.append(
            ft.Row(
                [avatar, bubble] if is_speaker_a else [bubble, avatar],
                alignment=(
                    ft.MainAxisAlignment.START
                    if is_speaker_a
                    else ft.MainAxisAlignment.END
                ),
            )
        )
        self.chat_column.update()
        self.chat_column.scroll_to(offset=-1, duration=self.tokens.motion.slow)
        if audio_path:
            play_audio_file(self.page, audio_path)

    def _advance_dialogue(self) -> None:
        if self.current_step_idx >= len(self.steps):
            self.options_container.controls = [
                ft.Text(
                    "Dialogue completed! 🎉",
                    size=self.tokens.typography.body_lg,
                    weight=ft.FontWeight.BOLD,
                    color=self.tokens.colors.success,
                )
            ]
            self.update()
            self.on_submit(True)
            return

        step = self.steps[self.current_step_idx]
        if step["type"] == "prompt":
            self._add_bubble(step["text"], is_speaker_a=True, audio_path=step.get("audio"))
            self.current_step_idx += 1
            self._advance_dialogue()
            return

        if step["type"] != "choice":
            return
        self.options_container.controls = [
            ft.Text(
                "Your turn: choose Speaker B’s response",
                size=self.tokens.typography.body_sm,
                weight=ft.FontWeight.W_500,
                color=self.tokens.colors.primary,
            )
        ]
        choices = list(step["distractors"]) + [step["correct"]]
        random.shuffle(choices)
        self.option_buttons = []
        for option in choices:
            button = answer_button(
                option["geo"],
                lambda _event, selected=option, correct=step["correct"]: self._handle_choice(
                    selected, correct
                ),
                width=self.tokens.dimensions.form_width,
                data=option,
                tokens=self.tokens,
            )
            self.option_buttons.append((button, option))
            self.options_container.controls.append(button)
        self.update()

    def _handle_choice(self, selected: dict, correct: dict) -> None:
        is_correct = selected["geo"] == correct["geo"]
        for button, option in self.option_buttons:
            button.disabled = True
            if option["geo"] == correct["geo"]:
                set_answer_button_state(button, "correct", tokens=self.tokens)
            elif option["geo"] == selected["geo"] and not is_correct:
                set_answer_button_state(button, "incorrect", tokens=self.tokens)

        body: list[ft.Control]
        if is_correct:
            body = [
                ft.Text(
                    f"{correct['geo']} ({correct.get('trans', '')}) — {correct.get('eng', '')}",
                    size=self.tokens.typography.body_sm,
                    color=self.tokens.colors.on_success_container,
                    text_align=ft.TextAlign.CENTER,
                )
            ]
        else:
            body = [
                ft.Text(
                    f"You selected: {selected['geo']} ({selected.get('trans', '')})",
                    size=self.tokens.typography.label,
                    color=self.tokens.colors.on_error_container,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    f"Correct: {correct['geo']} ({correct.get('trans', '')}) — {correct.get('eng', '')}",
                    size=self.tokens.typography.label,
                    color=self.tokens.colors.on_success_container,
                    text_align=ft.TextAlign.CENTER,
                ),
            ]
        panel = feedback_panel(
            success=is_correct,
            title="Excellent!" if is_correct else "Incorrect answer",
            body=body,
            width=self.tokens.dimensions.form_width,
            tokens=self.tokens,
        )
        self.options_container.controls.extend(
            [
                panel,
                primary_button(
                    "Next line",
                    lambda _event: self._next_step_after_choice(
                        correct["geo"], correct.get("audio")
                    ),
                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                    width=self.tokens.dimensions.form_width,
                    tokens=self.tokens,
                ),
            ]
        )
        self.update()
        self.scroll_to(offset=-1, duration=self.tokens.motion.slow)

    def _next_step_after_choice(self, correct_text: str, audio_path: str | None = None) -> None:
        self._add_bubble(correct_text, is_speaker_a=False, audio_path=audio_path)
        self.current_step_idx += 1
        self.options_container.controls.clear()
        self._advance_dialogue()


class DialoguePassiveView(ft.Column):
    def __init__(
        self,
        dialogue_lines: list,
        on_continue: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=tokens.spacing.md,
        )
        chat_column = ft.Column(
            spacing=tokens.spacing.md,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        for line in dialogue_lines:
            speaker, georgian = line[0], line[1]
            transliteration = line[2] if len(line) > 2 else ""
            english = line[3] if len(line) > 3 else ""
            audio = line[4] if len(line) > 4 else None
            is_speaker_a = speaker == "A"
            bubble = ChatBubble(
                text=georgian,
                is_speaker_a=is_speaker_a,
                subtext=f"{transliteration} — {english}" if transliteration or english else None,
                audio_path=audio,
                tokens=tokens,
            )
            avatar = dialogue_avatar(speaker, is_speaker_a, tokens)
            chat_column.controls.append(
                ft.Row(
                    [avatar, bubble] if is_speaker_a else [bubble, avatar],
                    alignment=(
                        ft.MainAxisAlignment.START
                        if is_speaker_a
                        else ft.MainAxisAlignment.END
                    ),
                )
            )

        self.controls = [
            ft.Text(
                "Reading Practice",
                size=tokens.typography.title,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.text_primary,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[audio_replay_hint(tokens), chat_column],
                    spacing=tokens.spacing.sm,
                ),
                height=320,
                width=tokens.dimensions.dialogue_width,
                padding=tokens.spacing.md,
                border=ft.border.all(1, tokens.colors.border),
                border_radius=tokens.radius.lg,
                bgcolor=tokens.colors.surface,
            ),
            primary_button(
                "Start roleplay",
                lambda _event: on_continue(True),
                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                width=tokens.dimensions.form_width,
                tokens=tokens,
            ),
        ]
