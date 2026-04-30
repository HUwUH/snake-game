"""
食物管理器 — 管理多个食物坐标，确保食物只生成在空白位置
"""

from __future__ import annotations

import random
from typing import List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .snake import Snake

Point = Tuple[int, int]


class FoodManager:
    def __init__(self, grid_width: int, grid_height: int, count: int = 1) -> None:
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.count = count
        self.positions: List[Point] = []

    def spawn_all(self, snakes: List[Snake]) -> None:
        """填满所有食物（初始化和被吃掉后补全时调用）"""
        occupied: Set[Point] = set()
        for s in snakes:
            occupied.update(s.body)

        # 也避免食物堆叠
        occupied.update(self.positions)

        while len(self.positions) < self.count:
            pos = (
                random.randrange(self.grid_width),
                random.randrange(self.grid_height),
            )
            if pos not in occupied:
                self.positions.append(pos)
                occupied.add(pos)

    def remove_eaten(self, snakes: List[Snake]) -> List[Point]:
        """检查哪些食物被蛇吃掉了, 返回被吃掉的食物坐标列表"""
        occupied_by_snakes: Set[Point] = set()
        for s in snakes:
            if s.alive:
                occupied_by_snakes.add(s.head)

        eaten: List[Point] = []
        remaining: List[Point] = []
        for pos in self.positions:
            if pos in occupied_by_snakes:
                eaten.append(pos)
            else:
                remaining.append(pos)

        self.positions = remaining
        return eaten

    def remove_all(self) -> None:
        self.positions.clear()
