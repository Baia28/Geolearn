import flet as ft
import random
from data.alphabet import alphabet
from data.anbani import anbani

class AnbanGame:
    def __init__(self, page, go_home_func, play_audio_func):
        self.page = page
        self.go_home = go_home_func
        self.play_audio = play_audio_func
        
        # --- GAME STATE ---
        self.score = 0
        self.remaining_letters = [] 

    # --- ENTRY POINT (Main calls this) ---
    def start_game(self):
        # Reset the score and fill the letter bag
        self.score = 0
        self.remaining_letters = anbani.copy() # Make a fresh copy of the list
        self.start_round()

    # --- THE LOOP ---
    def start_round(self):
        # 1. CHECK IF GAME IS OVER
        if len(self.remaining_letters) == 0:
            self.show_game_over()
            return

        # 2. Pick a random correct answer from REMAINING letters
        correct_letter_obj = random.choice(self.remaining_letters)
        
        # Remove it so it doesn't appear again!
        self.remaining_letters.remove(correct_letter_obj)
        
        correct_geo = correct_letter_obj["geo"]
        correct_data = alphabet[correct_geo]

        # 3. Pick 3 WRONG answers (from the full list to keep it hard)
        other_letters = [l for l in anbani if l["geo"] != correct_geo]
        wrong_answers = random.sample(other_letters, 3)

        # 4. Combine and Shuffle
        options = [correct_letter_obj] + wrong_answers
        random.shuffle(options)

        # 5. Build the UI
        self.page.controls.clear()
        self.page.vertical_alignment = "center"

        # Define controls BEFORE we use them in functions
        progress_text = ft.Text(f"Progress: {33 - len(self.remaining_letters)} / 33", size=16, color="grey")
        score_text = ft.Text(f"Score: {self.score}", size=20, weight="bold", color="blue")
        feedback_text = ft.Text("", size=20, weight="bold")
        
        # We need to define the button first, but its on_click calls start_round
        next_btn = ft.ElevatedButton("Next Question ->", on_click=lambda e: self.start_round(), disabled=True)

        options_row = ft.Row(wrap=True, alignment="center", spacing=20)

        # --- CHECK ANSWER LOGIC ---
        def check_answer(selected_letter, clicked_btn):
            # Lock all buttons
            for button in options_row.controls:
                button.disabled = True 
                # Highlight the correct one Green
                if button.content.value == correct_geo:
                    button.bgcolor = "green"
                    button.content.color = "white"
                    button.update()
                
            # If they were WRONG
            if selected_letter != correct_geo:
                clicked_btn.bgcolor = "red"
                clicked_btn.content.color = "white"
                feedback_text.value = f"❌ Oops! It was {correct_geo}"
                feedback_text.color = "red"
            else:
                # If they were RIGHT
                self.score += 1
                score_text.value = f"Score: {self.score}"
                feedback_text.value = "✅ Correct!"
                feedback_text.color = "green"
                self.play_audio(correct_data["letter_audio"])

            # Enable next button
            next_btn.disabled = False
            self.page.update()

        # --- CREATE BUTTONS ---
        for opt in options:
            btn = ft.Container(
                width=80, height=80, bgcolor="white", border_radius=10, 
                alignment=ft.alignment.center, ink=True,
                content=ft.Text(opt["geo"], size=30, weight="bold", color="black"),
                shadow=ft.BoxShadow(blur_radius=5, color="#00000010")
            )
            # Attach click event
            btn.on_click = lambda e, b=btn, val=opt["geo"]: check_answer(val, b)
            options_row.controls.append(btn)

        # --- ADD TO PAGE ---
        self.page.add(
            ft.Row(
                [
                    ft.IconButton(ft.icons.HOME, icon_size=30, on_click=lambda e: self.go_home()), 
                    score_text,
                    ft.Container(width=40)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            progress_text,
            ft.Divider(height=20, color="transparent"),
            ft.Text("Which letter matches this image?", size=18),
            ft.Container(height=20),
            ft.Image(src=correct_data["example"]["image"], width=200, height=200, fit="contain", border_radius=15),
            ft.Container(height=20),
            options_row,
            ft.Container(height=20),
            feedback_text,
            ft.Container(height=20),
            next_btn
        )
        self.page.update()

    # --- GAME OVER SCREEN ---
    def show_game_over(self):
        self.page.controls.clear()
        
        percentage = int((self.score / 33) * 100)
        
        if percentage == 100:
            msg = "🏆 PERFECT SCORE!"
            color = "green"
        elif percentage > 70:
            msg = "Great job!"
            color = "blue"
        else:
            msg = "Keep practicing!"
            color = "orange"

        self.page.add(
            ft.Column(
                [
                    ft.Icon(ft.icons.EMOJI_EVENTS_ROUNDED, size=100, color="yellow"),
                    ft.Text("GAME OVER", size=40, weight="bold"),
                    ft.Text(f"Final Score: {self.score} / 33", size=30, weight="bold"),
                    ft.Text(f"{percentage}%", size=50, color=color, weight="bold"),
                    ft.Text(msg, size=20),
                    ft.Container(height=30),
                    ft.ElevatedButton("Play Again", on_click=lambda e: self.start_game()),
                    ft.TextButton("Go Home", on_click=lambda e: self.go_home())
                ],
                alignment="center", horizontal_alignment="center"
            )
        )
        self.page.update()