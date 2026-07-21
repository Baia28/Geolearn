import flet as ft

class GeorgianKeyboard(ft.Container):
    def __init__(self, on_key_tap: callable, on_backspace: callable):
        super().__init__()
        self.on_key_tap = on_key_tap
        self.on_backspace = on_backspace
        self.is_shift = False
        
        # Standard Georgian QWERTY Mapping
        # Format: (Latin_lower, Geo_lower, Latin_upper, Geo_upper)
        # If Geo_upper is None, the key doesn't change on Shift.
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
        
        self.padding = 10
        self._build_keyboard()

    def _build_keyboard(self):
        rows = []
        for row_data in self.key_map:
            row_controls = []
            for key_data in row_data:
                latin_lower, geo_lower, latin_upper, geo_upper = key_data
                
                # Determine current display characters based on Shift state
                if self.is_shift and geo_upper:
                    current_geo = geo_upper
                    current_lat = latin_upper
                else:
                    current_geo = geo_lower
                    current_lat = latin_lower

                # Create the custom key
                key_btn = ft.Container(
                    width=42,
                    height=50,
                    bgcolor=ft.Colors.BLUE_GREY_50,
                    border_radius=6,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda e, char=current_geo: self._handle_tap(char, e),
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                content=ft.Text(current_lat, size=9, color=ft.Colors.GREY_500),
                                alignment=ft.alignment.top_left,
                                padding=ft.padding.only(left=3, top=2)
                            ),
                            ft.Container(
                                content=ft.Text(current_geo, size=18, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK87),
                                alignment=ft.alignment.center
                            )
                        ]
                    )
                )
                
                # Dim keys that don't have a shift variant when shift is active
                if self.is_shift and not geo_upper:
                    key_btn.opacity = 0.4
                    key_btn.disabled = True
                    
                row_controls.append(key_btn)
            
            rows.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=4))

        # Add Action Keys (Shift, Space, Backspace)
        shift_color = ft.Colors.BLUE_100 if self.is_shift else ft.Colors.BLUE_GREY_100
        action_row = ft.Row(
            controls=[
                ft.ElevatedButton("⇧ Shift", bgcolor=shift_color, color=ft.Colors.BLACK87, on_click=self._toggle_shift, width=85, height=42),
                ft.ElevatedButton("Space", bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: self._handle_tap(" ", e), expand=True, height=42),
                ft.ElevatedButton("⌫", bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: self.on_backspace(e), width=65, height=42),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4
        )
        rows.append(action_row)

        self.content = ft.Column(controls=rows, spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

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