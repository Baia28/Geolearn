import flet as ft
from data.alphabet import alphabet
from data.anbani import anbani

class LearnPage:
    def __init__(self, page, go_home_func, play_audio_func):
        # We store these tools so we can use them anywhere in this file
        self.page = page
        self.go_home = go_home_func     # The function to go back to Main Menu
        self.play_audio = play_audio_func # The function to play sound

    def show_anbani(self):
        self.page.controls.clear()

        self.page.add(
            ft.Row(
                [ 
                    # Left: The Home Button
                    ft.IconButton(ft.icons.HOME, icon_size=30, on_click=lambda e: self.go_home()), 

                    # Center: The Title
                    ft.Text("Learn Georgian Alphabet", size=32, weight="bold"),

                    # Right: Ghost Spacer
                    ft.Container(width=40, height=40)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
            ft.Text("Tap a letter to explore", size=16, color="grey"),

            #ft.divider(height=20, color="transparent"),

            ft.Row(
                [self.letter_card(l) for l in anbani], 
                wrap=True,
                spacing=12,
                alignment="center",
            ),
        )
        self.page.update()

    def show_letter_detail(self, letter):
        self.page.controls.clear()

        geo_char = letter["geo"]
        data = alphabet[geo_char]

        # Play sound immediately
        self.play_audio(data["letter_audio"])

        self.page.add(
            ft.TextButton(
                "← Back (უკან დაბრუნება)",
                on_click=lambda e: self.show_anbani()
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
                    on_click=lambda e: self.play_audio(data["letter_audio"])
                    ),
                    ft.ElevatedButton(
                        "Example word",
                        icon=ft.icons.VOLUME_UP,
                    on_click=lambda e: self.play_audio(data["example"]["audio"])
                    ),
                ],
                alignment="center",
                spacing = 20
            ),
        )
        self.page.update()

    def letter_card(self, letter):
       return ft.Container(
            width=120,
            height=120,
            border_radius=20,
            bgcolor="white",
            padding=10,
            ink=True,
            on_click=lambda e, l=letter: self.show_letter_detail(l),
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
    
    


