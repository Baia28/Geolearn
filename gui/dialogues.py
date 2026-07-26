import flet as ft
import random

class ChatBubble(ft.Container):
    """A visually appealing messenger bubble."""
    def __init__(self, text: str, is_speaker_a: bool):
        super().__init__()
        self.padding = ft.padding.symmetric(horizontal=15, vertical=10)
        self.border_radius = ft.border_radius.only(
            top_left=15, top_right=15,
            bottom_left=4 if is_speaker_a else 15,
            bottom_right=15 if is_speaker_a else 4
        )
        self.bgcolor = ft.Colors.BLUE_GREY_100 if is_speaker_a else ft.Colors.BLUE_100
        self.content = ft.Text(text, color=ft.Colors.BLACK87, size=16)

class LiveDialogueView(ft.Column):
    def __init__(self, steps: list, on_submit: callable):
        super().__init__()
        self.steps = steps
        self.on_submit = on_submit
        self.current_step_idx = 0
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # Setup scrollable chat window
        self.chat_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.chat_container = ft.Container(
            content=self.chat_column,
            height=200,
            width=400,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE
        )
        
        # Container for the interactive multiple choice buttons
        self.options_container = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.controls = [
            ft.Text("Live Conversation", size=20, weight=ft.FontWeight.BOLD),
            self.chat_container, 
            ft.Divider(color=ft.Colors.TRANSPARENT), 
            self.options_container
        ]
        
    def did_mount(self):
        """Fires automatically when the view is safely rendered on the page."""
        self._advance_dialogue()

    def _add_bubble(self, text, is_speaker_a):
        bubble = ChatBubble(text=text, is_speaker_a=is_speaker_a)
        avatar = ft.CircleAvatar(content=ft.Text("A" if is_speaker_a else "B"), radius=16, bgcolor=ft.Colors.GREY_300)
        row = ft.Row([avatar, bubble] if is_speaker_a else [bubble, avatar], 
                     alignment=ft.MainAxisAlignment.START if is_speaker_a else ft.MainAxisAlignment.END)
        self.chat_column.controls.append(row)
        
        # --- NEW CODE: Auto-scroll to the bottom ---
        self.chat_column.update() 
        self.chat_column.scroll_to(offset=-1, duration=300)

    def _advance_dialogue(self):
        # 1. Check if conversation is over
        if self.current_step_idx >= len(self.steps):
            self.options_container.controls = [
                ft.ElevatedButton("Finish Conversation ➔", width=350, height=55, on_click=lambda e: self.on_submit(True))
            ]
            self.update()
            return

        # 2. Process current step
        step = self.steps[self.current_step_idx]
        
        if step["type"] == "prompt":
            # Speaker A talks. Add to chat and immediately load the next step (User's turn)
            is_speaker_a = (step["speaker"] == "A")
            self._add_bubble(step["text"], is_speaker_a)
            self.current_step_idx += 1
            self._advance_dialogue()
            
        elif step["type"] == "choice":
            # Speaker B (User) turn. Render options.
            self.options_container.controls.clear()
            options = step["distractors"] + [step["correct"]]
            random.shuffle(options)
            
            self.option_buttons = []
            for opt in options:
                btn = ft.ElevatedButton(
                    text=opt, width=350, height=55,
                    on_click=lambda e, ans=opt, correct=step["correct"], spk=step["speaker"]: self._handle_choice(ans, correct, spk)
                )
                self.option_buttons.append(btn)
                self.options_container.controls.append(btn)
                
            self.update()

    def _handle_choice(self, selected, correct, speaker):
        is_correct = (selected == correct)
        
        # Highlight choices
        for btn in self.option_buttons:
            btn.disabled = True
            if btn.text == correct:
                btn.bgcolor = ft.Colors.GREEN_700
                btn.color = ft.Colors.WHITE
            elif btn.text == selected and not is_correct:
                btn.bgcolor = ft.Colors.RED_700
                btn.color = ft.Colors.WHITE
        
        # Provide a Next button to inject the correct answer into the chat and move on
        continue_btn = ft.ElevatedButton(
            "Next Line ➔", 
            width=200, 
            height=45,
            # Cleaner lambda that won't confuse Flet's event handler
            on_click=lambda e: self._next_step_after_choice(correct, speaker) 
        )
        self.options_container.controls.append(ft.Divider(color=ft.Colors.TRANSPARENT, height=5))
        self.options_container.controls.append(continue_btn)
        self.update()

    def _next_step_after_choice(self, correct_text, speaker):
        # Inject the correct answer into the chat log permanently
        is_speaker_a = (speaker == "A")
        self._add_bubble(correct_text, is_speaker_a)
        
        # Advance the state machine
        self.current_step_idx += 1
        self.options_container.controls.clear()
        self._advance_dialogue()

class DialoguePassiveView(ft.Column):
    """The original purely passive reference view."""
    def __init__(self, dialogue_lines: list, on_continue: callable):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        chat_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        for line in dialogue_lines:
            is_speaker_a = (line[0] == "A")
            bubble = ChatBubble(text=line[1], is_speaker_a=is_speaker_a)
            avatar = ft.CircleAvatar(content=ft.Text(line[0]), radius=16, bgcolor=ft.Colors.GREY_300)
            row = ft.Row([avatar, bubble] if is_speaker_a else [bubble, avatar], 
                         alignment=ft.MainAxisAlignment.START if is_speaker_a else ft.MainAxisAlignment.END)
            chat_column.controls.append(row)

        chat_box = ft.Container(
            content=chat_column, height=300, width=400, padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300), border_radius=10, bgcolor=ft.Colors.WHITE
        )
        
        self.controls = [
            ft.Text("Reading Practice", size=24, weight=ft.FontWeight.BOLD),
            chat_box,
            ft.ElevatedButton("Continue", on_click=lambda e: on_continue(True), width=350, height=55)
        ]