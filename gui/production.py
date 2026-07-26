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
    def __init__(self, target_data: dict, on_submit: callable):
        super().__init__()
        self.target = target_data
        self.on_submit = on_submit
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        self.english_prompt = ft.Text(self.target["eng"], size=28, weight=ft.FontWeight.W_500)
        
        # Make the input field read-only IF you want to force them to use the on-screen keyboard,
        # otherwise leave it editable so native physical keyboards work too!
        self.input_field = ft.TextField(
            label="Type in Georgian", 
            width=350, 
            text_align=ft.TextAlign.CENTER,
            on_submit=self._validate
        )
        
        # Instantiate our custom keyboard
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self._append_char,
            on_backspace=self._remove_char
        )
        
        self.submit_btn = ft.ElevatedButton("Check Answer", width=350, height=50, on_click=self._validate)
        
        self.controls = [
            self.english_prompt, 
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.input_field, 
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.keyboard,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            self.submit_btn
        ]
        
    def _append_char(self, char):
        # Add the tapped character to the text field
        current_text = self.input_field.value if self.input_field.value else ""
        self.input_field.value = current_text + char
        
    def _remove_char(self):
        # Handle backspace
        current_text = self.input_field.value if self.input_field.value else ""
        if len(current_text) > 0:
            self.input_field.value = current_text[:-1]

    def _validate(self, e):
        user_text = self.input_field.value.strip() if self.input_field.value else ""
        target_text = self.target["geo"].strip()
        
        # Remove common punctuation for lenient validation
        punctuation = "!?.,;:'\""
        clean_user = user_text.translate(str.maketrans('', '', punctuation)).lower()
        clean_target = target_text.translate(str.maketrans('', '', punctuation)).lower()
        
        is_correct = (clean_user == clean_target)
        self.on_submit(is_correct, user_input=user_text)