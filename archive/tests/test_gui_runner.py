import flet as ft
from alphabet.alphabet_hub import AlphabetPage

def main(page: ft.Page):
    page.title = "Georgian Learning App"
    page.window.width = 800
    page.window.height = 900
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def go_home():
        page.controls.clear()
        page.add(
            ft.Text("Main Dashboard View", size=30),
            ft.ElevatedButton("Enter Alphabet Hub", on_click=lambda e: load_alphabet_hub())
        )
        page.update()

    def load_alphabet_hub():
        page.controls.clear()
        alphabet_view = AlphabetPage(on_back_home=go_home)
        page.add(alphabet_view)
        page.update()

    go_home()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")