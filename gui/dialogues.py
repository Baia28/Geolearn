import flet as ft

class ChatBubble(ft.Container):
    """A purely visual widget representing one line of dialogue."""
    def __init__(self, text: str, is_speaker_a: bool):
        super().__init__()
        self.padding = 15
        self.border_radius = ft.border_radius.only(
            top_left=15, top_right=15,
            bottom_left=0 if is_speaker_a else 15,
            bottom_right=15 if is_speaker_a else 0
        )
        self.bgcolor = ft.Colors.BLUE_GREY_100 if is_speaker_a else ft.Colors.GREEN_100
        self.content = ft.Text(text, color=ft.Colors.BLACK87)
        self.alignment = ft.alignment.center_left if is_speaker_a else ft.alignment.center_right

class DialoguePassiveView(ft.Column):
    def __init__(self, dialogue_lines: list, on_continue: callable):
        super().__init__()
        self.scroll = ft.ScrollMode.AUTO
        self.controls = []
        
        for idx, line in enumerate(dialogue_lines):
            # Assuming line is a tuple: (speaker, geo, trans, eng)
            is_speaker_a = (line[0] == "A") 
            bubble = ChatBubble(text=line[1], is_speaker_a=is_speaker_a)
            # Wrap in row to push it left or right
            row = ft.Row(
                [bubble], 
                alignment=ft.MainAxisAlignment.START if is_speaker_a else ft.MainAxisAlignment.END
            )
            self.controls.append(row)
            
        self.controls.append(ft.ElevatedButton("Continue", on_click=lambda e: on_continue(True)))