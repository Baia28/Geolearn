import flet as ft
import time
from engine.lesson_engine import LessonSession

# Import our custom UI components from the gui/ folder
from gui.receptive import MultipleChoiceCard
from gui.production import TypeGeorgian, MatchMatrix3x3
from gui.dialogues import DialoguePassiveView, LiveDialogueView

class SessionView(ft.Column):
    def __init__(self, page: ft.Page, phase=None, unit=None, lesson=None, on_return=None):
        super().__init__()
        self.page = page
        self.on_return = on_return # <-- Store it
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO  
        
        # Initialize the Core Engine
        self.engine = LessonSession(phase_num=phase, unit_num=unit, lesson_num=lesson)
        
        # Setup Static UI Elements
        self.progress_bar = ft.ProgressBar(width=400, value=0.0, color=ft.Colors.GREEN_600, bgcolor=ft.Colors.GREY_200)
        self.status_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
        # says correct or incorrect
        
        # This container is our "stage"
        # This container is our "stage"
        self.card_stage = ft.Container(expand=True, alignment=ft.alignment.center)
        
        # --- UPDATED CODE: Create a permanent, hidden Continue button ---
        self.continue_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Text("Continue ➔", size=20, weight=ft.FontWeight.BOLD),  # <-- Larger text with bold weight
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                height=70,
                width=220,
                on_click=lambda _: self._clear_and_load_next()
            ),
            visible=False,
            padding=ft.padding.only(bottom=50, top=10) # <-- Adds space above the bottom screen edge
        )
        
        self.controls = [
            ft.Row([ft.Icon(ft.Icons.FLAG), self.progress_bar], alignment=ft.MainAxisAlignment.CENTER),
            self.status_text,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            self.card_stage,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            self.continue_btn # Added to the main stage layout
        ]
        
    def did_mount(self):
        """
        Flet automatically calls this method the moment page.add() finishes in main.py.
        It is now completely safe to load cards and call self.update().
        """
        self._load_next_card()

    def _load_next_card(self):
        """Fetches the next card from the engine and displays the correct UI component."""
        card_data = self.engine.get_next_exercise()
        
        # If there are no more cards, show the celebration screen
        if not card_data:
            self._show_completion_screen()
            return

        activity = card_data.get("activity")

        try:
            # 1. Receptive Multiple Choice Cards
            if "mc" in activity:
                self.card_stage.content = MultipleChoiceCard(
                    mode=activity,
                    target_data=card_data.get("target"),
                    distractors=card_data.get("distractors"),
                    on_submit=self._handle_submission
                )
            # 2. Production Typing / Dictation
            elif activity in ["type_georgian", "audio_dictation"]:
                self.card_stage.content = TypeGeorgian(
                    mode=activity,
                    target_data=card_data.get("target"),
                    on_submit=self._handle_submission
                )
            # ... (other routes here)

        except Exception as err:
            # Catch any rendering error and print it to screen!
            print(f"❌ Error loading card ({activity}): {err}")
            import traceback
            traceback.print_exc()
            self.card_stage.content = ft.Text(
                f"Error loading exercise '{activity}':\n{err}", 
                color=ft.Colors.RED_600, 
                size=16
            )
            

        # 1. Route: Multiple Choice
        if activity in ["mc_geo_to_eng", "mc_eng_to_geo", "mc_geo_pair_geo", "audio_mc_to_eng", "audio_mc_to_geo"]:
            self.card_stage.content = MultipleChoiceCard(
                mode=activity,
                target_data=card_data.get("target"),
                distractors=card_data.get("distractors", []),
                on_submit=self._handle_submission
            )
            
        # 2. Route: Match Matrix
        elif activity == "match_matrix_3x3":
            self.card_stage.content = MatchMatrix3x3(
                targets=card_data.get("targets", []), # Uses 'targets' array from wave_generator
                on_submit=self._handle_submission
            )
            
        # 3. Route: Type Georgian & Audio Dictation
        elif activity in ["type_georgian", "audio_dictation"]:
            self.card_stage.content = TypeGeorgian(
                mode=activity,
                target_data=card_data.get("target"),
                on_submit=self._handle_submission
            )
            
        # 4. Route: Passive Dialogue
        elif activity == "dialogue_passive":
            self.card_stage.content = DialoguePassiveView(
                dialogue_lines=card_data.get("target", {}).get("lines", []), 
                on_continue=lambda complete: self._handle_submission(True)
            )
            
        # 5. Route: Live Interactive Dialogue (Roleplay)
        elif activity in ["dialogue_roleplay_mc", "dialogue_activity", "dialogue_interactive"]:
            self.card_stage.content = LiveDialogueView(
                steps=card_data.get("target", {}).get("steps", []),
                on_submit=lambda complete: self._handle_submission(True)
            )
            
        # 6. Fallback Route
        else:
            self.card_stage.content = ft.Text(f"Unsupported Activity: {activity}", color=ft.Colors.RED)

        self.update()


    def _handle_submission(self, is_correct, user_input=None):
        """Logs the answer to the engine, updates progress, and pauses for reflection."""
        if is_correct:
            self.status_text.value = "Correct! ✨"
            self.status_text.color = ft.Colors.GREEN_600
        else:
            self.status_text.value = "Let's review that one again."
            self.status_text.color = ft.Colors.ORANGE_600
        
        result = self.engine.submit_answer(is_correct, user_input)
        self.progress_bar.value = result.get("progress", 0.0)
        
        # Reveal the continue button
        self.continue_btn.visible = True
        
        # Freeze the card stage so they can't click other options while reading feedback
        #self.card_stage.disabled = True 
        
        self.update()

    def _clear_and_load_next(self):
        """Resets the UI state and pulls the next flashcard."""
        self.status_text.value = ""
        self.continue_btn.visible = False
        self.card_stage.disabled = False # Unfreeze the stage
        self._load_next_card()

    def _show_completion_screen(self):
        """Displays the end-of-lesson celebration."""
        self.card_stage.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.EMOJI_EVENTS, size=80, color=ft.Colors.AMBER),
                ft.Text("Lesson Completed!", size=36, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    "Return to Unit ➔", 
                    on_click=lambda e: self.on_return() if self.on_return else print("No route for unit provided.")
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.update()