import flet as ft
import random

class MultipleChoiceCard(ft.Container):
    def __init__(self, mode: str, target_data: dict, distractors: list, on_submit: callable):
        super().__init__()
        self.mode = mode 
        self.target = target_data
        self.distractors = distractors
        self.on_submit = on_submit 
        
        self.padding = 20
        self.alignment = ft.alignment.center
        self.border_radius = 12
        
        self._build_ui()

    def _build_ui(self):
        # 1. Provide fallbacks to prevent UnboundLocalError
        prompt_text = "Missing Prompt"
        correct_ans = "Missing Answer"

        # 2. Extract Prompt and Correct Answer based on the specific mode
        if self.mode == "mc_geo_to_eng":
            prompt_text = self.target["geo"]
            correct_ans = self.target["eng"]
            
        elif self.mode == "mc_eng_to_geo":
            prompt_text = self.target["eng"]
            correct_ans = self.target["geo"]
            
        elif self.mode == "mc_geo_pair_geo":
            prompt_text = self.target["prompt_geo"]
            correct_ans = self.target["correct_geo"]
            
        # Audio Modes (Placeholder text prompt until actual audio files are integrated)
        elif self.mode == "audio_mc_to_eng":
            prompt_text = f"🔊 Audio: {self.target['geo']}" 
            correct_ans = self.target["eng"]
            
        elif self.mode == "audio_mc_to_geo":
            prompt_text = f"🔊 Audio: {self.target['geo']}"
            correct_ans = self.target["geo"]
            
        # Dialogue Modes
        elif self.mode == "dialogue_context_mc":
            prompt_text = f'"{self.target["quote_geo"]}"\n\n(What does this mean?)'
            correct_ans = self.target["correct_eng"]
            
        elif self.mode == "dialogue_roleplay_mc":
            # Target contains: "speaker", "correct_geo", "context_eng"
            prompt_text = f'Complete Speaker {self.target["speaker"]}\nHint: {self.target["context_eng"]}'
            correct_ans = self.target["correct_geo"]
            
        # 3. Mix options
        options = self.distractors + [correct_ans]
        random.shuffle(options)
        
        # 4. Create Option Buttons
        self.option_buttons = []
        for opt in options:
            btn = ft.ElevatedButton(
                text=opt,
                width=300,
                height=60,
                on_click=lambda e, ans=opt: self._handle_click(ans, correct_ans)
            )
            self.option_buttons.append(btn)
            
        # 5. Assemble View
        self.content = ft.Column(
            controls=[
                ft.Text(prompt_text, size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                *self.option_buttons
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
    def _handle_click(self, selected, correct):
        is_correct = (selected == correct)
        
        # Lock buttons to prevent double-clicking and reveal the correct answer
        for btn in self.option_buttons:
            btn.disabled = True
            if btn.text == correct:
                btn.bgcolor = ft.Colors.GREEN_700
                btn.color = ft.Colors.WHITE
            elif btn.text == selected and not is_correct:
                btn.bgcolor = ft.Colors.RED_700
                btn.color = ft.Colors.WHITE
                
        self.update()
        
        # Pass result back to LessonSession
        self.on_submit(is_correct, user_input=selected)