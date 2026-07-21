import flet as ft
import random
from gui.keyboard import GeorgianKeyboard

class MatchMatrix3x3(ft.Container):
    def __init__(self, targets: list, on_submit: callable):
        super().__init__()
        self.targets = targets # List of dicts: {"id": 1, "geo": "...", "eng": "..."}
        self.on_submit = on_submit
        
        self.selected_btn = None
        self.matches_found = 0
        self.padding = 20
        self._build_grid()

    def _build_grid(self):
        # Flatten geo and eng into a pool of buttons
        buttons_data = []
        for t in self.targets:
            buttons_data.append({"type": "geo", "text": t["geo"], "id": t["id"]})
            buttons_data.append({"type": "eng", "text": t["eng"], "id": t["id"]})
            
        random.shuffle(buttons_data)
        
        self.grid_controls = []
        for bd in buttons_data:
            btn = ft.ElevatedButton(
                text=bd["text"],
                data=bd, # Store the dict to reference ID later
                width=130,
                height=70,
                on_click=self._handle_tap
            )
            self.grid_controls.append(btn)
            
        self.content = ft.Row(
            controls=self.grid_controls,
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

    def _handle_tap(self, e):
        clicked_btn = e.control
        if self.selected_btn is None:
            # First tap
            self.selected_btn = clicked_btn
            clicked_btn.bgcolor = ft.Colors.BLUE_200
            self.update()
        else:
            # Second tap
            if self.selected_btn == clicked_btn:
                # Deselect
                self.selected_btn.bgcolor = None
                self.selected_btn = None
                self.update()
                return
                
            # Check match
            id1 = self.selected_btn.data["id"]
            id2 = clicked_btn.data["id"]
            type1 = self.selected_btn.data["type"]
            type2 = clicked_btn.data["type"]
            
            if id1 == id2 and type1 != type2:
                # Correct match!
                self.selected_btn.visible = False
                clicked_btn.visible = False
                self.matches_found += 1
                e.page.update()

                # Check if entire matrix batch is cleared
                if self.matches_found == len(self.targets):
                    self.on_submit(True)
            else:
                # Wrong Match
                self.selected_btn.bgcolor = None
                e.page.update()
            
            self.selected_btn = None



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
        is_correct = (user_text == self.target["geo"])
        self.on_submit(is_correct, user_input=user_text)