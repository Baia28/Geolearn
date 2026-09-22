"""Shared page headers, section labels, and task instructions."""

from collections.abc import Callable, Sequence

import flet as ft

from gui.components.buttons import back_button, text_button
from gui.core.theme import TOKENS, DesignTokens


def section_label(text: str, *, tokens: DesignTokens = TOKENS) -> ft.Text:
    return ft.Text(
        text.upper(),
        size=tokens.typography.label,
        weight=ft.FontWeight.BOLD,
        color=tokens.colors.text_secondary,
    )


def instruction_banner(icon, text: str, *, tokens: DesignTokens = TOKENS) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Icon(icon, size=tokens.dimensions.icon_sm, color=tokens.colors.text_muted),
            ft.Text(
                text,
                size=tokens.typography.body,
                color=tokens.colors.text_secondary,
                weight=ft.FontWeight.W_500,
                italic=True,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=tokens.spacing.sm,
        wrap=True,
    )


def page_header(
    title: str,
    *,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    on_back: Callable | None = None,
    back_label: str = "Back",
    trailing: ft.Control | None = None,
    max_width: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Container:
    leading = back_button(on_back, label=back_label, compact=True, tokens=tokens) if on_back else None
    end = trailing
    title_controls: list[ft.Control] = []
    if eyebrow:
        title_controls.append(
            ft.Text(
                eyebrow.upper(),
                size=tokens.typography.label,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.primary,
                text_align=ft.TextAlign.CENTER,
            )
        )
    title_controls.append(
        ft.Text(
            title,
            size=tokens.typography.page_title if not subtitle else tokens.typography.title,
            weight=ft.FontWeight.BOLD,
            color=tokens.colors.text_primary,
            text_align=ft.TextAlign.CENTER,
        )
    )
    if subtitle:
        title_controls.append(
            ft.Text(
                subtitle,
                size=tokens.typography.label,
                color=tokens.colors.text_secondary,
                text_align=ft.TextAlign.CENTER,
            )
        )

    return ft.Container(
        padding=ft.padding.symmetric(vertical=tokens.spacing.sm),
        content=ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=leading,
                    col={"xs": 3, "sm": 2},
                    alignment=ft.alignment.top_left,
                ),
                ft.Container(
                    content=ft.Column(
                        title_controls,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=tokens.spacing.xxs,
                    ),
                    col={"xs": 6, "sm": 8},
                    alignment=ft.alignment.top_center,
                ),
                ft.Container(
                    content=end,
                    col={"xs": 3, "sm": 2},
                    alignment=ft.alignment.top_right,
                ),
            ],
            columns=12,
            spacing=0,
            run_spacing=tokens.spacing.xs,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    )


def navigation_bar(
    *,
    on_back: Callable,
    back_label: str,
    on_home: Callable | None = None,
    actions: Sequence[ft.Control] | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Row:
    end_controls = list(actions or [])
    if on_home:
        end_controls.insert(0, text_button("Home", on_home, icon=ft.Icons.HOME_ROUNDED, tokens=tokens))
    return ft.Row(
        controls=[
            back_button(on_back, label=back_label, tokens=tokens),
            ft.Row(end_controls, spacing=tokens.spacing.xs, tight=True),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
