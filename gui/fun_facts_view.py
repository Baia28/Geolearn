import flet as ft

class FunFactsView(ft.View):
    def __init__(self, on_back):
        categories = {
            "Language 🗣️": [
                ("A Linguistic Island", "Georgian belongs to the Kartvelian language family, completely unrelated to any other major language group in the world.", ft.Icons.SPEAKER_NOTES),
                ("Tongue-Twisting Consonants", "It's famous for extreme consonant clusters. The word 'gvprtskvni' (გვფრცქვნი) means 'you are peeling us' and has 8 consonants in a row!", ft.Icons.RECORD_VOICE_OVER),
                ("Three Alphabets", "While Mkhedruli is used today, Georgia actually has three distinct alphabets (Asomtavruli, Nuskhuri, and Mkhedruli), all recognized by UNESCO.", ft.Icons.FONT_DOWNLOAD),
            ],
            "Culture & Wine 🍷": [
                ("The Birthplace of Wine", "Georgia has been producing wine for over 8,000 years. They traditionally ferment it in large clay jars called Qvevri, buried underground.", ft.Icons.WINE_BAR),
                ("The Supra", "A traditional Georgian feast is called a 'Supra', led by a 'Tamada' (toastmaster) who guides hours of poetic toasts, singing, and eating.", ft.Icons.RESTAURANT),
                ("Polyphonic Singing", "Georgian polyphonic singing is so culturally significant that the song 'Chakrulo' was sent into space on the Voyager Golden Record in 1977.", ft.Icons.LIBRARY_MUSIC),
            ],
            "Geography & History 🏔️": [
                ("Not 'Georgia' to Locals", "Georgians call their country 'Sakartvelo' (საქართველო), which translates to 'land of the Kartvelians'.", ft.Icons.MAP),
                ("Europe's Highest Village", "The village of Ushguli in the Svaneti region sits at 2,100 meters (6,900 ft), making it one of the highest continuously inhabited settlements in Europe.", ft.Icons.LANDSCAPE),
                ("First Europeans", "The 1.8-million-year-old skulls of Zezva and Mzia found in Dmanisi are the oldest hominid remains discovered outside of Africa.", ft.Icons.HISTORY),
            ]
        }

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            scrollable=True,
            tab_alignment=ft.TabAlignment.CENTER,
            indicator_color=ft.Colors.RED_800,
            label_color=ft.Colors.RED_900,
            unselected_label_color=ft.Colors.BLUE_GREY_400,
            tabs=[]
        )

        for cat_name, items in categories.items():
            tab_content = ft.ListView(
                expand=1, 
                spacing=15, 
                padding=ft.padding.only(top=15, bottom=20)
            )
            for title, desc, icon in items:
                tab_content.controls.append(
                    ft.Card(
                        elevation=2,
                        surface_tint_color=ft.Colors.WHITE,
                        content=ft.Container(
                            padding=20,
                            border_radius=10,
                            bgcolor=ft.Colors.WHITE,
                            content=ft.ListTile(
                                leading=ft.Icon(icon, size=40, color=ft.Colors.RED_800),
                                title=ft.Text(title, weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLACK87),
                                subtitle=ft.Text(desc, size=15, color=ft.Colors.BLACK54),
                            )
                        )
                    )
                )
            
            # Prominent tab title styling with enlarged text size and padding
            tabs.tabs.append(
                ft.Tab(
                    tab_content=ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        content=ft.Text(cat_name, size=16, weight=ft.FontWeight.BOLD)
                    ),
                    content=tab_content
                )
            )

        # Header Row aligned within the centered container bounds
        header = ft.Container(
            padding=ft.padding.only(top=15, bottom=10),
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_size=28,
                        icon_color=ft.Colors.RED_900,
                        on_click=on_back,
                        tooltip="Back to Home"
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Did You Know?", 
                            size=28, 
                            weight=ft.FontWeight.BOLD, 
                            color=ft.Colors.RED_900
                        ),
                        expand=True,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(width=48)  # Spacer balancing arrow button width for precise title centering
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        super().__init__(
            route="/fun_facts",
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            header,
                            tabs
                        ],
                        expand=True,
                        spacing=10
                    ),
                    expand=1,
                    width=850,
                    padding=ft.padding.symmetric(horizontal=15),
                    alignment=ft.alignment.top_center
                )
            ]
        )