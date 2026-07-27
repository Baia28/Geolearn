import flet as ft
import random

class MultipleChoiceCard(ft.Container):
    def __init__(self, mode: str, target_data: dict, distractors: list, on_submit: callable):
        super().__init__()
        self.mode = mode 
        self.target = target_data or {}
        self.distractors = distractors or []
        self.on_submit = on_submit 
        
        self.padding = ft.padding.only(top=0, left=20, right=20, bottom=10)
        self.alignment = ft.alignment.top_center
        self.border_radius = 12
        
        self._build_ui()

    def _build_ui(self):
        prompt_ui = None
        subtitle_ui = ft.Container()
        correct_ans = "Missing Answer"

        # -------------------------------------------------------------
        # 1. AUDIO MODES: Massive Audio Button + Guidance Subtitle
        # -------------------------------------------------------------
        if "audio_mc" in self.mode:
            audio_text = self.target.get("geo", "")
            correct_ans = self.target.get("eng") if self.mode == "audio_mc_to_eng" else self.target.get("geo")
            trans_text = self.target.get("trans", "")

            prompt_ui = ft.Container(
                width=110, 
                height=110, 
                bgcolor=ft.Colors.BLUE_100, 
                border_radius=55,
                alignment=ft.alignment.center, 
                ink=True,
                on_click=lambda e: self.trigger_audio(audio_text),
                content=ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=48, color=ft.Colors.BLUE_700)
            )
            # Subtitle with optional Transliteration
            subtitle_controls = [
                ft.Text("Listen and select the correct answer", size=13, color=ft.Colors.GREY_500, italic=True)
            ]
            #
            #
            ########################################
            # -------------------------------------------------------------
            # 🙈 COMMENT OUT THESE LINES TO HIDE TRANSLITERATION IN AUDIO MC:
            if trans_text:
                subtitle_controls.append(
                    ft.Text(f"({trans_text})", size=15, color=ft.Colors.BLUE_GREY_600, italic=True)
                )
            ######################################

            subtitle_ui = ft.Column(
                subtitle_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            )
            
            # Auto-play on entry
            self.trigger_audio(audio_text)

        # -------------------------------------------------------------
        # 2. GEORGIAN PROMPTS: Text + Small Audio Icon + Transliteration
        # -------------------------------------------------------------
        elif self.mode in ["mc_geo_to_eng", "mc_geo_pair_geo", "dialogue_context_mc"]:
            if self.mode == "mc_geo_to_eng":
                geo_text = self.target.get("geo", "")
                correct_ans = self.target.get("eng", "")
                trans_text = self.target.get("trans", "")
            elif self.mode == "mc_geo_pair_geo":
                geo_text = self.target.get("prompt_geo") or self.target.get("prompt", "")
                correct_ans = self.target.get("correct_geo") or self.target.get("correct", "")
                trans_text = self.target.get("prompt_trans") or self.target.get("trans", "")
            elif self.mode == "dialogue_context_mc":
                geo_text = self.target.get("quote_geo", "")
                correct_ans = self.target.get("correct_eng", "")
                trans_text = self.target.get("trans", "")
            else:
                geo_text = self.target.get("geo") or self.target.get("prompt", "Missing Prompt")
                correct_ans = self.target.get("eng") or self.target.get("correct", "Missing Answer")
                trans_text = self.target.get("trans", "")

            # Georgian Prompt Row with Audio Button
            prompt_ui = ft.Row([
                ft.Text(geo_text, size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.IconButton(
                    icon=ft.Icons.VOLUME_UP,
                    icon_color=ft.Colors.BLUE_600,
                    on_click=lambda e, txt=geo_text: self.trigger_audio(txt),
                    tooltip="Listen"
                )
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True)

            #if trans_text:
            #    subtitle_ui = ft.Text(trans_text, size=16, color=ft.Colors.GREY_500, italic=True)
            #else:
            #    subtitle_ui = ft.Container()
            subtitle_ui = ft.Text(trans_text, size=16, color=ft.Colors.GREY_500, italic=True)


        # -------------------------------------------------------------
        # 3. ENGLISH / OTHER PROMPTS: Clean Text Prompt
        # -------------------------------------------------------------
        else:
            if self.mode == "mc_eng_to_geo":
                prompt_text = self.target.get("eng", "")
                correct_ans = self.target.get("geo", "")
            elif self.mode == "dialogue_roleplay_mc":
                speaker = self.target.get("speaker", "A")
                context = self.target.get("context_eng", "")
                prompt_text = f"Complete Speaker {speaker}\nHint: {context}"
                correct_ans = self.target.get("correct_geo", "")
            else:
                prompt_text = self.target.get("prompt", self.target.get("eng", "Missing Prompt"))
                correct_ans = self.target.get("correct", self.target.get("geo", "Missing Answer"))

            # ---------------------------------------------------------
            # Image / Placeholder Widget
            # ---------------------------------------------------------
            image_src = self.target.get("image", None)

            if image_src:
                # Real Image (when provided in target dict)
                image_widget = ft.Image(
                    src=image_src,
                    width=160,
                    height=110,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(10)
                )
            else:
                # Placeholder Box (when no image exists yet)
                image_widget = ft.Container(
                    width=160,
                    height=110,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=40, color=ft.Colors.GREY_400)
                )

            # Stack the Image/Placeholder on top of your existing text prompt
            prompt_ui = ft.Column(
                controls=[
                    image_widget,
                    ft.Text(prompt_text, size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        # -------------------------------------------------------------
        # 4. Build Distractor Options
        # -------------------------------------------------------------
        options = list(self.distractors) + [correct_ans]
        random.shuffle(options)

        self.option_buttons = []
        for opt in options:
            btn = ft.ElevatedButton(
                content=ft.Text(opt, size=18, text_align=ft.TextAlign.CENTER),
                data=opt,  # Stores original option text securely for evaluation
                width=380, # width of the option button
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(vertical=20, horizontal=20)
                ),
                on_click=lambda e, ans=opt, corr=correct_ans: self._handle_click(ans, corr)
            )
            self.option_buttons.append(btn)

        # -------------------------------------------------------------
        # 5. Assemble View
        # -------------------------------------------------------------
        self.content = ft.Column(
            controls=[
                prompt_ui,
                subtitle_ui,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                # Group buttons in a nested Column with dedicated spacing
                ft.Column(
                    controls=self.option_buttons,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12  # <-- Adjust space BETWEEN option buttons here!
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            spacing=5  # Keeps prompt and subtitle tightly stacked
        )

    def trigger_audio(self, text: str = None):
        audio_target = text or self.target.get("geo") or self.target.get("prompt_geo", "Unknown")
        print(f"🔊 Playing audio for: {audio_target}")

    def _handle_click(self, selected, correct):
        is_correct = (selected == correct)
        
        # Lock buttons to prevent double-clicking and reveal correct vs wrong
        for btn in self.option_buttons:
            btn.disabled = True
            opt_value = btn.data
            if opt_value == correct:
                btn.bgcolor = ft.Colors.GREEN_700
                btn.color = ft.Colors.WHITE
            elif opt_value == selected and not is_correct:
                btn.bgcolor = ft.Colors.RED_700
                btn.color = ft.Colors.WHITE
                
        self.update()
        
        # Pass result back to SessionView / Engine
        self.on_submit(is_correct, user_input=selected)