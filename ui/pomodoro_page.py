from datetime import datetime
import uuid
import tkinter as tk
import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, PrimaryButton, SecondaryButton, AppEntry

class CircularTimer(ctk.CTkFrame):
    def __init__(self, parent, size=390):
        super().__init__(parent, fg_color="transparent")

        self.size = size
        self.progress = 0

        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=COLORS["card"],
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack()

        self.center = size // 2
        self.radius = 150
        self.ring_width = 20
        self.progress_color = COLORS["primary"]

        self.draw()

    def draw(self):
        self.canvas.delete("all")

        self.canvas.create_oval(
            self.center - self.radius,
            self.center - self.radius,
            self.center + self.radius,
            self.center + self.radius,
            outline="#27314D",
            width=self.ring_width
        )

        extent = self.progress * 360

        self.canvas.create_arc(
            self.center - self.radius,
            self.center - self.radius,
            self.center + self.radius,
            self.center + self.radius,
            start=90,
            extent=-extent,
            style="arc",
            outline=self.progress_color,
            width=self.ring_width
        )

    def set_progress(self, value):
        self.progress = max(0, min(1, value))
        self.draw()

    def set_progress_color(self, color):
        self.progress_color = color
        self.draw()

class PomodoroPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.is_running = False
        self.is_paused = False

        self.current_mode = "focus"  # focus, short_break, long_break
        self.completed_focus_count = 0

        self.focus_seconds = 25 * 60
        self.short_break_seconds = 5 * 60
        self.long_break_seconds = 15 * 60
        self.long_break_after = 4

        self.remaining_seconds = self.focus_seconds

        # Main page grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Scrollable page container
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg"],
            corner_radius=0
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_rowconfigure(1, weight=1)

        self.load_pomodoro_settings()

        self.create_header()
        self.create_content()

        self.update_timer_label()
        self.update_mode_ui()
        self.update_cycle_labels()

    def create_header(self):
        self.header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 12), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("regular_pomodoro"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(
            self.header,
            self.app.t("pomodoro_subtitle")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

    def create_content(self):
        self.content = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=36, pady=(4, 30), sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0, minsize=330)
        self.content.grid_rowconfigure(0, weight=1)

        self.create_timer_card()
        self.create_settings_panel()

    def create_timer_card(self):
        self.timer_card = AppCard(self.content)
        self.timer_card.grid(row=0, column=0, padx=(0, 16), sticky="nsew")
        self.timer_card.grid_columnconfigure(0, weight=1)
        self.timer_card.grid_rowconfigure(1, weight=1)

        self.ring_frame = ctk.CTkFrame(
            self.timer_card,
            fg_color=COLORS["card"],
            width=420,
            height=420
        )
        self.ring_frame.grid(row=0, column=0, pady=(34, 8))
        self.ring_frame.grid_propagate(False)

        self.circular_timer = CircularTimer(self.ring_frame, size=390)
        self.circular_timer.place(relx=0.5, rely=0.5, anchor="center")

        self.mode_pill = ctk.CTkLabel(
            self.ring_frame,
            text="🍅 " + self.app.t("focus_mode"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.mode_pill.place(relx=0.5, rely=0.34, anchor="center")

        self.timer_label = ctk.CTkLabel(
            self.ring_frame,
            text="25:00",
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=50, weight="bold")
        )
        self.timer_label.place(relx=0.5, rely=0.50, anchor="center")

        self.cycle_label = ctk.CTkLabel(
            self.ring_frame,
            text="#1 / 4",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=17, weight="bold")
        )
        self.cycle_label.place(relx=0.5, rely=0.68, anchor="center")

        self.button_frame = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, pady=(8, 22))

        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="▶",
            command=self.start_timer,
            width=72,
            height=72,
            corner_radius=36,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.reset_button = ctk.CTkButton(
            self.button_frame,
            text="↺",
            command=self.reset_timer,
            width=72,
            height=72,
            corner_radius=36,
            fg_color="#27314D",
            hover_color="#334155",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.reset_button.grid(row=0, column=1, padx=10)

        self.skip_button = ctk.CTkButton(
            self.button_frame,
            text="»",
            command=self.skip_session,
            width=72,
            height=72,
            corner_radius=36,
            fg_color="#27314D",
            hover_color="#334155",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=26, weight="bold")
        )
        self.skip_button.grid(row=0, column=2, padx=10)

        self.message_label = ctk.CTkLabel(
            self.timer_card,
            text="",
            text_color=COLORS["orange"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.message_label.grid(row=2, column=0, pady=(0, 26))

    def create_settings_panel(self):
        self.side_panel = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
            width=330
        )
        self.side_panel.grid(row=0, column=1, sticky="nsew")
        self.side_panel.grid_columnconfigure(0, weight=1)

        self.summary_card = AppCard(self.side_panel)
        self.summary_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.summary_card.grid_columnconfigure(0, weight=1)

        self.summary_title = ctk.CTkLabel(
            self.summary_card,
            text=self.app.t("current_cycle"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.summary_title.grid(row=0, column=0, padx=20, pady=(18, 8), sticky="w")

        self.cycle_dots_frame = ctk.CTkFrame(self.summary_card, fg_color="transparent")
        self.cycle_dots_frame.grid(row=1, column=0, padx=20, pady=(0, 14), sticky="w")

        self.cycle_dots = []

        for index in range(4):
            dot = ctk.CTkLabel(
                self.cycle_dots_frame,
                text="●",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=16)
            )
            dot.grid(row=0, column=index, padx=(0, 6))
            self.cycle_dots.append(dot)

        self.focus_info = self.create_session_info_row(
            parent=self.summary_card,
            row=2,
            color="#EF4444",
            label_key="focus_mode",
            value=f"{self.focus_seconds // 60} min"
        )

        self.short_break_info = self.create_session_info_row(
            parent=self.summary_card,
            row=3,
            color="#22C55E",
            label_key="short_break",
            value=f"{self.short_break_seconds // 60} min"
        )

        self.long_break_info = self.create_session_info_row(
            parent=self.summary_card,
            row=4,
            color="#3B82F6",
            label_key="long_break",
            value=f"{self.long_break_seconds // 60} min"
        )

        self.auto_card = AppCard(self.side_panel)
        self.auto_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.auto_card.grid_columnconfigure(0, weight=1)
        self.auto_card.grid_columnconfigure(1, weight=0, minsize=70)

        self.auto_title = ctk.CTkLabel(
            self.auto_card,
            text=self.app.t("auto_start"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.auto_title.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.auto_desc = ctk.CTkLabel(
            self.auto_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="w",
            wraplength=210
        )
        self.auto_desc.grid(row=1, column=0, padx=(20, 8), pady=(0, 18), sticky="ew")
        
        self.auto_switch = ctk.CTkSwitch(
            self.auto_card,
            text="",
            progress_color=COLORS["primary"],
            button_color=COLORS["text"],
            button_hover_color=COLORS["soft"],
            command=self.toggle_auto_start
        )
        self.auto_switch.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(8, 20),
            pady=18,
            sticky="e"
        )

        self.settings_card = AppCard(self.side_panel)
        self.settings_card.grid(row=2, column=0, sticky="ew")
        self.settings_card.grid_columnconfigure(1, weight=1)

        self.settings_title = ctk.CTkLabel(
            self.settings_card,
            text=self.app.t("pomodoro_settings"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.settings_title.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=20,
            pady=(20, 8),
            sticky="w"
        )

        self.save_status_label = ctk.CTkLabel(
            self.settings_card,
            text=" ",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=300,
            justify="left",
            anchor="w"
        )
        self.save_status_label.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=20,
            pady=(0, 10),
            sticky="ew"
        )

        self.focus_label = self.create_form_label(self.settings_card, "focus_duration", row=2)
        self.focus_entry = AppEntry(self.settings_card, width=90)
        self.focus_entry.grid(row=2, column=1, padx=20, pady=8, sticky="e")

        self.short_break_label = self.create_form_label(self.settings_card, "short_break", row=3)
        self.short_break_entry = AppEntry(self.settings_card, width=90)
        self.short_break_entry.grid(row=3, column=1, padx=20, pady=8, sticky="e")

        self.long_break_label = self.create_form_label(self.settings_card, "long_break", row=4)
        self.long_break_entry = AppEntry(self.settings_card, width=90)
        self.long_break_entry.grid(row=4, column=1, padx=20, pady=8, sticky="e")

        self.long_after_label = self.create_form_label(self.settings_card, "long_break_after", row=5)
        self.long_after_entry = AppEntry(self.settings_card, width=90)
        self.long_after_entry.grid(row=5, column=1, padx=20, pady=8, sticky="e")

        self.save_button = PrimaryButton(
            self.settings_card,
            text=self.app.t("save_pomodoro_settings"),
            command=self.save_pomodoro_settings,
            width=220
        )
        self.save_button.grid(
            row=6,
            column=0,
            columnspan=2,
            padx=20,
            pady=(18, 20),
            sticky="ew"
        )
        self.populate_settings_entries()
        self.update_auto_start_info()

    def create_session_info_row(self, parent, row, color, label_key, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=(0, 12), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        dot = ctk.CTkLabel(
            frame,
            text="●",
            text_color=color,
            font=ctk.CTkFont(size=16)
        )
        dot.grid(row=0, column=0, padx=(0, 10))

        label = ctk.CTkLabel(
            frame,
            text=self.app.t(label_key),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        label.grid(row=0, column=1, sticky="w")

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        value_label.grid(row=0, column=2, sticky="e")

        return {
            "frame": frame,
            "dot": dot,
            "label": label,
            "value": value_label
        }

    def create_form_label(self, parent, key, row):
        label = ctk.CTkLabel(
            parent,
            text=self.app.t(key),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        label.grid(row=row, column=0, padx=20, pady=8, sticky="w")
        return label

    def load_pomodoro_settings(self):
        settings = self.app.app_data.setdefault("settings", {})

        self.focus_seconds = settings.get("regular_focus_minutes", 25) * 60
        self.short_break_seconds = settings.get("regular_short_break_minutes", 5) * 60
        self.long_break_seconds = settings.get("regular_long_break_minutes", 15) * 60
        self.long_break_after = settings.get("regular_long_break_after", 4)

        self.remaining_seconds = self.focus_seconds

    def populate_settings_entries(self):
        self.focus_entry.delete(0, "end")
        self.focus_entry.insert(0, str(self.focus_seconds // 60))

        self.short_break_entry.delete(0, "end")
        self.short_break_entry.insert(0, str(self.short_break_seconds // 60))

        self.long_break_entry.delete(0, "end")
        self.long_break_entry.insert(0, str(self.long_break_seconds // 60))

        self.long_after_entry.delete(0, "end")
        self.long_after_entry.insert(0, str(self.long_break_after))

    def save_pomodoro_settings(self):
        try:
            focus_minutes = int(self.focus_entry.get().strip())
            short_break_minutes = int(self.short_break_entry.get().strip())
            long_break_minutes = int(self.long_break_entry.get().strip())
            long_break_after = int(self.long_after_entry.get().strip())

        except ValueError:
            self.save_status_label.configure(
                text=self.app.t("invalid_pomodoro_settings"),
                text_color=COLORS["red"]
            )
            return

        if (
            focus_minutes <= 0
            or short_break_minutes <= 0
            or long_break_minutes <= 0
            or long_break_after <= 0
        ):
            self.save_status_label.configure(
                text=self.app.t("invalid_pomodoro_settings"),
                text_color=COLORS["red"]
            )
            return

        settings = self.app.app_data.setdefault("settings", {})
        settings["regular_focus_minutes"] = focus_minutes
        settings["regular_short_break_minutes"] = short_break_minutes
        settings["regular_long_break_minutes"] = long_break_minutes
        settings["regular_long_break_after"] = long_break_after

        self.focus_seconds = focus_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.long_break_after = long_break_after

        if not self.is_running and not self.is_paused:
            self.current_mode = "focus"
            self.remaining_seconds = self.focus_seconds
            self.completed_focus_count = 0

        self.app.save_app_data()

        self.update_timer_label()
        self.update_mode_ui()
        self.update_cycle_labels()
        self.update_session_info_values()
        self.update_auto_start_info()

        self.save_status_label.configure(
            text=self.app.t("pomodoro_settings_saved"),
            text_color=COLORS["green"]
        )

        self.after(2500, lambda: self.save_status_label.configure(text=" "))

    def format_time(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_timer_label(self):
        self.timer_label.configure(text=self.format_time(self.remaining_seconds))
        self.update_progress_ring()

    def get_current_total_seconds(self):
        if self.current_mode == "focus":
            return self.focus_seconds

        if self.current_mode == "short_break":
            return self.short_break_seconds

        return self.long_break_seconds


    def update_progress_ring(self):
        total = self.get_current_total_seconds()

        if total <= 0:
            progress = 0
        else:
            elapsed = total - self.remaining_seconds
            progress = elapsed / total

        self.circular_timer.set_progress(progress)


    def update_auto_start_info(self):
        settings = self.app.app_data.get("settings", {})
        auto_break = settings.get("auto_start_break", False)
        auto_focus = settings.get("auto_start_focus", False)

        if auto_break and auto_focus:
            text = self.app.t("pomodoro_auto_start_all")
        elif auto_break:
            text = self.app.t("pomodoro_auto_start_break")
        elif auto_focus:
            text = self.app.t("pomodoro_auto_start_focus")
        else:
            text = self.app.t("pomodoro_auto_start_off")

        self.auto_desc.configure(text=text)

        if hasattr(self, "auto_switch"):
            self.update_auto_start_switch()

    def toggle_auto_start(self):
        is_enabled = bool(self.auto_switch.get())

        settings = self.app.app_data.setdefault("settings", {})
        settings["auto_start_break"] = is_enabled
        settings["auto_start_focus"] = is_enabled

        self.app.save_app_data()
        self.update_auto_start_info()

    def update_auto_start_switch(self):
        settings = self.app.app_data.get("settings", {})
        auto_break = settings.get("auto_start_break", False)
        auto_focus = settings.get("auto_start_focus", False)

        if auto_break and auto_focus:
            self.auto_switch.select()
        else:
            self.auto_switch.deselect()

    def update_session_info_values(self):
        self.focus_info["value"].configure(text=f"{self.focus_seconds // 60} min")
        self.short_break_info["value"].configure(text=f"{self.short_break_seconds // 60} min")
        self.long_break_info["value"].configure(text=f"{self.long_break_seconds // 60} min")

    def update_cycle_labels(self):
        cycle_number = (self.completed_focus_count % self.long_break_after) + 1

        self.summary_title.configure(
            text=f"{self.app.t('current_cycle')} {cycle_number} / {self.long_break_after}"
        )

        self.cycle_label.configure(
            text=f"#{cycle_number} / {self.long_break_after}"
        )

        for index, dot in enumerate(self.cycle_dots):
            if index < cycle_number:
                dot.configure(text_color=COLORS["primary"])
            else:
                dot.configure(text_color=COLORS["muted"])

    def update_mode_ui(self):
        if self.current_mode == "focus":
            self.mode_pill.configure(
                text=self.app.t("focus_mode"),
                text_color=COLORS["primary"]
            )
            self.circular_timer.set_progress_color(COLORS["primary"])

        elif self.current_mode == "short_break":
            self.mode_pill.configure(
                text=self.app.t("short_break_mode"),
                text_color="#22C55E"
            )
            self.circular_timer.set_progress_color("#22C55E")

        else:
            self.mode_pill.configure(
                text=self.app.t("long_break_mode"),
                text_color="#3B82F6"
            )
            self.circular_timer.set_progress_color("#3B82F6")

        self.focus_info["dot"].configure(text_color="#EF4444")
        self.short_break_info["dot"].configure(text_color="#22C55E")
        self.long_break_info["dot"].configure(text_color="#3B82F6")

        self.update_progress_ring()

    def start_timer(self):
        if self.is_running:
            self.pause_timer()
            return

        if self.is_paused:
            self.is_paused = False
            self.start_button.configure(text="Ⅱ")
            self.update_mode_ui()

        if not self.is_running:
            self.is_running = True
            self.message_label.configure(text="")
            self.start_button.configure(text="Ⅱ")
            self.count_down()

    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            self.start_button.configure(text="▶")
            self.mode_pill.configure(
                text=self.app.t("paused"),
                text_color="#FEF3C7"
            )

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.current_mode = "focus"
        self.completed_focus_count = 0
        self.remaining_seconds = self.focus_seconds
        self.message_label.configure(text="")
        self.start_button.configure(text="▶")

        self.update_timer_label()
        self.update_mode_ui()
        self.update_cycle_labels()

    def skip_session(self):
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = 0
        self.start_button.configure(text="▶")
        self.count_down()

    def count_down(self):
        if self.is_running and self.remaining_seconds > 0:
            self.update_timer_label()
            self.remaining_seconds -= 1
            self.after(1000, self.count_down)

        elif self.is_running and self.remaining_seconds <= 0:
            self.is_running = False
            self.timer_label.configure(text="00:00")

            if self.current_mode == "focus":
                self.completed_focus_count += 1
                self.log_regular_focus_session()

                self.app.app_data["total_focus_seconds_today"] = (
                    self.app.app_data.get("total_focus_seconds_today", 0)
                    + self.focus_seconds
                )
                self.app.save_app_data()

                if hasattr(self.app, "statistics_page"):
                    self.app.statistics_page.refresh_stats()

                should_long_break = (
                    self.completed_focus_count % self.long_break_after == 0
                )

                if should_long_break:
                    self.current_mode = "long_break"
                    self.remaining_seconds = self.long_break_seconds
                    self.message_label.configure(text=self.app.t("break_ready"))
                else:
                    self.current_mode = "short_break"
                    self.remaining_seconds = self.short_break_seconds
                    self.message_label.configure(text=self.app.t("break_ready"))

                self.update_timer_label()
                self.update_mode_ui()
                self.update_cycle_labels()

                auto_start_break = self.app.app_data.get("settings", {}).get("auto_start_break", False)
                if auto_start_break:
                    self.start_timer()
                else:
                    self.start_button.configure(text="▶")

            else:
                self.current_mode = "focus"
                self.remaining_seconds = self.focus_seconds
                self.message_label.configure(text=self.app.t("focus_ready"))
                self.update_timer_label()
                self.update_mode_ui()
                self.update_cycle_labels()

                auto_start_focus = self.app.app_data.get("settings", {}).get("auto_start_focus", False)
                if auto_start_focus:
                    self.start_timer()
                else:
                    self.start_button.configure(text="▶")

    def log_regular_focus_session(self):
        session = {
            "id": f"session_{uuid.uuid4().hex[:8]}",
            "task_id": None,
            "task_title": "Regular Pomodoro",
            "mode": "focus",
            "source": "regular_pomodoro",
            "duration_seconds": self.focus_seconds,
            "away_seconds": 0,
            "completed_at": datetime.now().isoformat(timespec="seconds")
        }

        self.app.app_data.setdefault("sessions", []).append(session)

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("regular_pomodoro"))
        self.subtitle_label.configure(text=self.app.t("pomodoro_subtitle"))

        self.settings_title.configure(text=self.app.t("pomodoro_settings"))

        self.focus_label.configure(text=self.app.t("focus_duration"))
        self.short_break_label.configure(text=self.app.t("short_break"))
        self.long_break_label.configure(text=self.app.t("long_break"))
        self.long_after_label.configure(text=self.app.t("long_break_after"))

        self.focus_info["label"].configure(text=self.app.t("focus_mode"))
        self.short_break_info["label"].configure(text=self.app.t("short_break"))
        self.long_break_info["label"].configure(text=self.app.t("long_break"))

        self.auto_title.configure(text=self.app.t("auto_start"))

        self.save_button.configure(text=self.app.t("save_pomodoro_settings"))

        self.update_mode_ui()
        self.update_cycle_labels()
        self.update_auto_start_info()
        self.update_session_info_values()