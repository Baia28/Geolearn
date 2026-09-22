"""Shared form controls and validation presentation."""

from collections.abc import Callable

import flet as ft

from gui.core.theme import TOKENS, DesignTokens


def text_input(
    *,
    label: str,
    value: str | None = None,
    hint_text: str | None = None,
    helper_text: str | None = None,
    error_text: str | None = None,
    width: int | None = None,
    required: bool = False,
    disabled: bool = False,
    text_align: ft.TextAlign = ft.TextAlign.LEFT,
    text_size: int | None = None,
    suffix: ft.Control | None = None,
    on_change: Callable | None = None,
    on_submit: Callable | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.TextField:
    display_label = f"{label} *" if required else label
    return ft.TextField(
        value=value,
        label=display_label,
        hint_text=hint_text,
        helper_text=helper_text,
        error_text=error_text,
        width=width,
        disabled=disabled,
        text_align=text_align,
        text_size=text_size,
        suffix=suffix,
        on_change=on_change,
        on_submit=on_submit,
        filled=True,
        fill_color=tokens.colors.surface,
        hover_color=tokens.colors.hover,
        color=tokens.colors.text_primary,
        border_color=tokens.colors.border_strong,
        focused_border_color=tokens.colors.primary,
        focused_border_width=2,
        border_radius=tokens.radius.md,
        cursor_color=tokens.colors.primary,
        error_style=ft.TextStyle(color=tokens.colors.error, size=tokens.typography.label),
        helper_style=ft.TextStyle(color=tokens.colors.text_secondary, size=tokens.typography.label),
        hint_style=ft.TextStyle(color=tokens.colors.text_muted),
    )


def search_input(
    on_change: Callable,
    *,
    hint_text: str = "Search",
    width: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.TextField:
    return text_input(
        label="Search",
        hint_text=hint_text,
        width=width,
        on_change=on_change,
        suffix=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=tokens.colors.text_secondary),
        tokens=tokens,
    )
