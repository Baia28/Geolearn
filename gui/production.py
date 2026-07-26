import flet as ft
import random
from gui.keyboard import GeorgianKeyboard

class MatchMatrix3x3(ft.Container):
    def __init__(self, targets: list, on_submit: callable):
        super().__init__()
        self.targets = targets  # List of dicts: {"id": 1, "geo": "...", "eng": "..."}
        self.on_submit = on_submit
        
        self.selected_btn = None
        self.matches_found = 0
        self.padding = 20
        self._build_grid()

    def _build_grid(self):
        # Separate Georgian and English into two clean columns
        geo_buttons = []
        eng_buttons = []
        
        for t in self.targets:
            geo_buttons.append({"type": "geo", "text": t["geo"], "id": t["id"]})
            eng_buttons.append({"type": "eng", "text": t["eng"], "id": t["id"]})
            
        random.shuffle(geo_buttons)
        random.shuffle(eng_buttons)
        
        geo_col = ft.Column([self._create_btn(b) for b in geo_buttons], spacing=10)
        eng_col = ft.Column([self._create_btn(b) for b in eng_buttons], spacing=10)
            
        self.content = ft.Row(
            controls=[geo_col, eng_col],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=40
        )

    def _create_btn(self, data):
        return ft.ElevatedButton(
            text=data["text"],
            data=data,
            width=150,
            height=60,
            on_click=self._handle_tap
        )

    def _handle_tap(self, e):
        clicked_btn = e.control

        # 1. Ignore clicks on already matched/disabled buttons
        if clicked_btn.disabled:
            return

        # 2. First tap selection
        if self.selected_btn is None:
            self.selected_btn = clicked_btn
            self.selected_btn.bgcolor = ft.Colors.BLUE_200
            self.update()
            return

        # 3. Deselect if tapping the same button twice
        if self.selected_btn == clicked_btn:
            self.selected_btn.bgcolor = None
            self.selected_btn = None
            self.update()
            return

        # 4. Evaluate pair match
        id1 = self.selected_btn.data["id"]
        id2 = clicked_btn.data["id"]
        type1 = self.selected_btn.data["type"]
        type2 = clicked_btn.data["type"]

        if id1 == id2 and type1 != type2:
            # Match success: fade both buttons out seamlessly
            fade_color = ft.Colors.GREEN_100
            
            self.selected_btn.bgcolor = fade_color
            self.selected_btn.opacity = 0.35
            self.selected_btn.disabled = True

            clicked_btn.bgcolor = fade_color
            clicked_btn.opacity = 0.35
            clicked_btn.disabled = True

            self.matches_found += 1
            self.selected_btn = None  # Reset active tracker immediately
            self.update()

            # Check if all pairs in this matrix are solved
            if self.matches_found == len(self.targets):
                self.on_submit(True)
        else:
            # Wrong match: reset selection color and clear tracker
            self.selected_btn.bgcolor = None
            self.selected_btn = None
            self.update()



class TypeGeorgian(ft.Column):
    def __init__(self, mode: str = "type_georgian", target_data: dict = None, on_submit: callable = None):
        super().__init__()
        self.mode = mode
        self.target = target_data or {}
        self.on_submit = on_submit
        self.evaluated = False
        
        #####
        # Lifts content upward towards the progress bar
        self.padding = ft.padding.only(top=0, left=15, right=15, bottom=5)
        self.alignment = ft.alignment.top_center  # <-- Ensures top alignment
        self.border_radius = 12
        #####

        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # State tracking for two-step feedback (Check -> Continue)
        #self.evaluated = False
        #self.is_correct = False
        #self.user_text = ""
        
        self._build_ui()

    def _build_ui(self):
        # 1. Setup Prompt UI according to Mode
        if self.mode == "audio_dictation":
            prompt_ui = ft.Container(
                width=100, height=100, bgcolor=ft.Colors.BLUE_100, border_radius=50,
                alignment=ft.alignment.center, ink=True,
                on_click=lambda e: self.trigger_audio(),
                content=ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=40, color=ft.Colors.BLUE_700)
            )
            subtitle_ui = ft.Text("Listen and type in Georgian", size=14, color=ft.Colors.GREY_500, italic=True)
            self.trigger_audio()
        else:
            prompt_ui = ft.Text(self.target.get("eng", ""), size=28, weight=ft.FontWeight.W_500)
            subtitle_ui = ft.Container()

        # 2. Input Field
        self.input_field = ft.TextField(
            label="Type in Georgian", 
            width=350, 
            text_align=ft.TextAlign.CENTER,
            on_submit=self._validate
        )
        
        # 3. Custom On-Screen Keyboard
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self._append_char,
            on_backspace=self._remove_char
        )
        
        # 4. Feedback Box (Hidden until user checks answer)
        self.feedback_container = ft.Container(visible=False)
        
        # 5. Action Button
        self.submit_btn = ft.ElevatedButton("Check Answer", width=350, height=50, on_click=self._validate)
        
        # Assemble
        self.controls = [
            prompt_ui,
            subtitle_ui,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.input_field, 
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.feedback_container,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.keyboard,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.submit_btn
        ]

    def _append_char(self, char):
        if self.evaluated:
            return # Block typing during feedback phase
        current_text = self.input_field.value if self.input_field.value else ""
        self.input_field.value = current_text + char
        self.input_field.update()

    def _remove_char(self):
        if self.evaluated:
            return # Block backspace during feedback phase
        current_text = self.input_field.value if self.input_field.value else ""
        if len(current_text) > 0:
            self.input_field.value = current_text[:-1]
            self.input_field.update()

    def trigger_audio(self):
        print(f"🔊 Playing audio for: {self.target.get('geo', 'Unknown')}")


    def _validate(self, e):
        if self.evaluated:
            return

        self.user_text = self.input_field.value.strip() if self.input_field.value else ""
        target_text = self.target.get("geo", "").strip()

        # 1. Clean punctuation for comparison
        punctuation = "!?.,;:'\""
        clean_user = self.user_text.translate(str.maketrans('', '', punctuation)).lower()
        clean_target = target_text.translate(str.maketrans('', '', punctuation)).lower()

        self.is_correct = (clean_user == clean_target)
        self.evaluated = True

        # 2. Lock inputs & hide internal keyboard/button so session_view takes over
        self.input_field.disabled = True
        self.keyboard.visible = False
        self.submit_btn.visible = False  # Hides internal button

        # 3. Configure visual feedback styles
        bg_color = ft.Colors.GREEN_50 if self.is_correct else ft.Colors.RED_50
        border_color = ft.Colors.GREEN_400 if self.is_correct else ft.Colors.RED_400
        icon_name = ft.Icons.CHECK_CIRCLE if self.is_correct else ft.Icons.CANCEL
        icon_color = ft.Colors.GREEN_600 if self.is_correct else ft.Colors.RED_600
        title_text = "Correct! 🎉" if self.is_correct else "Not quite..."

        geo_target = self.target.get("geo", "")
        trans_target = self.target.get("trans", "")

        # 4. Construct Feedback Panel UI
        feedback_column = [
            ft.Row([
                ft.Icon(icon_name, color=icon_color, size=24),
                ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD, color=icon_color)
            ], alignment=ft.MainAxisAlignment.CENTER),

            ft.Row([
                ft.Text(f"Target: {geo_target}", size=18, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.Icons.VOLUME_UP,
                    icon_color=ft.Colors.BLUE_600,
                    on_click=lambda _: self.trigger_audio(),
                    tooltip="Listen to correct audio"
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ]

        if trans_target:
            feedback_column.append(
                ft.Text(f"Transliteration: {trans_target}", size=14, color=ft.Colors.GREY_600, italic=True)
            )

        self.feedback_container.content = ft.Column(feedback_column, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.feedback_container.bgcolor = bg_color
        self.feedback_container.border = ft.border.all(1, border_color)
        self.feedback_container.border_radius = 10
        self.feedback_container.padding = 10
        self.feedback_container.width = 350
        self.feedback_container.visible = True

        # Auto-play correct audio if answer was incorrect
        if not self.is_correct:
            self.trigger_audio()

        self.update()

        # 5. Hand control off to session_view's global continue workflow
        self.on_submit(self.is_correct, user_input=self.user_text)