"""Card primitives shared by curriculum, tools, and reference screens."""

from collections.abc import Callable

import flet as ft

from gui.core.theme import TOKENS, DesignTokens


def content_card(
    content: ft.Control,
    *,
    on_click: Callable | None = None,
    padding: ft.PaddingValue = None,
    bgcolor: str | None = None,
    border_color: str | None = None,
    elevation: int | None = None,
    width: int | None = None,
    height: int | None = None,
    tooltip: str | None = None,
    alignment: ft.Alignment | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Card:
    """A surface card with one shared hover/ripple implementation."""
    base_color = bgcolor or tokens.colors.surface
    container = ft.Container(
        content=content,
        padding=padding if padding is not None else tokens.spacing.lg,
        bgcolor=base_color,
        border=ft.border.all(1, border_color or tokens.colors.border),
        border_radius=tokens.radius.lg,
        width=width,
        height=height,
        alignment=alignment,
        ink=on_click is not None,
        ink_color=tokens.colors.pressed,
        on_click=on_click,
        tooltip=tooltip,
    )

    if on_click is not None:
        def handle_hover(event) -> None:
            event.control.bgcolor = (
                tokens.colors.elevated_surface if event.data == "true" else base_color
            )
            event.control.update()

        container.on_hover = handle_hover

    return ft.Card(
        content=container,
        elevation=elevation if elevation is not None else tokens.elevation.card,
        color=base_color,
        surface_tint_color=tokens.colors.transparent,
        shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
    )


def action_card(
    title: str,
    description: str,
    icon,
    on_click: Callable | None,
    *,
    icon_color: str | None = None,
    icon_foreground: str | None = None,
    compact: bool = False,
    disabled: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.Card:
    accent = tokens.colors.text_muted if disabled else (icon_color or tokens.colors.primary)
    foreground = (
        tokens.colors.disabled_text
        if disabled
        else (icon_foreground or tokens.colors.on_primary)
    )
    icon_size = tokens.dimensions.icon_md if compact else tokens.dimensions.icon_lg
    icon_box_size = tokens.dimensions.touch_target if compact else 56
    return content_card(
        ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, size=icon_size, color=foreground),
                    bgcolor=accent,
                    width=icon_box_size,
                    height=icon_box_size,
                    border_radius=tokens.radius.md,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            title,
                            size=tokens.typography.body_lg if compact else tokens.typography.title_sm,
                            weight=ft.FontWeight.BOLD,
                            color=(
                                tokens.colors.text_muted
                                if disabled
                                else tokens.colors.text_primary
                            ),
                        ),
                        ft.Text(
                            description,
                            size=tokens.typography.label if compact else tokens.typography.body_sm,
                            color=tokens.colors.text_secondary,
                        ),
                    ],
                    spacing=tokens.spacing.xs,
                    expand=True,
                ),
                ft.Icon(
                    ft.Icons.LOCK_ROUNDED if disabled else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                    color=tokens.colors.text_muted,
                ),
            ],
            spacing=tokens.spacing.lg,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=None if disabled else on_click,
        bgcolor=tokens.colors.subtle_surface if disabled else None,
        padding=tokens.spacing.lg if compact else tokens.spacing.xl,
        elevation=tokens.elevation.raised,
        tooltip=title,
        tokens=tokens,
    )


def progress_card(
    *,
    eyebrow: str,
    title: str,
    progress: float,
    progress_label: str,
    on_click: Callable,
    tokens: DesignTokens = TOKENS,
) -> ft.Card:
    return content_card(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            eyebrow.upper(),
                            size=tokens.typography.caption,
                            weight=ft.FontWeight.BOLD,
                            color=tokens.colors.primary,
                        ),
                        ft.Text(
                            progress_label,
                            size=tokens.typography.caption,
                            color=tokens.colors.text_secondary,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    title,
                    size=tokens.typography.body_lg,
                    weight=ft.FontWeight.BOLD,
                    color=tokens.colors.text_primary,
                ),
                ft.Container(height=tokens.spacing.xs),
                ft.ProgressBar(
                    value=progress,
                    height=6,
                    color=tokens.colors.success,
                    bgcolor=tokens.colors.subtle_surface,
                    border_radius=tokens.radius.sm,
                ),
            ],
            spacing=tokens.spacing.xs,
        ),
        on_click=on_click,
        tokens=tokens,
    )


def tonal_card(
    content: ft.Control,
    *,
    tone: str = "primary",
    width: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Card:
    backgrounds = {
        "primary": tokens.colors.primary_container,
        "secondary": tokens.colors.secondary_container,
        "success": tokens.colors.success_container,
        "error": tokens.colors.error_container,
    }
    return content_card(
        content,
        bgcolor=backgrounds.get(tone, tokens.colors.subtle_surface),
        border_color=tokens.colors.border,
        width=width,
        elevation=tokens.elevation.flat,
        tokens=tokens,
    )
