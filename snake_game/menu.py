"""
主菜单 — 选关界面
"""

import tkinter as tk
from typing import Callable, Optional

from .config import GameConfig
from .modes import classic_config, battle_configs


class Menu:
    def __init__(self, root: tk.Tk, on_start: Callable[[GameConfig], None]) -> None:
        self.root = root
        self.on_start = on_start
        self.frame: Optional[tk.Frame] = None
        self._build()

    def _build(self) -> None:
        self.frame = tk.Frame(self.root, bg="#1a1a2e")
        self.frame.pack(fill="both", expand=True)

        # 标题
        tk.Label(
            self.frame,
            text="贪 吃 蛇",
            font=("Arial", 36, "bold"),
            fg="#4CAF50",
            bg="#1a1a2e",
            pady=30,
        ).pack()

        tk.Label(
            self.frame,
            text="选择模式",
            font=("Arial", 14),
            fg="#aaaaaa",
            bg="#1a1a2e",
            pady=5,
        ).pack()

        # --- 按钮 ---
        btn_frame = tk.Frame(self.frame, bg="#1a1a2e")
        btn_frame.pack()

        all_configs = [classic_config] + battle_configs
        for cfg in all_configs:
            tk.Button(
                btn_frame,
                text=cfg.name,
                font=("Arial", 16, "bold"),
                width=16,
                height=1,
                bg="#16213e",
                fg="white",
                activebackground="#0f3460",
                activeforeground="#4CAF50",
                relief="flat",
                bd=0,
                pady=8,
                cursor="hand2",
                command=lambda c=cfg: self._select(c),
            ).pack(pady=6)

        # 游戏说明按钮
        tk.Button(
            btn_frame,
            text="游戏说明",
            font=("Arial", 13),
            bg="#2a2a3e",
            fg="#aaaaaa",
            activebackground="#3a3a4e",
            activeforeground="white",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self._show_help,
        ).pack(pady=(14, 0))

        # 底部提示
        tk.Label(
            self.frame,
            text="经典模式: 方向键控制  |  对战模式: P1方向键 / P2 WASD",
            font=("Arial", 9),
            fg="#666666",
            bg="#1a1a2e",
            pady=20,
        ).pack()

    def _show_help(self) -> None:
        """弹出游戏说明窗口"""
        help_win = tk.Toplevel(self.root, bg="#1a1a2e")
        help_win.title("游戏说明")
        help_win.resizable(False, False)

        # 居中
        w, h = 520, 520
        sw = help_win.winfo_screenwidth()
        sh = help_win.winfo_screenheight()
        help_win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        instructions = (
            "═══ 操作说明 ═══\n\n"
            "■ 经典模式\n"
            "  · 方向键 ↑↓←→ 控制绿色蛇\n"
            "  · 吃红色食物变长、加速\n"
            "  · 撞墙或撞到自己 → 游戏结束\n"
            "  · 按方向键开始游戏\n\n"
            "■ 对战模式 (穿墙 / 多食物)\n"
            "  · P1: 方向键控制绿色蛇\n"
            "  · P2: W A S D 控制蓝色蛇\n"
            "  · AI: 自动控制其他颜色的蛇\n"
            "  · 穿墙: 出界后从对侧出现\n"
            "  · 蛇头撞到身体 (含自己的) → 死亡\n"
            "  · 两头相撞 → 双方都死亡\n"
            "  · 最后存活者获胜\n\n"
            "■ 通用按键\n"
            "  · ESC → 返回主菜单\n"
            "  · R → 重新开始当前模式\n\n"
            "■ AI 策略\n"
            "  · 默认贪心: 直行吃最近食物\n"
            "  · 保守: 周围危险(多蛇靠近/蛇短)\n"
            "  · 激进: 蛇长优势, 抢夺抢食物"
        )

        tk.Label(
            help_win,
            text=instructions,
            font=("Arial", 12),
            fg="#cccccc",
            bg="#1a1a2e",
            justify="left",
            padx=20,
            pady=20,
        ).pack()

        tk.Button(
            help_win,
            text="知道了",
            font=("Arial", 12, "bold"),
            bg="#16213e",
            fg="white",
            activebackground="#0f3460",
            activeforeground="#4CAF50",
            relief="flat",
            bd=0,
            padx=30,
            pady=6,
            cursor="hand2",
            command=help_win.destroy,
        ).pack(pady=(0, 20))

    def _select(self, cfg: GameConfig) -> None:
        self.destroy()
        self.on_start(cfg)

    def destroy(self) -> None:
        if self.frame:
            self.frame.destroy()
            self.frame = None
