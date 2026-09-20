"""Collapsible reference library for completed lesson material."""

import flet as ft


class PassiveReviewView(ft.View):
    """Render unit materials or the learner's unlockable global reference library."""

    def __init__(self, master_sheet: dict, unit_title: str, on_back: callable, play_audio: callable):
        has_locked_sections = any(section.get("locked", False) for section in master_sheet.values())
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            tab_alignment=ft.TabAlignment.CENTER,
            indicator_color=ft.Colors.PURPLE_600,
            label_color=ft.Colors.PURPLE_900,
            tabs=[],
        )
        vocab_list = self._new_list()
        phrases_list = self._new_list()
        dialogues_list = self._new_list()

        for raw_label, section in master_sheet.items():
            label = self._format_section_label(raw_label)
            if section.get("locked", False):
                continue

            vocab = section.get("vocab", [])
            if vocab:
                vocab_list.controls.append(
                    self._expandable_section(
                        label,
                        "Vocabulary",
                        ft.Icons.MENU_BOOK_OUTLINED,
                        self._vocabulary_grid(vocab, play_audio),
                    )
                )

            phrases = section.get("phrases", [])
            pairs = section.get("pairs", [])
            if phrases or pairs:
                phrases_list.controls.append(
                    self._expandable_section(
                        label,
                        "Phrases and conversation pairs",
                        ft.Icons.FORUM_OUTLINED,
                        self._phrases_grid(phrases, pairs, play_audio),
                    )
                )

            dialogues = section.get("dialogues", [])
            if dialogues:
                dialogues_list.controls.append(
                    self._expandable_section(
                        label,
                        f"{len(dialogues)} dialogue{'s' if len(dialogues) != 1 else ''}",
                        ft.Icons.RECORD_VOICE_OVER_OUTLINED,
                        self._dialogues(dialogues, play_audio),
                    )
                )

        if vocab_list.controls:
            tabs.tabs.append(ft.Tab(text="📖 Vocabulary", content=vocab_list))
        if phrases_list.controls:
            tabs.tabs.append(ft.Tab(text="💬 Phrases", content=phrases_list))
        if dialogues_list.controls:
            tabs.tabs.append(ft.Tab(text="🎭 Dialogues", content=dialogues_list))
        if not tabs.tabs:
            tabs.tabs.append(
                ft.Tab(
                    text="📚 Reference Materials",
                    content=ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Text("No reference material is available yet.", color=ft.Colors.GREY_600),
                    ),
                )
            )

        helper_text = "Open a lesson section to review its vocabulary, phrases, and dialogues."
        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=14,
            #bgcolor=ft.Colors.PURPLE_50,
            content=ft.Row(
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back, icon_color=ft.Colors.PURPLE_900),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(f"Memory Library: {unit_title}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                                ft.Text(helper_text, size=12, color=ft.Colors.BLUE_GREY_700),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        expand=True,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=48),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        course_map = self._course_map(master_sheet) if has_locked_sections else None
        view_controls = [header]
        if course_map:
            view_controls.append(course_map)
        view_controls.append(tabs)

        super().__init__(
            route="/passive_review",
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Column(view_controls, expand=True, spacing=12),
                    expand=1,
                    width=850,
                    padding=15,
                )
            ],
        )

    @staticmethod
    def _new_list() -> ft.ListView:
        return ft.ListView(expand=1, spacing=10, padding=ft.padding.only(left=8, right=8, bottom=20))

    @staticmethod
    def _format_section_label(raw_label) -> str:
        return f"Lesson {raw_label}" if isinstance(raw_label, int) else str(raw_label)

    @staticmethod
    def _rounded_card(content: ft.Control, bgcolor=ft.Colors.WHITE) -> ft.Container:
        return ft.Container(
            content=content,
            bgcolor=bgcolor,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
            border_radius=14,
            padding=12,
        )

    def _expandable_section(self, label: str, subtitle: str, icon, content: ft.Control) -> ft.Container:
        return ft.Container(
            border=ft.border.all(1, ft.Colors.PURPLE_100),
            border_radius=14,
            bgcolor=ft.Colors.WHITE,
            content=ft.ExpansionTile(
                title=ft.Text(label, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                subtitle=ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                leading=ft.Icon(icon, color=ft.Colors.PURPLE_700),
                controls=[content],
                controls_padding=ft.padding.only(left=12, right=12, bottom=12),
                collapsed_icon_color=ft.Colors.PURPLE_700,
                icon_color=ft.Colors.PURPLE_700,
                shape=ft.RoundedRectangleBorder(radius=14),
                collapsed_shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

    def _course_map(self, master_sheet: dict) -> ft.Container:
        phases = {}
        for section in master_sheet.values():
            phase_num = section.get("phase_num")
            unit_num = section.get("unit_num")
            if phase_num is None or unit_num is None:
                continue
            phases.setdefault(phase_num, {}).setdefault(unit_num, []).append(section)

        phase_controls = []
        for phase_num, units in sorted(phases.items()):
            completed_lessons = sum(
                not lesson.get("locked", False)
                for lessons in units.values()
                for lesson in lessons
            )
            total_lessons = sum(len(lessons) for lessons in units.values())
            if completed_lessons == 0:
                phase_controls.append(
                    self._rounded_card(
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.LOCK, color=ft.Colors.GREY_600, size=24),
                                ft.Column(
                                    controls=[
                                        ft.Text(f"Phase {phase_num}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                                        ft.Text("Locked — complete earlier lessons to begin this phase.", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.GREY_100,
                    )
                )
                continue

            unit_controls = []
            for unit_num, lessons in sorted(units.items()):
                completed_in_unit = sum(not lesson.get("locked", False) for lesson in lessons)
                is_complete = completed_in_unit == len(lessons)
                unit_controls.append(
                    self._rounded_card(
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if is_complete else ft.Icons.FOLDER,
                                    color=ft.Colors.GREEN_600 if is_complete else ft.Colors.AMBER_700,
                                    size=22,
                                ),
                                ft.Text(
                                    f"Unit {unit_num} · {completed_in_unit}/{len(lessons)} lessons unlocked",
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                ),
                            ],
                            spacing=10,
                        )
                    )
                )
            phase_controls.append(
                ft.Container(
                    border=ft.border.all(1, ft.Colors.TEAL_100),
                    border_radius=14,
                    bgcolor=ft.Colors.WHITE,
                    content=ft.ExpansionTile(
                        title=ft.Text(f"Phase {phase_num}", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                        subtitle=ft.Text(f"{completed_lessons}/{total_lessons} lessons unlocked", size=12, color=ft.Colors.GREY_600),
                        leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.TEAL_700),
                        controls=unit_controls,
                        controls_padding=ft.padding.only(left=12, right=12, bottom=12),
                        collapsed_icon_color=ft.Colors.TEAL_700,
                        icon_color=ft.Colors.TEAL_700,
                        shape=ft.RoundedRectangleBorder(radius=14),
                        collapsed_shape=ft.RoundedRectangleBorder(radius=14),
                    ),
                )
            )

        unlocked_count = sum(not section.get("locked", False) for section in master_sheet.values())
        return ft.Container(
            border=ft.border.all(1, ft.Colors.TEAL_100),
            border_radius=14,
            bgcolor=ft.Colors.TEAL_50,
            content=ft.ExpansionTile(
                title=ft.Text("Course Map", weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900),
                subtitle=ft.Text(f"{unlocked_count} lessons unlocked", size=12, color=ft.Colors.TEAL_800),
                leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.TEAL_700),
                controls=phase_controls,
                controls_padding=ft.padding.only(left=12, right=12, bottom=12),
                initially_expanded=False,
                collapsed_icon_color=ft.Colors.TEAL_700,
                icon_color=ft.Colors.TEAL_700,
                shape=ft.RoundedRectangleBorder(radius=14),
                collapsed_shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

    def _vocabulary_grid(self, vocab: list, play_audio: callable) -> ft.ResponsiveRow:
        grid = ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12)
        for item in vocab:
            audio_path = item.get("audio")
            grid.controls.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=self._rounded_card(
                        ft.ListTile(
                            title=ft.Text(item.get("geo", ""), size=18, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{item.get('trans', '')} • {item.get('eng', '')}", color=ft.Colors.BLACK54),
                            trailing=ft.IconButton(
                                icon=ft.Icons.VOLUME_UP_ROUNDED,
                                icon_color=ft.Colors.PURPLE_600,
                                on_click=lambda event, src=audio_path: play_audio(src),
                                visible=bool(audio_path),
                            ),
                        )
                    ),
                )
            )
        return grid

    def _phrases_grid(self, phrases: list, pairs: list, play_audio: callable) -> ft.ResponsiveRow:
        grid = ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12)
        for item in phrases:
            audio_path = item.get("audio")
            grid.controls.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=self._rounded_card(
                        ft.ListTile(
                            title=ft.Text(item.get("geo", ""), size=18, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{item.get('trans', '')} • {item.get('eng', '')}", color=ft.Colors.BLACK54),
                            trailing=ft.IconButton(
                                icon=ft.Icons.VOLUME_UP_ROUNDED,
                                icon_color=ft.Colors.PURPLE_600,
                                on_click=lambda event, src=audio_path: play_audio(src),
                                visible=bool(audio_path),
                            ),
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
                    content=self._rounded_card(
                        ft.Column(
                            controls=[
                                ft.Text(f"Q: {prompt['georgian']} ({prompt['english']})", weight=ft.FontWeight.W_600),
                                ft.Text(f"A: {response['georgian']} ({response['english']})", color=ft.Colors.PURPLE_800),
                            ],
                            spacing=5,
                        ),
                        bgcolor=ft.Colors.PURPLE_50,
                    ),
                )
            )
        return grid

    def _dialogues(self, dialogues: list, play_audio: callable) -> ft.Column:
        dialogue_cards = []
        for index, lines in enumerate(dialogues, start=1):
            line_controls = [
                ft.Text(f"Dialogue {index}", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_700)
            ]
            for line in lines:
                speaker_color = ft.Colors.BLUE_700 if line[0] == "A" else ft.Colors.GREEN_700
                row_controls = [
                    ft.Text(f"{line[0]}:", weight=ft.FontWeight.BOLD, color=speaker_color),
                    ft.Text(f"{line[1]} ({line[3]})", expand=True),
                ]
                if len(line) > 4 and line[4]:
                    row_controls.append(
                        ft.IconButton(
                            icon=ft.Icons.VOLUME_UP_ROUNDED,
                            icon_color=ft.Colors.PURPLE_600,
                            icon_size=18,
                            on_click=lambda event, src=line[4]: play_audio(src),
                        )
                    )
                line_controls.append(ft.Row(row_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER))
            dialogue_cards.append(self._rounded_card(ft.Column(line_controls, spacing=6), bgcolor=ft.Colors.BLUE_50))
        return ft.Column(dialogue_cards, spacing=10)
