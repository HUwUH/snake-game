"""
游戏核心 — 主循环、渲染、碰撞判定、胜负
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Optional, Set

from .config import GameConfig, SNAKE_COLORS
from .snake import Snake, Point
from .food import FoodManager
from .ai import compute_ai_direction


class Game:
    def __init__(
        self,
        root: tk.Tk,
        config: GameConfig,
        on_exit: Callable[[], None],
    ) -> None:
        self.root = root
        self.config = config
        self.on_exit = on_exit
        self.frame: Optional[tk.Frame] = None
        self.canvas: Optional[tk.Canvas] = None

        self.snakes: List[Snake] = []
        self.food_manager: Optional[FoodManager] = None
        self.running = False
        self.finished = False
        self._after_id: Optional[str] = None
        self._speed_ms = config.initial_speed

        # 暂存键盘输入
        self._p1_dir: Optional[str] = None
        self._p2_dir: Optional[str] = None

        # 开局已吃食物计数（用于加速）
        self._total_eaten = 0

        self._setup_ui()
        self._init_game()
        self._bind_keys()

        if not config.start_controlled:
            self.start()

    # ── UI ─────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # 顶部栏：返回按钮 + 分数
        top = tk.Frame(self.frame, bg="#1a1a2e")
        top.pack(fill="x", padx=10, pady=5)

        tk.Button(
            top,
            text="← 返回菜单",
            font=("Arial", 11),
            bg="#16213e",
            fg="white",
            activebackground="#0f3460",
            activeforeground="#4CAF50",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._exit,
        ).pack(side="left")

        self.score_labels: List[tk.StringVar] = []
        score_frame = tk.Frame(top, bg="#1a1a2e")
        score_frame.pack(side="right")
        for i in range(self.config.snake_count):
            color = self.config.colors[i]
            var = tk.StringVar(value=f"● 0")
            lbl = tk.Label(
                score_frame,
                textvariable=var,
                font=("Arial", 12, "bold"),
                fg=color,
                bg="#1a1a2e",
                padx=8,
            )
            lbl.pack(side="left")
            self.score_labels.append(var)

        # 模式名称
        tk.Label(
            self.frame,
            text=self.config.name,
            font=("Arial", 10),
            fg="#888888",
            bg="#1a1a2e",
        ).pack()

        # 画布
        self.canvas = tk.Canvas(
            self.frame,
            width=self.config.canvas_width,
            height=self.config.canvas_height,
            bg="#111111",
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=5)

        # 操作提示
        hints = []
        if self.config.player_count >= 1:
            hints.append("P1: ↑↓←→")
        if self.config.player_count >= 2:
            hints.append("P2: W A S D")
        if self.config.ai_count > 0:
            hints.append(f"AI: {self.config.ai_count} 条")
        tk.Label(
            self.frame,
            text="  |  ".join(hints),
            font=("Arial", 9),
            fg="#555555",
            bg="#1a1a2e",
            pady=3,
        ).pack()

    # ── 初始化 ──────────────────────────────────────────────

    def _init_game(self) -> None:
        self.snakes.clear()
        self._speed_ms = self.config.initial_speed
        self._total_eaten = 0
        self.running = False
        self.finished = False
        self._p1_dir = None
        self._p2_dir = None

        gw = self.config.grid_width
        gh = self.config.grid_height
        length = self.config.initial_length

        # 为每条蛇生成初始位置
        positions = self._starting_positions()
        # 身体延伸方向(相对于头部): 朝移动反方向延伸
        _body_dx: dict[str, int] = {"Right": -1, "Left": 1, "Down": 0, "Up": 0}
        _body_dy: dict[str, int] = {"Right": 0, "Left": 0, "Down": -1, "Up": 1}
        for i in range(self.config.snake_count):
            sx, sy, sdir = positions[i]
            bdx = _body_dx[sdir]
            bdy = _body_dy[sdir]
            body = [(sx + bdx * j, sy + bdy * j) for j in range(length)]
            snake = Snake(
                body=body,
                direction=sdir,
                color=self.config.colors[i],
                player_index=i,
                is_ai=(i >= self.config.player_count),
                config=self.config,
            )
            self.snakes.append(snake)

        self.food_manager = FoodManager(gw, gh, self.config.food_count)
        self.food_manager.spawn_all(self.snakes)
        self._update_score_labels()

    def _starting_positions(self) -> List[tuple]:
        """为每条蛇生成起始位置和方向"""
        gw = self.config.grid_width
        gh = self.config.grid_height
        # 预留边界安全距离
        margin = 5
        spots = [
            (margin, gh // 2, "Right"),                     # 左中 → 右
            (gw - margin - 1, gh // 2, "Left"),             # 右中 → 左
            (gw // 2, margin, "Down"),                       # 上中 → 下
            (gw // 2, gh - margin - 1, "Up"),               # 下中 → 上
            (margin, margin, "Right"),                       # 左上 → 右
        ]
        return spots[: self.config.snake_count]

    # ── 键盘绑定 ────────────────────────────────────────────

    def _bind_keys(self) -> None:
        self.root.bind("<KeyPress>", self._on_key)

    def _on_key(self, event: tk.Event) -> None:
        key = event.keysym

        # P1: 方向键
        p1_map = {"Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right"}
        if key in p1_map and self.config.player_count >= 1:
            self._p1_dir = p1_map[key]
            if not self.running and not self.finished:
                self.start()

        # P2: WASD
        p2_map = {"w": "Up", "s": "Down", "a": "Left", "d": "Right"}
        if key.lower() in p2_map and self.config.player_count >= 2:
            self._p2_dir = p2_map[key.lower()]

        # R 重启
        if key in ("r", "R") and self.finished:
            self._init_game()
            if not self.config.start_controlled:
                self.start()

        # Escape 返回菜单
        if key == "Escape":
            self._exit()

    # ── 开始 / 停止 ─────────────────────────────────────────

    def start(self) -> None:
        if self.running or self.finished:
            return
        self.running = True
        self.canvas.delete("overlay")
        self._tick()

    def stop(self) -> None:
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _exit(self) -> None:
        self.stop()
        # 解绑按键, 避免干扰菜单
        self.root.unbind("<KeyPress>")
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self.on_exit()

    # ── 主循环 ──────────────────────────────────────────────

    def _tick(self) -> None:
        if not self.running:
            return

        # 1. 处理玩家输入
        self._apply_player_inputs()

        # 2. AI 计算方向
        self._compute_ai()

        # 3. 计算新头部位置
        new_heads: Dict[Snake, Point] = {}
        wrap_w = self.config.grid_width if self.config.wrap_borders else -1
        wrap_h = self.config.grid_height if self.config.wrap_borders else -1
        for s in self.snakes:
            if s.alive:
                new_heads[s] = s.compute_new_head(wrap_w, wrap_h)

        # 4. 碰撞检测(用移动前的身体检测)
        dead_set: Set[Snake] = set()

        # 4a. 边界碰撞
        if not self.config.wrap_borders:
            for s, nh in new_heads.items():
                if not (0 <= nh[0] < self.config.grid_width and
                        0 <= nh[1] < self.config.grid_height):
                    dead_set.add(s)

        # 4b. 头部 vs 身体碰撞
        for s, nh in new_heads.items():
            if s in dead_set:
                continue
            for other in self.snakes:
                if not other.alive:
                    continue
                # 检查 nh 是否撞到 other 的当前身体
                # 如果是自己, 跳过头部(蛇头离开原位置)
                body_to_check = other.body[1:] if other is s else other.body
                if nh in body_to_check:
                    dead_set.add(s)
                    break

        # 4c. 头碰头
        head_map: Dict[Point, List[Snake]] = {}
        for s, nh in new_heads.items():
            if s not in dead_set:
                head_map.setdefault(nh, []).append(s)
        for group in head_map.values():
            if len(group) > 1:
                dead_set.update(group)

        # 5. 标记死亡
        for s in dead_set:
            s.alive = False

        # 6. 存活蛇移动
        for s in self.snakes:
            if s.alive:
                nh = new_heads[s]
                # 检查是否吃到食物
                ate = nh in (self.food_manager.positions if self.food_manager else [])
                s.apply_move(nh, ate)

        # 7. 移除被吃掉的食物并刷新
        if self.food_manager:
            eaten = self.food_manager.remove_eaten(self.snakes)
            new_eaten = len(eaten)
            if new_eaten > 0:
                self._total_eaten += new_eaten
                # 加速
                self._speed_ms = max(
                    self.config.min_speed,
                    self.config.initial_speed - self._total_eaten * self.config.speed_step,
                )
                self.food_manager.spawn_all(self.snakes)

        # 8. 更新分数
        self._update_score_labels()

        # 9. 检查胜负
        self._check_game_over()

        # 10. 渲染
        self._render()

        # 11. 下一 tick
        if self.running:
            self._after_id = self.root.after(self._speed_ms, self._tick)

    # ── 输入处理 ────────────────────────────────────────────

    def _apply_player_inputs(self) -> None:
        if self._p1_dir and self.config.player_count >= 1 and len(self.snakes) > 0:
            self.snakes[0].set_direction(self._p1_dir)
            self._p1_dir = None
        if self._p2_dir and self.config.player_count >= 2 and len(self.snakes) > 1:
            self.snakes[1].set_direction(self._p2_dir)
            self._p2_dir = None

    def _compute_ai(self) -> None:
        food_pos = self.food_manager.positions if self.food_manager else []
        for s in self.snakes:
            if s.alive and s.is_ai:
                new_dir = compute_ai_direction(
                    s, food_pos, self.snakes,
                    self.config.grid_width, self.config.grid_height,
                    self.config.wrap_borders,
                )
                s.set_direction(new_dir)

    # ── 胜负判定 ────────────────────────────────────────────

    def _check_game_over(self) -> None:
        alive = [s for s in self.snakes if s.alive]

        # 经典模式: 蛇死即结束
        if not self.config.wrap_borders:
            if len(alive) < self.config.snake_count:
                self._end_game("游戏结束！得分: ")
            return

        # 对战模式: 只剩一条蛇或全灭
        if len(alive) <= 1:
            self._end_game(None)

    def _end_game(self, message: Optional[str]) -> None:
        self.running = False
        self.finished = True

        if message:
            # 经典模式
            score = self.snakes[0].score if self.snakes else 0
            text = f"{message}{score}\n按 R 重新开始 | ESC 返回菜单"
        else:
            # 对战模式: 找出赢家
            alive = [s for s in self.snakes if s.alive]
            if len(alive) == 1:
                winner = alive[0]
                label = f"P{winner.player_index + 1}" if not winner.is_ai else f"AI {winner.player_index}"
                text = f"{label} 获胜！\n按 R 重新开始 | ESC 返回菜单"
            else:
                text = f"全员阵亡！\n按 R 重新开始 | ESC 返回菜单"

        self.canvas.delete("overlay")
        self.canvas.create_text(
            self.config.canvas_width // 2,
            self.config.canvas_height // 2,
            text=text,
            fill="white",
            font=("Arial", 18, "bold"),
            tags="overlay",
        )

    # ── 渲染 ────────────────────────────────────────────────

    def _render(self) -> None:
        self.canvas.delete("all")
        self._render_grid()
        self._render_food()
        self._render_snakes()

    def _render_grid(self) -> None:
        cs = self.config.cell_size
        w = self.config.canvas_width
        h = self.config.canvas_height
        for x in range(0, w, cs):
            self.canvas.create_line(x, 0, x, h, fill="#1a1a2e")
        for y in range(0, h, cs):
            self.canvas.create_line(0, y, w, y, fill="#1a1a2e")

    def _render_snakes(self) -> None:
        cs = self.config.cell_size
        for s in self.snakes:
            if not s.alive:
                continue
            for i, (x, y) in enumerate(s.body):
                px = x * cs + 1
                py = y * cs + 1
                size = cs - 2
                if i == 0:
                    color = s.color
                else:
                    # 身体渐暗
                    intensity = max(0.5, 1 - i * 0.015)
                    # 简单取色: 在原始颜色基础上调暗
                    color = self._dim_color(s.color, intensity)
                self.canvas.create_rectangle(
                    px, py, px + size, py + size,
                    fill=color, outline="",
                )

    def _render_food(self) -> None:
        cs = self.config.cell_size
        for fx, fy in (self.food_manager.positions if self.food_manager else []):
            px = fx * cs + 2
            py = fy * cs + 2
            r = cs // 2 - 2
            self.canvas.create_oval(
                px, py, px + r * 2, py + r * 2,
                fill="#FF5252", outline="",
            )

    @staticmethod
    def _dim_color(hex_color: str, factor: float) -> str:
        """将十六进制颜色调暗 factor 倍(0~1)"""
        hex_color = hex_color.lstrip("#")
        r = int(int(hex_color[0:2], 16) * factor)
        g = int(int(hex_color[2:4], 16) * factor)
        b = int(int(hex_color[4:6], 16) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── 分数 ────────────────────────────────────────────────

    def _update_score_labels(self) -> None:
        for i, s in enumerate(self.snakes):
            if i < len(self.score_labels):
                status = "💀" if not s.alive else "●"
                self.score_labels[i].set(f"{status} {s.score}")
