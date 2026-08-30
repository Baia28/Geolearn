import flet as ft
from gui.audio_utils import play_audio_file

class BigGeorgianKeyboard(ft.Container):
    """Enlarged interactive keyboard with audio feedback on key tap."""
    
    def __init__(self, on_key_tap: callable, on_backspace: callable):
        super().__init__()
        self.on_key_tap = on_key_tap
        self.on_backspace = on_backspace
        self.is_shift = False

        self.padding = 10
        self.alignment = ft.alignment.center
        
        # Standard Georgian QWERTY Mapping: (Latin_lower, Geo_lower, Latin_upper, Geo_upper)
        self.key_map = [
            # Top Row
            [('q', 'ქ', None, None), ('w', 'წ', 'W', 'ჭ'), ('e', 'ე', None, None), 
             ('r', 'რ', 'R', 'ღ'), ('t', 'ტ', 'T', 'თ'), ('y', 'ყ', None, None), 
             ('u', 'უ', None, None), ('i', 'ი', None, None), ('o', 'ო', None, None), 
             ('p', 'პ', None, None)],
            
            # Home Row
            [('a', 'ა', None, None), ('s', 'ს', 'S', 'შ'), ('d', 'დ', None, None), 
             ('f', 'ფ', None, None), ('g', 'გ', None, None), ('h', 'ჰ', None, None), 
             ('j', 'ჯ', 'J', 'ჟ'), ('k', 'კ', None, None), ('l', 'ლ', None, None)],
            
            # Bottom Row
            [('z', 'ზ', 'Z', 'ძ'), ('x', 'ხ', None, None), ('c', 'ც', 'C', 'ჩ'), 
             ('v', 'ვ', None, None), ('b', 'ბ', None, None), ('n', 'ნ', None, None), 
             ('m', 'მ', None, None)]
        ]
        
        self._build_keyboard()

    def _build_keyboard(self):
        rows = []
        for row_data in self.key_map:
            row_controls = []
            for key_data in row_data:
                latin_lower, geo_lower, latin_upper, geo_upper = key_data
                
                if self.is_shift and geo_upper:
                    current_geo = geo_upper
                    current_lat = latin_upper
                    is_shifted_key = True
                else:
                    current_geo = geo_lower
                    current_lat = latin_lower
                    is_shifted_key = False

                # Highlight shifted keys when shift is active
                key_bg = ft.Colors.AMBER_100 if (self.is_shift and geo_upper) else ft.Colors.BLUE_GREY_50

                key_btn = ft.Container(
                    width=58,   # Sized up from 40
                    height=68,  # Sized up from 50
                    bgcolor=key_bg,
                    border_radius=8,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda e, char=current_geo: self._handle_tap(char, e),
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                content=ft.Text(current_lat, size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.BOLD),
                                alignment=ft.alignment.top_left,
                                padding=ft.padding.only(left=5, top=4)
                            ),
                            ft.Container(
                                content=ft.Text(current_geo, size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                alignment=ft.alignment.center
                            )
                        ]
                    )
                )
                
                if self.is_shift and not geo_upper:
                    key_btn.opacity = 0.35
                    key_btn.disabled = True
                    
                row_controls.append(key_btn)
            
            rows.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=6))

        # Enlarged Action Row Buttons
        shift_bg = ft.Colors.AMBER_300 if self.is_shift else ft.Colors.BLUE_200
        
        shift_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, size=18, color=ft.Colors.BLACK87),
                ft.Text("SHIFT", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=3),
            width=110,
            height=54,
            bgcolor=shift_bg,
            border_radius=8,
            alignment=ft.alignment.center,
            ink=True,
            on_click=self._toggle_shift
        )

        space_btn = ft.Container(
            content=ft.Text("SPACE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            width=280,
            height=54,
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=8,
            alignment=ft.alignment.center,
            ink=True,
            on_click=lambda e: self._handle_tap(" ", e)
        )

        backspace_btn = ft.Container(
            content=ft.Icon(ft.Icons.BACKSPACE_OUTLINED, size=22, color=ft.Colors.RED_700),
            width=90,
            height=54,
            bgcolor=ft.Colors.RED_50,
            border_radius=8,
            alignment=ft.alignment.center,
            ink=True,
            on_click=self._handle_backspace
        )

        action_row = ft.Row(
            controls=[shift_btn, space_btn, backspace_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        )
        rows.append(action_row)

        self.content = ft.Column(controls=rows, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _toggle_shift(self, e):
        self.is_shift = not self.is_shift
        self._build_keyboard()
        self.update()

    def _handle_tap(self, char, e):
        self.on_key_tap(char)
        if self.is_shift:
            self.is_shift = False
            self._build_keyboard()
        e.page.update()

    def _handle_backspace(self, e):
        try:
            self.on_backspace()
        except TypeError:
            self.on_backspace(e)
        e.page.update()


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
        header = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, icon_size=28, on_click=lambda e: self.on_back_to_menu()),
                ft.Text("Georgian Keyboard Practice", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Output Typing Field
        self.display_field = ft.TextField(
            value="",
            hint_text="Tap any key below to type and hear its sound...",
            read_only=True,
            width=580,
            text_size=24,
            text_align=ft.TextAlign.CENTER,
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
        self.keyboard = BigGeorgianKeyboard(
            on_key_tap=self._handle_key_tap,
            on_backspace=self._handle_backspace
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
            self.display_field.update()

            # Play letter audio if available
            audio_path = self.audio_map.get(char)
            if audio_path and self.page:
                play_audio_file(self.page, audio_path)

    def _handle_backspace(self):
        current = self.display_field.value or ""
        if len(current) > 0:
            self.display_field.value = current[:-1]
            self.display_field.update()

    def _clear_text(self, e=None):
        self.display_field.value = ""
        self.display_field.update()