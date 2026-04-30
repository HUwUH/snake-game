"""
贪吃蛇 — 入口
"""

import tkinter as tk
from .config import GameConfig
from .menu import Menu
from .game import Game


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("贪吃蛇")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        self._current_view: object = None
        self._show_menu()

    def _show_menu(self) -> None:
        self._current_view = Menu(self.root, self._on_select_mode)

    def _on_select_mode(self, cfg: GameConfig) -> None:
        self._current_view = Game(self.root, cfg, self._show_menu)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
