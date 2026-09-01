import flet as ft

class HomeView(ft.Column):
    def __init__(
        self, 
        phases_summary: list, 
        on_select_phase: callable, 
        on_select_alphabet: callable,
        on_quick_review: callable
    ):
        super().__init__()
        self.phases_summary = phases_summary
        self.on_select_phase = on_select_phase
        self.on_select_alphabet = on_select_alphabet
        self.on_quick_review = on_quick_review
        
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        
        self._build_ui()

    def _build_ui(self):
        # 1. UPPER CENTER HEADER (Logo & Title)
        header = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("🇬🇪", size=36),
                        ft.Text("GeoLearn", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12
                ),
                ft.Text("Master the Georgian Language Step-by-Step", size=14, color=ft.Colors.GREY_600),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4
        )

        # 2. LEFT SIDEBAR / MAIN CURRICULUM COLUMN
        curriculum_controls = [
            ft.Text("CURRICULUM", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
            
            # --- CLEAN ALPHABET BUTTON (Sits directly above Phase 1) ---
            ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e: self.on_select_alphabet(),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.SORT_BY_ALPHA_ROUNDED, size=26, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.RED_700,
                                width=48, height=48,
                                border_radius=10,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(width=6),
                            ft.Column(
                                controls=[
                                    ft.Text("Georgian Alphabet (ანბანი)", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("Master Mkhedruli letters, sounds & visual mnemonics", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=2,
                                expand=True
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        spacing=15
                    )
                ),
                elevation=2
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT)
        ]

        # --- Dynamic Phase Cards (Phase 1, Phase 2, etc.) ---
        for p in self.phases_summary:
            p_num = p["phase_num"]
            p_title = p["title"]
            p_progress = p["progress"]  # 0.0 to 1.0
            completed = p["completed_lessons"]
            total = p["total_lessons"]
            
            phase_card = ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e, num=p_num: self.on_select_phase(num),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(f"PHASE {p_num}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                    ft.Text(f"{completed}/{total} Lessons", size=11, color=ft.Colors.GREY_600),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text(p_title, size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=4),
                            
                            # Thin grey-to-green progress bar
                            ft.ProgressBar(
                                value=p_progress, 
                                height=6, 
                                color=ft.Colors.GREEN_600, 
                                bgcolor=ft.Colors.GREY_200,
                                border_radius=3
                            )
                        ],
                        spacing=3
                    )
                ),
                elevation=1
            )
            curriculum_controls.append(phase_card)

        curriculum_column = ft.Column(controls=curriculum_controls, spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

        # 3. RIGHT SIDEBAR (Extra Entities & Quick Modules)
        sidebar_controls = [
            ft.Text("QUICK PRACTICE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
            
            # SRS Quick Review
            ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e: self.on_quick_review(),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.FLASH_ON, color=ft.Colors.AMBER_700, size=20),
                                    ft.Text("Quick SRS Review", size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8
                            ),
                            ft.Text("Review at least 15 due words based on memory decay.", size=11, color=ft.Colors.GREY_600),
                        ],
                        spacing=5
                    )
                ),
                elevation=1
            ),
            
            # Passive Reading Hub
            ft.Card(
                content=ft.Container(
                    padding=15,
                    on_click=lambda e: print("Passive Reading selected"),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.TEAL_600, size=20),
                                    ft.Text("Passive Reading", size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8
                            ),
                            ft.Text("Read full dialogues with side-by-side translations.", size=11, color=ft.Colors.GREY_600),
                        ],
                        spacing=5
                    )
                ),
                elevation=1
            ),
            
            # Fun Facts & Culture (Placeholder)
            ft.Card(
                content=ft.Container(
                    padding=15,
                    opacity=0.6,
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=ft.Colors.PURPLE_400, size=20),
                                    ft.Text("Culture & Fun Facts", size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8
                            ),
                            ft.Text("Discover Georgian history, food, and traditions.", size=11, color=ft.Colors.GREY_600),
                        ],
                        spacing=5
                    )
                ),
                elevation=0
            ),
        ]

        sidebar_column = ft.Column(controls=sidebar_controls, spacing=10, width=280)

        # 4. ASSEMBLE MAIN LAYOUT
        #Wrap the main row in a Container to lock the max width and center it
        main_content_row = ft.Container(
            content=ft.Row(
                controls=[
                    curriculum_column,
                    ft.VerticalDivider(width=20, color=ft.Colors.GREY_200),
                    sidebar_column
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True
            ),
            width=1000,
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [
            header,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            main_content_row
        ]