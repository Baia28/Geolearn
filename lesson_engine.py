import flet as ft
import random

# -Expanded mock data for testing lesson engine logic - greeting
MOCK_LESSON_DATA = {
    "phase_id": 1,
    "unit_id": 1,
    "lesson_id": 1,
    "lesson_title": "First Encounters",
    "intro_steps": [
        {
            "step_id": "V1",
            "type": "vocabulary",
            "georgian": "გამარჯობა",
            "english": "Hello",
            "transliteration": "Gamarjoba",
            "image": "https://picsum.photos/200", 
            "audio": "assets/audio/gamarjoba.m4a",
            "options": ["Goodbye", "Hello", "Thank you"],
            "correct": "Hello"
        },
        {
            "step_id": "PT1",
            "type": "pattern",
            "georgian": "როგორ ხარ?",
            "english": "How are you?",
            "transliteration": "Rogor khar?",
            "image": "https://picsum.photos/201",
            "audio": "assets/audio/rogor_khar.m4a",
            "options": ["What is your name?", "How are you?", "I am fine"],
            "correct": "How are you?"
        },
        {
            "step_id": "L_C1",
            "type": "listening_choice", # Listening-only challenge
            "audio": "assets/audio/gamarjoba.m4a",
            "options": ["Thank you", "Yes", "Hello"],
            "correct": "Hello"
        },
        {
            "step_id": "D1",
            "type": "dialogue",
            "lines": [
                {"speaker": "A", "geo": "გამარჯობა!", "eng": "Hello!"},
                {"speaker": "B", "geo": "გამარჯობა! როგორ ხარ?", "eng": "Hello! How are you?"},
                {"speaker": "A", "geo": "კარგად, მადლობა.", "eng": "Well, thank you."}
            ],
            "question": "What does 'მადლობა' (madloba) mean here?",
            "options": ["Sorry", "Please", "Thank you"],
            "correct": "Thank you"
        },
        {
            "step_id": "T_C1",
            "type": "typing_challenge", # Keyboard Input Challenge
            "prompt_text": "Type the Georgian translation for:",
            "georgian": "Hello",
            "audio": "assets/audio/gamarjoba.m4a",
            "correct": "გამარჯობა" # I could potentially add keyboard on the screen in future
        }
    ]
}

class LessonEngine:
    def __init__(self, page, go_home_func):
        self.page = page
        self.go_home = go_home_func
        
        # Engine State Tracking
        self.current_step_idx = 0
        self.score = 0
        
        # UI Element References (Instantiated globally to access values across closures)
        self.typing_input = None

    def start_lesson(self):
        self.current_step_idx = 0
        self.score = 0
        self.render_slide()

    # Mock audio engine hook - prints to console for tracking local files
    def trigger_audio(self, audio_path):
        print(f"🔊 Playing Audio: {audio_path}")
        #I shouldn't forget- When plugged into main.py, replace this line with: self.play_audio_func(audio_path)

    def render_slide(self):
        self.page.controls.clear()
        self.page.vertical_alignment = "start"

        steps = MOCK_LESSON_DATA["intro_steps"]
        
        if self.current_step_idx >= len(steps):
            self.show_lesson_complete()
            return

        current_item = steps[self.current_step_idx]

        ### Here is Top Header Navigation Bar
        self.page.add(
            ft.Row([
                ft.IconButton(ft.icons.CLOSE, on_click=lambda e: self.go_home()),
                ft.Text(MOCK_LESSON_DATA["lesson_title"], size=18, weight="bold"),
                ft.Text(f"Score: {self.score}", size=14, color="blue")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=(self.current_step_idx + 1) / len(steps), color="blue")
        )

        ### Dynamic content layout engine
        content_column = ft.Column(horizontal_alignment="center", spacing=15, expand=True)
        interaction_container = ft.Column(spacing=10, horizontal_alignment="center")
        
        feedback_text = ft.Text("", size=16, weight="bold")
        next_btn = ft.ElevatedButton("Continue", disabled=True, width=280, on_click=lambda e: self.advance_slide())

        #
        # TYPE 1 & 2: Standard Vocabulary & Pattern Cards
        # 
        if current_item["type"] in ["vocabulary", "pattern"]:
            content_column.controls.append(ft.Image(src=current_item["image"], width=130, height=130, border_radius=10))
            
            # Interactive Sound Icon next to text
            content_column.controls.append(
                ft.Row([
                    ft.Text(current_item["georgian"], size=36, weight="bold"),
                    ft.IconButton(ft.icons.VOLUME_UP_ROUNDED, icon_color="blue", icon_size=30,
                                  on_click=lambda e: self.trigger_audio(current_item["audio"]))
                ], alignment="center")
            )
            content_column.controls.append(ft.Text(current_item["transliteration"], size=18, italic=True, color="grey"))
            self.trigger_audio(current_item["audio"]) # Auto-play on slide entry

        # 
        # TYPE 3: Pure Auditory Listening Only 
        # 
        elif current_item["type"] == "listening_choice":
            content_column.controls.append(ft.Text("Listen closely and choose the correct meaning:", size=16, color="grey700"))
            
            # Massive Audio Button in place of visual hints
            content_column.controls.append(
                ft.Container(
                    width=120, height=120, bgcolor="blue100", border_radius=60,
                    alignment=ft.alignment.center, ink=True,
                    on_click=lambda e: self.trigger_audio(current_item["audio"]),
                    content=ft.Icon(ft.icons.VOLUME_UP_ROUNDED, size=50, color="blue")
                )
            )
            self.trigger_audio(current_item["audio"]) # Auto-play on entry

        # 
        # TYPE 4: Dialogue Mode 
        # 
        elif current_item["type"] == "dialogue":
            chat_box = ft.Column(spacing=10, width=320)
            for line in current_item["lines"]:
                is_me = line["speaker"] == "A"
                chat_box.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(line["geo"], size=16, weight="bold", color="white" if is_me else "black"),
                            ft.Text(line["eng"], size=12, color="white70" if is_me else "grey700")
                        ], spacing=2),
                        bgcolor="blue" if is_me else "white", padding=10,
                        border_radius=ft.border_radius.only(
                            top_left=12, top_right=12, 
                            bottom_left=2 if is_me else 12, bottom_right=12 if is_me else 2
                        ),
                        alignment=ft.alignment.center_right if is_me else ft.alignment.center_left,
                        shadow=ft.BoxShadow(blur_radius=4, color="#00000005")
                    )
                )
            content_column.controls.append(chat_box)
            content_column.controls.append(ft.Text(current_item["question"], size=16, weight="bold"))

        # 
        # TYPE 5: Active Recall Typing Practice 
        # 
        elif current_item["type"] == "typing_challenge":
            content_column.controls.append(ft.Text(current_item["prompt_text"], size=16, color="grey700"))
            
            content_column.controls.append(
                ft.Row([
                    ft.Text(current_item["georgian"], size=36, weight="bold"),
                    ft.IconButton(ft.icons.VOLUME_UP_ROUNDED, icon_color="blue",
                                  on_click=lambda e: self.trigger_audio(current_item["audio"]))
                ], alignment="center")
            )
            
            # Render custom text box for alphanumeric keyboard entry
            self.typing_input = ft.TextField(
                label="Type answer here...", width=280, 
                autofocus=True, text_align="center",
                on_submit=lambda e: evaluate_typing_input()
            )
            interaction_container.controls.append(self.typing_input)
            
            # Change the execution path for check buttons under typing mode
            check_typing_btn = ft.ElevatedButton("Check Answer", width=280, bgcolor="blue", color="white",
                                                 on_click=lambda e: evaluate_typing_input())
            interaction_container.controls.append(check_typing_btn)

        # EVALUATION LOGIC for CHOICE QUESTIONS 
        def select_option(e, selected_val):
            is_correct = selected_val == current_item["correct"]
            if is_correct:
                self.score += 1
                feedback_text.value = "✅ Correct!"
                feedback_text.color = "green"
            else:
                feedback_text.value = f"❌ Incorrect! Answer: {current_item['correct']}"
                feedback_text.color = "red"
            
            for btn in interaction_container.controls:
                if isinstance(btn, ft.ElevatedButton):
                    btn.disabled = True
                    if btn.text == current_item["correct"]:
                        btn.bgcolor = "green"
                        btn.color = "white"
                    elif btn.text == selected_val and not is_correct:
                        btn.bgcolor = "red"
                        btn.color = "white"

            next_btn.disabled = False
            self.page.update()

        # EVALUATION LOGIC for TYPING QUESTIONS 
        def evaluate_typing_input():
            user_raw_string = self.typing_input.value.strip().lower()
            is_correct = user_raw_string == current_item["correct"]
            
            if is_correct:
                self.score += 1
                feedback_text.value = "🎉 Flawless Typing!"
                feedback_text.color = "green"
                self.typing_input.border_color = "green"
            else:
                feedback_text.value = f"❌ Typo! Expected spelling: '{current_item['correct']}'"
                feedback_text.color = "red"
                self.typing_input.border_color = "red"
            
            self.typing_input.disabled = True
            # Remove the primary check button from the control array tree layout view
            interaction_container.controls.pop() 
            next_btn.disabled = False
            self.page.update()

        # Populate option buttons if the question isn't a typing challenge
        if current_item["type"] != "typing_challenge":
            for option in current_item["options"]:
                interaction_container.controls.append(
                    ft.ElevatedButton(
                        text=option, width=280, height=45,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e, val=option: select_option(e, val)
                    )
                )

        # Assemble elements cleanly onto the Flet root frame interface
        self.page.add(
            ft.Container(
                content=ft.Column([content_column, interaction_container, feedback_text, next_btn], 
                                  horizontal_alignment="center", spacing=15),
                padding=20, expand=True
            )
        )
        self.page.update()

    def advance_slide(self):
        self.current_step_idx += 1
        self.render_slide()

    def show_lesson_complete(self):
        self.page.controls.clear()
        self.page.vertical_alignment = "center"
        self.page.horizontal_alignment = "center"
        
        self.page.add(
            ft.Icon(ft.icons.CELEBRATION_ROUNDED, size=80, color="amber"),
            ft.Text("Lesson Completed!", size=28, weight="bold"),
            ft.Text(f"Final Score: {self.score} / {len(MOCK_LESSON_DATA['intro_steps'])}", size=18, color="grey"),
            ft.Container(height=20),
            ft.ElevatedButton("Return to Main Menu", width=220, on_click=lambda e: self.go_home())
        )
        self.page.update()