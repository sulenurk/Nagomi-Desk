from datetime import datetime, date, timedelta
import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, MetricCard


class StatisticsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_header()
        self.create_metric_grid()
        self.create_goal_card()
        self.create_weekly_card()

        self.refresh_stats()

    def create_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 12), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("statistics"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(
            self.header,
            self.app.t("statistics_subtitle")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

    def create_metric_grid(self):
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.grid(row=1, column=0, padx=36, pady=(12, 12), sticky="ew")

        for col in range(3):
            self.metrics_frame.grid_columnconfigure(col, weight=1)

        self.today_focus_card = MetricCard(
            self.metrics_frame,
            title=self.app.t("today_focus"),
            value="00:00",
            accent_color=COLORS["green"]
        )
        self.today_focus_card.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.sessions_card = MetricCard(
            self.metrics_frame,
            title=self.app.t("completed_sessions"),
            value="0",
            accent_color=COLORS["primary"]
        )
        self.sessions_card.grid(row=0, column=1, padx=10, sticky="ew")

        self.away_card = MetricCard(
            self.metrics_frame,
            title=self.app.t("away_time_total"),
            value="00:00",
            accent_color=COLORS["orange"]
        )
        self.away_card.grid(row=0, column=2, padx=(10, 0), sticky="ew")

    def create_goal_card(self):
        self.goal_card = AppCard(self)
        self.goal_card.grid(row=2, column=0, padx=36, pady=(8, 12), sticky="ew")
        self.goal_card.grid_columnconfigure(0, weight=1)

        self.goal_title = ctk.CTkLabel(
            self.goal_card,
            text=self.app.t("goal_progress"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.goal_title.grid(row=0, column=0, padx=22, pady=(20, 6), sticky="w")

        self.goal_detail = ctk.CTkLabel(
            self.goal_card,
            text="0%",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=14)
        )
        self.goal_detail.grid(row=1, column=0, padx=22, pady=(0, 10), sticky="w")

        self.goal_progress = ctk.CTkProgressBar(
            self.goal_card,
            height=16,
            corner_radius=8,
            progress_color=COLORS["primary"],
            fg_color=COLORS["surface"]
        )
        self.goal_progress.grid(row=2, column=0, padx=22, pady=(0, 24), sticky="ew")
        self.goal_progress.set(0)

    def create_weekly_card(self):
        self.weekly_card = AppCard(self)
        self.weekly_card.grid(row=3, column=0, padx=36, pady=(8, 30), sticky="nsew")
        self.weekly_card.grid_columnconfigure(0, weight=1)

        self.weekly_title = ctk.CTkLabel(
            self.weekly_card,
            text=self.app.t("weekly_overview"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.weekly_title.grid(row=0, column=0, padx=22, pady=(20, 12), sticky="w")

        self.weekly_bars_frame = ctk.CTkFrame(self.weekly_card, fg_color="transparent")
        self.weekly_bars_frame.grid(row=1, column=0, padx=22, pady=(0, 22), sticky="ew")

        for col in range(7):
            self.weekly_bars_frame.grid_columnconfigure(col, weight=1)

        self.weekly_day_widgets = []

        for col in range(7):
            day_frame = ctk.CTkFrame(
                self.weekly_bars_frame,
                fg_color=COLORS["surface"],
                corner_radius=14
            )
            day_frame.grid(row=0, column=col, padx=5, sticky="ew")

            value_label = ctk.CTkLabel(
                day_frame,
                text="0m",
                text_color=COLORS["primary"],
                font=ctk.CTkFont(size=16, weight="bold")
            )
            value_label.grid(row=0, column=0, padx=8, pady=(14, 2))

            day_label = ctk.CTkLabel(
                day_frame,
                text="-",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=12)
            )
            day_label.grid(row=1, column=0, padx=8, pady=(0, 14))

            self.weekly_day_widgets.append((value_label, day_label))

    def get_today_sessions(self):
        today_str = date.today().isoformat()
        sessions = self.app.app_data.get("sessions", [])

        today_sessions = []

        for session in sessions:
            completed_at = session.get("completed_at", "")
            if completed_at.startswith(today_str) and session.get("mode") == "focus":
                today_sessions.append(session)

        return today_sessions

    def get_weekly_focus_seconds(self):
        sessions = self.app.app_data.get("sessions", [])
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        daily_totals = {}

        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            daily_totals[current_day.isoformat()] = 0

        for session in sessions:
            if session.get("mode") != "focus":
                continue

            completed_at = session.get("completed_at", "")

            try:
                session_date = datetime.fromisoformat(completed_at).date()
            except ValueError:
                continue

            key = session_date.isoformat()

            if key in daily_totals:
                daily_totals[key] += session.get("duration_seconds", 0)

        return daily_totals

    def format_hours_minutes(self, seconds):
        total_minutes = seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def refresh_stats(self):
        today_sessions = self.get_today_sessions()

        total_focus_seconds = sum(
            session.get("duration_seconds", 0)
            for session in today_sessions
        )

        total_away_seconds = sum(
            session.get("away_seconds", 0)
            for session in today_sessions
        )

        completed_count = len(today_sessions)

        self.today_focus_card.update(
            title=self.app.t("today_focus"),
            value=self.format_hours_minutes(total_focus_seconds)
        )

        self.sessions_card.update(
            title=self.app.t("completed_sessions"),
            value=str(completed_count)
        )

        self.away_card.update(
            title=self.app.t("away_time_total"),
            value=self.format_hours_minutes(total_away_seconds)
        )

        goal_minutes = self.app.app_data.get("settings", {}).get("daily_focus_goal_minutes", 300)
        goal_seconds = goal_minutes * 60

        if goal_seconds > 0:
            progress = min(total_focus_seconds / goal_seconds, 1)
        else:
            progress = 0

        self.goal_progress.set(progress)

        percent = int(progress * 100)
        total_focus_text = self.format_hours_minutes(total_focus_seconds)
        goal_text = self.format_hours_minutes(goal_seconds)

        self.goal_detail.configure(
            text=f"{percent}% · {total_focus_text} / {goal_text}"
        )

        self.refresh_weekly_overview()

    def refresh_weekly_overview(self):
        daily_totals = self.get_weekly_focus_seconds()

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for index, (day_key, seconds) in enumerate(daily_totals.items()):
            minutes = seconds // 60

            value_label, day_label = self.weekly_day_widgets[index]
            value_label.configure(text=f"{minutes}m")
            day_label.configure(text=day_names[index])

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("statistics"))
        self.subtitle_label.configure(text=self.app.t("statistics_subtitle"))
        self.goal_title.configure(text=self.app.t("goal_progress"))
        self.weekly_title.configure(text=self.app.t("weekly_overview"))

        self.refresh_stats()