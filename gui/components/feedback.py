"""Reusable feedback, loading, empty, and completion states."""

from collections.abc import Callable

import flet as ft

from gui.components.buttons import primary_button, secondary_button
from gui.core.theme import TOKENS, DesignTokens


def review_badge(target: dict | None, *, tokens: DesignTokens = TOKENS) -> ft.Control | None:
    if not target or not target.get("is_review_item"):
        return None
    return ft.Text(
        "Review item",
        color=tokens.colors.warning,
        weight=ft.FontWeight.W_600,
        size=tokens.typography.body_sm,
        italic=True,
    )


def feedback_panel(
    *,
    success: bool,
    title: str,
    body: list[ft.Control] | None = None,
    width: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.Container:
    background = tokens.colors.success_container if success else tokens.colors.error_container
    foreground = tokens.colors.on_success_container if success else tokens.colors.on_error_container
    icon = ft.Icons.CHECK_CIRCLE_ROUNDED if success else ft.Icons.CANCEL_ROUNDED
    controls: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Icon(icon, color=foreground, size=tokens.dimensions.icon_md),
                ft.Text(title, size=tokens.typography.title_sm, weight=ft.FontWeight.BOLD, color=foreground),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
        )
    ]
    controls.extend(body or [])
    return ft.Container(
        content=ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=tokens.spacing.xs,
        ),
        bgcolor=background,
        border=ft.border.all(1, foreground),
        border_radius=tokens.radius.lg,
        padding=tokens.spacing.lg,
        width=width,
    )


def message_state(
    title: str,
    message: str,
    *,
    icon=ft.Icons.INFO_OUTLINE_ROUNDED,
    action_label: str | None = None,
    on_action: Callable | None = None,
    error: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.Container:
    color = tokens.colors.error if error else tokens.colors.primary
    controls: list[ft.Control] = [
        ft.Icon(icon, size=48, color=color),
        ft.Text(title, size=tokens.typography.title, weight=ft.FontWeight.BOLD, color=tokens.colors.text_primary),
        ft.Text(message, size=tokens.typography.body, color=tokens.colors.text_secondary, text_align=ft.TextAlign.CENTER),
    ]
    if action_label and on_action:
        controls.append(primary_button(action_label, on_action, tokens=tokens))
    return ft.Container(
        content=ft.Column(controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=tokens.spacing.md),
        alignment=ft.alignment.center,
        padding=tokens.spacing.xxl,
        expand=True,
    )


def loading_state(message: str = "Loading…", *, tokens: DesignTokens = TOKENS) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.ProgressRing(color=tokens.colors.primary),
                ft.Text(message, color=tokens.colors.text_secondary),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.md,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )


def completion_state(
    *,
    title: str,
    subtitle: str | None = None,
    primary_label: str,
    on_primary: Callable,
    secondary_label: str | None = None,
    on_secondary: Callable | None = None,
    score: str | None = None,
    body: list[ft.Control] | None = None,
    primary_icon=None,
    tokens: DesignTokens = TOKENS,
) -> ft.Container:
    controls: list[ft.Control] = [
        ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, size=80, color=tokens.colors.sunny),
        ft.Text(title, size=tokens.typography.page_title, weight=ft.FontWeight.BOLD, color=tokens.colors.text_primary, text_align=ft.TextAlign.CENTER),
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=tokens.typography.body_lg, color=tokens.colors.text_secondary, text_align=ft.TextAlign.CENTER))
    if score:
        controls.append(ft.Text(score, size=48, color=tokens.colors.success, weight=ft.FontWeight.BOLD))
    controls.extend(body or [])

    actions = [
        primary_button(
            primary_label,
            on_primary,
            icon=primary_icon,
            width=220,
            tokens=tokens,
        )
    ]
    if secondary_label and on_secondary:
        actions.append(secondary_button(secondary_label, on_secondary, width=220, tokens=tokens))
    controls.append(ft.Row(actions, alignment=ft.MainAxisAlignment.CENTER, spacing=tokens.spacing.lg, wrap=True))

    return ft.Container(
        content=ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
        ),
        alignment=ft.alignment.center,
        padding=tokens.spacing.xxl,
        expand=True,
    )
