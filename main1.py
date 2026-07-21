import flet as ft
from gui.session_view import SessionView

def main(page: ft.Page):
    # 1. Application Window Configuration
    page.title = "Georgian Language Platform"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # NEW: Updated window properties for Flet 0.23.0+
    page.window.width = 450
    page.window.height = 800

    # 2. Initialize the main study loop
    study_session = SessionView(page=page, phase=None, unit=None, lesson=None)
    
    # 3. Mount to screen
    page.add(study_session)

if __name__ == "__main__":
    ft.app(target=main)