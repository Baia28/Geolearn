# 33-letter study gallery and isolated letter detail cards

import flet as ft
from gui.audio_utils import play_audio_file  # Adjust to your project's audio helper path [source: 2, 3]

class AlphabetGalleryView(ft.Column):
    """Grid display of all 33 Mkhedruli letters and isolated letter detail view."""
    
    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.show_gallery()

    def show_gallery(self):
        self.controls.clear()
        letters = self.db.get_alphabet_letters()
        cards = []

        for item in letters:
            geo = item["georgian"]
            trans = item["transliteration"] or ""
            cards.append(
                ft.Container(
                    width=100,
                    height=100,
                    border_radius=14,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda e, g=geo: self.show_letter_detail(g),
                    content=ft.Column(
                        [
                            ft.Text(geo, size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ft.Text(trans, size=13, color=ft.Colors.GREY_600),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2
                    ),
                    shadow=ft.BoxShadow(blur_radius=5, color="#0000000D")
                )
            )

        header = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                ft.Text("Georgian Alphabet (33 Letters)", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        grid_layout = ft.Column(
            controls=[
                header,
                ft.Text("Select any letter to view sound playback and mnemonic word", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=10),
                ft.Row(controls=cards, wrap=True, spacing=12, alignment=ft.MainAxisAlignment.CENTER)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.controls = [grid_layout]
        if self.page:
            self.update()

    def show_letter_detail(self, letter_geo: str):
        self.controls.clear()
        detail = self.db.get_letter_detail(letter_geo)
        
        letter = detail["letter"]
        example = detail["example"]

        if not letter:
            self.show_gallery()
            return

        geo_char = letter["georgian"]
        latin = letter["transliteration"] or ""
        letter_audio = letter["letter_audio"]

        if letter_audio and self.page:
            play_audio_file(self.page, letter_audio)

        ex_word = example["word"] if example else "N/A"
        ex_meaning = example["meaning"] if example else "N/A"
        ex_image = example["image"] if example else None
        ex_audio = example["audio"] if example else None

        detail_card = ft.Container(
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=10, color="#0000000A"),
            width=480,
            content=ft.Column(
                controls=[
                    ft.Text(geo_char, size=88, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Text(f"Pronunciation: {latin}", size=18, color=ft.Colors.GREY_700),
                    ft.Divider(height=20, color=ft.Colors.GREY_200),
                    ft.Image(src=ex_image or "", width=180, height=180, fit=ft.ImageFit.CONTAIN) if ex_image else ft.Container(),
                    ft.Container(height=5),
                    ft.Text(f"{ex_word} — {ex_meaning}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Letter Sound", 
                                icon=ft.Icons.VOLUME_UP,
                                on_click=lambda e: play_audio_file(self.page, letter_audio)
                            ) if letter_audio else ft.Container(),
                            ft.ElevatedButton(
                                "Example Word", 
                                icon=ft.Icons.VOLUME_UP,
                                on_click=lambda e: play_audio_file(self.page, ex_audio)
                            ) if ex_audio else ft.Container(),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        )

        top_nav = ft.Row(
            controls=[
                ft.TextButton("← Back to Gallery", on_click=lambda e: self.show_gallery())
            ],
            alignment=ft.MainAxisAlignment.START,
            width=480
        )

        self.controls = [top_nav, detail_card]
        if self.page:
            self.update()