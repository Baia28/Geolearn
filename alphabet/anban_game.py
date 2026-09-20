"""Visual alphabet-association quiz with immediate pronunciation feedback."""

import flet as ft
import random
from gui.audio_utils import play_audio_file

class AnbanGameView(ft.Column):
    """Visual matching quiz mode generating distractor pools exclusively from alphabet content."""
    
    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        self.questions = []
        self.remaining_questions = []
        self.all_alphabet_letters = []
        self.letter_audio_by_geo = {}
        self.score = 0
        self.total_questions = 0

    def start_game(self):
        self.questions = self.db.get_anban_game_questions()
        self.remaining_questions = list(self.questions)
        self.all_alphabet_letters = [q["correct_geo"] for q in self.questions]
        self.letter_audio_by_geo = {
            question["correct_geo"]: question.get("letter_audio")
            for question in self.questions
        }
        self.score = 0
        self.total_questions = len(self.questions)
        
        self.play_round()

    def play_round(self):
        self.controls.clear()

        if not self.remaining_questions:
            self.show_game_over()
            return

        target = random.choice(self.remaining_questions)
        self.remaining_questions.remove(target)

        correct_geo = target["correct_geo"]
        letter_audio = target["letter_audio"]
        ex_image = target["example_image"]

        # Filter distractors exclusively from alphabet pool
        other_distractors = [g for g in self.all_alphabet_letters if g != correct_geo]
        wrong_choices = random.sample(other_distractors, min(3, len(other_distractors)))
        
        options = [correct_geo] + wrong_choices
        random.shuffle(options)

        score_text = ft.Text(f"Score: {self.score}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        progress_text = ft.Text(
            f"Progress: {self.total_questions - len(self.remaining_questions)} / {self.total_questions}", 
            size=14, color=ft.Colors.GREY_600
        )
        feedback_panel = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )
        next_btn = ft.ElevatedButton(
            "Next Question →", 
            width=350, 
            height=48, 
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE, 
            on_click=lambda e: self.play_round(), 
            disabled=True)
        options_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15)

        def replay_button(audio_path: str, tooltip: str):
            if not audio_path:
                return ft.Container()
            return ft.IconButton(
                icon=ft.Icons.VOLUME_UP_ROUNDED,
                icon_color=ft.Colors.BLUE_700,
                tooltip=tooltip,
                on_click=lambda _: play_audio_file(self.page, audio_path),
            )

        def check_answer(selected_geo: str, clicked_btn: ft.Container):
            for btn in options_row.controls:
                btn.disabled = True
                if btn.data == correct_geo:
                    btn.bgcolor = ft.Colors.GREEN
                    btn.content.color = ft.Colors.WHITE
                    btn.update()

            if selected_geo != correct_geo:
                clicked_btn.bgcolor = ft.Colors.RED
                clicked_btn.content.color = ft.Colors.WHITE
                selected_audio = self.letter_audio_by_geo.get(selected_geo)
                feedback_panel.controls = [
                    ft.Row(
                        controls=[
                            ft.Text("❌ You chose", size=18, color=ft.Colors.RED_700),
                            ft.Text(selected_geo, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                            replay_button(selected_audio, f"Hear {selected_geo}"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Correct answer:", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                            ft.Text(correct_geo, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                            replay_button(letter_audio, f"Hear {correct_geo}"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                    ),
                ]

            else:
                self.score += 1
                score_text.value = f"Score: {self.score}"
                feedback_panel.controls = [
                    ft.Text("✅ Correct!", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
                ]
                    
            next_btn.disabled = False
            self.update()

            # Preserve the previous automatic pronunciation of the correct letter.
            if letter_audio and self.page:
                play_audio_file(self.page, letter_audio)

        for opt in options:
            btn = ft.Container(
                width=75,
                height=75,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                alignment=ft.alignment.center,
                ink=True,
                data=opt,
                content=ft.Text(opt, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                shadow=ft.BoxShadow(blur_radius=4, color="#00000010")
            )
            btn.on_click = lambda e, val=opt, b=btn: check_answer(val, b)
            options_row.controls.append(btn)

        # Standardized Header
        header = ft.Container(
            width=650,
            content=ft.Row(
                controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                    ft.Text("Anbani Associations", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    score_text
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        game_layout = ft.Container(
            width=650,
            content=ft.Column(
                controls=[
                    header,
                    progress_text,
                    ft.Container(height=10),
                    ft.Text("Which letter goes with the image below?", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800), # orrr Which letter does the image below belong to               
                    ft.Container(height=10),
                    ft.Image(src=ex_image or "", width=180, height=180, fit=ft.ImageFit.CONTAIN),
                    ft.Container(height=15),
                    options_row,
                    ft.Container(height=10),
                    feedback_panel,
                    ft.Container(height=10),
                    next_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6
            )
        )

        main_wrapper = ft.Container(
            content=ft.Column(
                controls=[game_layout],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.padding.only(top=10, bottom=20),
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [main_wrapper]
        if self.page:
            self.update()

    def show_game_over(self):
        self.controls.clear()
        pct = int((self.score / self.total_questions) * 100) if self.total_questions > 0 else 0
        pct_color = ft.Colors.GREEN_600 if pct >= 70 else ft.Colors.BLUE_700

        play_again_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.REPLAY_ROUNDED, size=22),
                    ft.Text("Play Again", size=16, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            width=220,
            height=50,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: self.start_game()
        )

        back_hub_btn = ft.OutlinedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=20),
                    ft.Text("Alphabet Hub", size=16, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            width=220,
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: self.on_back_to_menu()
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, size=90, color=ft.Colors.AMBER_600),
                        ft.Text("QUIZ COMPLETE!", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ft.Text(f"Final Score: {self.score} / {self.total_questions}", size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                        ft.Text(f"{pct}%", size=48, color=pct_color, weight=ft.FontWeight.BOLD),
                        ft.Container(height=15),
                        ft.Row(
                            [play_again_btn, back_hub_btn],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=15
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8
                ),
                alignment=ft.alignment.top_center,  # Shifted from center to top_center
                padding=ft.padding.only(top=-100),     # Adjust this number to raise/lower
                expand=True
            )
        ]
        if self.page:
            self.update()
