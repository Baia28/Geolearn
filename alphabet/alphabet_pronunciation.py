import flet as ft
from gui.audio_utils import play_audio_file

class PhoneticsGuideView(ft.Column):
    """Interactive educational guide breaking down Georgian sounds, phonetics, and letter groups."""

    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 15

        # Load letter audio lookup table
        letters = self.db.get_alphabet_letters()
        self.audio_map = {item.get("georgian"): item.get("letter_audio") for item in letters if item.get("georgian")}

        self._build_ui()

    def _build_ui(self):
        self.controls.clear()

        # Header Row
        header = ft.Container(
            width=650,
            content=ft.Row(
                controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                    ft.Text("Phonetics & Sound Groups", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Container(width=40)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        intro_text = ft.Container(
            width=650,
            content=ft.Text(
                "Tap any letter chip to hear its exact sound. Use these groups to master subtle Georgian phonetic contrasts!",
                size=14, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER
            )
        )

        # Tab 1: Confusion Triads & Contrast Pairs
        triad_data = [
            ("Labials (B/P sound family)", ["ბ", "ფ", "პ"], "Voiced → Aspirated → Ejective"),
            ("Velars (G/K sound family)", ["გ", "ქ", "კ"], "Voiced → Aspirated → Ejective"),
            ("Dentals (D/T sound family)", ["დ", "თ", "ტ"], "Voiced → Aspirated → Ejective"),
            ("Dental Affricates (DZ/TS)", ["ძ", "ც", "წ"], "Voiced → Aspirated → Ejective"),
            ("Postalveolar Affricates (J/CH)", ["ჯ", "ჩ", "ჭ"], "Voiced → Aspirated → Ejective"),
            ("Gutturals & Throat Sounds", ["ღ", "ხ", "ჰ"], "Deep Voiced → Harsh Voiceless → Soft H"),
        ]

        # Tab 2: Sound Types (Aspirated, Ejectives, Gutturals)
        sound_types = [
            ("Ejective Sounds (Glottalized Stop)", ["ტ", "კ", "პ", "წ", "ჭ", "ყ"], "Sharply popped sounds produced with closed vocal cords.", ft.Colors.RED_100, ft.Colors.RED_900),
            ("Aspirated Sounds (Puffed Air)", ["თ", "ფ", "ქ"], "Accompanied by a strong puff of air (similar to English p, t, k).", ft.Colors.BLUE_100, ft.Colors.BLUE_900),
            ("Affricates (Combination Sounds)", ["ც", "ძ", "ჩ", "ჯ", "წ", "ჭ"], "Starts as a stop consonant and releases into a fricative.", ft.Colors.PURPLE_100, ft.Colors.PURPLE_900),
            ("Gutturals & Throat Consonants", ["ხ", "ღ", "ყ", "ქ"], "Pronounced deeper back in the palate/throat.", ft.Colors.AMBER_100, ft.Colors.AMBER_900),
        ]

        # Tab 3: Linguistic Articulation Chart
        articulation_data = [
            ("Bilabial (Both Lips)", ["ბ", "პ", "ფ", "მ"]),
            ("Dental / Alveolar (Tongue to Teeth/Ridge)", ["დ", "თ", "ტ", "ს", "ზ", "ლ", "რ", "ნ", "ც", "ძ", "წ"]),
            ("Postalveolar (Behind Tooth Ridge)", ["შ", "ჟ", "ჩ", "ჯ", "ჭ"]),
            ("Velar (Soft Palate)", ["გ", "კ", "ქ", "ხ"]),
            ("Uvular (Back Throat)", ["ღ", "ყ"]),
            ("Glottal (Vocal Cords)", ["ჰ"]),
        ]

        # Tab 4: Voiced vs Voicless
        pair_data = [("Voiced vs. Voiceless Pairs", [("ბ", "პ"), ("გ", "კ"), ("დ", "ტ"), ("ზ", "ს"), ("ჟ", "შ"), ("ძ", "ც"), ("ჯ", "ჩ"), ("ღ", "ხ")])]


        # Build UI Cards
        triad_cards = [self._create_group_card(title, letters, sub) for title, letters, sub in triad_data]
        sound_type_cards = [self._create_category_card(title, letters, desc, bg, fg) for title, letters, desc, bg, fg in sound_types]
        articulation_cards = [self._create_simple_card(title, letters) for title, letters in articulation_data]
        pair_cards = [self._create_pairs_card(title, letters) for title, letters in pair_data]


        # Tabs configured without height expansion conflicts
        tabs = ft.Container(
            width=650,
            content=ft.Tabs(
                selected_index=0,
                animation_duration=200,
                tabs=[
                    ft.Tab(
                        text="Confusion Groups",
                        icon=ft.Icons.COMPARE_ARROWS_ROUNDED,
                        content=ft.Column(controls=triad_cards, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Tab(
                        text="Sound Categories",
                        icon=ft.Icons.RECORD_VOICE_OVER_ROUNDED,
                        content=ft.Column(controls=sound_type_cards, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Tab(
                        text="Place of Articulation",
                        icon=ft.Icons.ANALYTICS_ROUNDED,
                        content=ft.Column(controls=articulation_cards, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Tab(
                        text="Voiced vs. Voiceless",
                        icon=ft.Icons.SWAP_HORIZ_ROUNDED,
                        content=ft.Column(controls=pair_cards, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                ],
            )
        )

        self.controls = [
            ft.Container(height=10),
            header,
            intro_text,
            tabs,
            ft.Container(height=30)
        ]

    def _play_sound(self, char: str):
        path = self.audio_map.get(char)
        if path and self.page:
            play_audio_file(self.page, path)

    def _create_letter_chip(self, char: str, bg_color=ft.Colors.BLUE_50, text_color=ft.Colors.BLUE_900):
        return ft.Container(
            width=52,
            height=52,
            bgcolor=bg_color,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            alignment=ft.alignment.center,
            ink=True,
            on_click=lambda e: self._play_sound(char),
            tooltip=f"Tap to hear {char}",
            content=ft.Text(char, size=24, weight=ft.FontWeight.BOLD, color=text_color)
        )

    def _create_group_card(self, title: str, letters: list, subtitle: str):
        chips = [self._create_letter_chip(char) for char in letters]
        return ft.Card(
            content=ft.Container(
                padding=14,
                content=ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY_600, italic=True),
                    ft.Row(controls=chips, spacing=10)
                ], spacing=8)
            ),
            width=650
        )

    def _create_category_card(self, title: str, letters: list, desc: str, bg_color, text_color):
        chips = [self._create_letter_chip(char, bg_color=bg_color, text_color=text_color) for char in letters]
        return ft.Card(
            content=ft.Container(
                padding=14,
                content=ft.Column([
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=text_color),
                    ft.Text(desc, size=13, color=ft.Colors.GREY_700),
                    ft.Row(controls=chips, wrap=True, spacing=8)
                ], spacing=8)
            ),
            width=650
        )

    def _create_simple_card(self, title: str, letters: list):
        chips = [self._create_letter_chip(char) for char in letters]
        return ft.Card(
            content=ft.Container(
                padding=14,
                content=ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD),
                    ft.Row(controls=chips, wrap=True, spacing=8)
                ], spacing=6)
            ),
            width=650
        )
    
    def _create_pairs_card(self, title: str, pairs: list):
        pair_boxes = []
        for voiced, voiceless in pairs:
            v_chip = self._create_letter_chip(voiced, bg_color=ft.Colors.TEAL_100, text_color=ft.Colors.TEAL_900)
            vl_chip = self._create_letter_chip(voiceless, bg_color=ft.Colors.INDIGO_100, text_color=ft.Colors.INDIGO_900)
            
            box = ft.Container(
                padding=8,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_300),
                content=ft.Row(
                    controls=[
                        v_chip,
                        ft.Text("vs", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                        vl_chip
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
            pair_boxes.append(box)

        return ft.Card(
            content=ft.Container(
                padding=18,
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ft.Text("Teal = Voiced (vocal cords vibrate)  |  Indigo = Voiceless", size=12, color=ft.Colors.GREY_600, italic=True),
                        ft.Container(height=6),
                        ft.Row(
                            controls=pair_boxes,
                            wrap=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=12,
                            run_spacing=12
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8
                )
            ),
            width=650
        )