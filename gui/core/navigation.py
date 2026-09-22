"""A small, view-agnostic navigation history for the app's central stage."""

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft


ScreenFactory = Callable[[], ft.Control]


@dataclass(frozen=True)
class ScreenEntry:
    factory: ScreenFactory
    name: str


class NavigationController:
    """Render one screen at a time and provide one authoritative back action."""

    def __init__(self, page: ft.Page, stage: ft.Container):
        self.page = page
        self.stage = stage
        self._history: list[ScreenEntry] = []
        self._current: ScreenEntry | None = None

    @property
    def can_go_back(self) -> bool:
        return bool(self._history)

    @property
    def current_name(self) -> str | None:
        return self._current.name if self._current else None

    def show(
        self,
        factory: ScreenFactory,
        *,
        name: str,
        clear_history: bool = False,
        replace: bool = False,
    ) -> None:
        if clear_history:
            self._history.clear()
        elif self._current is not None and not replace:
            self._history.append(self._current)

        self._current = ScreenEntry(factory=factory, name=name)
        self._render_current()

    def back(self, _event=None) -> None:
        if not self._history:
            return
        self._current = self._history.pop()
        self._render_current()

    def refresh(self) -> None:
        if self._current:
            self._render_current()

    def _render_current(self) -> None:
        if self._current is None:
            return
        self.stage.content = self._current.factory()
        self.page.update()
