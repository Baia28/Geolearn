import flet as ft
import time
from engine.lesson_engine import LessonSession

# Import our custom UI components from the gui/ folder
from gui.receptive import MultipleChoiceCard
from gui.production import TypeGeorgian, MatchMatrix3x3
from gui.dialogues import DialoguePassiveView

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
        self.card_stage = ft.Container(expand=True, alignment=ft.alignment.center)
        
        self.controls = [
            ft.Row([ft.Icon(ft.icons.FLAG), self.progress_bar], alignment=ft.MainAxisAlignment.CENTER),
            self.status_text,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            self.card_stage
        ]
        
        # NOTE: We DO NOT call self._load_next_card() here anymore!

    def did_mount(self):
        """
        Flet automatically calls this method the moment page.add() finishes in main.py.
        It is now completely safe to load cards and call self.update().
        """
        self._load_next_card()

    def _load_next_card(self):
        """Fetches the active card from the queue and routes it to the right GUI."""
        card_data = self.engine.get_next_exercise()
        
        # Check for Lesson Completion
        if not card_data:
            self._show_completion_screen()
            return
            
        activity = card_data.get("activity")
        
        # Route: Multiple Choice
        if activity in ["mc_geo_to_eng", "mc_eng_to_geo", "mc_geo_pair_geo", 
                        "audio_mc_to_eng", "audio_mc_to_geo", 
                        "dialogue_context_mc", "dialogue_roleplay_mc"]:
            self.card_stage.content = MultipleChoiceCard(
                mode=activity,
                target_data=card_data.get("target"),
                distractors=card_data.get("distractors", []),
                on_submit=self._handle_submission
            )
            
        # Route: Production
        elif activity in ["type_georgian", "audio_dictation"]:
            self.card_stage.content = TypeGeorgian(
                target_data=card_data.get("target"),
                on_submit=self._handle_submission
            )
            
        # Route: Matching Matrix
        elif activity == "match_matrix_3x3":
            self.card_stage.content = MatchMatrix3x3(
                targets=card_data.get("targets", []),
                on_submit=self._handle_submission
            )
            
        # Route: Passive Reading
        elif activity == "dialogue_passive":
            self.card_stage.content = DialoguePassiveView(
                dialogue_lines=card_data.get("target", {}).get("lines", []), 
                on_continue=lambda complete: self._handle_submission(True)
            )
            
        else:
            self.card_stage.content = ft.Text(f"Unsupported Activity: {activity}", color=ft.Colors.RED)
            
        # This is now 100% safe because did_mount guarantees the UI exists.
        self.update()

    def _handle_submission(self, is_correct, user_input=None):
        """Logs the answer to the engine, updates progress, and queues the next card."""
        if is_correct:
            self.status_text.value = "Correct! ✨"
            self.status_text.color = ft.Colors.GREEN_600
        else:
            self.status_text.value = "Let's review that one again."
            self.status_text.color = ft.Colors.ORANGE_600
        self.update()
        
        result = self.engine.submit_answer(is_correct, user_input)
        
        self.progress_bar.value = result.get("progress", 0.0)
        self.update()
        
        time.sleep(1.0)
        self.status_text.value = ""
        self._load_next_card()

    def _show_completion_screen(self):
        """Displays the end-of-lesson celebration."""
        self.card_stage.content = ft.Column(
            controls=[
                ft.Icon(ft.icons.EMOJI_EVENTS, size=80, color=ft.Colors.AMBER),
                ft.Text("Lesson Completed!", size=36, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Return to Home", on_click=lambda e: print("Routing home..."))
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.update()