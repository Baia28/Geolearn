"""GeoLearn's semantic design tokens and Flet theme configuration.

Controls use the semantic values in ``TOKENS.colors``.  Flet resolves those
values against ``LIGHT_THEME`` or ``DARK_THEME`` at render time, so changing
theme mode does not require screen-specific color branches or a screen rebuild.
"""

from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class ColorTokens:
    background: str = ft.Colors.SURFACE
    surface: str = ft.Colors.SURFACE
    elevated_surface: str = ft.Colors.SURFACE_CONTAINER_HIGHEST
    subtle_surface: str = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)
    phase_surface: str = ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY)
    unit_surface: str = ft.Colors.SURFACE
    lesson_surface: str = ft.Colors.SURFACE_CONTAINER_HIGHEST
    primary: str = ft.Colors.PRIMARY
    on_primary: str = ft.Colors.ON_PRIMARY
    primary_container: str = ft.Colors.PRIMARY_CONTAINER
    on_primary_container: str = ft.Colors.ON_PRIMARY_CONTAINER
    secondary: str = ft.Colors.SECONDARY
    on_secondary: str = ft.Colors.ON_SECONDARY
    secondary_container: str = ft.Colors.SECONDARY_CONTAINER
    on_secondary_container: str = ft.Colors.ON_SECONDARY_CONTAINER
    success: str = ft.Colors.TERTIARY
    on_success: str = ft.Colors.ON_TERTIARY
    success_container: str = ft.Colors.TERTIARY_CONTAINER
    on_success_container: str = ft.Colors.ON_TERTIARY_CONTAINER
    error: str = ft.Colors.ERROR
    on_error: str = ft.Colors.ON_ERROR
    error_container: str = ft.Colors.ERROR_CONTAINER
    on_error_container: str = ft.Colors.ON_ERROR_CONTAINER
    warning: str = ft.Colors.ORANGE_700
    sunny: str = "#FBBF24"
    on_sunny: str = "#422006"
    moon: str = ft.Colors.BLACK
    text_primary: str = ft.Colors.ON_SURFACE
    text_secondary: str = ft.Colors.ON_SURFACE_VARIANT
    text_muted: str = ft.Colors.with_opacity(0.72, ft.Colors.ON_SURFACE_VARIANT)
    border: str = ft.Colors.OUTLINE_VARIANT
    border_strong: str = ft.Colors.OUTLINE
    disabled: str = ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
    disabled_text: str = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
    hover: str = ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)
    pressed: str = ft.Colors.with_opacity(0.20, ft.Colors.PRIMARY)
    focus: str = ft.Colors.with_opacity(0.18, ft.Colors.PRIMARY)
    scrim: str = ft.Colors.with_opacity(0.54, ft.Colors.ON_SURFACE)
    transparent: str = ft.Colors.TRANSPARENT


@dataclass(frozen=True)
class SpacingTokens:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    xxxl: int = 32


@dataclass(frozen=True)
class RadiusTokens:
    sm: int = 6
    md: int = 10
    lg: int = 14
    xl: int = 20
    pill: int = 999


@dataclass(frozen=True)
class DimensionTokens:
    button_height: int = 48
    compact_button_height: int = 40
    input_height: int = 52
    icon_sm: int = 18
    icon_md: int = 22
    icon_lg: int = 28
    touch_target: int = 48
    form_width: int = 350
    session_progress_width: int = 400
    dialogue_width: int = 420
    reading_width: int = 650
    keyboard_content_width: int = 700
    content_width: int = 850
    wide_content_width: int = 1000
    sidebar_width: int = 280
    wide_input_width: int = 580
    illustration_size: int = 180
    alphabet_card_width: int = 135
    alphabet_detail_card_width: int = 520


@dataclass(frozen=True)
class TypographyTokens:
    caption: int = 11
    label: int = 12
    body_sm: int = 13
    body: int = 14
    body_lg: int = 16
    title_sm: int = 18
    title: int = 24
    page_title: int = 28
    display: int = 36


@dataclass(frozen=True)
class ElevationTokens:
    flat: int = 0
    card: int = 1
    raised: int = 2


@dataclass(frozen=True)
class MotionTokens:
    fast: int = 120
    normal: int = 200
    slow: int = 300


@dataclass(frozen=True)
class DesignTokens:
    colors: ColorTokens = ColorTokens()
    spacing: SpacingTokens = SpacingTokens()
    radius: RadiusTokens = RadiusTokens()
    dimensions: DimensionTokens = DimensionTokens()
    typography: TypographyTokens = TypographyTokens()
    elevation: ElevationTokens = ElevationTokens()
    motion: MotionTokens = MotionTokens()


TOKENS = DesignTokens()


def _color_scheme(*, dark: bool) -> ft.ColorScheme:
    if dark:
        return ft.ColorScheme(
            primary="#93C5FD",
            on_primary="#0B1F3A",
            primary_container="#1E3A5F",
            on_primary_container="#DBEAFE",
            secondary="#5EEAD4",
            on_secondary="#042F2E",
            secondary_container="#134E4A",
            on_secondary_container="#CCFBF1",
            tertiary="#4ADE80",
            on_tertiary="#052E16",
            tertiary_container="#166534",
            on_tertiary_container="#DCFCE7",
            error="#FB7185",
            on_error="#4C0519",
            error_container="#881337",
            on_error_container="#FFE4E6",
            background="#0B1220",
            on_background="#E5E7EB",
            surface="#111827",
            on_surface="#F1F5F9",
            surface_variant="#1E293B",
            on_surface_variant="#CBD5E1",
            outline="#64748B",
            outline_variant="#334155",
            shadow="#000000",
        )

    return ft.ColorScheme(
        primary="#2563EB",
        on_primary="#FFFFFF",
        primary_container="#DBEAFE",
        on_primary_container="#1E3A8A",
        secondary="#0F766E",
        on_secondary="#FFFFFF",
        secondary_container="#CCFBF1",
        on_secondary_container="#134E4A",
        tertiary="#07883F",
        on_tertiary="#FFFFFF",
        tertiary_container="#BBF7D0",
        on_tertiary_container="#14532D",
        error="#D92D4A",
        on_error="#FFFFFF",
        error_container="#FECACA",
        on_error_container="#881337",
        background="#F8FAFC",
        on_background="#0F172A",
        surface="#FFFFFF",
        on_surface="#0F172A",
        surface_variant="#F1F5F9",
        on_surface_variant="#475569",
        outline="#94A3B8",
        outline_variant="#E2E8F0",
        shadow="#0F172A",
    )


def build_flet_theme(*, dark: bool) -> ft.Theme:
    """Build the native theme that backs the semantic component tokens."""
    colors = _color_scheme(dark=dark)
    return ft.Theme(
        color_scheme=colors,
        use_material3=True,
        scaffold_bgcolor=colors.background,
        card_color=colors.surface,
        divider_color=colors.outline_variant,
        disabled_color=colors.on_surface_variant,
        hover_color=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
        focus_color=ft.Colors.with_opacity(0.18, ft.Colors.PRIMARY),
        card_theme=ft.CardTheme(
            color=colors.surface,
            elevation=TOKENS.elevation.card,
            shape=ft.RoundedRectangleBorder(radius=TOKENS.radius.lg),
            margin=0,
        ),
        button_theme=ft.ButtonTheme(
            height=TOKENS.dimensions.button_height,
            shape=ft.RoundedRectangleBorder(radius=TOKENS.radius.md),
            padding=ft.padding.symmetric(
                horizontal=TOKENS.spacing.lg,
                vertical=TOKENS.spacing.sm,
            ),
        ),
        divider_theme=ft.DividerTheme(color=colors.outline_variant, thickness=1),
        progress_indicator_theme=ft.ProgressIndicatorTheme(
            color=colors.tertiary,
            linear_track_color=colors.surface_variant,
            linear_min_height=6,
        ),
        tabs_theme=ft.TabsTheme(
            indicator_color=colors.primary,
            label_color=colors.on_surface,
            unselected_label_color=colors.on_surface_variant,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(size=TOKENS.typography.body, color=colors.on_surface),
            body_small=ft.TextStyle(size=TOKENS.typography.body_sm, color=colors.on_surface_variant),
            title_large=ft.TextStyle(size=TOKENS.typography.title, weight=ft.FontWeight.BOLD),
            title_medium=ft.TextStyle(size=TOKENS.typography.title_sm, weight=ft.FontWeight.BOLD),
            label_medium=ft.TextStyle(size=TOKENS.typography.label, weight=ft.FontWeight.W_600),
        ),
    )


LIGHT_THEME = build_flet_theme(dark=False)
DARK_THEME = build_flet_theme(dark=True)


class ThemeController:
    """Own the app theme mode and configure Flet once at the page boundary."""

    def __init__(self, page: ft.Page, initial_mode: ft.ThemeMode = ft.ThemeMode.LIGHT):
        self.page = page
        self.page.theme = LIGHT_THEME
        self.page.dark_theme = DARK_THEME
        self.page.theme_mode = initial_mode
        self.page.bgcolor = TOKENS.colors.background

    @property
    def is_dark(self) -> bool:
        return self.page.theme_mode == ft.ThemeMode.DARK

    def toggle(self) -> None:
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.is_dark else ft.ThemeMode.DARK
        self.page.update()
