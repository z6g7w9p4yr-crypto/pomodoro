# -*- coding: utf-8 -*-
"""
桌面番茄钟 —— 现代化界面版，用 CustomTkinter 做界面。

功能：
  - 专注 / 休息 计时，一段结束自动切到下一段
  - 圆环倒计时，随时间平滑缩短
  - 时间长度可以自己设置
  - 每段结束时播放提示音
  - 现代深色界面，专注/休息用不同强调色
"""

import threading
import tkinter as tk
import customtkinter as ctk

# winsound 是 Windows 自带的，用来发提示音
try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False


# ---- 外观：整体深色 + 蓝色主题 ----
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# 专注 / 休息 的强调色（圆环 + 标题）
FOCUS_COLOR = "#FF6B6B"   # 专注：珊瑚红
BREAK_COLOR = "#4ECDC4"   # 休息：青绿
RING_TRACK = "#2B2B2B"    # 圆环底槽
CARD_BG = "#1E1E1E"       # 圆环所在画布的底色，跟窗口协调
TEXT_COLOR = "#F5F5F5"

# 圆环几何参数
CANVAS_SIZE = 260
RING_WIDTH = 16
RING_PAD = 22
FULL_ARC = -359.999   # tkinter 画整圈：不能正好 360，负号表示顺时针
SETTING_FONT = ("微软雅黑", 13)


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟")
        self.root.geometry("380x540")
        self.root.resizable(False, False)

        # 计时状态
        self.focus_minutes = 25
        self.break_minutes = 5
        self.is_focus = True
        self.remaining = self.total   # total 由 is_focus 派生，见下方 property
        self.running = False
        self._timer_job = None

        self._build_ui()
        self._apply_phase_style()
        self._update_time_label()

    @property
    def total(self):
        """当前这一段的总秒数，由所处阶段派生，不单独存状态。"""
        mins = self.focus_minutes if self.is_focus else self.break_minutes
        return mins * 60

    # ---------- 界面 ----------
    def _build_ui(self):
        # 阶段标题
        self.phase_label = ctk.CTkLabel(
            self.root, text="专注中",
            font=ctk.CTkFont(family="微软雅黑", size=22, weight="bold"),
        )
        self.phase_label.pack(pady=(28, 10))

        # 圆环倒计时（用画布画弧线）
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_SIZE, height=CANVAS_SIZE,
            highlightthickness=0, bg=CARD_BG,
        )
        self.canvas.pack(pady=6)

        box = (RING_PAD, RING_PAD,
               CANVAS_SIZE - RING_PAD, CANVAS_SIZE - RING_PAD)
        self.track_arc = self.canvas.create_arc(
            *box, start=90, extent=FULL_ARC, style="arc",
            width=RING_WIDTH, outline=RING_TRACK,
        )
        self.progress_arc = self.canvas.create_arc(
            *box, start=90, extent=FULL_ARC, style="arc",
            width=RING_WIDTH, outline=FOCUS_COLOR,
        )
        c = CANVAS_SIZE / 2
        # 初始文字留空，由 __init__ 里的 _update_time_label() 统一填充
        self.time_text = self.canvas.create_text(
            c, c, text="", fill=TEXT_COLOR,
            font=("Consolas", 46, "bold"),
        )

        # 按钮区
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(pady=(14, 6))

        self.start_btn = ctk.CTkButton(
            btn_frame, text="开始", width=90, height=40, corner_radius=20,
            font=ctk.CTkFont(family="微软雅黑", size=14),
            command=self.toggle,
        )
        self.start_btn.grid(row=0, column=0, padx=6)

        self.reset_btn = self._make_secondary_button(btn_frame, "重置", self.reset)
        self.reset_btn.grid(row=0, column=1, padx=6)

        self.skip_btn = self._make_secondary_button(btn_frame, "跳过", self.skip)
        self.skip_btn.grid(row=0, column=2, pme.pack(pady=16, padx=30, fill="x")

        self.focus_var = tk.StringVar(value=str(self.focus_minutes))
        self.break_var = tk.StringVar(value=str(self.break_minutes))
        self._add_duration_setting(setting_frame, "专注", self.focus_var, 0)
        self._add_duration_setting(setting_frame, "休息", self.break_var, 3)

        self.focus_var.trace_add("write", lambda *a: self._on_setting_change())
        self.break_var.trace_add("write", lambda *a: self._on_setting_change())

    def _make_secondary_button(self, parent, text, command):
        """次要按钮（重置/跳过）共用的灰色圆角样式。"""
        return ctk.CTkButton(
            parent, text=text, width=90, height=40, corner_radius=20,
            fg_color="#3A3A3A", hover_color="#4A4A4A",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            command=command,
        )

    def _add_duration_setting(self, parent, text, var, start_col):
        """放一组「<名称> [输入框] 分」控件到设置卡片里。"""
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*SETTING_FONT)).grid(
            row=0, column=start_col, padx=(20, 6), pady=14)
        ctk.CTkEntry(parent, width=50, textvariable=var, justify="center").grid(
            row=0, column=start_col + 1, pady=14)
        ctk.CTkLabel(parent, text="分", font=ctk.CTkFont(*SETTING_FONT)).grid(
            row=0, column=start_col + 2, padx=(4, 20), pady=14)

    def _apply_phase_style(self):
        """根据当前阶段刷新强调色。"""
        color = FOCUS_COLOR if self.is_focus else BREAK_COLOR
        self.canvas.itemconfigure(self.progress_arc, outline=color)
        self.phase_label.configure(
            text="专注中" if self.is_focus else "休息中",
            text_color=color,
        )
        self.start_btn.configure(fg_color=color, hover_color=color)

    # ---------- 计时逻辑 ----------
    def _cancel_timer(self):
        """取消排队中的秒计时（如果有）。"""
        if self._timer_job:
            self.root.after_cancel(self._timer_job)
            self._timer_job = None

    def _advance_phase(self):
        """切到下一段（专注<->休息），重置计时并刷新界面。"""
        self.is_focus = not self.is_focus
        self.remaining = self.total
        self._apply_phase_style()
        self._update_time_label()

    def toggle(self):
        if self.running:
            self.running = False
            self.start_btn.configure(text="继续")
            self._cancel_timer()
        else:
            self.running = True
            self.start_btn.configure(text="暂停")
            self._tick()

    def _tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self._update_time_label()
            self._timer_job = self.root.after(1000, self._tick)
        else:
            self._phase_finished()

    def _phase_finished(self):
        self._play_sound()
        self._advance_phase()
        # 自动继续下一段
        self._timer_job = self.root.after(1000, self._tick)

    def reset(self):
        self.running = False
        self._cancel_timer()
        self.remaining = self.total
        self.start_btn.configure(text="开始")
        self._update_time_label()

    def skip(self):
        self._cancel_timer()
        self._advance_phase()
        if self.running:
            self._tick()

    # ---------- 辅助 ----------
    def _update_time_label(self):
        m, s = divmod(self.remaining, 60)
        self.canvas.itemconfigure(self.time_text, text=f"{m:02d}:{s:02d}")
        frac = self.remaining / self.total if self.total else 0
        # 剩余为 0 时也保留极小的弧，tkinter 不接受 extent 恰好为 0
        extent = FULL_ARC * frac if frac else -0.001
        self.canvas.itemconfigure(self.progress_arc, extent=extent)

    def _on_setting_change(self):
        try:
            f = int(self.focus_var.get())
            b = int(self.break_var.get())
        except ValueError:
            return
        if f < 1 or b < 1:
            return
        self.focus_minutes = f
        self.break_minutes = b
        if not self.running:
            self.remaining = self.total
            self._update_time_label()

    def _play_sound(self):
        """提示音。放到后台线程里，避免 600ms 的 Beep 卡住界面。"""
        if not HAS_SOUND:
            self.root.bell()
            return

        def beep():
            try:
                winsound.Beep(880, 300)
                winsound.Beep(660, 300)
            except RuntimeError:
                self.root.bell()

        threading.Thread(target=beep, daemon=True).start()


def main():
    root = ctk.CTk()
    PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
