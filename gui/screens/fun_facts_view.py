"""Culture and language facts screen."""

from collections.abc import Callable

import flet as ft

from gui.components import content_card, page_header
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


FACT_CATEGORIES = {
    "Language 🗣️": [
        (
            "A Linguistic Island",
            "Georgian belongs to the Kartvelian language family, completely unrelated to any other major language group in the world.",
            ft.Icons.SPEAKER_NOTES_ROUNDED,
        ),
        (
            "Tongue-Twisting Consonants",
            "It is famous for extreme consonant clusters. The word 'gvprtskvni' (გვფრცქვნი) means 'you are peeling us' and has eight consonants in a row.",
            ft.Icons.RECORD_VOICE_OVER_ROUNDED,
        ),
        (
            "Three Alphabets",
            "While Mkhedruli is used today, Georgia has three distinct alphabets: Asomtavruli, Nuskhuri, and Mkhedruli.",
            ft.Icons.FONT_DOWNLOAD_ROUNDED,
        ),
    ],
    "Culture & Wine 🍷": [
        (
            "The Birthplace of Wine",
            "Georgia has been producing wine for over 8,000 years, traditionally fermenting it in clay qvevri buried underground.",
            ft.Icons.WINE_BAR_ROUNDED,
        ),
        (
            "The Supra",
            "A traditional Georgian feast is called a supra and is led by a tamada, or toastmaster.",
            ft.Icons.RESTAURANT_ROUNDED,
        ),
        (
            "Polyphonic Singing",
            "Georgian polyphonic singing is so culturally significant that 'Chakrulo' was included on the Voyager Golden Record.",
            ft.Icons.LIBRARY_MUSIC_ROUNDED,
        ),
    ],
    "Geography & History 🏔️": [
        (
            "Not 'Georgia' to Locals",
            "Georgians call their country Sakartvelo (საქართველო), meaning the land of the Kartvelians.",
            ft.Icons.MAP_ROUNDED,
        ),
        (
            "Europe's Highest Village",
            "Ushguli in Svaneti sits around 2,100 meters above sea level, making it one of Europe's highest continuously inhabited settlements.",
            ft.Icons.LANDSCAPE_ROUNDED,
        ),
        (
            "First Europeans",
            "The 1.8-million-year-old remains found in Dmanisi are among the oldest hominin remains discovered outside Africa.",
            ft.Icons.HISTORY_ROUNDED,
        ),
    ],
}


class FunFactsView(ft.Column):
    def __init__(
        self,
        on_back: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.tokens = tokens
        self.controls = [self._build(on_back)]

    def _build(self, on_back: Callable) -> ft.Control:
        tokens = self.tokens
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=tokens.motion.slow,
            expand=1,
            scrollable=True,
            tab_alignment=ft.TabAlignment.CENTER,
            indicator_color=tokens.colors.error,
            label_color=tokens.colors.text_primary,
            unselected_label_color=tokens.colors.text_muted,
            tabs=[],
        )
        for category, items in FACT_CATEGORIES.items():
            cards = [
                content_card(
                    ft.ListTile(
                        leading=ft.Icon(icon, size=36, color=tokens.colors.error),
                        title=ft.Text(
                            title,
                            weight=ft.FontWeight.BOLD,
                            size=tokens.typography.title_sm,
                            color=tokens.colors.text_primary,
                        ),
                        subtitle=ft.Text(
                            description,
                            size=tokens.typography.body,
                            color=tokens.colors.text_secondary,
                        ),
                    ),
                    padding=tokens.spacing.xs,
                    elevation=tokens.elevation.raised,
                    tokens=tokens,
                )
                for title, description, icon in items
            ]
            tabs.tabs.append(
                ft.Tab(
                    text=category,
                    content=ft.ListView(
                        controls=cards,
                        spacing=tokens.spacing.lg,
                        padding=ft.padding.only(
                            top=tokens.spacing.lg,
                            bottom=tokens.spacing.xl,
                        ),
                    ),
                )
            )

        return page_shell(
            [
                page_header(
                    "Did You Know?",
                    subtitle="Language, culture, geography, and history",
                    on_back=on_back,
                    back_label="Back to home",
                    max_width=tokens.dimensions.content_width,
                    tokens=tokens,
                ),
                tabs,
            ],
            max_width=tokens.dimensions.content_width,
            scroll=False,
            tokens=tokens,
        )
