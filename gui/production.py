import flet as ft
import random
from gui.keyboard import GeorgianKeyboard
from gui.audio_utils import play_audio_file
from gui.gui_helper import create_review_badge

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

        # 1. Group the columns into a Row first (this used to be self.content directly)
        grid_row = ft.Row(
            controls=[geo_col, eng_col],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=40
        )

        # 2. Create the beautiful Instruction Banner
        instruction_ui = ft.Row(
            controls=[
                ft.Icon(ft.Icons.JOIN_INNER, size=16, color=ft.Colors.GREY_500),
                ft.Text("Match the corresponding pairs", size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500, italic=True)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6
        )

        # 3. Stack the instruction banner on top of the grid
        self.content = ft.Column(
            controls=[
                instruction_ui,
                ft.Container(height=10),
                grid_row
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
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
        
        # Proper Column alignment and tight gap spacing (replaces dividers)
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 14  # Tightens spacing across all elements
        
        self._build_ui()

    def did_mount(self):
        # Auto-play audio upon loading in dictation mode once page context is ready
        if self.mode == "audio_dictation":
            self.trigger_audio()

    def _build_ui(self):
        # Dynamic Instruction Banner 
        task_icon = ft.Icons.HEADSET if self.mode == "audio_dictation" else ft.Icons.KEYBOARD
        task_instruction = "Listen and type what you hear" if self.mode == "audio_dictation" else "Translate and type in Georgian"
        
        instruction_ui = ft.Row(
            controls=[
                ft.Icon(task_icon, size=16, color=ft.Colors.GREY_500),
                ft.Text(task_instruction, size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500, italic=True)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6
        )

        # 1. Setup Prompt UI according to Mode
        if self.mode == "audio_dictation":
            audio_btn = ft.Container(
                width=90, 
                height=90, 
                bgcolor=ft.Colors.BLUE_100, 
                border_radius=45,
                alignment=ft.alignment.center, 
                ink=True,
                on_click=lambda e: self.trigger_audio(),
                content=ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=38, color=ft.Colors.BLUE_700),
                margin=ft.margin.only(top=-5)  # Lift audio icon closer to progress bar
            )
            #subtitle_ui = ft.Text("Listen and type in Georgian", size=13, color=ft.Colors.GREY_500, italic=True)
            #self.trigger_audio()

            prompt_ui = ft.Column(
                controls=[
                    audio_btn,
                    ft.Text("Tap button to listen again", size=12, color=ft.Colors.GREY_600, italic=True)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4
            )
        else:
            prompt_ui = ft.Text(self.target.get("eng", ""), size=28, weight=ft.FontWeight.W_500)
            # Add clear instructions for typing
            #subtitle_ui = ft.Text("Translate and type in Georgian", size=13, color=ft.Colors.GREY_500, italic=True)

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
        self.keyboard.margin = ft.margin.only(top=-2)  # Tighten gap under input/feedback panel
        
        # 4. Feedback Box (Hidden until user checks answer)
        self.feedback_container = ft.Container(visible=False)
        
        # 5. Blue Action Button (Wrapped in Container for negative top margin)
        self.submit_btn = ft.Container(
            content=ft.ElevatedButton(
                "Check Answer", 
                width=350, 
                height=48, 
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                on_click=self._validate
            ),
            margin=ft.margin.only(top=-4)  # Pulls blue button up closer to spacebar
        )

        review_badge = create_review_badge(self.target)

        # Assemble layout without transparent Dividers
        self.controls = []
        if review_badge:
            self.controls.append(review_badge)

        self.controls.extend([
            instruction_ui,
            ft.Container(height=5),
            prompt_ui,
            self.input_field, 
            self.feedback_container,
            self.keyboard,
            self.submit_btn
        ])

    def _append_char(self, char):
        if self.evaluated:
            return  # Block typing during feedback phase
        current_text = self.input_field.value if self.input_field.value else ""
        self.input_field.value = current_text + char
        self.input_field.update()

    def _remove_char(self):
        if self.evaluated:
            return  # Block backspace during feedback phase
        current_text = self.input_field.value if self.input_field.value else ""
        if len(current_text) > 0:
            self.input_field.value = current_text[:-1]
            self.input_field.update()

    def trigger_audio(self):
        audio_path = self.target.get("audio") or self.target.get("audio_path")
        play_audio_file(self.page, audio_path)
        print(f"🔊 Playing audio for: {self.target.get('geo', 'Unknown')}")

    def _validate(self, e):
        if self.evaluated:
            return

        self.user_text = self.input_field.value.strip() if self.input_field.value else ""
        target_text = self.target.get("geo", "").strip()

        punctuation = "!?.,;:'\""
        clean_user = self.user_text.translate(str.maketrans('', '', punctuation)).lower()
        clean_target = target_text.translate(str.maketrans('', '', punctuation)).lower()

        self.is_correct = (clean_user == clean_target)
        self.evaluated = True

        # Lock inputs & hide internal keyboard/button so session_view takes over
        self.input_field.disabled = True
        self.keyboard.visible = False
        self.submit_btn.visible = False  # Hides container and button seamlessly

        bg_color = ft.Colors.GREEN_50 if self.is_correct else ft.Colors.RED_50
        border_color = ft.Colors.GREEN_400 if self.is_correct else ft.Colors.RED_400
        icon_name = ft.Icons.CHECK_CIRCLE if self.is_correct else ft.Icons.CANCEL
        icon_color = ft.Colors.GREEN_600 if self.is_correct else ft.Colors.RED_600
        title_text = "Correct! 🎉" if self.is_correct else "Not quite..."

        geo_target = self.target.get("geo", "")
        trans_target = self.target.get("trans", "")

        # Select label based on user outcome
        target_label = "Correct Answer:" if self.is_correct else "Expected Answer:"

        geo_target = self.target.get("geo", "")
        trans_target = self.target.get("trans", "")

        feedback_column = [
            ft.Row([
                ft.Icon(icon_name, color=icon_color, size=24),
                ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD, color=icon_color)
            ], alignment=ft.MainAxisAlignment.CENTER),

            ft.Row([
                ft.Text(f"{target_label} {geo_target}", size=18, weight=ft.FontWeight.BOLD),
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

        if not self.is_correct:
            self.trigger_audio()

        self.update()
        self.on_submit(self.is_correct, user_input=self.user_text)