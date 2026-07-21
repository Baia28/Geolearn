import flet as ft

class UnitsView(ft.Column):
    def __init__(
        self,
        phase_num: int,
        phase_title: str,
        units_summary: list,
        on_select_unit: callable,
        on_back: callable,
        on_home: callable
    ):
        super().__init__()
        self.phase_num = phase_num
        self.phase_title = phase_title
        self.units_summary = units_summary
        self.on_select_unit = on_select_unit
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
                ft.TextButton("Back to Phases", icon=ft.icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                ft.TextButton("Home", icon=ft.icons.HOME, on_click=lambda e: self.on_home()),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 2. Phase Header
        header = ft.Column(
            controls=[
                ft.Text(f"PHASE {self.phase_num}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ft.Text(self.phase_title, size=28, weight=ft.FontWeight.BOLD),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # 3. Units List
        unit_cards = []
        for u in self.units_summary:
            u_num = u["unit_num"]
            u_title = u["title"]
            u_progress = u["progress"]  # Float 0.0 -> 1.0
            completed = u["completed_lessons"]
            total = u["total_lessons"]

            card = ft.Card(
                content=ft.Container(
                    padding=18,
                    on_click=lambda e, num=u_num: self.on_select_unit(self.phase_num, num),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(f"UNIT {u_num}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                    ft.Text(f"{completed}/{total} Completed", size=11, color=ft.Colors.GREY_600),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text(u_title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(height=4),
                            
                            # Thin grey-to-green progress bar
                            ft.ProgressBar(
                                value=u_progress,
                                height=6,
                                color=ft.Colors.GREEN_600,
                                bgcolor=ft.Colors.GREY_200,
                                border_radius=3
                            )
                        ],
                        spacing=4
                    )
                ),
                elevation=1
            )
            unit_cards.append(card)

        units_column = ft.Column(controls=unit_cards, spacing=12, width=600)

        self.controls = [
            nav_bar,
            header,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            units_column
        ]