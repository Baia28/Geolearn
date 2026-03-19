from data.alphabet import alphabet 
from data.anbani import anbani 
import flet as ft


def main(page: ft.Page):
    page.title = "GeoLearn"
    page.bgcolor = "#F7F6FB"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"
    page.padding = 15
    page.scroll = "auto"


    #--- Updated Audio Function ---
    def play_audio(src):
        page.overlay.clear()
        audio = ft.Audio(src=src, autoplay=True)

        page.overlay.append(audio)
        page.update()



    def show_anbani():
        page.controls.clear()
        page.add(
            ft.Text("Learn Georgian Alphabet", size=32, weight="bold"),
            ft.Text("Tap a letter to explore", size=16, color="grey"),
            ft.Row(
                [letter_card(l) for l in anbani], 
                wrap=True,
                spacing=12,
                alignment="center",
            ),
        )
        page.update()



    def show_letter(letter):
        page.controls.clear()

        geo_char = letter["geo"]
        data = alphabet[geo_char]

        # Auto-play letter sound when opening the page
        play_audio(data["letter_audio"])

        page.add(
            ft.TextButton(
                "← Back (უკან დაბრუნება)",
                on_click=lambda e: show_anbani()
            ),

            ft.Text(geo_char, size=96, weight="bold"),
            ft.Text(f'Pronunciation: {letter["latin"]}', size=20, color ="grey"),

            ft.Image(
                src=data["example"]["image"],
                width=200,
                height=200,
                fit="contain"
            ),

            ft.Container(height=20), ### spacer

            ft.Text(
                f'{data["example"]["word"]} — {data["example"]["meaning"]}',
                size=22,
                weight="bold"
            ),

            ft.Row(
                [
                    ft.ElevatedButton(
                        "Letter sound", #🔊 
                        icon=ft.icons.VOLUME_UP,
                    on_click=lambda e: play_audio(data["letter_audio"])
                    ),
                    ft.ElevatedButton(
                        "Example word",
                        icon=ft.icons.VOLUME_UP,
                    on_click=lambda e: play_audio(data["example"]["audio"])
                    ),
                ],
                alignment="center",
                spacing = 20
            ),
        )
        page.update()



    def letter_card(letter):
        return ft.Container(
            width=120,
            height=120,
            border_radius=20,
            bgcolor="white",
            padding=10,
            ink=True,
            on_click=lambda e, l=letter: show_letter(l),
            content=ft.Column(
                [
                    ft.Text(letter["geo"], size=48, weight="bold", color="#333333"),
                    ft.Text(letter["latin"], size=16, color="grey"),
                ],
                alignment="center",
                horizontal_alignment="center",
            ),
            shadow=ft.BoxShadow(
                blur_radius=10,
                color="#00000010",
                offset=ft.Offset(0, 4),
            ),
        )

    show_anbani()



ft.app(
    target=main,
    # Just tell Flet that your project root is the assets directory so I can see and access to pictures.
    assets_dir="."   #OPTION 2 (cleaner long-term, but optional)   assets_dir="assets"
)


        



