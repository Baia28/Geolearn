import flet as ft
import random
from gui.audio_utils import play_audio_file
from gui.keyboard import GeorgianKeyboard  
VOWELS = {"ა", "ე", "ი", "ო", "უ"}

class AlphabetTypingGameView(ft.Column):
    """Audio dictation game where users listen to a Georgian letter sound and type it using the keyboard."""
    
    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        self.questions = []
        self.remaining_questions = []
        self.current_target = None
        self.score = 0
        self.total_questions = 0
        self.evaluated = False

    def start_game(self):
        """Fetches letters with audio from the database and initializes a new game session."""
        all_letters = self.db.get_alphabet_letters()
        # Filter strictly letters that have audio files available
        self.questions = [item for item in all_letters if item.get("letter_audio")]
        random.shuffle(self.questions)
        
        self.remaining_questions = list(self.questions)
        self.score = 0
        self.total_questions = len(self.questions)
        
        self.play_round()

    def play_round(self):
        self.controls.clear()
        self.evaluated = False

        if not self.remaining_questions:
            self.show_game_over()
            return

        self.current_target = self.remaining_questions.pop(0)

        # Header controls
        score_text = ft.Text(f"Score: {self.score}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        progress_text = ft.Text(
            f"Progress: {self.total_questions - len(self.remaining_questions)} / {self.total_questions}", 
            size=14, color=ft.Colors.GREY_600
        )

        instruction_ui = ft.Row(
            controls=[
                ft.Icon(ft.Icons.HEADSET, size=18, color=ft.Colors.BLUE_600),
                ft.Text("Listen and type what you hear", size=15, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500, italic=True)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6
        )

        # Big Audio Sound Button
        audio_btn = ft.Container(
            width=90, 
            height=90, 
            bgcolor=ft.Colors.BLUE_100, 
            border_radius=45,
            alignment=ft.alignment.center, 
            ink=True,
            on_click=lambda e: self.trigger_audio(),
            content=ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=42, color=ft.Colors.BLUE_700),
            shadow=ft.BoxShadow(blur_radius=6, color="#00000015")
        )

        prompt_ui = ft.Column(
            controls=[
                audio_btn,
                ft.Text("Tap button to listen again", size=12, color=ft.Colors.GREY_600, italic=True)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4
        )

        # Input Field
        self.input_field = ft.TextField(
            label="Type in Georgian", 
            width=350, 
            text_align=ft.TextAlign.CENTER,
            on_submit=self._validate
        )

        # Feedback Panel Container (Hidden initially)
        self.feedback_container = ft.Container(visible=False)

        # Custom Georgian On-Screen Keyboard
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self._append_char,
            on_backspace=self._remove_char
        )

        # Submit / Action Button
        self.submit_btn = ft.Container(
            content=ft.ElevatedButton(
                "Check Answer", 
                width=350, 
                height=48, 
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                on_click=self._validate
            )
        )

        # Next Button (Replaces Submit after checking answer)
        self.next_btn = ft.ElevatedButton(
            "Next Question →", 
            width=350,
            height=48,
            visible=False,
            on_click=lambda e: self.play_round()
        )

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
                ft.Container(height=5),
                instruction_ui,
                ft.Container(height=5),
                prompt_ui,
                self.input_field,
                self.feedback_container,
                self.keyboard,
                ft.Container(height=5),
                self.submit_btn,
                self.next_btn
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        main_wrapper = ft.Container(
            content=game_layout,
            padding=ft.padding.only(left=30, right=30, top=10, bottom=20),
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [main_wrapper]
        if self.page:
            self.update()
            self.trigger_audio()

    def trigger_audio(self):
        """Plays current letter audio dictation."""
        if self.current_target and self.page:
            audio_path = self.current_target.get("letter_audio")
            if audio_path:
                play_audio_file(self.page, audio_path)

    def _append_char(self, char):
        if self.evaluated:
            return
        current_text = self.input_field.value if self.input_field.value else ""
        self.input_field.value = current_text + char
        self.input_field.update()

    def _remove_char(self):
        if self.evaluated:
            return
        current_text = self.input_field.value if self.input_field.value else ""
        if len(current_text) > 0:
            self.input_field.value = current_text[:-1]
            self.input_field.update()

    def _validate(self, e=None):
        if self.evaluated:
            return

        user_text = (self.input_field.value or "").strip()
        correct_geo = self.current_target.get("georgian", "").strip()
        linguistic_desc = self.current_target.get("linguistic_desc") or self.current_target.get("transliteration", "")

        is_correct = (user_text == correct_geo)
        self.evaluated = True

        if is_correct:
            self.score += 1

        # Lock text field and hide keyboard & submit button to clear screen space
        self.input_field.disabled = True
        self.keyboard.visible = False
        self.submit_btn.visible = False
        self.next_btn.visible = True

        # Styles
        bg_color = ft.Colors.GREEN_50 if is_correct else ft.Colors.RED_50
        border_color = ft.Colors.GREEN_300 if is_correct else ft.Colors.RED_300
        icon_name = ft.Icons.CHECK_CIRCLE if is_correct else ft.Icons.CANCEL
        icon_color = ft.Colors.GREEN_600 if is_correct else ft.Colors.RED_600
        title_text = "Correct! 🎉" if is_correct else "Not quite..."
        target_label = "Correct Answer:" if is_correct else "Expected Answer:"
        letter_color = ft.Colors.RED_600 if correct_geo in VOWELS else ft.Colors.BLUE_900

        feedback_column = [
            ft.Row([
                ft.Icon(icon_name, color=icon_color, size=22),
                ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD, color=icon_color)
            ], alignment=ft.MainAxisAlignment.CENTER),

            ft.Text(target_label, size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),

            ft.Text(
                correct_geo, 
                size=44, 
                weight=ft.FontWeight.BOLD, 
                color=letter_color,
                text_align=ft.TextAlign.CENTER
            ),

            ft.IconButton(
                icon=ft.Icons.VOLUME_UP_ROUNDED,
                icon_color=ft.Colors.BLUE_600,
                icon_size=26,
                on_click=lambda _: self.trigger_audio(),
                tooltip="Listen again"
            )
        ]

        if linguistic_desc:
            feedback_column.append(
                ft.Text(
                    f"Pronunciation: {linguistic_desc}", 
                    size=14, 
                    color=ft.Colors.GREY_700, 
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                )
            )

        self.feedback_container.content = ft.Column(
            controls=feedback_column,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4
        )
        self.feedback_container.bgcolor = bg_color
        self.feedback_container.border = ft.border.all(1, border_color)
        self.feedback_container.border_radius = 12
        self.feedback_container.padding = 14
        self.feedback_container.width = 350
        self.feedback_container.visible = True

        if not is_correct:
            self.trigger_audio()

        self.update()

    def show_game_over(self):
        self.controls.clear()
        pct = int((self.score / self.total_questions) * 100) if self.total_questions > 0 else 0
        
        self.controls = [
            ft.Column(
                [
                    ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, size=90, color=ft.Colors.AMBER),
                    ft.Text("TYPING QUIZ COMPLETE!", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Final Score: {self.score} / {self.total_questions}", size=22, weight=ft.FontWeight.BOLD),
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