"""Present and advance exercises from a study-session engine."""

from collections.abc import Callable

import flet as ft

from engine.lesson_engine import LessonSession
from engine.review_engine import ReviewSession
from gui.activities.dialogues import DialoguePassiveView, LiveDialogueView
from gui.activities.production import MatchMatrix3x3, TypeGeorgian
from gui.activities.receptive import MultipleChoiceCard
from gui.components import (
    completion_state,
    content_card,
    exercise_action_button,
    icon_button,
    message_state,
)
from gui.core.theme import TOKENS, DesignTokens
from gui.services.audio import play_audio_file


class SessionView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        engine=None,
        phase=None,
        unit=None,
        lesson=None,
        on_return: Callable | None = None,
        completion_title: str = "Lesson Completed!",
        completion_action_label: str = "Home",
        completion_action_icon=ft.Icons.HOME_ROUNDED,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        self.page = page
        self.on_return = on_return
        self.completion_title = completion_title
        self.completion_action_label = completion_action_label
        self.completion_action_icon = completion_action_icon
        self.tokens = tokens
        if engine is not None:
            self.engine = engine
        elif lesson is not None:
            self.engine = LessonSession(phase_num=phase, unit_num=unit, lesson_num=lesson)
        else:
            self.engine = ReviewSession(phase_num=phase, unit_num=unit)

        self.current_card_data: dict | None = None
        self.mastered_content: dict[tuple[str, object], dict] = {}

        self.progress_bar = ft.ProgressBar(
            expand=True,
            value=0.0,
            color=tokens.colors.success,
            bgcolor=tokens.colors.subtle_surface,
            border_radius=tokens.radius.sm,
        )
        self.status_text = ft.Text(
            "",
            size=tokens.typography.title_sm,
            weight=ft.FontWeight.BOLD,
        )
        self.card_stage = ft.Container(alignment=ft.alignment.center)
        self.continue_btn = ft.Container(
            content=exercise_action_button(
                "continue",
                lambda _event: self._clear_and_load_next(),
                tokens=tokens,
            ),
            visible=False,
            padding=ft.padding.only(bottom=tokens.spacing.xxxl, top=tokens.spacing.sm),
        )
        self.activity_scroller = ft.Column(
            controls=[self.card_stage, self.continue_btn],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FLAG_ROUNDED, color=tokens.colors.primary),
                    self.progress_bar,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=tokens.dimensions.session_progress_width,
            ),
            self.status_text,
            self.activity_scroller,
        ]

    def did_mount(self) -> None:
        self._load_next_card()

    def _load_next_card(self) -> None:
        card_data = self.engine.get_next_exercise()
        if not card_data:
            self.current_card_data = None
            self._show_completion_screen()
            return

        self.current_card_data = card_data

        activity = card_data.get("activity", "")
        try:
            if activity in {
                "mc_geo_to_eng",
                "mc_eng_to_geo",
                "mc_geo_pair_geo",
                "audio_mc_to_eng",
                "audio_mc_to_geo",
            }:
                self.card_stage.content = MultipleChoiceCard(
                    mode=activity,
                    target_data=card_data.get("target"),
                    distractors=card_data.get("distractors", []),
                    on_submit=self._handle_submission,
                    tokens=self.tokens,
                )
            elif activity == "match_matrix_3x3":
                self.card_stage.content = MatchMatrix3x3(
                    targets=card_data.get("targets", []),
                    on_submit=self._handle_submission,
                    tokens=self.tokens,
                )
            elif activity in {"type_georgian", "audio_dictation"}:
                self.card_stage.content = TypeGeorgian(
                    mode=activity,
                    target_data=card_data.get("target"),
                    on_submit=self._handle_submission,
                    tokens=self.tokens,
                )
            elif activity == "dialogue_passive":
                self.card_stage.content = DialoguePassiveView(
                    dialogue_lines=card_data.get("target", {}).get("lines", []),
                    on_continue=lambda _complete: self._handle_submission(True),
                    tokens=self.tokens,
                )
            elif activity in {
                "dialogue_roleplay_mc",
                "dialogue_activity",
                "dialogue_interactive",
            }:
                self.card_stage.content = LiveDialogueView(
                    steps=card_data.get("target", {}).get("steps", []),
                    on_submit=lambda _complete: self._handle_submission(True),
                    tokens=self.tokens,
                )
            else:
                self.card_stage.content = message_state(
                    "Unsupported activity",
                    f"This version cannot display '{activity}'.",
                    icon=ft.Icons.EXTENSION_OFF_OUTLINED,
                    error=True,
                    tokens=self.tokens,
                )
        except Exception as error:
            self.card_stage.content = message_state(
                "Exercise could not be loaded",
                f"{activity}: {error}",
                icon=ft.Icons.ERROR_OUTLINE_ROUNDED,
                error=True,
                tokens=self.tokens,
            )
        self.update()

    def _handle_submission(self, is_correct, user_input=None) -> None:
        if is_correct:
            self.status_text.value = "Correct! ✨"
            self.status_text.color = self.tokens.colors.success
        else:
            self.status_text.value = "Let’s review that one again."
            self.status_text.color = self.tokens.colors.error

        if is_correct and self.current_card_data:
            self._record_mastered_content(self.current_card_data)

        result = self.engine.submit_answer(is_correct, user_input)
        self.progress_bar.value = result.get("progress", 0.0)
        self.continue_btn.visible = True
        self.update()

    def _clear_and_load_next(self) -> None:
        self.status_text.value = ""
        self.continue_btn.visible = False
        self.card_stage.disabled = False
        self._load_next_card()

    def _record_mastered_content(self, card: dict) -> None:
        """Collect unique non-dialogue material mastered during this session."""
        activity = card.get("activity", "")
        if activity.startswith("dialogue"):
            return

        is_review = bool(
            card.get("is_review_item")
            or (card.get("target") or {}).get("is_review_item")
        )
        if activity == "match_matrix_3x3":
            for target in card.get("targets", []):
                self._remember_mastered_item(target, target.get("id"), False, activity)
            return

        target = card.get("target") or {}
        content_id = card.get("content_id") or target.get("id")
        self._remember_mastered_item(target, content_id, is_review, activity)

    def _remember_mastered_item(
        self,
        target: dict,
        content_id,
        is_review: bool,
        activity: str,
    ) -> None:
        content_type = str(target.get("content_type") or "").casefold()
        is_phrase = content_type == "phrase" or activity == "mc_geo_pair_geo"
        kind = "reviews" if is_review else ("phrases" if is_phrase else "words")
        georgian = target.get("geo") or target.get("correct_geo") or ""
        english = target.get("eng") or target.get("correct_eng") or ""
        if not georgian and not english:
            return
        identity = content_id or target.get("id") or f"{georgian}|{english}"
        key = (kind, identity)
        self.mastered_content.setdefault(
            key,
            {
                "kind": kind,
                "geo": georgian,
                "eng": english,
                "trans": target.get("trans") or "",
                "audio": target.get("audio") or target.get("audio_path"),
            },
        )

    @staticmethod
    def _count_label(count: int, singular: str, plural: str | None = None) -> str:
        return f"{count} {singular if count == 1 else (plural or singular + 's')}"

    def _completion_summary(self) -> tuple[str | None, list[ft.Control]]:
        tokens = self.tokens
        items = list(self.mastered_content.values())
        counts = {
            kind: sum(item["kind"] == kind for item in items)
            for kind in ("words", "phrases", "reviews")
        }
        total = len(items)
        if not total:
            return None, [
                ft.Text(
                    "Every activity completed — congratulations!",
                    size=tokens.typography.body_lg,
                    color=tokens.colors.success,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                )
            ]

        achievements = []
        if counts["words"]:
            achievements.append(self._count_label(counts["words"], "word"))
        if counts["phrases"]:
            achievements.append(self._count_label(counts["phrases"], "phrase"))
        if counts["reviews"]:
            achievements.append(self._count_label(counts["reviews"], "review"))

        item_cards = [self._mastered_item_card(item) for item in items]
        recap = ft.Container(
            width=tokens.dimensions.form_width,
            content=ft.ExpansionTile(
                title=ft.Text(
                    "Review what you practiced",
                    weight=ft.FontWeight.BOLD,
                    color=tokens.colors.text_primary,
                ),
                subtitle=ft.Text(
                    f"{total} mastered item{'' if total == 1 else 's'}",
                    size=tokens.typography.label,
                    color=tokens.colors.text_secondary,
                ),
                leading=ft.Icon(
                    ft.Icons.MENU_BOOK_ROUNDED,
                    color=tokens.colors.primary,
                ),
                controls=[ft.Column(item_cards, spacing=tokens.spacing.sm)],
                controls_padding=ft.padding.only(
                    left=tokens.spacing.sm,
                    right=tokens.spacing.sm,
                    bottom=tokens.spacing.md,
                ),
                collapsed_icon_color=tokens.colors.primary,
                icon_color=tokens.colors.primary,
                shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
                collapsed_shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
            ),
        )
        return f"{total}/{total}", [
            ft.Text(
                " • ".join(achievements),
                size=tokens.typography.title_sm,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.text_primary,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Mastered — congratulations!",
                size=tokens.typography.body_lg,
                color=tokens.colors.success,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            recap,
        ]

    def _mastered_item_card(self, item: dict) -> ft.Card:
        tokens = self.tokens
        kind = item["kind"]
        label = {"words": "Word", "phrases": "Phrase", "reviews": "Review"}[kind]
        icon = {
            "words": ft.Icons.TRANSLATE_ROUNDED,
            "phrases": ft.Icons.FORUM_ROUNDED,
            "reviews": ft.Icons.REPLAY_ROUNDED,
        }[kind]
        subtitle = " • ".join(
            value for value in (label, item.get("trans"), item.get("eng")) if value
        )
        trailing = (
            icon_button(
                ft.Icons.VOLUME_UP_ROUNDED,
                lambda _event, source=item["audio"]: play_audio_file(self.page, source),
                tooltip="Play audio",
                tokens=tokens,
            )
            if item.get("audio")
            else None
        )
        return content_card(
            ft.ListTile(
                leading=ft.Icon(icon, color=tokens.colors.primary),
                title=ft.Text(
                    item.get("geo") or item.get("eng"),
                    weight=ft.FontWeight.BOLD,
                    color=tokens.colors.text_primary,
                ),
                subtitle=(
                    ft.Text(subtitle, color=tokens.colors.text_secondary)
                    if subtitle
                    else None
                ),
                trailing=trailing,
                dense=True,
            ),
            padding=tokens.spacing.xs,
            elevation=tokens.elevation.flat,
            tokens=tokens,
        )

    def _show_completion_screen(self) -> None:
        score, summary = self._completion_summary()
        self.card_stage.content = completion_state(
            title=self.completion_title,
            primary_label=self.completion_action_label,
            on_primary=lambda _event: self.on_return() if self.on_return else None,
            primary_icon=self.completion_action_icon,
            score=score,
            body=summary,
            tokens=self.tokens,
        )
        self.update()
