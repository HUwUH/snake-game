"""
对战模式配置: 穿墙, 多食物, 多蛇
最后存活的蛇获胜
"""

from ..config import GameConfig, BATTLE_GRID_WIDTH, BATTLE_GRID_HEIGHT, FOOD_COUNT


def _battle_config(
    name: str,
    players: int,
    ai_count: int,
) -> GameConfig:
    return GameConfig(
        name=name,
        grid_width=BATTLE_GRID_WIDTH,
        grid_height=BATTLE_GRID_HEIGHT,
        food_count=FOOD_COUNT,
        snake_count=players + ai_count,
        player_count=players,
        ai_count=ai_count,
        wrap_borders=True,
        start_controlled=False,  # 选完就开
    )


battle_configs = [
    _battle_config("双人对战",  players=2, ai_count=0),
    _battle_config("双人 AI",   players=1, ai_count=1),
    _battle_config("三人 AI",   players=1, ai_count=2),
    _battle_config("四人 AI",   players=1, ai_count=3),
]
