"""Large keyboard-practice view built from the shared Georgian keyboard."""

import flet as ft

from gui.audio_utils import play_audio_file
from gui.keyboard import GeorgianKeyboard


class AlphabetKeyboardView(ft.Column):
    """Interactive practice page with a large keyboard, real-time sound, typing field, and shift key tutorials."""

    def __init__(self, db, on_back_to_menu):
        super().__init__()
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Audio lookup table
        letters = self.db.get_alphabet_letters()
        self.audio_map = {item.get("georgian"): item.get("letter_audio") for item in letters if item.get("georgian")}

        self._build_ui()

    def _build_ui(self):
        self.controls.clear()

        # Header
        header = ft.Container(
            width=650,
            content=ft.Row(
                controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                    ft.Text("Georgian Keyboard Practice", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Container(width=48)  # Equal spacer width matching back icon button size
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        # Output Typing Field
        self.display_field = ft.TextField(
            value="",
            hint_text="Type or tap a key to write and hear Georgian...",
            width=580,
            text_size=24,
            text_align=ft.TextAlign.CENTER,
            on_change=self._translate_physical_input,
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR_ROUNDED,
                tooltip="Clear text",
                on_click=self._clear_text
            )
        )

        # Instructional Info Card
        instructions_card = ft.Container(
            padding=16,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=12,
            width=680,
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_ROUNDED, color=ft.Colors.BLUE_700, size=20),
                        ft.Text("How the Georgian Layout Works", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
                    ], spacing=6),
                    ft.Text(
                        "• Standard keys map phonetically to Latin counterparts (e.g. A ➔ ა, B ➔ ბ, D ➔ დ).\n"
                        "• Tap Shift (or hold uppercase) to reveal 7 special Georgian letters: "
                        "W ➔ ჭ, R ➔ ღ, T ➔ თ, S ➔ შ, J ➔ ჟ, Z ➔ ძ, C ➔ ჩ.\n"
                        "• Modern Georgian has no uppercase/lowercase distinction—Shift is used purely to fit all 33 letters on a standard layout!",
                        size=13,
                        color=ft.Colors.GREY_800
                    )
                ],
                spacing=6
            )
        )

        # Big Interactive Keyboard
        self.keyboard = GeorgianKeyboard(
            on_key_tap=self._handle_key_tap,
            on_backspace=self._handle_backspace,
            size="large",
        )

        game_layout = ft.Column(
            controls=[
                header,
                ft.Container(height=5),
                instructions_card,
                ft.Container(height=10),
                self.display_field,
                ft.Container(height=10),
                self.keyboard,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        main_wrapper = ft.Container(
            content=game_layout,
            padding=ft.padding.only(left=30, right=30, top=15, bottom=20),
            alignment=ft.alignment.top_center,
            expand=True
        )

        self.controls = [main_wrapper]

    def _handle_key_tap(self, char: str):
        if char != " ":
            self.display_field.value = (self.display_field.value or "") + char
            self._last_display_value = self.display_field.value
            self.display_field.update()

            # Play letter audio if available
            audio_path = self.audio_map.get(char)
            if audio_path and self.page:
                play_audio_file(self.page, audio_path)

    def _handle_backspace(self):
        current = self.display_field.value or ""
        if len(current) > 0:
            self.display_field.value = current[:-1]
            self._last_display_value = self.display_field.value
            self.display_field.update()

    def _clear_text(self, e=None):
        self.display_field.value = ""
        self._last_display_value = ""
        self.display_field.update()

    def _translate_physical_input(self, event):
        """Convert a physical Latin keyboard's input to the Georgian layout."""
        typed_value = event.control.value or ""
        georgian_value = GeorgianKeyboard.translate_latin_text(typed_value)
        if georgian_value != typed_value:
            event.control.value = georgian_value
            event.control.update()

        previous_value = getattr(self, "_last_display_value", "")
        if len(georgian_value) == len(previous_value) + 1:
            audio_path = self.audio_map.get(georgian_value[-1])
            if audio_path and self.page:
                play_audio_file(self.page, audio_path)
        self._last_display_value = georgian_value
