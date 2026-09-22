"""Consistent button primitives with shared interaction states."""

from collections.abc import Callable
from typing import Any, Literal

import flet as ft

from gui.core.theme import TOKENS, DesignTokens, ThemeController


def _state_values(default: Any, hover: Any, pressed: Any, disabled: Any) -> dict:
    return {
        ft.ControlState.DEFAULT: default,
        ft.ControlState.HOVERED: hover,
        ft.ControlState.FOCUSED: hover,
        ft.ControlState.PRESSED: pressed,
        ft.ControlState.DISABLED: disabled,
    }


def _loading_button_content(tokens: DesignTokens) -> ft.Control:
    return ft.Row(
        controls=[
            ft.ProgressRing(width=18, height=18, stroke_width=2, color=tokens.colors.on_primary),
            ft.Text("Please wait…", weight=ft.FontWeight.W_600),
        ],
        tight=True,
        spacing=tokens.spacing.sm,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def primary_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    width: int | None = None,
    height: int | None = None,
    tooltip: str | None = None,
    disabled: bool = False,
    loading: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.ElevatedButton:
    colors = tokens.colors
    style = ft.ButtonStyle(
        color=_state_values(colors.on_primary, colors.on_primary, colors.on_primary, colors.disabled_text),
        bgcolor=_state_values(colors.primary, colors.primary, colors.primary, colors.disabled),
        overlay_color=_state_values(
            colors.transparent,
            ft.Colors.with_opacity(0.14, colors.on_primary),
            ft.Colors.with_opacity(0.24, colors.on_primary),
            colors.transparent,
        ),
        elevation=_state_values(tokens.elevation.card, tokens.elevation.raised, tokens.elevation.flat, tokens.elevation.flat),
        shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
        padding=ft.padding.symmetric(horizontal=tokens.spacing.lg, vertical=tokens.spacing.sm),
        text_style=ft.TextStyle(weight=ft.FontWeight.W_600),
        mouse_cursor={
            ft.ControlState.DEFAULT: ft.MouseCursor.CLICK,
            ft.ControlState.DISABLED: ft.MouseCursor.BASIC,
        },
        animation_duration=tokens.motion.fast,
    )
    common = {
        "on_click": None if loading else on_click,
        "width": width,
        "height": height or tokens.dimensions.button_height,
        "tooltip": tooltip,
        "disabled": disabled or loading,
        "style": style,
    }
    if loading:
        return ft.ElevatedButton(content=_loading_button_content(tokens), **common)

    # Flet 0.25 requires ``icon`` to be paired with the native ``text``
    # property. Supplying an icon beside custom content renders an ErrorWidget.
    return ft.ElevatedButton(text=label, icon=icon, **common)


def exercise_action_button(
    action: Literal["check_answer", "continue"],
    on_click: Callable | None,
    *,
    disabled: bool = False,
    loading: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.ElevatedButton:
    """Primary exercise action with one shared label, icon, and size contract."""
    presets = {
        "check_answer": ("Check answer", None),
        "continue": ("Continue", ft.Icons.ARROW_FORWARD_ROUNDED),
    }
    label, icon = presets[action]
    return primary_button(
        label,
        on_click,
        icon=icon,
        width=tokens.dimensions.form_width,
        tooltip=label,
        disabled=disabled,
        loading=loading,
        tokens=tokens,
    )


def secondary_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    width: int | None = None,
    height: int | None = None,
    tooltip: str | None = None,
    disabled: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.OutlinedButton:
    colors = tokens.colors
    return ft.OutlinedButton(
        text=label,
        icon=icon,
        on_click=on_click,
        width=width,
        height=height or tokens.dimensions.button_height,
        tooltip=tooltip,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=_state_values(colors.primary, colors.primary, colors.primary, colors.disabled_text),
            overlay_color=_state_values(colors.transparent, colors.hover, colors.pressed, colors.transparent),
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, colors.border_strong),
                ft.ControlState.FOCUSED: ft.BorderSide(2, colors.primary),
                ft.ControlState.DISABLED: ft.BorderSide(1, colors.disabled),
            },
            shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
            padding=ft.padding.symmetric(horizontal=tokens.spacing.lg, vertical=tokens.spacing.sm),
            mouse_cursor={
                ft.ControlState.DEFAULT: ft.MouseCursor.CLICK,
                ft.ControlState.DISABLED: ft.MouseCursor.BASIC,
            },
            animation_duration=tokens.motion.fast,
        ),
    )


def destructive_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    width: int | None = None,
    disabled: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.ElevatedButton:
    colors = tokens.colors
    return ft.ElevatedButton(
        text=label,
        icon=icon,
        on_click=on_click,
        width=width,
        height=tokens.dimensions.button_height,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=_state_values(colors.on_error, colors.on_error, colors.on_error, colors.disabled_text),
            bgcolor=_state_values(colors.error, colors.error, colors.error, colors.disabled),
            overlay_color=_state_values(
                colors.transparent,
                ft.Colors.with_opacity(0.10, colors.on_error),
                ft.Colors.with_opacity(0.18, colors.on_error),
                colors.transparent,
            ),
            shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
            mouse_cursor={
                ft.ControlState.DEFAULT: ft.MouseCursor.CLICK,
                ft.ControlState.DISABLED: ft.MouseCursor.BASIC,
            },
        ),
    )


def text_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    tooltip: str | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.TextButton:
    return ft.TextButton(
        text=label,
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        height=tokens.dimensions.compact_button_height,
        style=ft.ButtonStyle(
            color=tokens.colors.primary,
            overlay_color=_state_values(
                tokens.colors.transparent,
                tokens.colors.hover,
                tokens.colors.pressed,
                tokens.colors.transparent,
            ),
            shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
            mouse_cursor=ft.MouseCursor.CLICK,
        ),
    )


def icon_button(
    icon,
    on_click: Callable | None,
    *,
    tooltip: str,
    selected: bool = False,
    selected_icon=None,
    color: str | None = None,
    size: int | None = None,
    tokens: DesignTokens = TOKENS,
) -> ft.IconButton:
    """Create an accessible icon-only button; a tooltip is intentionally required."""
    return ft.IconButton(
        icon=icon,
        selected=selected,
        selected_icon=selected_icon,
        icon_color=color or tokens.colors.primary,
        selected_icon_color=color or tokens.colors.primary,
        icon_size=size or tokens.dimensions.icon_md,
        tooltip=tooltip,
        on_click=on_click,
        width=tokens.dimensions.touch_target,
        height=tokens.dimensions.touch_target,
        hover_color=tokens.colors.hover,
        focus_color=tokens.colors.focus,
        splash_color=tokens.colors.pressed,
        style=ft.ButtonStyle(shape=ft.CircleBorder(), mouse_cursor=ft.MouseCursor.CLICK),
    )


def audio_button(
    on_click: Callable,
    *,
    tooltip: str = "Play audio",
    diameter: int = 90,
    icon_size: int = 38,
    tokens: DesignTokens = TOKENS,
) -> ft.IconButton:
    """Prominent circular audio action used by listening activities."""
    return ft.IconButton(
        icon=ft.Icons.VOLUME_UP_ROUNDED,
        icon_color=tokens.colors.on_primary_container,
        icon_size=icon_size,
        tooltip=tooltip,
        on_click=on_click,
        width=diameter,
        height=diameter,
        style=ft.ButtonStyle(
            bgcolor=_state_values(
                tokens.colors.primary_container,
                tokens.colors.elevated_surface,
                tokens.colors.primary_container,
                tokens.colors.disabled,
            ),
            overlay_color=_state_values(
                tokens.colors.transparent,
                tokens.colors.hover,
                tokens.colors.pressed,
                tokens.colors.transparent,
            ),
            shape=ft.CircleBorder(),
            mouse_cursor=ft.MouseCursor.CLICK,
            animation_duration=tokens.motion.fast,
        ),
    )


def answer_button(
    label: str,
    on_click: Callable,
    *,
    width: int = 350,
    height: int | None = None,
    text_size: int | None = None,
    data=None,
    tokens: DesignTokens = TOKENS,
) -> ft.ElevatedButton:
    """Neutral answer choice with the same hover, focus, and shape everywhere."""
    return ft.ElevatedButton(
        content=ft.Text(
            label,
            size=text_size or tokens.typography.body_lg,
            text_align=ft.TextAlign.CENTER,
        ),
        data=data,
        width=width,
        height=height or tokens.dimensions.button_height,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=_state_values(
                tokens.colors.text_primary,
                tokens.colors.text_primary,
                tokens.colors.text_primary,
                tokens.colors.disabled_text,
            ),
            bgcolor=_state_values(
                tokens.colors.surface,
                tokens.colors.elevated_surface,
                tokens.colors.primary_container,
                tokens.colors.disabled,
            ),
            overlay_color=_state_values(
                tokens.colors.transparent,
                tokens.colors.hover,
                tokens.colors.pressed,
                tokens.colors.transparent,
            ),
            side=ft.BorderSide(1, tokens.colors.border),
            elevation=_state_values(
                tokens.elevation.card,
                tokens.elevation.raised,
                tokens.elevation.flat,
                tokens.elevation.flat,
            ),
            shape=ft.RoundedRectangleBorder(radius=tokens.radius.md),
            padding=ft.padding.symmetric(horizontal=tokens.spacing.lg, vertical=tokens.spacing.md),
            mouse_cursor={
                ft.ControlState.DEFAULT: ft.MouseCursor.CLICK,
                ft.ControlState.DISABLED: ft.MouseCursor.BASIC,
            },
            animation_duration=tokens.motion.fast,
        ),
    )


def set_answer_button_state(
    button: ft.ElevatedButton,
    state: str,
    *,
    tokens: DesignTokens = TOKENS,
) -> None:
    """Apply selected/correct/incorrect feedback while retaining disabled contrast."""
    palette = {
        "selected": (tokens.colors.primary_container, tokens.colors.on_primary_container),
        "correct": (tokens.colors.success, tokens.colors.on_success),
        "incorrect": (tokens.colors.error, tokens.colors.on_error),
        "matched": (tokens.colors.success_container, tokens.colors.on_success_container),
        "default": (tokens.colors.surface, tokens.colors.text_primary),
    }
    background, foreground = palette[state]
    button.style.bgcolor = {
        ft.ControlState.DEFAULT: background,
        ft.ControlState.DISABLED: background,
    }
    button.style.color = {
        ft.ControlState.DEFAULT: foreground,
        ft.ControlState.DISABLED: foreground,
    }


def back_button(
    on_click: Callable,
    *,
    label: str = "Back",
    compact: bool = False,
    tokens: DesignTokens = TOKENS,
) -> ft.Control:
    if compact:
        return icon_button(ft.Icons.ARROW_BACK_ROUNDED, on_click, tooltip=label, tokens=tokens)
    return text_button(label, on_click, icon=ft.Icons.ARROW_BACK_ROUNDED, tooltip=label, tokens=tokens)


def theme_toggle_button(controller: ThemeController, *, tokens: DesignTokens = TOKENS) -> ft.IconButton:
    icon_color = tokens.colors.sunny if controller.is_dark else tokens.colors.moon
    button = icon_button(
        ft.Icons.LIGHT_MODE_ROUNDED if controller.is_dark else ft.Icons.DARK_MODE_ROUNDED,
        None,
        tooltip="Use light theme" if controller.is_dark else "Use dark theme",
        color=icon_color,
        tokens=tokens,
    )

    def toggle_theme(event) -> None:
        controller.toggle()
        event.control.icon = (
            ft.Icons.LIGHT_MODE_ROUNDED if controller.is_dark else ft.Icons.DARK_MODE_ROUNDED
        )
        event.control.tooltip = "Use light theme" if controller.is_dark else "Use dark theme"
        event.control.icon_color = (
            tokens.colors.sunny if controller.is_dark else tokens.colors.moon
        )
        event.control.selected_icon_color = event.control.icon_color
        event.control.update()

    button.on_click = toggle_theme
    return button
