import flet as ft

class PassiveReviewView(ft.View):
    def __init__(self, master_sheet: dict, unit_title: str, on_back: callable, play_audio: callable):
        
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            tab_alignment=ft.TabAlignment.CENTER,
            indicator_color=ft.Colors.PURPLE_600,
            label_color=ft.Colors.PURPLE_900,
            tabs=[]
        )

        vocab_list = ft.ListView(expand=1, spacing=15, padding=20)
        phrases_list = ft.ListView(expand=1, spacing=15, padding=20)
        dialogues_list = ft.ListView(expand=1, spacing=15, padding=20)

        for section_label, content in master_sheet.items():
            lesson_header = ft.Text(section_label, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800)
            # --- Vocabulary (Single Words) ---
            if content['vocab']:
                vocab_list.controls.append(lesson_header)
                for item in content['vocab']:
                    audio_btn = ft.IconButton(
                        icon=ft.Icons.VOLUME_UP, 
                        icon_color=ft.Colors.PURPLE_600,
                        on_click=lambda e, src=item['audio']: play_audio(src),
                        visible=bool(item['audio'])
                    )
                    vocab_list.controls.append(
                        ft.Card(
                            elevation=1, surface_tint_color=ft.Colors.WHITE,
                            content=ft.ListTile(
                                title=ft.Text(item['geo'], size=18, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(f"{item['trans']} • {item['eng']}", color=ft.Colors.BLACK54),
                                trailing=audio_btn
                            )
                        )
                    )
            
            # --- Phrases & Pairs ---
            if content['phrases'] or content['pairs']:
                phrases_list.controls.append(ft.Text(section_label, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800))                
                # Render Standalone Phrases
                for item in content['phrases']:
                    audio_btn = ft.IconButton(
                        icon=ft.Icons.VOLUME_UP, 
                        icon_color=ft.Colors.PURPLE_600,
                        on_click=lambda e, src=item['audio']: play_audio(src),
                        visible=bool(item['audio'])
                    )
                    phrases_list.controls.append(
                        ft.Card(
                            elevation=1, surface_tint_color=ft.Colors.WHITE,
                            content=ft.ListTile(
                                title=ft.Text(item['geo'], size=18, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(f"{item['trans']} • {item['eng']}", color=ft.Colors.BLACK54),
                                trailing=audio_btn
                            )
                        )
                    )

                # Render Q&A Pairs
                for pair in content['pairs']:
                    prompt = pair['prompt']
                    resp = pair['correct_response']
                    phrases_list.controls.append(
                        ft.Card(
                            elevation=1, surface_tint_color=ft.Colors.WHITE,
                            content=ft.Container(
                                padding=15,
                                content=ft.Column([
                                    ft.Text(f"Q: {prompt['georgian']} ({prompt['english']})", weight=ft.FontWeight.W_600),
                                    ft.Text(f"A: {resp['georgian']} ({resp['english']})", color=ft.Colors.PURPLE_800)
                                ])
                            )
                        )
                    )
            
            # --- Dialogues ---
            if content['dialogues']:
                dialogues_list.controls.append(ft.Text(section_label, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800))
                for idx, lines in enumerate(content['dialogues']):
                    col = ft.Column(spacing=5)
                    col.controls.append(ft.Text(f"Dialogue {idx + 1}", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_600))
                    for line in lines:
                        speaker_color = ft.Colors.BLUE_700 if line[0] == 'A' else ft.Colors.GREEN_700
                        
                        # Added Audio Button for individual dialogue lines if they exist
                        row_controls = [
                            ft.Text(f"{line[0]}:", weight=ft.FontWeight.BOLD, color=speaker_color),
                            ft.Text(f"{line[1]} ({line[3]})")
                        ]
                        
                        if len(line) > 4 and line[4]:
                            row_controls.append(
                                ft.IconButton(
                                    icon=ft.Icons.VOLUME_UP,
                                    icon_color=ft.Colors.PURPLE_600,
                                    icon_size=16,
                                    on_click=lambda e, src=line[4]: play_audio(src)
                                )
                            )

                        col.controls.append(ft.Row(row_controls))
                        
                    dialogues_list.controls.append(
                        ft.Card(elevation=1, surface_tint_color=ft.Colors.WHITE, content=ft.Container(padding=15, content=col))
                    )

        # Conditionally append tabs based on whether their lists contain controls
        if vocab_list.controls:
            tabs.tabs.append(ft.Tab(text="📖 Vocabulary", content=vocab_list))
        
        if phrases_list.controls:
            tabs.tabs.append(ft.Tab(text="💬 Phrases", content=phrases_list))
            
        if dialogues_list.controls:
            tabs.tabs.append(ft.Tab(text="🎭 Dialogues", content=dialogues_list))

        header = ft.Container(
            padding=ft.padding.only(top=15, bottom=10),
            content=ft.Row(
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back, icon_color=ft.Colors.PURPLE_900),
                    ft.Text(f"Review: {unit_title}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                    ft.Container(width=48)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        super().__init__(
            route="/passive_review",
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Column([header, tabs], expand=True),
                    expand=1, width=850, padding=15
                )
            ]
        )