import flet as ft
from data.alphabet import alphabet
from data.anbani import anbani

# NEW: Import the class we just created
from learn_page import LearnPage 
from anban_game import AnbanGame
from lesson_engine import LessonEngine



def main(page: ft.Page):
    page.title = "GeoLearn"    
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F7F6FB"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"
    page.padding = 20
    page.scroll = "auto"

    # --- SHARED AUDIO PLAYER ---
    def play_audio(src):
        page.overlay.clear()
        try:
            audio = ft.Audio(src=src, autoplay=True)
            page.overlay.append(audio)
            page.update()
        except Exception as e:
            print(f"Audio Error: {e}")

    # --- SETUP PAGES ---
    # We initialize the separate page and give it the tools it needs (page, home function, audio function)
    # Note: We pass 'show_home' so the other file knows how to get back here!
    # 1. Initialize Learn Page
    learn_section = LearnPage(page, lambda: show_home(), play_audio)
    # 2. Initialize Game Page (YOU WERE MISSING THIS LINE!)
    game_section = AnbanGame(page, lambda: show_home(), play_audio)
    # 3. Initialize Lesson Engine
    lesson_section = LessonEngine(page, lambda: show_home())

    # ==========================================
    # NAVIGATION HUB (HOME)
    # ==========================================
    def show_home():
        page.controls.clear()
        page.vertical_alignment = "center"
        
        page.add(
            ft.Column(
                [
                    ft.Icon(ft.icons.SCHOOL_ROUNDED, size=80, color="red"),
                    ft.Text("GeoLearn", size=40, weight="bold"),
                    
                    ft.Container(height=30), 
                    
                    # LINK TO NEW FILE -> We call learn_section.show_gallery()
                    ft.Container(
                        width=280, height=80, bgcolor="white", border_radius=15, ink=True,
                        on_click=lambda e: learn_section.show_anbani(), 
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.MENU_BOOK, color="orange", size=30),
                                ft.Text("Learn Alphabet", size=20, weight="bold"),
                                ft.Icon(ft.icons.ARROW_FORWARD_IOS, color="grey", size=16),
                            ],
                            alignment="spaceAround"
                        ),
                        shadow=ft.BoxShadow(blur_radius=10, color="#00000010", offset=ft.Offset(0,4))
                    ),
                    
                    ft.Container(height=15),

                    # LINK TO GAME (Still here for now)
                    ft.Container(
                        width=280, height=80, bgcolor="white", border_radius=15, ink=True,
                        on_click=lambda e: game_section.start_game(), 
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.GAMES_ROUNDED, color="green", size=30),
                                ft.Text("Practice Alphabet", size=20, weight="bold"),
                                ft.Icon(ft.icons.ARROW_FORWARD_IOS, color="grey", size=16),
                            ],
                            alignment="spaceAround"
                        ),
                        shadow=ft.BoxShadow(blur_radius=10, color="#00000010", offset=ft.Offset(0,4))
                    ),

                    ft.Container(
                        width=280, height=80, bgcolor="white", border_radius=15, ink=True,
                        on_click=lambda e: lesson_section.start_lesson(), 
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.LIGHTBULB_ROUNDED, color="amber", size=30),
                                ft.Text("Start Lesson 1", size=20, weight="bold"),
                                ft.Icon(ft.icons.ARROW_FORWARD_IOS, color="grey", size=16),
                            ],
                            alignment="spaceAround"
                        ),
                        shadow=ft.BoxShadow(blur_radius=10, color="#00000010", offset=ft.Offset(0,4))
                    ),
                ],
                alignment="center", horizontal_alignment="center",
            )
        )
        page.update()

    show_home()

ft.app(target=main, assets_dir=".")

