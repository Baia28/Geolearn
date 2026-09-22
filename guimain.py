"""GeoLearn application composition root and route controller."""

import os

import flet as ft

from alphabet.alphabet_hub import AlphabetPage
from engine.db_managers import ContentDBManager, ProgressDBManager
from engine.lesson_engine import LessonSession
from engine.passive_review import PassiveReviewEngine
from engine.review_engine import ReviewSession
from gui.services.audio import play_audio_file
from gui.screens.fun_facts_view import FunFactsView
from gui.screens.home_view import HomeView
from gui.screens.lessons_view import LessonsView
from gui.screens.passive_rev_view import PassiveReviewView
from gui.screens.session_view import SessionView
from gui.screens.units_view import UnitsView
from gui.components import text_button, theme_toggle_button
from gui.core.navigation import NavigationController
from gui.core.theme import TOKENS, ThemeController


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DB_PATH = os.path.join(BASE_DIR, "database", "content_poolbook.db")
PROGRESS_DB_PATH = os.path.join(BASE_DIR, "database", "user_progress.db")


class GeoLearnApp:
    """Coordinate application services, screen construction, and navigation."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.tokens = TOKENS
        self._configure_page()
        self.theme_controller = ThemeController(page)

        self.content_db = ContentDBManager(CONTENT_DB_PATH)
        self.progress_db = ProgressDBManager(PROGRESS_DB_PATH)
        self.passive_engine = PassiveReviewEngine(self.content_db)

        self.stage = ft.Container(expand=True, alignment=ft.alignment.top_center)
        self.page.add(self.stage)
        self.navigator = NavigationController(self.page, self.stage)

    def _configure_page(self) -> None:
        self.page.title = "GeoLearn - Georgian Language Platform"
        self.page.padding = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.window.width = 900
        self.page.window.height = 900
        self.page.window.min_width = 420
        self.page.window.min_height = 640

    def start(self) -> None:
        self.show_home()

    def show_home(self) -> None:
        def build() -> ft.Control:
            completed_ids = self.progress_db.get_completed_lesson_ids()
            return HomeView(
                phases_summary=self.content_db.get_phases_summary(completed_ids),
                on_select_phase=self.show_units,
                on_select_alphabet=self.show_alphabet,
                on_open_fun_facts=self.show_fun_facts,
                on_quick_review=lambda: self.show_session(),
                on_global_passive_review=self.show_global_passive_review,
                theme_action=theme_toggle_button(self.theme_controller),
                tokens=self.tokens,
            )

        self.navigator.show(build, name="home", clear_history=True)

    def show_alphabet(self) -> None:
        self.navigator.show(
            lambda: AlphabetPage(
                on_back_home=self.navigator.back,
                tokens=self.tokens,
            ),
            name="alphabet",
        )

    def show_fun_facts(self, _event=None) -> None:
        self.navigator.show(
            lambda: FunFactsView(on_back=self.navigator.back, tokens=self.tokens),
            name="fun_facts",
        )

    def show_units(self, phase_num: int) -> None:
        def build() -> ft.Control:
            completed_ids = self.progress_db.get_completed_lesson_ids()
            units = self.content_db.get_units_for_phase(phase_num, completed_ids)
            phases = self.content_db.get_phases_summary(completed_ids)
            phase_title = next(
                (phase["title"] for phase in phases if phase["phase_num"] == phase_num),
                f"Phase {phase_num}",
            )
            return UnitsView(
                phase_num=phase_num,
                phase_title=phase_title,
                units_summary=units,
                on_select_unit=self.show_lessons,
                on_back=self.navigator.back,
                on_home=self.show_home,
                tokens=self.tokens,
            )

        self.navigator.show(build, name=f"phase:{phase_num}")

    def show_lessons(self, phase_num: int, unit_num: int) -> None:
        def build() -> ft.Control:
            completed_ids = self.progress_db.get_completed_lesson_ids()
            lessons = self.content_db.get_lessons_for_unit(
                phase_num, unit_num, completed_ids
            )
            accessible_ids = set(self._get_accessible_lesson_ids())
            units = self.content_db.get_units_for_phase(phase_num, completed_ids)
            unit_title = next(
                (unit["title"] for unit in units if unit["unit_num"] == unit_num),
                f"Unit {unit_num}",
            )
            return LessonsView(
                phase_num=phase_num,
                unit_num=unit_num,
                unit_title=unit_title,
                lessons_list=lessons,
                on_select_lesson=self.show_lesson_session,
                on_passive_read=self.show_unit_passive_review,
                on_unit_review=self.show_unit_review,
                on_back=self.navigator.back,
                on_home=self.show_home,
                has_review_material=any(
                    lesson["lesson_id"] in accessible_ids for lesson in lessons
                ),
                tokens=self.tokens,
            )

        self.navigator.show(build, name=f"unit:{phase_num}:{unit_num}")

    def show_global_passive_review(self) -> None:
        accessible_ids = self._get_accessible_lesson_ids()
        master_sheet = self.passive_engine.build_global_master_sheet(accessible_ids)
        self._show_passive_review(master_sheet, "Your Learning Path", "library:global")

    def show_unit_passive_review(self, phase_num: int, unit_num: int) -> None:
        master_sheet = self.passive_engine.build_unit_master_sheet(
            phase_num,
            unit_num,
            self._get_accessible_lesson_ids(),
        )
        self._show_passive_review(
            master_sheet,
            f"Phase {phase_num} · Unit {unit_num}",
            f"library:{phase_num}:{unit_num}",
        )

    def _get_accessible_lesson_ids(self) -> list[int]:
        lesson_ids = set(self.progress_db.get_completed_lesson_ids())
        for phase_num, unit_num, lesson_num in self.progress_db.get_started_lesson_coordinates():
            lesson_id = self.content_db.resolve_lesson_id(phase_num, unit_num, lesson_num)
            if lesson_id is not None:
                lesson_ids.add(lesson_id)
        return sorted(lesson_ids)

    def _show_passive_review(self, master_sheet: dict, title: str, name: str) -> None:
        self.navigator.show(
            lambda: PassiveReviewView(
                master_sheet=master_sheet,
                unit_title=title,
                on_back=self.navigator.back,
                play_audio=lambda raw_path: play_audio_file(self.page, raw_path),
                tokens=self.tokens,
            ),
            name=name,
        )

    def show_lesson_session(self, phase_num: int, unit_num: int, lesson_num: int) -> None:
        engine = LessonSession(
            phase_num=phase_num,
            unit_num=unit_num,
            lesson_num=lesson_num,
        )
        self._show_session(
            engine,
            f"lesson:{phase_num}:{unit_num}:{lesson_num}",
            completion_title="Lesson Completed!",
        )

    def show_unit_review(self, phase_num: int, unit_num: int) -> None:
        engine = ReviewSession(phase_num=phase_num, unit_num=unit_num, max_items=10)
        self._show_session(
            engine,
            f"review:{phase_num}:{unit_num}",
            completion_title="Review Completed!",
        )

    def show_session(self) -> None:
        self._show_session(
            ReviewSession(phase_num=None, unit_num=None, max_items=10),
            "review:global",
            completion_title="Review Completed!",
        )

    def _show_session(
        self,
        engine,
        name: str,
        *,
        completion_title: str,
    ) -> None:
        def build() -> ft.Control:
            return ft.Column(
                controls=[
                    ft.Container(
                        content=text_button(
                            "Exit session",
                            self.navigator.back,
                            icon=ft.Icons.CLOSE_ROUNDED,
                            tooltip="Exit session",
                            tokens=self.tokens,
                        ),
                        padding=ft.padding.only(
                            left=self.tokens.spacing.lg,
                            top=self.tokens.spacing.sm,
                        ),
                    ),
                    SessionView(
                        page=self.page,
                        engine=engine,
                        on_return=self.show_home,
                        completion_title=completion_title,
                        completion_action_label="Home",
                        completion_action_icon=ft.Icons.HOME_ROUNDED,
                        tokens=self.tokens,
                    ),
                ],
                expand=True,
                spacing=self.tokens.spacing.xs,
            )

        self.navigator.show(build, name=name)


def main(page: ft.Page) -> None:
    GeoLearnApp(page).start()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
