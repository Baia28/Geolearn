"""Collapsible reference library for completed lesson material."""

from collections.abc import Callable

import flet as ft

from gui.activities.dialogues import ChatBubble, audio_replay_hint, dialogue_avatar
from gui.components import content_card, icon_button, message_state, page_header
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


class PassiveReviewView(ft.Column):
    """Render unit materials or the learner's unlockable global library."""

    def __init__(
        self,
        master_sheet: dict,
        unit_title: str,
        on_back: Callable,
        play_audio: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.tokens = tokens
        self.play_audio = play_audio
        self.master_sheet = master_sheet
        self.controls = [self._build(unit_title, on_back)]

    def _build(self, unit_title: str, on_back: Callable) -> ft.Control:
        tokens = self.tokens
        unit_scope = self._is_unit_scope()
        tab_specs = [
            ("📖 Vocabulary", "vocab"),
            ("💬 Phrases", "phrases"),
            ("🎭 Dialogues", "dialogues"),
        ]
        if unit_scope:
            tab_specs = [
                spec
                for spec in tab_specs
                if any(
                    self._section_has_category(section, spec[1])
                    for section in self.master_sheet.values()
                )
            ]
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=tokens.motion.slow,
            expand=1,
            tab_alignment=ft.TabAlignment.CENTER,
            indicator_color=tokens.colors.primary,
            label_color=tokens.colors.text_primary,
            unselected_label_color=tokens.colors.text_muted,
            tabs=[],
        )
        tabs.tabs.extend(
            ft.Tab(text=label, content=self._hierarchy(category))
            for label, category in tab_specs
        )

        controls: list[ft.Control] = [
            page_header(
                "Memory Library",
                eyebrow=self._scope_label(unit_title),
                subtitle=(
                    "Choose a lesson to browse its unlocked material."
                    if unit_scope
                    else "Expand a phase, unit, and lesson to browse your unlocked material."
                ),
                on_back=on_back,
                back_label="Back",
                max_width=tokens.dimensions.content_width,
                tokens=tokens,
            )
        ]
        controls.append(
            tabs
            if tab_specs
            else message_state(
                "No reference material yet",
                "Start a lesson in this unit to add material to your library.",
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                tokens=tokens,
            )
        )
        return page_shell(
            controls,
            max_width=tokens.dimensions.content_width,
            scroll=False,
            tokens=tokens,
        )

    def _new_list(self, controls: list[ft.Control] | None = None) -> ft.ListView:
        return ft.ListView(
            controls=controls or [],
            expand=1,
            spacing=self.tokens.spacing.md,
            padding=ft.padding.only(
                left=self.tokens.spacing.sm,
                right=self.tokens.spacing.sm,
                bottom=self.tokens.spacing.xl,
            ),
        )

    @staticmethod
    def _numbered_title(kind: str, number: int, title: str | None) -> str:
        prefix = f"{kind} {number}"
        clean_title = (title or "").strip()
        if not clean_title or clean_title.casefold() == prefix.casefold():
            return prefix
        return f"{prefix} — {clean_title[:1].upper()}{clean_title[1:]}"

    def _scope_label(self, fallback: str) -> str:
        sections = list(self.master_sheet.values())
        coordinates = {
            (section.get("phase_num"), section.get("unit_num"))
            for section in sections
        }
        if len(coordinates) != 1 or not sections:
            return fallback
        section = sections[0]
        return " • ".join(
            [
                self._numbered_title(
                    "Phase", section.get("phase_num", 0), section.get("phase_title")
                ),
                self._numbered_title(
                    "Unit", section.get("unit_num", 0), section.get("unit_title")
                ),
            ]
        )

    def _is_unit_scope(self) -> bool:
        """A unit library already identifies its phase and unit in the page header."""
        coordinates = {
            (section.get("phase_num"), section.get("unit_num"))
            for section in self.master_sheet.values()
        }
        return bool(self.master_sheet) and len(coordinates) == 1

    @staticmethod
    def _loaded_category_count(section: dict, category: str) -> int:
        if category == "vocab":
            return len(section.get("vocab", []))
        if category == "phrases":
            return len(section.get("phrases", [])) + len(section.get("pairs", []))
        return len(section.get("dialogues", []))

    def _section_has_category(self, section: dict, category: str) -> bool:
        if section.get("locked", False):
            return section.get("category_counts", {}).get(category, 0) > 0
        return self._loaded_category_count(section, category) > 0

    def _grouped_sections(self, category: str | None = None) -> dict:
        phases: dict = {}
        for section in self.master_sheet.values():
            if category and not self._section_has_category(section, category):
                continue
            phase_num = section.get("phase_num", 0)
            unit_num = section.get("unit_num", 0)
            phase = phases.setdefault(
                phase_num,
                {"title": section.get("phase_title"), "units": {}},
            )
            unit = phase["units"].setdefault(
                unit_num,
                {"title": section.get("unit_title"), "lessons": []},
            )
            unit["lessons"].append(section)
        return phases

    def _hierarchy(self, category: str) -> ft.ListView:
        grouped = self._grouped_sections(category)
        if not grouped:
            return self._new_list()
        if self._is_unit_scope():
            phase = next(iter(grouped.values()))
            unit = next(iter(phase["units"].values()))
            lessons = sorted(
                unit["lessons"],
                key=lambda item: item.get("lesson_num", 0),
            )
            return self._new_list(
                [self._lesson_section(lesson, category) for lesson in lessons]
            )

        phase_cards: list[ft.Control] = []
        for phase_num, phase in sorted(grouped.items()):
            lessons = [
                lesson
                for unit in phase["units"].values()
                for lesson in unit["lessons"]
            ]
            unlocked = sum(not lesson.get("locked", False) for lesson in lessons)
            locked = unlocked == 0
            unit_cards = [
                self._unit_section(unit_num, unit, category)
                for unit_num, unit in sorted(phase["units"].items())
            ]
            phase_cards.append(
                self._hierarchy_tile(
                    self._numbered_title("Phase", phase_num, phase["title"]),
                    self._availability_label(unlocked, len(lessons)),
                    ft.Icons.AUTO_STORIES_ROUNDED,
                    unit_cards,
                    locked=locked,
                    level="phase",
                )
            )
        return self._new_list(phase_cards)

    def _unit_section(self, unit_num: int, unit: dict, category: str) -> ft.Card:
        lessons = sorted(unit["lessons"], key=lambda item: item.get("lesson_num", 0))
        unlocked = sum(not lesson.get("locked", False) for lesson in lessons)
        return self._hierarchy_tile(
            self._numbered_title("Unit", unit_num, unit["title"]),
            self._availability_label(unlocked, len(lessons)),
            ft.Icons.FOLDER_ROUNDED,
            [self._lesson_section(lesson, category) for lesson in lessons],
            locked=unlocked == 0,
            level="unit",
        )

    def _lesson_section(self, section: dict, category: str) -> ft.Card:
        label = self._numbered_title(
            "Lesson",
            section.get("lesson_num", 0),
            section.get("lesson_title"),
        )
        if section.get("locked", False):
            return self._hierarchy_tile(
                label,
                "Locked — complete or begin this lesson to unlock its material.",
                ft.Icons.MENU_BOOK_OUTLINED,
                [],
                locked=True,
                level="lesson",
            )

        content, count = self._category_content(section, category)
        noun = {
            "vocab": "vocabulary item",
            "phrases": "phrase or conversation pair",
            "dialogues": "dialogue",
        }[category]
        subtitle = f"{count} {noun}{'' if count == 1 else 's'}"
        return self._hierarchy_tile(
            label,
            subtitle,
            ft.Icons.MENU_BOOK_OUTLINED,
            [content],
            locked=False,
            level="lesson",
        )

    def _category_content(self, section: dict, category: str) -> tuple[ft.Control, int]:
        if category == "vocab":
            items = section.get("vocab", [])
            return self._vocabulary_grid(items), len(items)
        if category == "phrases":
            phrases = section.get("phrases", [])
            pairs = section.get("pairs", [])
            return self._phrases_grid(phrases, pairs), len(phrases) + len(pairs)
        dialogues = section.get("dialogues", [])
        return self._dialogues(dialogues), len(dialogues)

    @staticmethod
    def _availability_label(unlocked: int, total: int) -> str:
        if unlocked == 0:
            return "Locked — complete or begin an earlier lesson to continue."
        return f"{unlocked} of {total} lessons available"

    def _hierarchy_tile(
        self,
        label: str,
        subtitle: str,
        icon,
        controls: list[ft.Control],
        *,
        locked: bool,
        level: str,
    ) -> ft.Card:
        tokens = self.tokens
        background = {
            "phase": tokens.colors.phase_surface,
            "unit": tokens.colors.unit_surface,
            "lesson": tokens.colors.lesson_surface,
        }[level]
        accent = {
            "phase": tokens.colors.text_primary,
            "unit": tokens.colors.warning,
            "lesson": tokens.colors.primary,
        }[level]
        return content_card(
            ft.ExpansionTile(
                title=ft.Text(
                    label,
                    size=tokens.typography.body_lg,
                    weight=ft.FontWeight.BOLD,
                    color=(tokens.colors.text_muted if locked else tokens.colors.text_primary),
                ),
                subtitle=ft.Text(
                    subtitle,
                    size=tokens.typography.label,
                    color=tokens.colors.text_muted if locked else tokens.colors.text_secondary,
                ),
                leading=ft.Icon(
                    ft.Icons.LOCK_ROUNDED if locked else icon,
                    color=tokens.colors.text_muted if locked else accent,
                ),
                trailing=(
                    ft.Icon(ft.Icons.LOCK_ROUNDED, color=tokens.colors.text_muted)
                    if locked
                    else None
                ),
                show_trailing_icon=not locked,
                disabled=locked,
                controls=controls,
                controls_padding=ft.padding.only(
                    left=tokens.spacing.md,
                    right=tokens.spacing.md,
                    bottom=tokens.spacing.md,
                ),
                collapsed_icon_color=accent,
                icon_color=accent,
                shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
                collapsed_shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
            ),
            bgcolor=background,
            padding=0,
            elevation=tokens.elevation.flat,
            tokens=tokens,
        )

    def _surface_card(
        self,
        content: ft.Control,
        *,
        bgcolor: str | None = None,
    ) -> ft.Card:
        return content_card(
            content,
            bgcolor=bgcolor,
            padding=self.tokens.spacing.md,
            elevation=self.tokens.elevation.flat,
            tokens=self.tokens,
        )

    def _audio_action(self, audio_path: str | None, label: str) -> ft.Control:
        if not audio_path:
            return ft.Container(width=self.tokens.dimensions.touch_target)
        return icon_button(
            ft.Icons.VOLUME_UP_ROUNDED,
            lambda _event, source=audio_path: self.play_audio(source),
            tooltip=label,
            tokens=self.tokens,
        )

    def _vocabulary_grid(self, vocab: list) -> ft.ResponsiveRow:
        tokens = self.tokens
        grid = ft.ResponsiveRow(columns=12, spacing=tokens.spacing.md, run_spacing=tokens.spacing.md)
        for item in vocab:
            grid.controls.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=self._surface_card(
                        ft.ListTile(
                            title=ft.Text(
                                item.get("geo", ""),
                                size=tokens.typography.title_sm,
                                weight=ft.FontWeight.BOLD,
                                color=tokens.colors.text_primary,
                            ),
                            subtitle=ft.Text(
                                f"{item.get('trans', '')} • {item.get('eng', '')}",
                                color=tokens.colors.text_secondary,
                            ),
                            trailing=self._audio_action(item.get("audio"), "Play vocabulary audio"),
                        )
                    ),
                )
            )
        return grid

    def _phrases_grid(self, phrases: list, pairs: list) -> ft.ResponsiveRow:
        tokens = self.tokens
        grid = ft.ResponsiveRow(columns=12, spacing=tokens.spacing.md, run_spacing=tokens.spacing.md)
        for item in phrases:
            grid.controls.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=self._surface_card(
                        ft.ListTile(
                            title=ft.Text(
                                item.get("geo", ""),
                                size=tokens.typography.title_sm,
                                weight=ft.FontWeight.BOLD,
                                color=tokens.colors.text_primary,
                            ),
                            subtitle=ft.Text(
                                f"{item.get('trans', '')} • {item.get('eng', '')}",
                                color=tokens.colors.text_secondary,
                            ),
                            trailing=self._audio_action(item.get("audio"), "Play phrase audio"),
                        )
                    ),
                )
            )

        for pair in pairs:
            prompt = pair["prompt"]
            response = pair["correct_response"]
            grid.controls.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=self._surface_card(
                        ft.Column(
                            controls=[
                                ft.Text(
                                    f"Q: {prompt['georgian']} ({prompt['english']})",
                                    weight=ft.FontWeight.W_600,
                                    color=tokens.colors.text_primary,
                                ),
                                ft.Text(
                                    f"A: {response['georgian']} ({response['english']})",
                                    color=tokens.colors.on_primary_container,
                                ),
                            ],
                            spacing=tokens.spacing.xs,
                        ),
                        bgcolor=tokens.colors.primary_container,
                    ),
                )
            )
        return grid

    def _dialogues(self, dialogues: list) -> ft.Column:
        tokens = self.tokens
        dialogue_cards = []
        for index, lines in enumerate(dialogues, start=1):
            chat_rows: list[ft.Control] = []
            has_audio = any(len(line) > 4 and line[4] for line in lines)
            for line in lines:
                speaker = line[0]
                georgian = line[1]
                transliteration = line[2] if len(line) > 2 else ""
                english = line[3] if len(line) > 3 else ""
                audio_path = line[4] if len(line) > 4 else None
                is_speaker_a = speaker == "A"
                subtext = " — ".join(
                    value for value in (transliteration, english) if value
                )
                bubble = ChatBubble(
                    text=georgian,
                    is_speaker_a=is_speaker_a,
                    subtext=subtext or None,
                    audio_path=audio_path,
                    on_play=self.play_audio,
                    tokens=tokens,
                )
                avatar = dialogue_avatar(speaker, is_speaker_a, tokens)
                chat_rows.append(
                    ft.Row(
                        [avatar, bubble] if is_speaker_a else [bubble, avatar],
                        alignment=(
                            ft.MainAxisAlignment.START
                            if is_speaker_a
                            else ft.MainAxisAlignment.END
                        ),
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    )
                )
            content_controls: list[ft.Control] = [
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.FORUM_ROUNDED,
                            color=tokens.colors.primary,
                            size=tokens.dimensions.icon_sm,
                        ),
                        ft.Text(
                            f"Dialogue {index}",
                            weight=ft.FontWeight.BOLD,
                            color=tokens.colors.text_primary,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{len(lines)} lines",
                                size=tokens.typography.caption,
                                color=tokens.colors.on_primary_container,
                            ),
                            bgcolor=tokens.colors.primary_container,
                            padding=ft.padding.symmetric(
                                horizontal=tokens.spacing.sm,
                                vertical=tokens.spacing.xs,
                            ),
                            border_radius=tokens.radius.pill,
                        ),
                    ],
                    spacing=tokens.spacing.sm,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ]
            if has_audio:
                content_controls.append(audio_replay_hint(tokens))
            content_controls.append(ft.Column(chat_rows, spacing=tokens.spacing.md))
            dialogue_cards.append(
                self._surface_card(
                    ft.Column(content_controls, spacing=tokens.spacing.md),
                    bgcolor=tokens.colors.surface,
                )
            )
        return ft.Column(dialogue_cards, spacing=tokens.spacing.md)
