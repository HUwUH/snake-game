"""
蛇实体 — 管理一条蛇的位置、移动、碰撞检测
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from .config import GameConfig


Point = Tuple[int, int]

# 方向向量
DIR_VECTORS = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
}

OPPOSITE = {
    "Up": "Down",
    "Down": "Up",
    "Left": "Right",
    "Right": "Left",
}


class Snake:
    def __init__(
        self,
        body: List[Point],
        direction: str,
        color: str,
        player_index: int,
        is_ai: bool = False,
        config: Optional[GameConfig] = None,
    ) -> None:
        self.body = body[:]
        self.direction = direction
        self.next_direction = direction
        self.color = color
        self.player_index = player_index
        self.is_ai = is_ai
        self.alive = True
        self.score = 0
        self.config = config
        self.grew_this_tick = False

    @property
    def head(self) -> Point:
        return self.body[0]

    def set_direction(self, direction: str) -> None:
        if direction != OPPOSITE.get(self.direction):
            self.next_direction = direction

    def compute_new_head(self, wrap_width: int, wrap_height: int) -> Point:
        dx, dy = DIR_VECTORS[self.next_direction]
        hx, hy = self.head
        new_x = hx + dx
        new_y = hy + dy

        if wrap_width > 0:
            new_x %= wrap_width
        if wrap_height > 0:
            new_y %= wrap_height

        return (new_x, new_y)

    def apply_move(self, new_head: Point, ate_food: bool) -> None:
        self.grew_this_tick = ate_food
        self.direction = self.next_direction
        self.body.insert(0, new_head)
        if not ate_food:
            self.body.pop()
        else:
            self.score += 1

    def reset_grew_flag(self) -> None:
        self.grew_this_tick = False

    def occupies(self, point: Point) -> bool:
        return point in self.body

    def head_collides_with(self, other_body: List[Point]) -> bool:
        return self.head in other_body

    @staticmethod
    def head_on_head(snakes: List[Snake]) -> List[Snake]:
        head_map: dict[Point, List[Snake]] = {}
        for s in snakes:
            if not s.alive:
                continue
            head_map.setdefault(s.head, []).append(s)

        dead: List[Snake] = []
        for group in head_map.values():
            if len(group) > 1:
                dead.extend(group)
        return dead

    def __repr__(self) -> str:
        return f"Snake({self.player_index}, alive={self.alive}, head={self.head})"
