"""
AI 逻辑 — BFS 洪泛 + 空间控制 (Battlesnake 方案)

核心思路:
  每 tick, 对每个安全方向模拟一步移动,
  用 BFS 计算移动后自己和对手的可达空间,
  选"扩张自己空间 + 压缩对手空间"得分最高的方向。

攻击性自然涌现: 压缩对手空间 → 包围 → 击杀。
"""

from __future__ import annotations

from collections import deque
from typing import List, Set, Dict, Tuple, Optional, TYPE_CHECKING

from .snake import DIR_VECTORS

if TYPE_CHECKING:
    from .snake import Snake

Point = Tuple[int, int]

_OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}

# ── 评分权重(可在 config.py 覆盖) ─────────────────────────
WEIGHT_SPACE_SELF = 1.5      # 自己每格可达空间的价值
WEIGHT_SPACE_OPP = -0.9      # 每格对手可达空间的负分(压缩对手=正收益)
WEIGHT_FOOD = 25.0           # 接近食物的奖励
WEIGHT_DEATH = -100000       # 致死方向的惩罚(绝对值极大)
WEIGHT_OPP_KILL = 800.0      # 此方向能导致对手死亡的奖励
WEIGHT_STRAIGHT = 0.8        # 保持直行的奖励(减少无意义转弯)


def compute_ai_direction(
    snake: "Snake",
    food_positions: List[Point],
    all_snakes: List["Snake"],
    grid_width: int,
    grid_height: int,
    wrap: bool,
) -> str:
    """
    为 AI 蛇计算下一帧方向。

    对 4 个方向逐个模拟:
      1. 构建移动后的临时身体和障碍集
      2. BFS 计算自己的可达空间
      3. BFS 计算每个对手的可达空间
      4. 综合评分(空间 + 食物 + 安全 + 是否击杀对手)
    返回得分最高的方向。
    """
    head = snake.head
    alive_opponents = [s for s in all_snakes if s.alive and s is not snake]
    default_result = snake.direction

    best_dir = default_result
    best_score = float("-inf")

    for d in ("Up", "Down", "Left", "Right"):
        if d == _OPPOSITE.get(snake.direction, ""):
            continue  # 禁止 180° 掉头

        # ── 计算新头部位置 ──
        dx, dy = DIR_VECTORS[d]
        nh = (head[0] + dx, head[1] + dy)
        if wrap:
            nh = (nh[0] % grid_width, nh[1] % grid_height)
        elif not (0 <= nh[0] < grid_width and 0 <= nh[1] < grid_height):
            continue  # 经典模式出界 → 不可选

        # ── 检查是否立即致死 ──
        would_eat = nh in food_positions
        my_new_body = _simulated_body(snake, nh, ate_food=would_eat)

        if _is_lethal(nh, my_new_body, all_snakes, snake):
            # 致死方向: 打分极低, 但仍录入(万一无路可走时兜底)
            if best_score <= WEIGHT_DEATH:
                best_score = WEIGHT_DEATH
                best_dir = d
            continue

        # ── 构建模拟障碍集 ──
        obstacles = _build_obstacles_for_sim(my_new_body, all_snakes, snake)

        # ── BFS: 自己的可达空间 ──
        my_space = _bfs_flood(nh, obstacles, grid_width, grid_height, wrap)

        # ── BFS: 每个对手的可达空间 ──
        total_opp_space = 0
        opp_killed = False
        for opp in alive_opponents:
            opp_new_body = _simulated_opp_body(opp, food_positions)
            opp_obstacles = _build_obstacles_for_opp(my_new_body, opp_new_body, opp, all_snakes)
            opp_space = _bfs_flood(opp.head, opp_obstacles, grid_width, grid_height, wrap)

            if opp_space == 0:
                # 对手无路可走 → 本方向间接导致对手死亡
                opp_killed = True
            total_opp_space += opp_space

        # ── 综合评分 ──
        score = 0.0

        # 空间项
        score += my_space * WEIGHT_SPACE_SELF
        score += total_opp_space * WEIGHT_SPACE_OPP  # 负权重, 压缩对手加分

        # 食物项: 距最近食物的倒数
        if food_positions:
            nearest_food_dist = min(
                _wrap_dist(nh, f, grid_width, grid_height, wrap)
                for f in food_positions
            )
            score += WEIGHT_FOOD / (nearest_food_dist + 1.0)

        # 击杀奖励
        if opp_killed:
            score += WEIGHT_OPP_KILL

        # 直行奖励(减少抖动)
        if d == snake.direction:
            score += WEIGHT_STRAIGHT

        if score > best_score:
            best_score = score
            best_dir = d

    return best_dir


# ═══════════════════════════════════════════════════════════
#  BFS 洪水填充
# ═══════════════════════════════════════════════════════════

def _bfs_flood(
    start: Point,
    obstacles: Set[Point],
    gw: int,
    gh: int,
    wrap: bool,
    max_cells: int = 9999,
) -> int:
    """返回从 start 出发能到达的空白格数量(不含障碍物)"""
    if start in obstacles:
        return 0

    visited: Set[Point] = set()
    queue: deque[Point] = deque()
    visited.add(start)
    queue.append(start)

    while queue and len(visited) < max_cells:
        x, y = queue.popleft()
        for ddx, ddy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + ddx, y + ddy
            if wrap:
                nx %= gw
                ny %= gh
            elif not (0 <= nx < gw and 0 <= ny < gh):
                continue
            pos = (nx, ny)
            if pos not in visited and pos not in obstacles:
                visited.add(pos)
                queue.append(pos)

    return len(visited)


# ═══════════════════════════════════════════════════════════
#  模拟身体状态
# ═══════════════════════════════════════════════════════════

def _simulated_body(snake: "Snake", new_head: Point, ate_food: bool) -> List[Point]:
    """模拟移动后的完整身体: [new_head, 旧body(去尾或不去)]"""
    tail_slice = -1 if not ate_food else None
    return [new_head] + snake.body[:tail_slice]


def _simulated_opp_body(opp: "Snake", food_positions: List[Point]) -> List[Point]:
    """
    保守预测对手移动后的身体:
    假设对手不吃食物(尾一定会缩, 减少我方的假想障碍)。
    虽然不完全准确, 但让我们对对手空间的估计偏乐观→更安全。
    """
    # 对手的下一个方向未知, 我们悲观假设其身体不变(不移动)
    # 这样对手的 BFS 起点的障碍最密→对手空间最小→我们不会低估危险
    return opp.body[:]


# ═══════════════════════════════════════════════════════════
#  障碍物构建
# ═══════════════════════════════════════════════════════════

def _build_obstacles_for_sim(
    my_new_body: List[Point],
    all_snakes: List["Snake"],
    exclude_me: "Snake",
) -> Set[Point]:
    """
    构建"我自己移动后"的障碍集。
    包含: 我的新身体 + 其他所有活蛇的当前身体(除头部外
          因为头部是 BFS 起点, 不会成为障碍)
    """
    obs: Set[Point] = set(my_new_body)
    for s in all_snakes:
        if s is exclude_me or not s.alive:
            continue
        # 对方头部不作为障碍(它是 BFS 起点, BFS 不会从障碍开始)
        obs.update(s.body)
    return obs


def _build_obstacles_for_opp(
    my_new_body: List[Point],
    opp_body: List[Point],
    opponent: "Snake",
    all_snakes: List["Snake"],
) -> Set[Point]:
    """
    构建"某个对手 BFS 用"的障碍集。
    包含: 我的新身体 + 该对手的身体 + 其他蛇的身体。
    注意: 对手自己的头部不在障碍中(它是 BFS 起点)。
    """
    obs: Set[Point] = set(my_new_body)
    # 该对手自己的身体(不含头)
    obs.update(opp_body[1:])
    # 其他蛇
    for s in all_snakes:
        if s is opponent or not s.alive:
            continue
        obs.update(s.body)
    return obs


# ═══════════════════════════════════════════════════════════
#  碰撞判断
# ═══════════════════════════════════════════════════════════

def _is_lethal(
    new_head: Point,
    my_new_body: List[Point],
    all_snakes: List["Snake"],
    exclude_me: "Snake",
) -> bool:
    """检查 new_head 是否在任何蛇的身体上(立即致死)"""
    # 自己的新身体(跳过 head, 即跳过 new_head 自己)
    if new_head in my_new_body[1:]:
        return True
    # 其他蛇的整个身体(含其头部, 因为撞到对手头也属于身体碰撞)
    for s in all_snakes:
        if s is exclude_me or not s.alive:
            continue
        if new_head in s.body:
            return True
    return False


# ═══════════════════════════════════════════════════════════
#  距离工具
# ═══════════════════════════════════════════════════════════

def _wrap_dist(a: Point, b: Point, gw: int, gh: int, wrap: bool) -> int:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if wrap:
        dx = min(dx, gw - dx)
        dy = min(dy, gh - dy)
    return dx + dy
