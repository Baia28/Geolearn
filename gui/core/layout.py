"""Small layout primitives and shared responsive decisions."""

from collections.abc import Sequence

import flet as ft

from gui.core.theme import TOKENS, DesignTokens


def page_shell(
    controls: Sequence[ft.Control],
    *,
    max_width: int | None = None,
    scroll: bool = True,
    spacing: int | None = None,
    padding: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Container:
    """Create a centered, responsive page body with one scroll owner."""
    if max_width is None or max_width >= tokens.dimensions.wide_content_width:
        columns = {"xs": 12, "md": 12, "lg": 11, "xl": 10}
    elif max_width >= tokens.dimensions.content_width:
        columns = {"xs": 12, "md": 11, "lg": 10, "xl": 8}
    else:
        columns = {"xs": 12, "md": 10, "lg": 8, "xl": 6}
    column = ft.Column(
        controls=list(controls),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=spacing if spacing is not None else tokens.spacing.lg,
        scroll=ft.ScrollMode.AUTO if scroll else None,
        expand=True,
    )

    return ft.Container(
        content=ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=column,
                    col=columns,
                    alignment=ft.alignment.top_center,
                )
            ],
            columns=12,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
        padding=padding if padding is not None else tokens.spacing.lg,
        alignment=ft.alignment.top_center,
        expand=True,
    )


def responsive_split(
    primary: ft.Control,
    secondary: ft.Control,
    *,
    primary_columns: int = 8,
    secondary_columns: int = 4,
    tokens: DesignTokens = TOKENS,
) -> ft.ResponsiveRow:
    """Stack on narrow windows and use a shared 12-column split otherwise."""
    return ft.ResponsiveRow(
        controls=[
            ft.Container(content=primary, col={"xs": 12, "md": primary_columns}),
            ft.Container(content=secondary, col={"xs": 12, "md": secondary_columns}),
        ],
        columns=12,
        spacing=tokens.spacing.xl,
        run_spacing=tokens.spacing.xl,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def responsive_grid(
    controls: Sequence[ft.Control],
    *,
    xs: int = 12,
    sm: int = 6,
    md: int = 4,
    lg: int = 3,
    tokens: DesignTokens = TOKENS,
) -> ft.ResponsiveRow:
    return ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=control,
                col={"xs": xs, "sm": sm, "md": md, "lg": lg},
                alignment=ft.alignment.center,
            )
            for control in controls
        ],
        columns=12,
        spacing=tokens.spacing.md,
        run_spacing=tokens.spacing.md,
    )
