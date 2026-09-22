"""Reusable Georgian keyboard control and Latin-to-Georgian input conversion."""

from collections.abc import Callable

import flet as ft

from gui.core.theme import TOKENS, DesignTokens


class GeorgianKeyboard(ft.Container):
    """On-screen Georgian keyboard with compact and practice-sized layouts."""

    KEY_MAP = (
        (
            ("q", "ქ", None, None), ("w", "წ", "W", "ჭ"),
            ("e", "ე", None, None), ("r", "რ", "R", "ღ"),
            ("t", "ტ", "T", "თ"), ("y", "ყ", None, None),
            ("u", "უ", None, None), ("i", "ი", None, None),
            ("o", "ო", None, None), ("p", "პ", None, None),
        ),
        (
            ("a", "ა", None, None), ("s", "ს", "S", "შ"),
            ("d", "დ", None, None), ("f", "ფ", None, None),
            ("g", "გ", None, None), ("h", "ჰ", None, None),
            ("j", "ჯ", "J", "ჟ"), ("k", "კ", None, None),
            ("l", "ლ", None, None),
        ),
        (
            ("z", "ზ", "Z", "ძ"), ("x", "ხ", None, None),
            ("c", "ც", "C", "ჩ"), ("v", "ვ", None, None),
            ("b", "ბ", None, None), ("n", "ნ", None, None),
            ("m", "მ", None, None),
        ),
    )

    _STYLES = {
        "compact": {
            "key_width": 40, "key_height": 50,
            "key_spacing": 4, "latin_size": 9, "geo_size": 18,
            "action_height": 44, "shift_width": 80, "space_width": 200,
            "backspace_width": 65, "action_spacing": 6,
        },
        "large": {
            "key_width": 58, "key_height": 68,
            "key_spacing": 6, "latin_size": 14, "geo_size": 26,
            "action_height": 54, "shift_width": 110, "space_width": 280,
            "backspace_width": 90, "action_spacing": 8,
        },
    }

    _LATIN_TO_GEORGIAN = {
        latin: georgian
        for row in KEY_MAP
        for lower_latin, lower_georgian, _, shifted_georgian in row
        for latin, georgian in (
            (lower_latin, lower_georgian),
            (lower_latin.upper(), shifted_georgian or lower_georgian),
        )
    }

    def __init__(
        self,
        on_key_tap: Callable[[str], None],
        on_backspace: Callable,
        size: str = "compact",
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__()
        if size not in self._STYLES:
            raise ValueError(f"Unknown keyboard size: {size}")

        self.on_key_tap = on_key_tap
        self.on_backspace = on_backspace
        self.tokens = tokens
        self.style = self._STYLES[size]
        self.is_large = size == "large"
        self.is_shift = False
        self.padding = tokens.spacing.md
        self.alignment = ft.alignment.center
        self._build_keyboard()

    @classmethod
    def translate_latin_text(cls, text: str) -> str:
        """Map physical Latin-key input to the matching Georgian keyboard layout."""
        return "".join(cls._LATIN_TO_GEORGIAN.get(character, character) for character in text)

    def _build_keyboard(self):
        colors = self.tokens.colors
        rows = []
        for row_data in self.KEY_MAP:
            row_controls = []
            for latin_lower, geo_lower, latin_upper, geo_upper in row_data:
                is_shifted_key = self.is_shift and geo_upper is not None
                current_geo = geo_upper if is_shifted_key else geo_lower
                current_lat = latin_upper if is_shifted_key else latin_lower
                key_bg = colors.secondary_container if self.is_large and is_shifted_key else colors.surface

                key_btn = ft.Container(
                    width=self.style["key_width"],
                    height=self.style["key_height"],
                    bgcolor=key_bg,
                    border_radius=self.tokens.radius.md if self.is_large else self.tokens.radius.sm,
                    border=ft.border.all(1, colors.border),
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda event, char=current_geo: self._handle_tap(char, event),
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                content=ft.Text(current_lat, size=self.style["latin_size"], color=colors.text_secondary, weight=ft.FontWeight.BOLD if self.is_large else None),
                                alignment=ft.alignment.top_left,
                                padding=ft.padding.only(left=5 if self.is_large else 3, top=4 if self.is_large else 2),
                            ),
                            ft.Container(
                                content=ft.Text(current_geo, size=self.style["geo_size"], weight=ft.FontWeight.BOLD if self.is_large else ft.FontWeight.W_500, color=colors.text_primary),
                                alignment=ft.alignment.center,
                            ),
                        ]
                    ),
                )

                if self.is_shift and geo_upper is None:
                    key_btn.opacity = 0.35 if self.is_large else 0.4
                    key_btn.disabled = True
                row_controls.append(key_btn)

            rows.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=self.style["key_spacing"]))

        shift_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, size=18 if self.is_large else 14, color=colors.text_primary),
                    ft.Text("SHIFT" if self.is_large else "Shift", size=13 if self.is_large else 12, weight=ft.FontWeight.BOLD, color=colors.text_primary),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=3 if self.is_large else 2,
            ),
            width=self.style["shift_width"],
            height=self.style["action_height"],
            bgcolor=colors.primary_container if self.is_shift else colors.subtle_surface,
            border_radius=self.tokens.radius.md if self.is_large else self.tokens.radius.sm,
            border=ft.border.all(1, colors.border),
            alignment=ft.alignment.center,
            ink=True,
            on_click=self._toggle_shift,
        )
        space_btn = ft.Container(
            content=ft.Text("SPACE", size=12 if self.is_large else 11, weight=ft.FontWeight.BOLD, color=colors.text_secondary),
            width=self.style["space_width"], height=self.style["action_height"],
            bgcolor=colors.subtle_surface, border_radius=self.tokens.radius.md if self.is_large else self.tokens.radius.sm,
            border=ft.border.all(1, colors.border),
            alignment=ft.alignment.center, ink=True,
            on_click=lambda event: self._handle_tap(" ", event),
        )
        backspace_btn = ft.Container(
            content=ft.Icon(ft.Icons.BACKSPACE_OUTLINED, size=22 if self.is_large else 18, color=colors.error),
            width=self.style["backspace_width"], height=self.style["action_height"],
            bgcolor=colors.error_container, border_radius=self.tokens.radius.md if self.is_large else self.tokens.radius.sm,
            border=ft.border.all(1, colors.border),
            alignment=ft.alignment.center, ink=True, on_click=self._handle_backspace,
        )
        rows.append(ft.Row(controls=[shift_btn, space_btn, backspace_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=self.style["action_spacing"]))
        self.content = ft.Column(controls=rows, spacing=self.style["key_spacing"], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _toggle_shift(self, event):
        self.is_shift = not self.is_shift
        self._build_keyboard()
        self.update()

    def _handle_tap(self, char, event):
        self.on_key_tap(char)
        if self.is_shift:
            self.is_shift = False
            self._build_keyboard()
        event.page.update()

    def _handle_backspace(self, event):
        try:
            self.on_backspace()
        except TypeError:
            self.on_backspace(event)
        event.page.update()
