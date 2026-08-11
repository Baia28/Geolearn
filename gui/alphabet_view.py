import flet as ft
import random
from gui.audio_utils import play_audio_file

class AlphabetPage(ft.Column):
    """Separate page dedicated to Alphabet learning with 2 main sub-modules."""
    def __init__(self, content_db, on_back):
        super().__init__()
        self.content_db = content_db
        self.on_back = on_back

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 15

        self.show_main_menu()

    # =========================================================================
    # 1. MAIN ALPHABET PAGE (2 BUTTONS MENU)
    # =========================================================================
    def show_main_menu(self):
        self.controls.clear()

        header = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back()),
                ft.Text("Georgian Alphabet (ანბანი)", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # BUTTON 1: Alphabet Gallery
        btn_gallery = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.show_gallery(),
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
                                ft.Text("Browse all 33 letters, pronunciations & mnemonics", size=13, color=ft.Colors.GREY_600),
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

        # BUTTON 2: Anban Game
        btn_game = ft.Card(
            content=ft.Container(
                padding=20,
                on_click=lambda e: self.start_anban_game(),
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
                                ft.Text("Visual practice exercise: match pictures to letters", size=13, color=ft.Colors.GREY_600),
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

        menu_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("SELECT AN ACTIVITY", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    btn_gallery,
                    ft.Container(height=5),
                    btn_game,
                ],
                spacing=12
            ),
            width=650,
            alignment=ft.alignment.top_center
        )

        self.controls = [
            header,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            menu_container
        ]
        if self.page:
            self.update()

    # =========================================================================
    # 2. ALPHABET GALLERY (33 LETTERS GRID)
    # =========================================================================
    def show_gallery(self):
        self.controls.clear()

        letters = self.content_db.get_alphabet_letters()
        cards = []

        for item in letters:
            # item = (content_id, georgian, transliteration, english, letter_audio)
            geo, trans = item[1], item[2]
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
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.show_main_menu()),
                ft.Text("Learn Georgian Alphabet", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        grid_column = ft.Column(
            controls=[
                header,
                ft.Text("Tap a letter to explore its sound and example word", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=10),
                ft.Row(controls=cards, wrap=True, spacing=12, alignment=ft.MainAxisAlignment.CENTER)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.controls = [grid_column]
        self.update()

    # =========================================================================
    # 3. INDIVIDUAL LETTER DETAIL CARD
    # =========================================================================
    def show_letter_detail(self, letter_geo):
        self.controls.clear()

        detail = self.content_db.get_alphabet_detail(letter_geo)
        letter = detail["letter"]
        example = detail["example"]

        geo_char = letter[1]
        latin = letter[2]
        letter_audio = letter[4]

        if letter_audio and self.page:
            play_audio_file(self.page, letter_audio)

        ex_word = example[1] if example else "N/A"
        ex_meaning = example[2] if example else "N/A"
        ex_image = example[4] if example else None
        ex_audio = example[5] if example else None

        detail_card = ft.Container(
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=10, color="#0000000A"),
            width=500,
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

        top_row = ft.Row(
            controls=[
                ft.TextButton("← Back to Gallery", on_click=lambda e: self.show_gallery())
            ],
            alignment=ft.MainAxisAlignment.START,
            width=500
        )

        self.controls = [
            top_row,
            detail_card
        ]
        self.update()

    # =========================================================================
    # 4. ANBAN GAME (VISUAL RECOGNITION EXERCISE)
    # =========================================================================
    def start_anban_game(self):
        raw_items = self.content_db.get_alphabet_game_items()
        all_items = [i for i in raw_items if i[5]]  # Ensure item has an image
        remaining_items = list(all_items)
        score = 0
        total_questions = len(remaining_items)

        def play_round():
            self.controls.clear()

            if not remaining_items:
                show_game_over(score, total_questions)
                return

            target = random.choice(remaining_items)
            remaining_items.remove(target)

            correct_geo = target[0]
            letter_audio = target[2]
            ex_image = target[5]

            other_items = [i for i in all_items if i[0] != correct_geo]
            wrong_samples = random.sample(other_items, min(3, len(other_items)))
            options = [target] + wrong_samples
            random.shuffle(options)

            score_text = ft.Text(f"Score: {score}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
            progress_text = ft.Text(f"Progress: {total_questions - len(remaining_items)} / {total_questions}", size=14, color=ft.Colors.GREY_600)
            feedback_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD)

            next_btn = ft.ElevatedButton("Next Question →", on_click=lambda e: play_round(), disabled=True)
            options_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15)

            def check_answer(selected_geo, clicked_btn):
                nonlocal score
                for btn in options_row.controls:
                    btn.disabled = True
                    if btn.data == correct_geo:
                        btn.bgcolor = ft.Colors.GREEN
                        btn.content.color = ft.Colors.WHITE
                        btn.update()

                if selected_geo != correct_geo:
                    clicked_btn.bgcolor = ft.Colors.RED
                    clicked_btn.content.color = ft.Colors.WHITE
                    feedback_text.value = f"❌ Oops! It was {correct_geo}"
                    feedback_text.color = ft.Colors.RED
                else:
                    score += 1
                    score_text.value = f"Score: {score}"
                    feedback_text.value = "✅ Correct!"
                    feedback_text.color = ft.Colors.GREEN
                    if letter_audio and self.page:
                        play_audio_file(self.page, letter_audio)

                next_btn.disabled = False
                self.update()

            for opt in options:
                opt_geo = opt[0]
                btn = ft.Container(
                    width=75,
                    height=75,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    alignment=ft.alignment.center,
                    ink=True,
                    data=opt_geo,
                    content=ft.Text(opt_geo, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    shadow=ft.BoxShadow(blur_radius=4, color="#00000010")
                )
                btn.on_click = lambda e, val=opt_geo, b=btn: check_answer(val, b)
                options_row.controls.append(btn)

            game_view = ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.show_main_menu()),
                            score_text,
                            ft.Container(width=40)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    progress_text,
                    ft.Container(height=10),
                    ft.Text("Which letter matches this image?", size=18, weight=ft.FontWeight.W_500),
                    ft.Container(height=10),
                    ft.Image(src=ex_image, width=180, height=180, fit=ft.ImageFit.CONTAIN),
                    ft.Container(height=15),
                    options_row,
                    ft.Container(height=10),
                    feedback_text,
                    ft.Container(height=10),
                    next_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )

            self.controls = [game_view]
            self.update()

        def show_game_over(final_score, total):
            self.controls.clear()
            pct = int((final_score / total) * 100) if total > 0 else 0
            self.controls = [
                ft.Column(
                    [
                        ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, size=90, color=ft.Colors.AMBER),
                        ft.Text("QUIZ COMPLETE!", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Final Score: {final_score} / {total}", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{pct}%", size=44, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.ElevatedButton("Play Again", on_click=lambda e: self.start_anban_game()),
                        ft.TextButton("Back to Alphabet Menu", on_click=lambda e: self.show_main_menu())
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ]
            self.update()

        play_round()