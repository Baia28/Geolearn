import flet as ft

def main(page: ft.Page):
    page.title = "Flet Test"
    page.add(ft.Text("Hello, Flet 0.25.2!"))

ft.app(target=main)