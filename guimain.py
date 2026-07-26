import flet as ft
import os

# Import Database Managers
from engine.db_managers import ContentDBManager, ProgressDBManager

# Import GUI Views
from gui.home_view import HomeView
from gui.units_view import UnitsView
from gui.lessons_view import LessonsView
from gui.session_view import SessionView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If your .db files are in the ROOT project folder:
CONTENT_DB_PATH = os.path.join(BASE_DIR, "database", "content_poolbook.db")
PROGRESS_DB_PATH = os.path.join(BASE_DIR, "database", "user_progress.db")

def main(page: ft.Page):
    # 1. Page & Window Configuration
    page.title = "GeoLearn - Georgian Language Platform"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

    page.window.width = 900
    page.window.height = 900

    # 2. Initialize Database Connection Managers
    content_db = ContentDBManager(CONTENT_DB_PATH)
    progress_db = ProgressDBManager(PROGRESS_DB_PATH)

    # 3. Central Navigation Container (Root View Stage)
    main_stage = ft.Container(expand=True)
    page.add(main_stage)

    # =========================================================================
    # ROUTING CONTROLLERS
    # =========================================================================

    def show_home():
        """Loads and renders the main dashboard."""
        completed_ids = progress_db.get_completed_lesson_ids()
        phases_summary = content_db.get_phases_summary(completed_ids)
        
        home_view = HomeView(
            phases_summary=phases_summary,
            on_select_phase=show_units,
            on_select_alphabet=lambda: show_session(phase=0, unit=1, lesson=1),
            on_quick_review=lambda: show_session(phase=None, unit=None, lesson=None)
        )
        
        main_stage.content = home_view
        page.update()

    def show_units(phase_num: int):
        """Loads and renders the units page for a chosen phase."""
        completed_ids = progress_db.get_completed_lesson_ids()
        units_summary = content_db.get_units_for_phase(phase_num, completed_ids)
        
        # Get phase name fallback
        phases_summary = content_db.get_phases_summary(completed_ids)
        phase_title = next((p["title"] for p in phases_summary if p["phase_num"] == phase_num), f"Phase {phase_num}")

        units_view = UnitsView(
            phase_num=phase_num,
            phase_title=phase_title,
            units_summary=units_summary,
            on_select_unit=show_lessons,
            on_back=show_home,
            on_home=show_home
        )
        
        main_stage.content = units_view
        page.update()

    def show_lessons(phase_num: int, unit_num: int):
        """Loads and renders the individual interactive lessons page for a unit."""
        completed_ids = progress_db.get_completed_lesson_ids()
        lessons_list = content_db.get_lessons_for_unit(phase_num, unit_num, completed_ids)
        
        # Get unit name fallback
        units_summary = content_db.get_units_for_phase(phase_num, completed_ids)
        unit_title = next((u["title"] for u in units_summary if u["unit_num"] == unit_num), f"Unit {unit_num}")

        lessons_view = LessonsView(
            phase_num=phase_num,
            unit_num=unit_num,
            unit_title=unit_title,
            lessons_list=lessons_list,
            on_select_lesson=lambda p, u, l: show_session(phase=p, unit=u, lesson=l),
            on_passive_read=lambda p, u: print(f"Opening passive read for Phase {p}, Unit {u}"),
            on_unit_review=lambda p, u: show_session(phase=p, unit=u, lesson=None),
            on_back=lambda: show_units(phase_num),
            on_home=show_home
        )
        
        main_stage.content = lessons_view
        page.update()

    def show_session(phase=None, unit=None, lesson=None):
        """Launches the interactive flashcard / study session runner."""
        session_view = SessionView(
            page=page, 
            phase=phase, 
            unit=unit, 
            lesson=lesson
        )
        
        # Add a top bar to allow quitting back to Home at any time during a session
        exit_bar = ft.Row(
            controls=[
                ft.TextButton("Exit Session", icon=ft.Icons.CLOSE, on_click=lambda e: show_home())
            ],
            alignment=ft.MainAxisAlignment.START
        )
        
        main_stage.content = ft.Column(
            controls=[
                exit_bar,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                session_view
            ],
            expand=True
        )
        page.update()

    # 4. Kickoff the App on Home Screen
    show_home()

if __name__ == "__main__":
    ft.app(target=main)