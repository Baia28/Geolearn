import flet as ft
import time
from engine.lesson_engine import LessonSession

# Import our custom UI components from the gui/ folder
from gui.receptive import MultipleChoiceCard
from gui.production import TypeGeorgian, MatchMatrix3x3
from gui.dialogues import DialoguePassiveView, LiveDialogueView

class SessionView(ft.Column):
    def __init__(self, page: ft.Page, phase=None, unit=None, lesson=None):
        super().__init__()
        self.page = page
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.expand = True
        
        # Initialize the Core Engine
        self.engine = LessonSession(phase_num=phase, unit_num=unit, lesson_num=lesson)
        
        # Setup Static UI Elements
        self.progress_bar = ft.ProgressBar(width=400, value=0.0, color=ft.Colors.GREEN_600, bgcolor=ft.Colors.GREY_200)
        self.status_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        
        # This container is our "stage"
        # This container is our "stage"
        self.card_stage = ft.Container(expand=True, alignment=ft.alignment.center)
        
        # --- NEW CODE: Create a permanent, hidden Continue button ---
        self.continue_btn = ft.ElevatedButton(
            "Continue ➔",
            visible=False, # Hidden by default
            width=200,
            height=50,
            on_click=lambda e: self._clear_and_load_next()
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
                target_data=card_data.get("target"),
                on_submit=self._handle_submission
            )
            
        # 4. Route: Passive Dialogue
        elif activity == "dialogue_passive":
            self.card_stage.content = DialoguePassiveView(
                dialogue_lines=card_data.get("target", {}).get("lines", []), 
                on_continue=lambda complete: self._handle_submission(True)
            )
            
        # 5. Route: Live Interactive Dialogue
        elif activity == "dialogue_interactive":
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
        self.card_stage.disabled = True 
        
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
                ft.ElevatedButton("Return to Home", on_click=lambda e: print("Routing home..."))
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.update()