# Visual practice quiz mode with strict distractor pools

import flet as ft
import random
from gui.audio_utils import play_audio_file  # Adjust to your project's audio helper path [source: 2, 3]

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
        self.score = 0
        self.total_questions = 0

    def start_game(self):
        self.questions = self.db.get_anban_game_questions()
        self.remaining_questions = list(self.questions)
        self.all_alphabet_letters = [q["correct_geo"] for q in self.questions]
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
        feedback_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
        next_btn = ft.ElevatedButton("Next Question →", on_click=lambda e: self.play_round(), disabled=True)
        options_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15)

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
                feedback_text.value = f"❌ Incorrect! It was {correct_geo}"
                feedback_text.color = ft.Colors.RED
            else:
                self.score += 1
                score_text.value = f"Score: {self.score}"
                feedback_text.value = "✅ Correct!"
                feedback_text.color = ft.Colors.GREEN
                if letter_audio and self.page:
                    play_audio_file(self.page, letter_audio)
                    
            next_btn.disabled = False
            self.update()

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

        game_layout = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                        score_text,
                        ft.Container(width=40)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                progress_text,
                ft.Container(height=10),
                ft.Text("Which letter matches this image?", size=18, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                ft.Image(src=ex_image or "", width=180, height=180, fit=ft.ImageFit.CONTAIN),
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

        self.controls = [game_layout]
        if self.page:
            self.update()

    def show_game_over(self):
        self.controls.clear()
        pct = int((self.score / self.total_questions) * 100) if self.total_questions > 0 else 0
        self.controls = [
            ft.Column(
                [
                    ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, size=90, color=ft.Colors.AMBER),
                    ft.Text("QUIZ COMPLETE!", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Final Score: {self.score} / {self.total_questions}", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{pct}%", size=44, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    ft.ElevatedButton("Play Again", on_click=lambda e: self.start_game()),
                    ft.TextButton("Back to Alphabet Menu", on_click=lambda e: self.on_back_to_menu())
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            )
        ]
        if self.page:
            self.update()