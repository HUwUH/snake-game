"""
游戏配置文件 — 所有可调参数集中在此
修改后无需改动其他文件
"""

from dataclasses import dataclass, field
from typing import Optional

# ── 显示参数 ─────────────────────────────────────────────
CELL_SIZE = 20  # 每格像素大小

# ── 经典模式参数 ─────────────────────────────────────────
CLASSIC_GRID_WIDTH = 20
CLASSIC_GRID_HEIGHT = 20

# ── 对战模式参数 ─────────────────────────────────────────
BATTLE_GRID_WIDTH = 30
BATTLE_GRID_HEIGHT = 30
FOOD_COUNT = 4                # 同时存在的食物数量
INITIAL_SPEED_MS = 200        # 初始 tick 间隔(ms)
MIN_SPEED_MS = 80             # 最快速度
SPEED_STEP = 5                # 每吃一个食物减少的 ms

# ── 蛇的颜色（按玩家索引） ──────────────────────────────
SNAKE_COLORS = [
    "#4CAF50",  # 0: P1 绿色
    "#2196F3",  # 1: P2/第一个AI 蓝色
    "#FF9800",  # 2: AI2 橙色
    "#9C27B0",  # 3: AI3 紫色
    "#00BCD4",  # 4: AI4 青色
]

# ── 初始蛇长度 ───────────────────────────────────────────
INITIAL_SNAKE_LENGTH = 3


@dataclass
class GameConfig:
    """单一模式的所有配置"""
    name: str
    grid_width: int
    grid_height: int
    food_count: int
    snake_count: int
    player_count: int       # 人类玩家数(1 或 2)
    ai_count: int            # AI 蛇数
    wrap_borders: bool       # True=穿墙, False=撞墙死
    start_controlled: bool   # True=需按键开始, False=直接开始

    # 可选覆盖
    initial_speed: int = INITIAL_SPEED_MS
    min_speed: int = MIN_SPEED_MS
    speed_step: int = SPEED_STEP
    cell_size: int = CELL_SIZE
    initial_length: int = INITIAL_SNAKE_LENGTH
    colors: tuple = field(default_factory=lambda: tuple(SNAKE_COLORS))

    @property
    def canvas_width(self) -> int:
        return self.grid_width * self.cell_size

    @property
    def canvas_height(self) -> int:
        return self.grid_height * self.cell_size
