import flet as ft
import random

class ChatBubble(ft.Container):
    """A messenger bubble with support for display_text and optional translations."""
    def __init__(self, text: str, is_speaker_a: bool, subtext: str = None):
        super().__init__()
        self.padding = ft.padding.symmetric(horizontal=15, vertical=10)
        self.border_radius = ft.border_radius.only(
            top_left=15, top_right=15,
            bottom_left=4 if is_speaker_a else 15,
            bottom_right=15 if is_speaker_a else 4
        )
        self.bgcolor = ft.Colors.BLUE_GREY_100 if is_speaker_a else ft.Colors.BLUE_100
        
        controls = [ft.Text(text, color=ft.Colors.BLACK87, size=16, weight=ft.FontWeight.W_500)]
        if subtext:
            controls.append(ft.Text(subtext, color=ft.Colors.BLACK54, size=12, italic=True))
            
        self.content = ft.Column(controls, spacing=2, tight=True)


class LiveDialogueView(ft.Column):
    """Interactive chat view where user plays Speaker B with full error feedback."""
    def __init__(self, steps: list, on_submit: callable):
        super().__init__()
        self.steps = steps
        self.on_submit = on_submit
        self.current_step_idx = 0
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # Enable scrolling on main column so feedback cards never cut off buttons
        self.scroll = ft.ScrollMode.AUTO

        # Scrollable chat window
        self.chat_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.chat_container = ft.Container(
            content=self.chat_column,
            height=220,
            width=400,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE
        )
        
        # Interactive options and feedback container
        self.options_container = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.controls = [
            ft.Row([
                ft.Text("Roleplay Practice", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text("You: Speaker B", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE_600,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            self.chat_container, 
            ft.Divider(color=ft.Colors.TRANSPARENT, height=10), 
            self.options_container
        ]
        
    def did_mount(self):
        """Starts dialogue progression when rendered."""
        self._advance_dialogue()

    def _add_bubble(self, text: str, is_speaker_a: bool, subtext: str = None):
        bubble = ChatBubble(text=text, is_speaker_a=is_speaker_a, subtext=subtext)
        avatar = ft.CircleAvatar(
            content=ft.Text("A" if is_speaker_a else "B", weight=ft.FontWeight.BOLD), 
            radius=16, 
            bgcolor=ft.Colors.BLUE_GREY_300 if is_speaker_a else ft.Colors.BLUE_300
        )
        row = ft.Row(
            [avatar, bubble] if is_speaker_a else [bubble, avatar], 
            alignment=ft.MainAxisAlignment.START if is_speaker_a else ft.MainAxisAlignment.END
        )
        self.chat_column.controls.append(row)
        self.chat_column.update() 
        self.chat_column.scroll_to(offset=-1, duration=300)

    def _advance_dialogue(self):
        # 1. End of dialogue check
        if self.current_step_idx >= len(self.steps):
            self.options_container.controls = [
                ft.Text("🎉 Dialogue Completed!", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.Container(height=8),
            ]
            self.update()

            # Directly notify the parent session runner that this card activity is finished!
            self.on_submit(True)
            return

        step = self.steps[self.current_step_idx]
        
        if step["type"] == "prompt":
            # Speaker A talks automatically
            self._add_bubble(step["text"], is_speaker_a=True)
            self.current_step_idx += 1
            self._advance_dialogue()  # Advance to next step (e.g. User's turn)
            
        elif step["type"] == "choice":
            # Speaker B turn (User responds)
            self.options_container.controls.clear()
            self.options_container.controls.append(
                ft.Text("Your Turn (Speaker B): Choose a response", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_800)
            )
            self.options_container.controls.append(ft.Container(height=5))
            
            # Options setup
            options = step["distractors"] + [step["correct"]]
            random.shuffle(options)
            
            self.option_buttons = []
            for opt in options:
                btn = ft.ElevatedButton(
                    text=opt["geo"], 
                    width=350, 
                    height=48,
                    on_click=lambda e, selected_opt=opt, correct_opt=step["correct"]: self._handle_choice(selected_opt, correct_opt)
                )
                self.option_buttons.append((btn, opt))
                self.options_container.controls.append(btn)
                
            self.update()

    def _handle_choice(self, selected_opt, correct_opt):
        is_correct = (selected_opt["geo"] == correct_opt["geo"])
        
        # Highlight choice buttons
        for btn, opt in self.option_buttons:
            btn.disabled = True
            if opt["geo"] == correct_opt["geo"]:
                btn.bgcolor = ft.Colors.GREEN_700
                btn.color = ft.Colors.WHITE
            elif opt["geo"] == selected_opt["geo"] and not is_correct:
                btn.bgcolor = ft.Colors.RED_700
                btn.color = ft.Colors.WHITE

        # Build Rich Feedback Card explaining meaning
        if is_correct:
            feedback_card = ft.Container(
                content=ft.Column([
                    ft.Text("✅ Excellent!", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                    ft.Text(f"\"{correct_opt['geo']}\" ({correct_opt.get('trans', '')}) — '{correct_opt.get('eng', '')}'", size=13, color=ft.Colors.GREEN_900)
                ], spacing=2),
                padding=10,
                border_radius=8,
                bgcolor=ft.Colors.GREEN_50,
                border=ft.border.all(1, ft.Colors.GREEN_300),
                width=350
            )
        else:
            feedback_card = ft.Container(
                content=ft.Column([
                    ft.Text("❌ Incorrect Answer", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800),
                    ft.Text(f"You selected: \"{selected_opt['geo']}\" ({selected_opt.get('trans', '')})", size=12, color=ft.Colors.RED_900),
                    ft.Text(f"Meaning: \"{selected_opt.get('eng', 'N/A')}\"", size=12, italic=True, color=ft.Colors.RED_800),
                    ft.Divider(height=8, color=ft.Colors.RED_200),
                    ft.Text(f"Correct response: \"{correct_opt['geo']}\" ({correct_opt.get('trans', '')})", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_900),
                    ft.Text(f"Meaning: \"{correct_opt.get('eng', 'N/A')}\"", size=12, italic=True, color=ft.Colors.GREEN_800)
                ], spacing=2),
                padding=10,
                border_radius=8,
                bgcolor=ft.Colors.RED_50,
                border=ft.border.all(1, ft.Colors.RED_300),
                width=350
            )

        continue_btn = ft.ElevatedButton(
            "Next Line ➔", 
            width=350, 
            height=45,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            on_click=lambda e: self._next_step_after_choice(correct_opt["geo"]) 
        )

        self.options_container.controls.append(ft.Container(height=8))
        self.options_container.controls.append(feedback_card)
        self.options_container.controls.append(ft.Container(height=8))
        self.options_container.controls.append(continue_btn)

        self.update()
        # Auto-scroll main window down so the Continue button is immediately visible
        self.scroll_to(offset=-1, duration=300)

    def _next_step_after_choice(self, correct_text):
        # Inject Speaker B's line into the chat log permanently
        self._add_bubble(correct_text, is_speaker_a=False)
        
        # Advance the state machine
        self.current_step_idx += 1
        self.options_container.controls.clear()
        self._advance_dialogue()


class DialoguePassiveView(ft.Column):
    """Passive reference view showing full dialogue with translations."""
    def __init__(self, dialogue_lines: list, on_continue: callable):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.scroll = ft.ScrollMode.AUTO
        
        chat_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        for line in dialogue_lines:
            # Tuple: (speaker, rendered_georgian, transliteration, english)
            speaker = line[0]
            rendered_geo = line[1]
            trans = line[2] if len(line) > 2 else ""
            eng = line[3] if len(line) > 3 else ""
            
            is_speaker_a = (speaker == "A")
            subtext = f"{trans} — '{eng}'" if trans or eng else None
            
            bubble = ChatBubble(text=rendered_geo, is_speaker_a=is_speaker_a, subtext=subtext)
            avatar = ft.CircleAvatar(
                content=ft.Text(speaker, weight=ft.FontWeight.BOLD), 
                radius=16, 
                bgcolor=ft.Colors.BLUE_GREY_300 if is_speaker_a else ft.Colors.BLUE_300
            )
            row = ft.Row(
                [avatar, bubble] if is_speaker_a else [bubble, avatar], 
                alignment=ft.MainAxisAlignment.START if is_speaker_a else ft.MainAxisAlignment.END
            )
            chat_column.controls.append(row)

        chat_box = ft.Container(
            content=chat_column, height=320, width=400, padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300), border_radius=10, bgcolor=ft.Colors.WHITE
        )
        
        self.controls = [
            ft.Text("Reading Practice", size=22, weight=ft.FontWeight.BOLD),
            chat_box,
            #ft.Container(height=10),
            ft.ElevatedButton("Start Roleplay ➔", on_click=lambda e: on_continue(True), width=350, height=50)
        ]