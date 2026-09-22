"""Browse the Mkhedruli alphabet and inspect individual letters."""

from collections.abc import Callable

import flet as ft

from gui.services.audio import play_audio_file
from gui.components import content_card, icon_button, page_header, secondary_button
from gui.core.layout import page_shell
from gui.core.theme import TOKENS, DesignTokens


VOWELS = {"ა", "ე", "ი", "ო", "უ"}


class AlphabetGalleryView(ft.Column):
    def __init__(
        self,
        db,
        on_back_to_menu: Callable,
        tokens: DesignTokens = TOKENS,
    ):
        super().__init__(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.db = db
        self.on_back_to_menu = on_back_to_menu
        self.tokens = tokens
        self.auto_sound_enabled = True
        self.show_images = True
        self.show_gallery()

    def toggle_sound(self, _event=None) -> None:
        self.auto_sound_enabled = not self.auto_sound_enabled
        self.show_gallery()

    def toggle_images(self, _event=None) -> None:
        self.show_images = not self.show_images
        self.show_gallery()

    def _handle_card_hover(self, event, audio_path: str | None) -> None:
        if event.data == "true" and self.auto_sound_enabled and audio_path and self.page:
            play_audio_file(self.page, audio_path)

    def _letter_card(self, item: dict, index: int) -> ft.Card:
        tokens = self.tokens
        georgian = item.get("georgian", "")
        image_path = item.get("example_image")
        audio_path = item.get("letter_audio")
        card_controls: list[ft.Control] = [
            ft.Text(
                georgian,
                size=40,
                weight=ft.FontWeight.BOLD,
                color=(tokens.colors.error if georgian in VOWELS else tokens.colors.on_primary_container),
            )
        ]
        if self.show_images:
            card_controls.append(
                ft.Image(src=image_path, width=50, height=50, fit=ft.ImageFit.CONTAIN)
                if image_path
                else ft.Container(height=50)
            )
        card_controls.append(
            ft.Text(
                item.get("transliteration") or "",
                size=tokens.typography.body,
                weight=ft.FontWeight.W_500,
                color=tokens.colors.text_secondary,
            )
        )
        card = content_card(
            ft.Column(
                card_controls,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.spacing.xs,
            ),
            on_click=lambda _event: self.show_letter_detail(index),
            width=tokens.dimensions.alphabet_card_width,
            height=170 if self.show_images else 120,
            padding=tokens.spacing.md,
            tooltip=f"Open {georgian}",
            tokens=tokens,
        )
        shared_hover = card.content.on_hover

        def handle_hover(event) -> None:
            shared_hover(event)
            self._handle_card_hover(event, audio_path)

        card.content.on_hover = handle_hover
        return card

    def show_gallery(self) -> None:
        tokens = self.tokens
        cards = [
            self._letter_card(item, index)
            for index, item in enumerate(self.db.get_alphabet_letters())
        ]
        actions = ft.Row(
            controls=[
                icon_button(
                    ft.Icons.IMAGE_ROUNDED if self.show_images else ft.Icons.HIDE_IMAGE_ROUNDED,
                    self.toggle_images,
                    tooltip=("Hide illustrations" if self.show_images else "Show illustrations"),
                    selected=self.show_images,
                    tokens=tokens,
                ),
                icon_button(
                    ft.Icons.VOLUME_UP_ROUNDED if self.auto_sound_enabled else ft.Icons.VOLUME_OFF_ROUNDED,
                    self.toggle_sound,
                    tooltip=("Disable hover sound" if self.auto_sound_enabled else "Enable hover sound"),
                    selected=self.auto_sound_enabled,
                    tokens=tokens,
                ),
            ],
            spacing=0,
            tight=True,
            wrap=True,
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Georgian Alphabet (33 Letters)",
                        subtitle="Hover to hear a sound; select a letter for details",
                        on_back=lambda _event: self.on_back_to_menu(),
                        back_label="Back to alphabet hub",
                        trailing=actions,
                        max_width=tokens.dimensions.wide_content_width,
                        tokens=tokens,
                    ),
                    ft.Row(
                        controls=cards,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=tokens.spacing.md,
                        run_spacing=tokens.spacing.md,
                    ),
                ],
                max_width=tokens.dimensions.wide_content_width,
                tokens=tokens,
            )
        ]
        if self.page:
            self.update()

    def show_letter_detail(self, letter_index: int) -> None:
        tokens = self.tokens
        detail = self.db.get_letter_detail_by_index(letter_index)
        letter = detail.get("letter")
        if not letter:
            self.show_gallery()
            return
        example = detail.get("example") or {}
        total = detail.get("total", 0)
        georgian = letter.get("georgian", "")
        description = letter.get("linguistic_desc") or letter.get("transliteration", "")
        letter_audio = letter.get("letter_audio")
        if letter_audio and self.page:
            play_audio_file(self.page, letter_audio)

        detail_controls: list[ft.Control] = [
            ft.Text(
                georgian,
                size=88,
                weight=ft.FontWeight.BOLD,
                color=(tokens.colors.error if georgian in VOWELS else tokens.colors.on_primary_container),
            ),
            ft.Text(
                f"Pronunciation: {description}",
                size=tokens.typography.title_sm,
                weight=ft.FontWeight.W_500,
                color=tokens.colors.text_secondary,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if letter_audio:
            detail_controls.append(
                secondary_button(
                    "Letter sound",
                    lambda _event: play_audio_file(self.page, letter_audio),
                    icon=ft.Icons.VOLUME_UP_ROUNDED,
                    tokens=tokens,
                )
            )
        if example.get("image"):
            detail_controls.append(
                ft.Image(
                    src=example["image"],
                    width=170,
                    height=170,
                    fit=ft.ImageFit.CONTAIN,
                )
            )
        detail_controls.append(
            ft.Text(
                f"{example.get('word', 'N/A')} — {example.get('meaning', 'N/A')}",
                size=tokens.typography.title_sm,
                weight=ft.FontWeight.BOLD,
                color=tokens.colors.text_primary,
                text_align=ft.TextAlign.CENTER,
            )
        )
        if example.get("audio"):
            detail_controls.append(
                secondary_button(
                    "Example word sound",
                    lambda _event: play_audio_file(self.page, example["audio"]),
                    icon=ft.Icons.VOLUME_UP_ROUNDED,
                    tokens=tokens,
                )
            )
        detail_card = content_card(
            ft.Column(
                detail_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.spacing.md,
            ),
            padding=ft.padding.only(
                left=tokens.spacing.xxl,
                top=tokens.spacing.xxl,
                right=tokens.spacing.xxl,
                bottom=tokens.spacing.xxxl + tokens.spacing.lg,
            ),
            width=tokens.dimensions.alphabet_detail_card_width,
            elevation=tokens.elevation.raised,
            tokens=tokens,
        )

        def handle_swipe(event) -> None:
            velocity = event.primary_velocity or event.velocity_x or 0
            if abs(velocity) < 150:
                return
            next_index = letter_index + (1 if velocity < 0 else -1)
            if 0 <= next_index < total:
                self.show_letter_detail(next_index)

        previous_button = icon_button(
            ft.Icons.CHEVRON_LEFT_ROUNDED,
            lambda _event: self.show_letter_detail(letter_index - 1),
            tooltip="Previous letter",
            size=36,
            tokens=tokens,
        )
        previous_button.disabled = letter_index == 0
        next_button = icon_button(
            ft.Icons.CHEVRON_RIGHT_ROUNDED,
            lambda _event: self.show_letter_detail(letter_index + 1),
            tooltip="Next letter",
            size=36,
            tokens=tokens,
        )
        next_button.disabled = letter_index == total - 1
        carousel = ft.Row(
            controls=[
                previous_button,
                ft.GestureDetector(
                    content=ft.Container(
                        content=detail_card,
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                    on_horizontal_drag_end=handle_swipe,
                    drag_interval=tokens.motion.fast,
                    expand=True,
                ),
                next_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=tokens.spacing.sm,
        )
        position = ft.Text(
            f"{letter_index + 1} / {total} • Swipe or use arrows",
            size=tokens.typography.caption,
            color=tokens.colors.text_secondary,
            text_align=ft.TextAlign.CENTER,
        )
        self.controls = [
            page_shell(
                [
                    page_header(
                        "Letter detail",
                        on_back=lambda _event: self.show_gallery(),
                        back_label="Back to gallery",
                        max_width=tokens.dimensions.reading_width,
                        tokens=tokens,
                    ),
                    carousel,
                    position,
                ],
                max_width=tokens.dimensions.reading_width,
                tokens=tokens,
            )
        ]
        if self.page:
            self.update()
