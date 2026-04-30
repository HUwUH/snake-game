"""
经典模式配置: 边界即死, 单食物, 单人
"""

from ..config import GameConfig, CLASSIC_GRID_WIDTH, CLASSIC_GRID_HEIGHT

classic_config = GameConfig(
    name="经典模式",
    grid_width=CLASSIC_GRID_WIDTH,
    grid_height=CLASSIC_GRID_HEIGHT,
    food_count=1,
    snake_count=1,
    player_count=1,
    ai_count=0,
    wrap_borders=False,
    start_controlled=True,  # 按方向键开始
)
