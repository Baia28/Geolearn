"""Regression coverage for the database-backed learning experience."""

import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import flet as ft

from alphabet.alphabet_db import AlphabetDB
from alphabet.alphabet_hub import AlphabetPage
from alphabet.alphabet_gallery import AlphabetGalleryView
from alphabet.alphabet_pronunciation import PhoneticsGuideView
from alphabet.alphabet_typing import AlphabetTypingGameView
from alphabet.anban_game import AnbanGameView
from engine.db_managers import ContentDBManager, ProgressDBManager
from engine.lesson_engine import LessonSession
from engine.passive_review import PassiveReviewEngine
from engine.review_engine import ReviewSession
from gui.screens.home_view import HomeView
from gui.screens.lessons_view import LessonsView
from gui.screens.passive_rev_view import PassiveReviewView
from gui.screens.session_view import SessionView
from gui.screens.units_view import UnitsView
from gui.activities.dialogues import ChatBubble, DialoguePassiveView, LiveDialogueView
from gui.activities.production import MatchMatrix3x3
from gui.core.theme import TOKENS
from guimain import GeoLearnApp


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DB = ROOT / "database" / "content_poolbook.db"
PROGRESS_DB = ROOT / "database" / "user_progress.db"


class FakeWindow:
    width = None
    height = None
    min_width = None
    min_height = None


class FakePage:
    """Small Page surface for route composition without opening a window."""

    def __init__(self):
        self.window = FakeWindow()
        self.controls = []
        self.overlay = []
        self.update_count = 0
        self.theme = None
        self.dark_theme = None
        self.theme_mode = None
        self.bgcolor = None

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *_controls):
        self.update_count += 1


class FakeSessionEngine:
    queue = [
        {
            "activity": "mc_eng_to_geo",
            "target": {"eng": "Hello", "geo": "გამარჯობა"},
            "distractors": ["მადლობა", "ნახვამდის"],
        }
    ]

    def get_next_exercise(self):
        return self.queue[0]

    def submit_answer(self, *_args, **_kwargs):
        return {"progress": 1.0}


def find_control(root: ft.Control, control_type: type[ft.Control]):
    if isinstance(root, control_type):
        return root
    for child in root._get_children():
        found = find_control(child, control_type)
        if found is not None:
            return found
    return None


def find_card_by_title(root: ft.Control, title: str) -> ft.Card | None:
    if isinstance(root, ft.Card):
        for child in root._get_children():
            if isinstance(child, ft.Text) and child.value == title:
                return root
            nested = find_control(child, ft.Text)
            if nested is not None and nested.value == title:
                return root
    for child in root._get_children():
        card = find_card_by_title(child, title)
        if card is not None:
            return card
    return None


def action_card_accent(card: ft.Card) -> str:
    return card.content.content.controls[0].bgcolor


class CurriculumDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = ContentDBManager(str(CONTENT_DB))
        cls.progress = ProgressDBManager(str(PROGRESS_DB))
        cls.completed = cls.progress.get_completed_lesson_ids()

    def test_complete_curriculum_is_still_reachable_from_navigation_queries(self):
        phases = self.content.get_phases_summary(self.completed)
        self.assertEqual(len(phases), 2)

        units = []
        lessons = []
        for phase in phases:
            phase_units = self.content.get_units_for_phase(
                phase["phase_num"], self.completed
            )
            self.assertTrue(phase_units)
            units.extend(phase_units)
            for unit in phase_units:
                unit_lessons = self.content.get_lessons_for_unit(
                    phase["phase_num"], unit["unit_num"], self.completed
                )
                self.assertTrue(unit_lessons)
                lessons.extend(unit_lessons)

        self.assertEqual(len(units), 9)
        self.assertEqual(len(lessons), 27)

    def test_every_lesson_builds_supported_real_activities(self):
        supported = {
            "mc_geo_to_eng",
            "mc_eng_to_geo",
            "mc_geo_pair_geo",
            "audio_mc_to_eng",
            "audio_mc_to_geo",
            "match_matrix_3x3",
            "type_georgian",
            "audio_dictation",
            "dialogue_passive",
            "dialogue_roleplay_mc",
            "dialogue_activity",
            "dialogue_interactive",
        }
        generated = set()
        with contextlib.redirect_stdout(io.StringIO()):
            for phase in self.content.get_phases_summary(self.completed):
                phase_num = phase["phase_num"]
                for unit in self.content.get_units_for_phase(
                    phase_num, self.completed
                ):
                    unit_num = unit["unit_num"]
                    for lesson in self.content.get_lessons_for_unit(
                        phase_num, unit_num, self.completed
                    ):
                        session = LessonSession(
                            phase_num=phase_num,
                            unit_num=unit_num,
                            lesson_num=lesson["lesson_num"],
                        )
                        self.assertTrue(
                            session.queue,
                            f"Empty queue for {phase_num}/{unit_num}/{lesson['lesson_num']}",
                        )
                        generated.update(card["activity"] for card in session.queue)

        self.assertTrue(generated)
        self.assertFalse(generated - supported)

    def test_reference_library_reuses_lesson_content(self):
        library = PassiveReviewEngine(self.content)
        unit_lesson_ids = [
            self.content.resolve_lesson_id(1, 1, lesson_num)
            for lesson_num in range(1, 5)
        ]
        unit_sheet = library.build_unit_master_sheet(1, 1, unit_lesson_ids)
        self.assertEqual(len(unit_sheet), 4)
        self.assertTrue(any(section["vocab"] for section in unit_sheet.values()))
        self.assertTrue(any(section["phrases"] for section in unit_sheet.values()))
        self.assertTrue(any(section["dialogues"] for section in unit_sheet.values()))

        first_lesson_only = library.build_unit_master_sheet(
            1,
            1,
            unit_lesson_ids[:1],
        )
        self.assertFalse(first_lesson_only[1]["locked"])
        self.assertTrue(first_lesson_only[2]["locked"])
        self.assertEqual(first_lesson_only[2]["vocab"], [])
        self.assertGreater(first_lesson_only[2]["category_counts"]["phrases"], 0)
        self.assertEqual(first_lesson_only[1]["phase_title"], "Basic Survival")
        self.assertEqual(first_lesson_only[1]["unit_title"], "greeting")

        global_sheet = library.build_global_master_sheet(self.completed)
        self.assertEqual(len(global_sheet), 27)
        self.assertEqual(
            sum(not section["locked"] for section in global_sheet.values()),
            len(self.completed),
        )

    def test_memory_library_uses_nested_named_phase_unit_and_lesson_sections(self):
        first_lesson_id = self.content.resolve_lesson_id(0, 1, 1)
        sheet = PassiveReviewEngine(self.content).build_global_master_sheet(
            [first_lesson_id]
        )
        view = PassiveReviewView(sheet, "Your Learning Path", lambda: None, lambda _: None)
        tabs = find_control(view, ft.Tabs)

        phases = view._grouped_sections()
        self.assertEqual(phases[0]["title"], "Alphabet")
        self.assertEqual(phases[0]["units"][1]["title"], "Vowels")
        self.assertEqual(len(tabs.tabs), 3)

        vocabulary = view._hierarchy("vocab")
        phase_zero_tile = vocabulary.controls[0].content.content
        phase_one_tile = vocabulary.controls[1].content.content
        unit_one_tile = phase_zero_tile.controls[0].content.content
        unit_two_tile = phase_zero_tile.controls[1].content.content
        lesson_one_tile = unit_one_tile.controls[0].content.content

        self.assertEqual(phase_zero_tile.title.value, "Phase 0 — Alphabet")
        self.assertEqual(unit_one_tile.title.value, "Unit 1 — Vowels")
        self.assertEqual(lesson_one_tile.title.value, "Lesson 1")
        self.assertFalse(phase_zero_tile.disabled)
        self.assertTrue(phase_one_tile.disabled)
        self.assertTrue(unit_two_tile.disabled)
        self.assertFalse(phase_one_tile.show_trailing_icon)
        self.assertEqual(phase_one_tile.trailing.name, ft.Icons.LOCK_ROUNDED)
        self.assertEqual(
            vocabulary.controls[0].content.bgcolor,
            TOKENS.colors.phase_surface,
        )
        self.assertEqual(
            phase_zero_tile.controls[0].content.bgcolor,
            TOKENS.colors.unit_surface,
        )
        self.assertEqual(phase_zero_tile.leading.color, TOKENS.colors.text_primary)
        self.assertEqual(unit_one_tile.leading.color, TOKENS.colors.warning)
        self.assertEqual(lesson_one_tile.leading.color, TOKENS.colors.primary)
        self.assertEqual(
            unit_one_tile.controls[0].content.bgcolor,
            TOKENS.colors.lesson_surface,
        )

    def test_unit_memory_library_starts_at_lessons_without_redundant_levels(self):
        lesson_ids = [
            self.content.resolve_lesson_id(1, 1, lesson_num)
            for lesson_num in range(1, 5)
        ]
        sheet = PassiveReviewEngine(self.content).build_unit_master_sheet(
            1,
            1,
            lesson_ids[:1],
        )
        view = PassiveReviewView(sheet, "Phase 1 · Unit 1", lambda: None, lambda _: None)
        vocabulary = view._hierarchy("vocab")

        self.assertEqual(len(vocabulary.controls), 2)
        first_lesson = vocabulary.controls[0].content.content
        locked_lesson = vocabulary.controls[1].content.content
        self.assertEqual(first_lesson.title.value, "Lesson 1")
        self.assertEqual(locked_lesson.title.value, "Lesson 3")
        self.assertTrue(locked_lesson.disabled)
        self.assertEqual(
            vocabulary.controls[0].content.bgcolor,
            TOKENS.colors.lesson_surface,
        )

    def test_unit_memory_library_hides_tabs_absent_from_that_unit(self):
        lesson_id = self.content.resolve_lesson_id(0, 1, 1)
        sheet = PassiveReviewEngine(self.content).build_unit_master_sheet(
            0,
            1,
            [lesson_id],
        )
        view = PassiveReviewView(sheet, "Phase 0 · Unit 1", lambda: None, lambda _: None)
        tabs = find_control(view, ft.Tabs)

        self.assertEqual(len(tabs.tabs), 1)
        self.assertEqual(tabs.tabs[0].text, "📖 Vocabulary")


class UnitReviewAccessTests(unittest.TestCase):
    def test_unit_review_only_draws_from_completed_or_started_lessons(self):
        completed_lesson = ContentDBManager(str(CONTENT_DB)).resolve_lesson_id(1, 1, 1)
        started_lesson = ContentDBManager(str(CONTENT_DB)).resolve_lesson_id(1, 1, 2)

        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "progress.db"
            connection = sqlite3.connect(progress_path)
            connection.executescript("""
                CREATE TABLE lesson_progress (
                    lesson_id INTEGER PRIMARY KEY,
                    is_completed INTEGER
                );
                CREATE TABLE research_activity_log (
                    phase_num INTEGER,
                    unit_num INTEGER,
                    lesson_num INTEGER
                );
                CREATE TABLE srs_registry (
                    content_id INTEGER PRIMARY KEY,
                    next_review_date TEXT,
                    ease_factor REAL,
                    mastery_level INTEGER,
                    repetitions INTEGER
                );
            """)
            connection.execute(
                "INSERT INTO lesson_progress VALUES (?, 1)",
                (completed_lesson,),
            )
            connection.execute(
                "INSERT INTO research_activity_log VALUES (1, 1, 2)"
            )
            connection.commit()
            connection.close()

            session = ReviewSession.__new__(ReviewSession)
            session.db_path = str(CONTENT_DB)
            session.progress_db_path = str(progress_path)
            session.phase_num = 1
            session.unit_num = 1

            selected_ids = set(session._get_review_content_ids(limit=100))

        content_connection = sqlite3.connect(CONTENT_DB)
        placeholders = ",".join("?" for _ in (completed_lesson, started_lesson))
        expected_ids = {
            row[0]
            for row in content_connection.execute(f"""
                SELECT DISTINCT lc.associated_id
                FROM lesson_contents lc
                JOIN lesson_component_types lct
                  ON lc.component_type_id = lct.component_type_id
                WHERE lc.lesson_id IN ({placeholders})
                  AND lct.name = 'monologue'
            """, (completed_lesson, started_lesson))
        }
        future_ids = {
            row[0]
            for row in content_connection.execute("""
                SELECT DISTINCT lc.associated_id
                FROM lesson_contents lc
                JOIN lesson_component_types lct
                  ON lc.component_type_id = lct.component_type_id
                WHERE lc.lesson_id = ? AND lct.name = 'monologue'
            """, (ContentDBManager(str(CONTENT_DB)).resolve_lesson_id(1, 1, 3),))
        }
        content_connection.close()

        self.assertEqual(selected_ids, expected_ids)
        self.assertFalse(selected_ids & (future_ids - expected_ids))


class ApplicationRouteTests(unittest.TestCase):
    def setUp(self):
        self.page = FakePage()
        self.app = GeoLearnApp(self.page)
        self.app.start()

    def test_home_units_lessons_session_and_back_history(self):
        self.assertEqual(self.app.navigator.current_name, "home")
        self.assertIsInstance(self.app.stage.content, HomeView)
        self.assertEqual(len(self.app.stage.content.phases_summary), 2)

        self.app.show_units(1)
        self.assertEqual(self.app.navigator.current_name, "phase:1")
        self.assertIsInstance(self.app.stage.content, UnitsView)
        self.assertEqual(len(self.app.stage.content.units_summary), 4)

        self.app.show_lessons(1, 1)
        self.assertEqual(self.app.navigator.current_name, "unit:1:1")
        self.assertIsInstance(self.app.stage.content, LessonsView)
        self.assertEqual(len(self.app.stage.content.lessons_list), 4)

        with contextlib.redirect_stdout(io.StringIO()):
            self.app.show_lesson_session(1, 1, 1)
        self.assertEqual(self.app.navigator.current_name, "lesson:1:1:1")
        session = find_control(self.app.stage.content, SessionView)
        self.assertIsNotNone(session)
        self.assertTrue(session.engine.queue)

        self.app.navigator.back()
        self.assertEqual(self.app.navigator.current_name, "unit:1:1")
        self.assertIsInstance(self.app.stage.content, LessonsView)

    def test_home_and_unit_tools_use_semantic_action_colors(self):
        home = self.app.stage.content
        self.assertEqual(
            action_card_accent(find_card_by_title(home, "Active Review")),
            TOKENS.colors.warning,
        )
        self.assertEqual(
            action_card_accent(find_card_by_title(home, "Memory Library")),
            TOKENS.colors.primary,
        )
        fun_facts = find_card_by_title(home, "Culture & Fun Facts")
        self.assertEqual(action_card_accent(fun_facts), TOKENS.colors.sunny)
        self.assertEqual(
            fun_facts.content.content.controls[0].content.color,
            TOKENS.colors.on_sunny,
        )

        self.app.show_units(1)
        self.app.show_lessons(1, 1)
        lessons = self.app.stage.content
        self.assertEqual(
            action_card_accent(find_card_by_title(lessons, "Practice Review")),
            TOKENS.colors.warning,
        )
        self.assertEqual(
            action_card_accent(find_card_by_title(lessons, "Reference Materials")),
            TOKENS.colors.primary,
        )

    def test_reference_alphabet_and_culture_routes_are_not_orphaned(self):
        self.app.show_units(1)
        self.app.show_lessons(1, 1)
        self.app.show_unit_passive_review(1, 1)
        self.assertEqual(self.app.navigator.current_name, "library:1:1")
        self.assertIsInstance(self.app.stage.content, PassiveReviewView)
        self.assertTrue(self.app.stage.content.master_sheet)
        self.app.navigator.back()
        self.assertEqual(self.app.navigator.current_name, "unit:1:1")

        self.app.show_home()
        self.app.show_alphabet()
        self.assertEqual(self.app.navigator.current_name, "alphabet")
        self.app.navigator.back()
        self.assertEqual(self.app.navigator.current_name, "home")

        self.app.show_global_passive_review()
        self.assertEqual(self.app.navigator.current_name, "library:global")
        self.assertIsInstance(self.app.stage.content, PassiveReviewView)
        self.assertEqual(len(self.app.stage.content.master_sheet), 27)
        self.app.navigator.back()
        self.assertEqual(self.app.navigator.current_name, "home")

        self.app.show_fun_facts()
        self.assertEqual(self.app.navigator.current_name, "fun_facts")
        self.app.navigator.back()
        self.assertEqual(self.app.navigator.current_name, "home")

    @patch("guimain.ReviewSession", return_value=FakeSessionEngine())
    def test_quick_and_unit_review_routes_reach_session_ui(self, review_session):
        self.app.show_session()
        self.assertEqual(self.app.navigator.current_name, "review:global")
        self.assertIsNotNone(find_control(self.app.stage.content, SessionView))
        review_session.assert_called_with(
            phase_num=None,
            unit_num=None,
            max_items=10,
        )

        self.app.show_home()
        self.app.show_units(1)
        self.app.show_lessons(1, 1)
        self.app.show_unit_review(1, 1)
        self.assertEqual(self.app.navigator.current_name, "review:1:1")
        session = find_control(self.app.stage.content, SessionView)
        self.assertIsNotNone(session)
        review_session.assert_called_with(phase_num=1, unit_num=1, max_items=10)

        session._show_completion_screen()
        home_button = find_control(session.card_stage.content, ft.ElevatedButton)
        self.assertEqual(home_button.text, "Home")
        home_button.on_click(None)
        self.assertEqual(self.app.navigator.current_name, "home")


class SessionCompletionTests(unittest.TestCase):
    def test_completion_rewards_unique_mastered_content_and_links_home(self):
        returned = []
        view = SessionView(
            page=FakePage(),
            engine=FakeSessionEngine(),
            on_return=lambda: returned.append("home"),
        )
        word = {
            "content_id": 1,
            "activity": "mc_geo_to_eng",
            "target": {
                "id": 1,
                "geo": "სახლი",
                "eng": "house",
                "trans": "sakhli",
                "content_type": "word",
            },
        }
        view._record_mastered_content(word)
        view._record_mastered_content({**word, "activity": "audio_dictation"})
        view._record_mastered_content(
            {
                "content_id": 2,
                "activity": "type_georgian",
                "target": {
                    "id": 2,
                    "geo": "დიდი მადლობა",
                    "eng": "thank you very much",
                    "content_type": "phrase",
                },
            }
        )
        view._record_mastered_content(
            {
                "content_id": 3,
                "activity": "type_georgian",
                "is_review_item": True,
                "target": {
                    "id": 3,
                    "geo": "კი",
                    "eng": "yes",
                    "content_type": "word",
                },
            }
        )
        view._record_mastered_content(
            {"content_id": "diag_1", "activity": "dialogue_roleplay_mc", "target": {}}
        )
        view._show_completion_screen()

        completion = view.card_stage.content.content
        trophy, title, score = completion.controls[:3]
        recap = completion.controls[5].content
        actions = completion.controls[6]

        self.assertEqual(trophy.color, TOKENS.colors.sunny)
        self.assertEqual(title.value, "Lesson Completed!")
        self.assertEqual(score.value, "3/3")
        self.assertEqual(completion.controls[3].value, "1 word • 1 phrase • 1 review")
        self.assertEqual(len(recap.controls[0].controls), 3)
        self.assertEqual(actions.controls[0].text, "Home")
        self.assertEqual(actions.controls[0].icon, ft.Icons.HOME_ROUNDED)
        actions.controls[0].on_click(None)
        self.assertEqual(returned, ["home"])


class AlphabetUXTests(unittest.TestCase):
    def setUp(self):
        self.db = AlphabetDB()

    def test_phonetics_letter_chips_center_their_content(self):
        guide = PhoneticsGuideView(self.db, lambda: None)
        chip = guide._letter_chip("ა")

        self.assertEqual(chip.content.alignment, ft.alignment.center)

    def test_alphabet_hub_uses_distinct_activity_accents(self):
        hub = AlphabetPage(lambda: None)
        expected = {
            "Alphabet Gallery": TOKENS.colors.error,
            "Phonetics & Sound Groups": TOKENS.colors.secondary,
            "Georgian Keyboard Practice": TOKENS.colors.primary,
            "Anbani Associations": TOKENS.colors.warning,
            "Listen & Type": TOKENS.colors.success,
        }

        for title, color in expected.items():
            self.assertEqual(action_card_accent(find_card_by_title(hub, title)), color)

    def test_gallery_cards_wrap_as_soon_as_another_fixed_card_fits(self):
        gallery = AlphabetGalleryView(self.db, lambda: None)
        shell = gallery.controls[0]
        page_column = shell.content.controls[0].content
        grid = page_column.controls[1]

        self.assertEqual(len(grid.controls), 33)
        self.assertIsInstance(grid, ft.Row)
        self.assertTrue(grid.wrap)
        self.assertEqual(grid.spacing, gallery.tokens.spacing.md)
        self.assertEqual(
            grid.controls[0].content.width,
            gallery.tokens.dimensions.alphabet_card_width,
        )

    def test_letter_detail_supports_side_controls_and_swiping(self):
        gallery = AlphabetGalleryView(self.db, lambda: None)
        gallery.show_letter_detail(0)
        shell = gallery.controls[0]
        page_column = shell.content.controls[0].content
        carousel = page_column.controls[1]

        self.assertIsInstance(carousel, ft.Row)
        self.assertIsInstance(carousel.controls[1], ft.GestureDetector)
        self.assertTrue(carousel.controls[0].disabled)
        self.assertFalse(carousel.controls[2].disabled)

        carousel.controls[1].on_horizontal_drag_end(
            SimpleNamespace(primary_velocity=-500, velocity_x=-500)
        )
        updated_column = gallery.controls[0].content.controls[0].content
        self.assertTrue(updated_column.controls[2].value.startswith("2 / 33"))
        self.assertEqual(
            updated_column.controls[2].size,
            gallery.tokens.typography.caption,
        )

    def test_anbani_game_uses_large_letter_choices(self):
        game = AnbanGameView(self.db, lambda: None)
        game.start_game()
        page_column = game.controls[0].content.controls[0].content
        option_row = page_column.controls[4]
        continue_button = page_column.controls[-1]

        self.assertEqual(len(option_row.controls), 4)
        self.assertTrue(
            all(
                button.content.size == game.tokens.typography.page_title
                for button in option_row.controls
            )
        )
        self.assertEqual(continue_button.text, "Continue")
        self.assertFalse(continue_button.visible)

    def test_alphabet_typing_reuses_shared_check_and_continue_actions(self):
        game = AlphabetTypingGameView(self.db, lambda: None)
        game.start_game()

        self.assertEqual(game.submit_btn.content.text, "Check answer")
        self.assertEqual(game.next_btn.text, "Continue")
        self.assertFalse(game.next_btn.visible)
        self.assertEqual(
            game.submit_btn.content.width,
            game.next_btn.width,
        )


class DialogueUXTests(unittest.TestCase):
    def test_chat_boxes_explain_that_messages_replay_audio(self):
        live = LiveDialogueView([], lambda _correct: None)
        passive = DialoguePassiveView(
            [["A", "გამარჯობა", "gamarjoba", "Hello", "audio/hello.mp3"]],
            lambda _correct: None,
        )

        live_hint = live.chat_container.content.controls[0]
        passive_hint = passive.controls[1].content.controls[0]
        for hint in (live_hint, passive_hint):
            self.assertEqual(hint.value, "Click a message to hear it again")
            self.assertEqual(hint.size, TOKENS.typography.caption)

    def test_memory_library_dialogues_use_alternating_replayable_chat_bubbles(self):
        played = []
        library = PassiveReviewView(
            {},
            "Memory Library",
            lambda: None,
            played.append,
        )
        rendered = library._dialogues(
            [[
                ["A", "გამარჯობა", "gamarjoba", "Hello", "audio/hello.mp3"],
                ["B", "გაგიმარჯოს", "gagimarjos", "Hello to you", None],
            ]]
        )

        dialogue_column = rendered.controls[0].content.content
        hint = dialogue_column.controls[1]
        chat = dialogue_column.controls[2]
        first_row, second_row = chat.controls
        first_bubble = first_row.controls[1]
        second_bubble = second_row.controls[0]

        self.assertEqual(hint.value, "Click a message to hear it again")
        self.assertIsInstance(first_bubble, ChatBubble)
        self.assertIsInstance(second_bubble, ChatBubble)
        self.assertIsInstance(first_row.controls[0], ft.CircleAvatar)
        self.assertIsInstance(second_row.controls[1], ft.CircleAvatar)
        self.assertEqual(
            first_bubble.content.controls[1].value,
            "gamarjoba — Hello",
        )
        first_bubble.on_click(None)
        self.assertEqual(played, ["audio/hello.mp3"])


class MatchingUXTests(unittest.TestCase):
    def test_match_columns_are_close_and_long_answers_resize(self):
        matrix = MatchMatrix3x3(
            [
                {"id": 1, "geo": "კი", "eng": "Yes"},
                {
                    "id": 2,
                    "geo": "ძალიან დიდი მადლობა დახმარებისთვის",
                    "eng": "Thank you very much for all of your help today",
                },
            ],
            lambda _correct: None,
        )
        grid = matrix.content.controls[2]
        buttons = [button for column in grid.controls for button in column.controls]
        short_button = next(button for button in buttons if button.content.value == "Yes")
        long_button = next(
            button for button in buttons if button.content.value.startswith("Thank you very")
        )

        self.assertTrue(grid.tight)
        self.assertEqual(grid.spacing, TOKENS.spacing.sm)
        self.assertEqual(grid.controls[0].width, 160)
        self.assertGreater(long_button.height, short_button.height)
        self.assertLess(long_button.content.size, short_button.content.size)


if __name__ == "__main__":
    unittest.main()
