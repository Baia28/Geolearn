import flet as ft

class LessonsView(ft.Column):
    def __init__(
        self,
        phase_num: int,
        unit_num: int,
        unit_title: str,
        lessons_list: list,
        on_select_lesson: callable,
        on_passive_read: callable,
        on_unit_review: callable,
        on_back: callable,
        on_home: callable
    ):
        super().__init__()
        self.phase_num = phase_num
        self.unit_num = unit_num
        self.unit_title = unit_title
        self.lessons_list = lessons_list
        self.on_select_lesson = on_select_lesson
        self.on_passive_read = on_passive_read
        self.on_unit_review = on_unit_review
        self.on_back = on_back
        self.on_home = on_home

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20

        self._build_ui()

    def _build_ui(self):
        # 1. Navigation Bar
        nav_bar = ft.Row(
            controls=[
                ft.TextButton("Back to Units", icon=ft.icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                ft.TextButton("Home", icon=ft.icons.HOME, on_click=lambda e: self.on_home()),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 2. Header
        header = ft.Column(
            controls=[
                ft.Text(f"PHASE {self.phase_num} • UNIT {self.unit_num}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ft.Text(self.unit_title, size=28, weight=ft.FontWeight.BOLD),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 3. Interactive Lesson List (Left Column)
        lesson_cards = []
        for l_data in self.lessons_list:
            l_num = l_data["lesson_num"]
            l_title = l_data["title"]
            is_completed = l_data["is_completed"]

            # Visual state: completed lessons turn green
            status_icon = ft.icons.CHECK_CIRCLE if is_completed else ft.icons.PLAY_CIRCLE_FILL
            icon_color = ft.Colors.GREEN_600 if is_completed else ft.Colors.BLUE_600
            card_bg = ft.Colors.GREEN_50 if is_completed else ft.Colors.WHITE

            card = ft.Card(
                content=ft.Container(
                    padding=15,
                    bgcolor=card_bg,
                    border_radius=8,
                    on_click=lambda e, num=l_num: self.on_select_lesson(self.phase_num, self.unit_num, num),
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(status_icon, color=icon_color, size=26),
                                    ft.Column(
                                        controls=[
                                            #ft.Text(f"Lesson {l_num}", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.BOLD),
                                            ft.Text(l_title, size=16, weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=2
                                    )
                                ],
                                spacing=12
                            ),
                            ft.ElevatedButton(
                                "Review" if is_completed else "Start",
                                bgcolor=ft.Colors.GREEN_600 if is_completed else ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ),
                elevation=1
            )
            lesson_cards.append(card)

        lessons_column = ft.Column(controls=lesson_cards, spacing=10, expand=True)

        # 4. Unit Tools Sidebar (Right Column)
        side_options = [
            ft.Text("UNIT TOOLS", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
            
            # Unit Vocabulary Review
            ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e: self.on_unit_review(self.phase_num, self.unit_num),
                    content=ft.Column(
                        controls=[
                            ft.Row([ft.Icon(ft.icons.REPLAY, color=ft.Colors.AMBER_700), ft.Text("Unit SRS Review", weight=ft.FontWeight.BOLD)]),
                            ft.Text("Review at least 15 vocabulary items from this unit.", size=11, color=ft.Colors.GREY_600)
                        ],
                        spacing=5
                    )
                ),
                elevation=1
            ),
            
            # Passive Reading Mode
            ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e: self.on_passive_read(self.phase_num, self.unit_num),
                    content=ft.Column(
                        controls=[
                            ft.Row([ft.Icon(ft.icons.MENU_BOOK, color=ft.Colors.TEAL_600), ft.Text("Passive Read", weight=ft.FontWeight.BOLD)]),
                            ft.Text("Read full unit dialogues with dual scripts and translations.", size=11, color=ft.Colors.GREY_600)
                        ],
                        spacing=5
                    )
                ),
                elevation=1
            )
        ]
        side_column = ft.Column(controls=side_options, spacing=10, width=260)

        # 5. Assemble Main Layout
        main_row = ft.Row(
            controls=[
                lessons_column,
                ft.VerticalDivider(width=20, color=ft.Colors.GREY_200),
                side_column
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True
        )

        self.controls = [
            nav_bar,
            header,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            main_row
        ]