"""Focused regression tests for shared UI architecture."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import flet as ft

from gui.activities.keyboard import GeorgianKeyboard
from gui.components import (
    answer_button,
    action_card,
    content_card,
    exercise_action_button,
    guidance_button,
    icon_button,
    primary_button,
    page_header,
    review_badge,
    set_answer_button_state,
    text_input,
    theme_toggle_button,
)
from gui.core.navigation import NavigationController
from gui.core.theme import DARK_THEME, LIGHT_THEME, TOKENS, ThemeController


class FakePage:
    def __init__(self):
        self.theme = None
        self.dark_theme = None
        self.theme_mode = None
        self.bgcolor = None
        self.update_count = 0

    def update(self):
        self.update_count += 1


class ThemeTests(unittest.TestCase):
    def test_light_and_dark_palettes_share_semantic_component_tokens(self):
        self.assertNotEqual(
            LIGHT_THEME.color_scheme.primary,
            DARK_THEME.color_scheme.primary,
        )
        self.assertEqual(TOKENS.colors.primary, ft.Colors.PRIMARY)
        self.assertEqual(TOKENS.colors.text_primary, ft.Colors.ON_SURFACE)

    def test_theme_controller_configures_and_toggles_page(self):
        page = FakePage()
        controller = ThemeController(page)

        self.assertIs(page.theme, LIGHT_THEME)
        self.assertIs(page.dark_theme, DARK_THEME)
        self.assertEqual(page.theme_mode, ft.ThemeMode.LIGHT)

        controller.toggle()

        self.assertEqual(page.theme_mode, ft.ThemeMode.DARK)
        self.assertEqual(page.update_count, 1)

    def test_theme_toggle_uses_dark_moon_and_sunny_light_icon(self):
        page = FakePage()
        controller = ThemeController(page)
        button = theme_toggle_button(controller)

        self.assertEqual(button.icon, ft.Icons.DARK_MODE_ROUNDED)
        self.assertEqual(button.icon_color, TOKENS.colors.moon)
        with patch.object(button, "update"):
            button.on_click(SimpleNamespace(control=button))

        self.assertEqual(button.icon, ft.Icons.LIGHT_MODE_ROUNDED)
        self.assertEqual(button.icon_color, TOKENS.colors.sunny)

    def test_feedback_palettes_use_lively_accessible_tones(self):
        self.assertEqual(LIGHT_THEME.color_scheme.error, "#D92D4A")
        self.assertEqual(LIGHT_THEME.color_scheme.error_container, "#FECACA")
        self.assertEqual(LIGHT_THEME.color_scheme.tertiary, "#07883F")
        self.assertEqual(LIGHT_THEME.color_scheme.tertiary_container, "#BBF7D0")
        self.assertEqual(DARK_THEME.color_scheme.error, "#FB7185")
        self.assertEqual(DARK_THEME.color_scheme.tertiary, "#4ADE80")


class ComponentTests(unittest.TestCase):
    def test_page_header_keeps_navigation_and_titles_in_consistent_responsive_slots(self):
        header = page_header(
            "Lesson title",
            subtitle="Supporting context",
            on_back=lambda _event: None,
            trailing=ft.IconButton(icon=ft.Icons.HOME_ROUNDED),
        )
        grid = header.content
        leading, title, trailing = grid.controls

        self.assertIsInstance(grid, ft.ResponsiveRow)
        self.assertEqual(grid.vertical_alignment, ft.CrossAxisAlignment.START)
        self.assertEqual(leading.col, {"xs": 3, "sm": 2})
        self.assertEqual(title.col, {"xs": 6, "sm": 8})
        self.assertEqual(trailing.col, {"xs": 3, "sm": 2})
        self.assertEqual(leading.alignment, ft.alignment.top_left)
        self.assertEqual(title.alignment, ft.alignment.top_center)
        self.assertEqual(trailing.alignment, ft.alignment.top_right)
        self.assertEqual(leading.content.icon, ft.Icons.ARROW_BACK_ROUNDED)
        self.assertEqual(
            leading.content.width,
            TOKENS.dimensions.touch_target,
        )

    def test_action_card_supports_accessible_bright_accents(self):
        card = action_card(
            "Fun Facts",
            "Explore culture",
            ft.Icons.LIGHTBULB_ROUNDED,
            lambda _event: None,
            icon_color=TOKENS.colors.sunny,
            icon_foreground=TOKENS.colors.on_sunny,
        )
        icon_box = card.content.content.controls[0]

        self.assertEqual(icon_box.bgcolor, TOKENS.colors.sunny)
        self.assertEqual(icon_box.content.color, TOKENS.colors.on_sunny)

    def test_clickable_card_avoids_incompatible_animated_clip_combination(self):
        card = content_card(ft.Text("Curriculum"), on_click=lambda _event: None)

        self.assertIsNone(card.clip_behavior)
        self.assertIsNone(card.content.animate)
        self.assertTrue(card.content.ink)
        self.assertIsNotNone(card.content.on_hover)

    def test_primary_button_owns_shared_states_and_loading_behavior(self):
        button = primary_button("Save", lambda _event: None, loading=True)

        self.assertTrue(button.disabled)
        self.assertEqual(button.height, TOKENS.dimensions.button_height)
        self.assertIn(ft.ControlState.HOVERED, button.style.overlay_color)
        self.assertIn(ft.ControlState.DISABLED, button.style.bgcolor)

    def test_primary_button_pairs_an_icon_with_native_text(self):
        button = primary_button(
            "Continue",
            lambda _event: None,
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
        )

        self.assertEqual(button.text, "Continue")
        self.assertEqual(button.icon, ft.Icons.ARROW_FORWARD_ROUNDED)
        self.assertIsNone(button.content)
        self.assertNotEqual(
            button.style.overlay_color[ft.ControlState.HOVERED],
            button.style.overlay_color[ft.ControlState.PRESSED],
        )

    def test_exercise_actions_share_labels_dimensions_and_button_states(self):
        check = exercise_action_button("check_answer", lambda _event: None)
        proceed = exercise_action_button("continue", lambda _event: None)

        self.assertEqual(check.text, "Check answer")
        self.assertIsNone(check.icon)
        self.assertEqual(proceed.text, "Continue")
        self.assertEqual(proceed.icon, ft.Icons.ARROW_FORWARD_ROUNDED)
        for button in (check, proceed):
            self.assertEqual(button.width, TOKENS.dimensions.form_width)
            self.assertEqual(button.height, TOKENS.dimensions.button_height)
            self.assertIn(ft.ControlState.HOVERED, button.style.overlay_color)

    def test_icon_button_has_accessible_tooltip_and_touch_target(self):
        button = icon_button(
            ft.Icons.ARROW_BACK_ROUNDED,
            lambda _event: None,
            tooltip="Back to units",
        )

        self.assertEqual(button.tooltip, "Back to units")
        self.assertEqual(button.width, TOKENS.dimensions.touch_target)
        self.assertEqual(button.height, TOKENS.dimensions.touch_target)

    def test_guidance_button_opens_and_closes_an_accessible_dialog(self):
        button = guidance_button(
            "How to use this page",
            "A short introduction.",
            [("First step", "Do this first."), ("Next step", "Then do this.")],
        )
        page = SimpleNamespace(
            opened=[],
            closed=[],
            open=lambda dialog: page.opened.append(dialog),
            close=lambda dialog: page.closed.append(dialog),
        )

        button.on_click(SimpleNamespace(page=page))

        self.assertEqual(button.icon, ft.Icons.HELP_OUTLINE_ROUNDED)
        self.assertEqual(button.tooltip, "How to use this page")
        self.assertEqual(button.width, TOKENS.dimensions.touch_target)
        self.assertEqual(len(page.opened), 1)
        dialog = page.opened[0]
        self.assertTrue(dialog.modal)
        self.assertTrue(dialog.scrollable)
        self.assertEqual(dialog.title.value, "How to use this page")
        dialog.actions[0].on_click(SimpleNamespace(page=page))
        self.assertEqual(page.closed, [dialog])

    def test_answer_feedback_retains_contrast_while_disabled(self):
        button = answer_button("Answer", lambda _event: None)
        set_answer_button_state(button, "correct")

        self.assertEqual(
            button.style.bgcolor[ft.ControlState.DISABLED],
            TOKENS.colors.success,
        )
        self.assertEqual(
            button.style.color[ft.ControlState.DISABLED],
            TOKENS.colors.on_success,
        )

    def test_review_item_is_a_compact_orange_text_label(self):
        badge = review_badge({"is_review_item": True})

        self.assertIsInstance(badge, ft.Text)
        self.assertEqual(badge.value, "Review item")
        self.assertEqual(badge.color, TOKENS.colors.warning)

    def test_form_field_uses_shared_focus_and_error_tokens(self):
        field = text_input(label="Name", required=True, error_text="Required")

        self.assertEqual(field.label, "Name *")
        self.assertEqual(field.focused_border_color, TOKENS.colors.primary)
        self.assertEqual(field.error_style.color, TOKENS.colors.error)


class NavigationTests(unittest.TestCase):
    def test_navigation_history_has_one_authoritative_back_action(self):
        page = FakePage()
        stage = ft.Container()
        navigation = NavigationController(page, stage)

        navigation.show(lambda: ft.Text("Home"), name="home", clear_history=True)
        navigation.show(lambda: ft.Text("Units"), name="units")
        navigation.show(lambda: ft.Text("Lessons"), name="lessons")

        self.assertEqual(navigation.current_name, "lessons")
        navigation.back()
        self.assertEqual(navigation.current_name, "units")
        navigation.back()
        self.assertEqual(navigation.current_name, "home")


class GeorgianInputTests(unittest.TestCase):
    def test_physical_keyboard_translation_is_shared(self):
        self.assertEqual(GeorgianKeyboard.translate_latin_text("gamarjoba"), "გამარჯობა")
        self.assertEqual(GeorgianKeyboard.translate_latin_text("WRTSJZC"), "ჭღთშჟძჩ")


if __name__ == "__main__":
    unittest.main()
