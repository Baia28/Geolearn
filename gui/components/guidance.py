"""Small, accessible help dialogs for page-level guidance."""

from collections.abc import Sequence

import flet as ft

from gui.components.buttons import icon_button
from gui.core.theme import TOKENS, DesignTokens


def _guidance_item(
    number: int,
    heading: str,
    body: str,
    *,
    tokens: DesignTokens,
) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Container(
                content=ft.Text(
                    str(number),
                    size=tokens.typography.label,
                    weight=ft.FontWeight.BOLD,
                    color=tokens.colors.on_primary_container,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=28,
                height=28,
                border_radius=tokens.radius.pill,
                bgcolor=tokens.colors.primary_container,
                alignment=ft.alignment.center,
            ),
            ft.Column(
                controls=[
                    ft.Text(
                        heading,
                        size=tokens.typography.body_lg,
                        weight=ft.FontWeight.BOLD,
                        color=tokens.colors.text_primary,
                    ),
                    ft.Text(
                        body,
                        size=tokens.typography.body,
                        color=tokens.colors.text_secondary,
                    ),
                ],
                spacing=tokens.spacing.xxs,
                expand=True,
            ),
        ],
        spacing=tokens.spacing.md,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def guidance_button(
    title: str,
    introduction: str,
    items: Sequence[tuple[str, str]],
    *,
    tooltip: str = "How to use this page",
    tokens: DesignTokens = TOKENS,
) -> ft.IconButton:
    """Return a help icon that opens structured instructions in a dialog."""
    dialog = ft.AlertDialog(
        modal=True,
        icon=ft.Icon(
            ft.Icons.INFO_OUTLINE_ROUNDED,
            color=tokens.colors.primary,
            size=tokens.dimensions.icon_lg,
        ),
        title=ft.Text(
            title,
            size=tokens.typography.title,
            weight=ft.FontWeight.BOLD,
            color=tokens.colors.text_primary,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        introduction,
                        size=tokens.typography.body,
                        color=tokens.colors.text_secondary,
                    ),
                    ft.Divider(height=tokens.spacing.lg, color=tokens.colors.border),
                    *[
                        _guidance_item(index, heading, body, tokens=tokens)
                        for index, (heading, body) in enumerate(items, start=1)
                    ],
                ],
                spacing=tokens.spacing.lg,
                tight=True,
            ),
            width=520,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=tokens.radius.lg),
        scrollable=True,
    )

    def show_dialog(event) -> None:
        page = event.page

        def close_dialog(_event) -> None:
            page.close(dialog)

        dialog.actions = [
            ft.TextButton(
                "Got it",
                icon=ft.Icons.CHECK_ROUNDED,
                on_click=close_dialog,
                style=ft.ButtonStyle(
                    color=tokens.colors.primary,
                    shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
                ),
            )
        ]
        page.open(dialog)

    return icon_button(
        ft.Icons.HELP_OUTLINE_ROUNDED,
        show_dialog,
        tooltip=tooltip,
        tokens=tokens,
    )
