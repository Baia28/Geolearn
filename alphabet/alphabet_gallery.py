import flet as ft
from gui.audio_utils import play_audio_file

# Set of Georgian vowels to highlight in red
VOWELS = {"ა", "ე", "ი", "ო", "უ"}

class AlphabetGalleryView(ft.Column):
    """Grid display of all 33 Mkhedruli letters with image cards and isolated letter detail view."""
    
    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Audio state
        self.auto_sound_enabled = True
        
        self.show_gallery()

    def toggle_sound(self, e=None):
        """Toggles hover auto-sound playback on and off."""
        self.auto_sound_enabled = not self.auto_sound_enabled
        self.show_gallery()

    def _handle_card_hover(self, e, audio_path: str):
        """Plays letter audio on mouse cursor enter if auto-sound is active."""
        if e.data == "true" and self.auto_sound_enabled and audio_path and self.page:
            play_audio_file(self.page, audio_path)

    def show_gallery(self):
        self.controls.clear()
        letters = self.db.get_alphabet_letters()
        cards = []

        for idx, item in enumerate(letters):
            geo = item.get("georgian", "")
            trans = item.get("transliteration") or ""
            img_path = item.get("example_image")
            audio_path = item.get("letter_audio")
            
            # Highlight vowels in red, consonants in deep blue
            letter_color = ft.Colors.RED_600 if geo in VOWELS else ft.Colors.BLUE_900

            cards.append(
                ft.Container(
                    width=135,
                    height=170,
                    border_radius=16,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda e, i=idx: self.show_letter_detail(i),
                    on_hover=lambda e, a=audio_path: self._handle_card_hover(e, a),
                    content=ft.Column(
                        [
                            ft.Text(geo, size=40, weight=ft.FontWeight.BOLD, color=letter_color),
                            ft.Image(src=img_path or "", width=50, height=50, fit=ft.ImageFit.CONTAIN) if img_path else ft.Container(height=50),
                            ft.Text(trans, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4
                    ),
                    shadow=ft.BoxShadow(blur_radius=6, color="#00000010")
                )
            )

        sound_icon = ft.Icons.VOLUME_UP_ROUNDED if self.auto_sound_enabled else ft.Icons.VOLUME_OFF_ROUNDED
        sound_color = ft.Colors.BLUE_700 if self.auto_sound_enabled else ft.Colors.GREY_500

        header = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                ft.Text("Georgian Alphabet (33 Letters)", size=24, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=sound_icon, 
                    icon_color=sound_color, 
                    icon_size=28,
                    tooltip="Toggle Hover Sound",
                    on_click=self.toggle_sound
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        grid_layout = ft.Column(
            controls=[
                header,
                ft.Text("Hover over a letter to hear its sound. Tap to open full details.", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=15),
                ft.Row(controls=cards, wrap=True, spacing=12, alignment=ft.MainAxisAlignment.CENTER)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # Flexible wrapper with 50px side margins so cards reflow freely across big displays        main_wrapper = ft.Container(
        main_wrapper = ft.Container(
            content=grid_layout,
            padding=ft.padding.only(left=50, right=50, top=20, bottom=20),
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [main_wrapper]
        if self.page:
            self.update()

    def show_letter_detail(self, letter_index: int):
        self.controls.clear()
        detail_data = self.db.get_letter_detail_by_index(letter_index)
        
        letter = detail_data.get("letter")
        example = detail_data.get("example")
        total = detail_data.get("total", 0)

        if not letter:
            self.show_gallery()
            return

        geo_char = letter.get("georgian", "")
        trans = letter.get("transliteration") or ""
        linguistic_desc = letter.get("linguistic_desc") or trans
        letter_audio = letter.get("letter_audio")

        # Auto-play letter sound on load
        if letter_audio and self.page:
            play_audio_file(self.page, letter_audio)

        letter_color = ft.Colors.RED_600 if geo_char in VOWELS else ft.Colors.BLUE_900

        ex_word = example.get("word") if example else "N/A"
        ex_meaning = example.get("meaning") if example else "N/A"
        ex_image = example.get("image") if example else None
        ex_audio = example.get("audio") if example else None

        detail_card = ft.Container(
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=10, color="#0000000A"),
            width=480,
            content=ft.Column(
                controls=[
                    ft.Text(geo_char, size=88, weight=ft.FontWeight.BOLD, color=letter_color),
                    ft.Text(f"Pronunciation: {linguistic_desc}", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800),
                    ft.Container(height=2),
                    ft.ElevatedButton(
                        "Letter Sound", 
                        icon=ft.Icons.VOLUME_UP,
                        on_click=lambda e: play_audio_file(self.page, letter_audio)
                    ) if letter_audio else ft.Container(),
                    ft.Divider(height=25, color=ft.Colors.GREY_200),
                    ft.Image(src=ex_image or "", width=170, height=170, fit=ft.ImageFit.CONTAIN) if ex_image else ft.Container(),
                    ft.Container(height=5),
                    ft.Text(f"{ex_word} — {ex_meaning}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Example Word Sound", 
                        icon=ft.Icons.VOLUME_UP,
                        on_click=lambda e: play_audio_file(self.page, ex_audio)
                    ) if ex_audio else ft.Container(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        )

        prev_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
            icon_size=48,
            disabled=(letter_index == 0),
            on_click=lambda e: self.show_letter_detail(letter_index - 1)
        )
        
        next_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
            icon_size=48,
            disabled=(letter_index == total - 1),
            on_click=lambda e: self.show_letter_detail(letter_index + 1)
        )

        nav_row = ft.Row(
            controls=[prev_btn, detail_card, next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

        # Centered Back Button with margin spacer from the top edge and Gallery Icon after text
        centered_back_bar = ft.Column(
            controls=[
                ft.Container(height=25),  # Gives space from the top edge
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=20),
                                    ft.Text("Back to Gallery", size=15, weight=ft.FontWeight.W_500),
                                    ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=20),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                                tight=True
                            ),
                            on_click=lambda e: self.show_gallery(),
                            style=ft.ButtonStyle(padding=14)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]
        )

        layout_wrapper = ft.Container(
            content=ft.Column(
                controls=[
                    centered_back_bar,
                    ft.Container(height=15),
                    nav_row
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.padding.only(left=30, right=30, bottom=30),
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [layout_wrapper]
        if self.page:
            self.update()