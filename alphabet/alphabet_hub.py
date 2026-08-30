# Sub-controller managing routing, state, and hub navigation

import flet as ft
from alphabet.alphabet_db import AlphabetDB
from alphabet.alphabet_gallery import AlphabetGalleryView
from alphabet.anban_game import AnbanGameView
from alphabet.alphabet_typing import AlphabetTypingGameView
from alphabet.alphabet_keyboard import AlphabetKeyboardView
from alphabet.alphabet_pronunciation import PhoneticsGuideView

class AlphabetPage(ft.Column):
    """Sub-controller inside main_stage managing navigation between Gallery, Games, Keyboard, and Home Dashboard."""
    
    def __init__(self, on_back_home):
        super().__init__()
        self.on_back_home = on_back_home
        self.db = AlphabetDB()
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.scroll = ft.ScrollMode.AUTO
        
        self.show_main_menu()

    def show_main_menu(self):
        self.controls.clear()

        header = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_home()),
                ft.Text("Georgian Alphabet Hub (ანბანი)", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 33 Letters gallery (with images and sounds)
        btn_gallery = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.launch_gallery(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_600,
                            width=56, height=56,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Alphabet Gallery", size=18, weight=ft.FontWeight.BOLD),
                                ft.Text("Browse all 33 Mkhedruli letters, sounds & examples", size=13, color=ft.Colors.GREY_600),
                            ],
                            spacing=4,
                            expand=True
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                    ],
                    spacing=15
                )
            ),
            elevation=2
        )

        # Activity Card for Phonetics Guide
        btn_phonetics = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.launch_phonetics_guide(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.RECORD_VOICE_OVER_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.TEAL_600,
                            width=56, height=56,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Phonetics & Sound Groups", size=18, weight=ft.FontWeight.BOLD),
                                ft.Text("Master ejectives, confusion triads (ბ-ფ-პ), & sound families", size=13, color=ft.Colors.GREY_600),
                            ],
                            spacing=4,
                            expand=True
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                    ],
                    spacing=15
                )
            ),
            elevation=2
        )

        # Match the Gallery Image to the letter
        btn_game = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.launch_game(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.SPORTS_ESPORTS_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.GREEN_600,
                            width=56, height=56,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Anban Game", size=18, weight=ft.FontWeight.BOLD),
                                ft.Text("Visual matching practice: match pictures from Gallery to letters", size=13, color=ft.Colors.GREY_600),
                            ],
                            spacing=4,
                            expand=True
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                    ],
                    spacing=15
                )
            ),
            elevation=2
        )


        btn_typing_game = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.launch_typing_game(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.HEADSET_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.PURPLE_600,
                            width=56, height=56,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Listen & Type Game", size=18, weight=ft.FontWeight.BOLD),
                                ft.Text("Audio dictation practice: listen and type letters", size=13, color=ft.Colors.GREY_600),
                            ],
                            spacing=4,
                            expand=True
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                    ],
                    spacing=15
                )
            ),
            elevation=2
        )

        btn_keyboard = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.launch_keyboard_explorer(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.KEYBOARD_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.AMBER_700,
                            width=56, height=56,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Georgian Keyboard Practice", size=18, weight=ft.FontWeight.BOLD),
                                ft.Text("Interactive large keyboard explorer with audio & Shift tutorials", size=13, color=ft.Colors.GREY_600),
                            ],
                            spacing=4,
                            expand=True
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400)
                    ],
                    spacing=15
                )
            ),
            elevation=2
        )

        # Bottom Call-to-Action Banner encouraging users to move to Phase 0
        bottom_cta_banner = ft.Container(
            padding=16,
            margin=ft.margin.only(top=15, bottom=20),
            bgcolor=ft.Colors.AMBER_50,
            border=ft.border.all(1, ft.Colors.AMBER_300),
            border_radius=14,
            width=650,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, size=24, color=ft.Colors.AMBER_900),
                            ft.Text("Ready for the Next Challenge?", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900)
                        ],
                        spacing=8
                    ),
                    ft.Text(
                        "If you've spent enough time practicing here and feel confident with letter sounds, head back to the main menu and begin Phase 0: Alphabet Testing!",
                        size=13,
                        color=ft.Colors.GREY_800
                    ),
                    ft.Container(height=4),
                    ft.ElevatedButton(
                        "Go to Main Page (Phase 0) →",
                        bgcolor=ft.Colors.AMBER_700,
                        color=ft.Colors.WHITE,
                        on_click=lambda e: self.on_back_home()
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        )

        menu = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("SELECT AN ACTIVITY", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    btn_gallery,
                    ft.Container(height=2),
                    btn_phonetics,
                    ft.Container(height=2),
                    btn_keyboard,
                    ft.Container(height=2),
                    btn_game,
                    ft.Container(height=2),
                    btn_typing_game,
                    bottom_cta_banner,
                ],
                spacing=10
            ),
            width=650,
            alignment=ft.alignment.top_center
        )

        self.controls = [header, ft.Divider(height=10, color=ft.Colors.TRANSPARENT), menu]
        if self.page:
            self.update()

    def launch_gallery(self):
        gallery_view = AlphabetGalleryView(db=self.db, on_back_to_menu=self.show_main_menu)
        self.controls = [gallery_view]
        self.update()

    def launch_phonetics_guide(self):
        guide_view = PhoneticsGuideView(db=self.db, on_back_to_menu=self.show_main_menu)
        self.controls = [guide_view]
        self.update()

    def launch_game(self):
        game_view = AnbanGameView(db=self.db, on_back_to_menu=self.show_main_menu)
        self.controls = [game_view]
        self.update()
        game_view.start_game()

    def launch_typing_game(self):
        typing_view = AlphabetTypingGameView(db=self.db, on_back_to_menu=self.show_main_menu)
        self.controls = [typing_view]
        self.update()
        typing_view.start_game()

    def launch_keyboard_explorer(self):
        keyboard_view = AlphabetKeyboardView(db=self.db, on_back_to_menu=self.show_main_menu)
        self.controls = [keyboard_view]
        self.update()