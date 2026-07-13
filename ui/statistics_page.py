from datetime import datetime, date, timedelta
import math
import tkinter as tk
import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, MetricCard

class WeeklyLineChart(ctk.CTkFrame):
    def __init__(self, parent, width=760, height=260):
        super().__init__(parent, fg_color=COLORS["surface"], corner_radius=18)

        self.width = width
        self.height = height
        self.labels = []
        self.values = []

        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg=COLORS["surface"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

    def set_data(self, labels, values):
        self.labels = labels
        self.values = values
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        if not self.values:
            return

        padding_left = 48
        padding_right = 24
        padding_top = 34
        padding_bottom = 42

        chart_width = self.width - padding_left - padding_right
        chart_height = self.height - padding_top - padding_bottom

        max_value = max(self.values)

        if max_value <= 0:
            max_value = 1

        # grid lines
        for i in range(4):
            y = padding_top + (chart_height / 3) * i

            self.canvas.create_line(
                padding_left,
                y,
                self.width - padding_right,
                y,
                fill=COLORS["card_soft"],
                width=1
            )

        points = []

        for index, value in enumerate(self.values):
            x = padding_left + (chart_width / 6) * index
            ratio = value / max_value
            y = padding_top + chart_height - (chart_height * ratio)

            points.append((x, y, value))

        # line
        for index in range(len(points) - 1):
            x1, y1, _ = points[index]
            x2, y2, _ = points[index + 1]

            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=COLORS["primary"],
                width=4,
                smooth=True
            )

        # points and labels
        for index, (x, y, value) in enumerate(points):
            self.canvas.create_oval(
                x - 6,
                y - 6,
                x + 6,
                y + 6,
                fill=COLORS["primary"],
                outline=COLORS["white"],
                width=2
            )

            self.canvas.create_text(
                x,
                y - 18,
                text=f"{value}",
                fill=COLORS["text"],
                font=("Arial", 10, "bold")
            )

            self.canvas.create_text(
                x,
                self.height - 22,
                text=self.labels[index],
                fill=COLORS["muted"],
                font=("Arial", 10)
            )
            
class SubjectDonutChart(ctk.CTkFrame):
    def __init__(self, parent, width=260, height=220):
        super().__init__(parent, fg_color=COLORS["surface"], corner_radius=18)

        self.width = width
        self.height = height
        self.data = []
        self.total_minutes = 0
        self.center_text = ""

        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg=COLORS["surface"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

    def set_data(self, data, total_minutes, center_text):
        self.data = data
        self.total_minutes = total_minutes
        self.center_text = center_text
        self.draw()

    def draw_empty_donut(self, cx, cy, x1, y1, x2, y2, inner_radius):
        empty_ring_color = COLORS.get("card_soft", COLORS["surface"])
        border_color = COLORS.get("card_border", COLORS["muted"])

        self.canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            fill=empty_ring_color,
            outline=border_color,
            width=1
        )

        self.canvas.create_oval(
            cx - inner_radius,
            cy - inner_radius,
            cx + inner_radius,
            cy + inner_radius,
            fill=COLORS["surface"],
            outline=border_color,
            width=1
        )

        self.canvas.create_text(
            cx,
            cy - 8,
            text="0",
            fill=COLORS["muted"],
            font=("Arial", 22, "bold")
        )

        self.canvas.create_text(
            cx,
            cy + 18,
            text=self.center_text,
            fill=COLORS["muted"],
            font=("Arial", 11)
        )

    def draw(self):
        self.canvas.delete("all")

        cx = self.width / 2
        cy = self.height / 2
        outer_radius = 78
        inner_radius = 48

        x1 = cx - outer_radius
        y1 = cy - outer_radius
        x2 = cx + outer_radius
        y2 = cy + outer_radius

        if self.total_minutes <= 0 or not self.data:
            self.draw_empty_donut(cx, cy, x1, y1, x2, y2, inner_radius)
            return

        start_angle = 90

        for index, item in enumerate(self.data):
            value = item.get("minutes", 0)
            color = item.get("color", COLORS.get("primary", "#8B5CF6"))

            if value <= 0:
                continue

            extent = -360 * (value / self.total_minutes)

            self.canvas.create_arc(
                x1,
                y1,
                x2,
                y2,
                start=start_angle,
                extent=extent,
                fill=color,
                outline=COLORS["surface"],
                width=2
            )

            start_angle += extent

        self.canvas.create_oval(
            cx - inner_radius,
            cy - inner_radius,
            cx + inner_radius,
            cy + inner_radius,
            fill=COLORS["surface"],
            outline=COLORS["surface"]
        )

        self.canvas.create_text(
            cx,
            cy - 8,
            text=str(self.total_minutes),
            fill=COLORS["text"],
            font=("Arial", 22, "bold")
        )

        self.canvas.create_text(
            cx,
            cy + 18,
            text=self.center_text,
            fill=COLORS["muted"],
            font=("Arial", 11)
        )
        
class StatisticsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        self.selected_subject_id = "all"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["card_soft"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_metric_grid()
        self.create_breakdown_card()
        self.create_goal_card()
        self.create_subject_filter_card()
        self.create_subject_distribution_card()
        self.create_weekly_card()
        self.create_recent_sessions_card()

        self.refresh_stats()

    def create_header(self):
        self.header = ctk.CTkFrame(self.scroll, fg_color="transparent")
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
        self.metrics_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
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

    def create_breakdown_card(self):
        self.breakdown_card = AppCard(self.scroll)
        self.breakdown_card.grid(row=2, column=0, padx=36, pady=(8, 12), sticky="ew")
        self.breakdown_card.grid_columnconfigure(0, weight=1)

        self.breakdown_title = ctk.CTkLabel(
            self.breakdown_card,
            text=self.app.t("focus_breakdown"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.breakdown_title.grid(row=0, column=0, padx=22, pady=(20, 12), sticky="w")

        self.breakdown_frame = ctk.CTkFrame(
            self.breakdown_card,
            fg_color="transparent"
        )
        self.breakdown_frame.grid(row=1, column=0, padx=0, pady=(0, 22), sticky="ew")
        for col in range(12):
            self.breakdown_frame.grid_columnconfigure(col, weight=1, uniform="breakdown")
        
        self.study_plan_focus_card = MetricCard(
            self.breakdown_frame,
            title=self.app.t("study_plan_focus"),
            value="00:00",
            accent_color=COLORS["primary"]
        )
        self.study_plan_focus_card.grid(
            row=0,
            column=0,
            columnspan=4,
            padx=(0, 8),
            sticky="ew"
        )
        self.regular_pomodoro_focus_card = MetricCard(
            self.breakdown_frame,
            title=self.app.t("regular_pomodoro_focus"),
            value="00:00",
            accent_color=COLORS["orange"]
        )
        self.regular_pomodoro_focus_card.grid(
            row=0,
            column=4,
            columnspan=3,
            padx=(0, 8),
            sticky="ew"
        )
        self.total_breakdown_focus_card = MetricCard(
            self.breakdown_frame,
            title=self.app.t("total_focus"),
            value="00:00",
            accent_color=COLORS["green"]
        )
        self.total_breakdown_focus_card.grid(
            row=0,
            column=8,
            columnspan=4,
            padx=(10, 22),
            sticky="ew"
        )

    def create_goal_card(self):
        self.goal_card = AppCard(self.scroll)
        self.goal_card.grid(row=3, column=0, padx=36, pady=(8, 12), sticky="ew")
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

    def create_subject_distribution_card(self):
        self.subject_distribution_card = AppCard(self.scroll)
        self.subject_distribution_card.grid(row=4, column=0, padx=36, pady=(8, 12), sticky="ew")
        self.subject_distribution_card.grid_columnconfigure(0, weight=1)

        self.subject_distribution_title = ctk.CTkLabel(
            self.subject_distribution_card,
            text=self.app.t("weekly_subject_distribution"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.subject_distribution_title.grid(
            row=0,
            column=0,
            padx=22,
            pady=(20, 6),
            sticky="w"
        )

        self.subject_distribution_subtitle = ctk.CTkLabel(
            self.subject_distribution_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        self.subject_distribution_subtitle.grid(
            row=1,
            column=0,
            padx=22,
            pady=(0, 12),
            sticky="w"
        )

        self.subject_distribution_content = ctk.CTkFrame(
            self.subject_distribution_card,
            fg_color="transparent"
        )
        self.subject_distribution_content.grid(
            row=2,
            column=0,
            padx=22,
            pady=(0, 22),
            sticky="ew"
        )

        self.subject_distribution_content.grid_columnconfigure(0, weight=0)
        self.subject_distribution_content.grid_columnconfigure(1, weight=1)

        self.subject_donut_chart = SubjectDonutChart(
            self.subject_distribution_content,
            width=260,
            height=220
        )
        self.subject_donut_chart.grid(
            row=0,
            column=0,
            padx=(0, 24),
            pady=(0, 0),
            sticky="nw"
        )

        self.subject_distribution_frame = ctk.CTkFrame(
            self.subject_distribution_content,
            fg_color="transparent"
        )
        self.subject_distribution_frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )
        self.subject_distribution_frame.grid_columnconfigure(0, weight=1)
    
    def get_weekly_subject_minutes_for_donut(self):
        sessions = self.app.app_data.get("sessions", [])
        start_of_week = self.get_week_start_date()
        end_of_week = start_of_week + timedelta(days=7)

        subject_totals = {}

        for session in sessions:
            if session.get("mode") != "focus":
                continue

            completed_at = session.get("completed_at", "")

            try:
                session_date = datetime.fromisoformat(completed_at).date()
            except ValueError:
                continue

            if not (start_of_week <= session_date < end_of_week):
                continue

            subject_name = session.get("subject_name", self.app.t("other_subject"))
            duration_minutes = session.get("duration_seconds", 0) // 60

            subject_totals[subject_name] = subject_totals.get(subject_name, 0) + duration_minutes

        donut_data = [
            {
                "subject_name": subject_name,
                "minutes": minutes
            }
            for subject_name, minutes in subject_totals.items()
            if minutes > 0
        ]

        donut_data.sort(key=lambda item: item["minutes"], reverse=True)

        subject_names = [item["subject_name"] for item in donut_data]
        color_map = self.get_subject_chart_colors(subject_names)

        for item in donut_data:
            item["color"] = color_map[item["subject_name"]]

        return donut_data
    
    def get_subject_chart_colors(self, subject_names):
        palette = [
            "#8B5CF6",  # violet
            "#6366F1",  # indigo
            "#3B82F6",  # blue
            "#06B6D4",  # cyan
            "#14B8A6",  # teal
            "#F59E0B",  # amber
            "#EC4899",  # pink
        ]

        color_map = {}

        for index, subject_name in enumerate(subject_names):
            color_map[subject_name] = palette[index % len(palette)]

        return color_map
    
    def refresh_subject_donut_chart(self):
        if not hasattr(self, "subject_donut_chart"):
            return

        donut_data = self.get_weekly_subject_minutes_for_donut()
        total_minutes = sum(item.get("minutes", 0) for item in donut_data)

        self.subject_donut_chart.set_data(
            data=donut_data,
            total_minutes=total_minutes,
            center_text=self.app.t("minute_short")
        )

    def create_subject_filter_card(self):
        self.subject_filter_card = AppCard(self.scroll)
        self.subject_filter_card.grid(row=5, column=0, padx=36, pady=(8, 12), sticky="ew")
        self.subject_filter_card.grid_columnconfigure(0, weight=1)

        self.subject_filter_title = ctk.CTkLabel(
            self.subject_filter_card,
            text=self.app.t("subject_filter"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.subject_filter_title.grid(row=0, column=0, padx=22, pady=(20, 6), sticky="w")

        self.subject_filter_subtitle = ctk.CTkLabel(
            self.subject_filter_card,
            text=self.app.t("subject_filter_subtitle"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        self.subject_filter_subtitle.grid(row=1, column=0, padx=22, pady=(0, 12), sticky="w")

        self.subject_filter_menu = ctk.CTkOptionMenu(
            self.subject_filter_card,
            values=[
                option["name"]
                for option in self.get_subject_filter_options()
            ],
            width=260,
            height=42,
            fg_color=COLORS["input"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["input_text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            command=self.change_subject_filter
        )
        self.subject_filter_menu.set(self.app.t("all_subjects"))
        self.subject_filter_menu.grid(row=2, column=0, padx=22, pady=(0, 22), sticky="w")

    def create_weekly_card(self):
        self.weekly_card = AppCard(self.scroll)
        self.weekly_card.grid(row=6, column=0, padx=36, pady=(8, 30), sticky="nsew")
        self.weekly_card.grid_columnconfigure(0, weight=1)

        self.weekly_title = ctk.CTkLabel(
            self.weekly_card,
            text=self.app.t("weekly_overview"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.weekly_title.grid(row=0, column=0, padx=22, pady=(20, 6), sticky="w")

        self.weekly_subtitle = ctk.CTkLabel(
            self.weekly_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        self.weekly_subtitle.grid(row=1, column=0, padx=22, pady=(0, 12), sticky="w")

        self.weekly_line_chart = WeeklyLineChart(
            self.weekly_card,
            width=780,
            height=260
        )
        self.weekly_line_chart.grid(row=2, column=0, padx=22, pady=(0, 22), sticky="ew")
        
    def create_recent_sessions_card(self):
        self.recent_card = AppCard(self.scroll)
        self.recent_card.grid(row=7, column=0, padx=36, pady=(8, 30), sticky="ew")
        self.recent_card.grid_columnconfigure(0, weight=1)

        self.recent_title = ctk.CTkLabel(
            self.recent_card,
            text=self.app.t("recent_sessions"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.recent_title.grid(row=0, column=0, padx=22, pady=(20, 12), sticky="w")

        self.recent_list_frame = ctk.CTkFrame(
            self.recent_card,
            fg_color="transparent"
        )
        self.recent_list_frame.grid(row=1, column=0, padx=22, pady=(0, 22), sticky="ew")
        self.recent_list_frame.grid_columnconfigure(0, weight=1)

    def get_subject_filter_options(self):
        subjects = self.app.app_data.get("subjects", [])

        options = [
            {
                "id": "all",
                "name": self.app.t("all_subjects")
            }
        ]

        for subject in subjects:
            options.append({
                "id": subject.get("id", "subject_other"),
                "name": subject.get("name", self.app.t("other_subject"))
            })

        return options
    
    def change_subject_filter(self, selected_name):
        selected_id = "all"

        for option in self.get_subject_filter_options():
            if option["name"] == selected_name:
                selected_id = option["id"]
                break

        self.selected_subject_id = selected_id
        self.refresh_stats()

    def get_subject_name_by_id(self, subject_id):
        if subject_id == "all":
            return self.app.t("all_subjects")

        for subject in self.app.app_data.get("subjects", []):
            if subject.get("id") == subject_id:
                return subject.get("name", self.app.t("other_subject"))

        return self.app.t("other_subject")

    def get_week_start_date(self):
        today = date.today()
        settings = self.app.app_data.get("settings", {})
        week_start_day = settings.get("week_start_day", "monday")

        if week_start_day == "sunday":
            days_since_sunday = (today.weekday() + 1) % 7
            return today - timedelta(days=days_since_sunday)

        return today - timedelta(days=today.weekday())

    def get_today_sessions(self):
        today_str = date.today().isoformat()
        sessions = self.app.app_data.get("sessions", [])

        today_sessions = []

        for session in sessions:
            completed_at = session.get("completed_at", "")
            if completed_at.startswith(today_str) and session.get("mode") == "focus":
                today_sessions.append(session)

        return today_sessions
    
    def get_today_focus_by_source(self):
        today_sessions = self.get_today_sessions()

        totals = {
            "study_plan": 0,
            "regular_pomodoro": 0
        }

        for session in today_sessions:
            source = session.get("source", "study_plan")

            if source == "regular_pomodoro":
                totals["regular_pomodoro"] += session.get("duration_seconds", 0)
            else:
                totals["study_plan"] += session.get("duration_seconds", 0)

        return totals

    def get_weekly_focus_seconds(self, subject_id="all"):
        sessions = self.app.app_data.get("sessions", [])
        today = date.today()
        start_of_week = self.get_week_start_date()

        daily_totals = {}

        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            daily_totals[current_day.isoformat()] = 0

        for session in sessions:
            if session.get("mode") != "focus":
                continue

            if subject_id != "all" and session.get("subject_id", "subject_other") != subject_id:
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
    
    def get_weekly_focus_by_subject(self):
        sessions = self.app.app_data.get("sessions", [])
        today = date.today()
        start_of_week = self.get_week_start_date()

        subject_totals = {}

        for session in sessions:
            if session.get("mode") != "focus":
                continue

            completed_at = session.get("completed_at", "")

            try:
                session_date = datetime.fromisoformat(completed_at).date()
            except ValueError:
                continue

            if session_date < start_of_week or session_date > today:
                continue

            subject_id = session.get("subject_id", "subject_other")
            subject_name = session.get("subject_name", self.app.t("other_subject"))
            duration_seconds = session.get("duration_seconds", 0)

            if subject_id not in subject_totals:
                subject_totals[subject_id] = {
                    "name": subject_name,
                    "seconds": 0
                }

            subject_totals[subject_id]["seconds"] += duration_seconds

        return subject_totals

    def format_hours_minutes(self, seconds):
        total_minutes = seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def refresh_stats(self):
        self.refresh_subject_filter_menu()
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

        source_totals = self.get_today_focus_by_source()

        study_plan_seconds = source_totals.get("study_plan", 0)
        regular_pomodoro_seconds = source_totals.get("regular_pomodoro", 0)

        self.study_plan_focus_card.update(
            title=self.app.t("study_plan_focus"),
            value=self.format_hours_minutes(study_plan_seconds)
        )

        self.regular_pomodoro_focus_card.update(
            title=self.app.t("regular_pomodoro_focus"),
            value=self.format_hours_minutes(regular_pomodoro_seconds)
        )

        self.total_breakdown_focus_card.update(
            title=self.app.t("total_focus"),
            value=self.format_hours_minutes(total_focus_seconds)
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
        
        self.refresh_subject_donut_chart()
        self.render_subject_distribution()
        self.refresh_weekly_overview()
        self.render_recent_sessions()

    def get_week_day_labels(self):
        settings = self.app.app_data.get("settings", {})
        week_start_day = settings.get("week_start_day", "monday")

        monday_first = [
            self.app.t("day_mon_short"),
            self.app.t("day_tue_short"),
            self.app.t("day_wed_short"),
            self.app.t("day_thu_short"),
            self.app.t("day_fri_short"),
            self.app.t("day_sat_short"),
            self.app.t("day_sun_short"),
        ]

        if week_start_day == "sunday":
            return [
                self.app.t("day_sun_short"),
                self.app.t("day_mon_short"),
                self.app.t("day_tue_short"),
                self.app.t("day_wed_short"),
                self.app.t("day_thu_short"),
                self.app.t("day_fri_short"),
                self.app.t("day_sat_short"),
            ]

        return monday_first

    def refresh_weekly_overview(self):
        daily_totals = self.get_weekly_focus_seconds(self.selected_subject_id)

        day_names = self.get_week_day_labels()
        
        values = [
            seconds // 60
            for seconds in daily_totals.values()
        ]

        weekly_total_minutes = sum(values)

        selected_subject_name = self.get_subject_name_by_id(self.selected_subject_id)

        self.weekly_subtitle.configure(
            text=(
                f"{self.app.t('weekly_total')}: "
                f"{weekly_total_minutes}{self.app.t('minute_short')} · "
                f"{selected_subject_name}"
            )
        )

        self.weekly_line_chart.set_data(day_names, values)

    def refresh_subject_filter_menu(self):
        if not hasattr(self, "subject_filter_menu"):
            return

        options = self.get_subject_filter_options()
        values = [option["name"] for option in options]

        current_name = self.get_subject_name_by_id(self.selected_subject_id)

        self.subject_filter_menu.configure(values=values)

        if current_name in values:
            self.subject_filter_menu.set(current_name)
        else:
            self.selected_subject_id = "all"
            self.subject_filter_menu.set(self.app.t("all_subjects"))

    def render_subject_distribution(self):
        for widget in self.subject_distribution_frame.winfo_children():
            widget.destroy()

        subject_totals = self.get_weekly_focus_by_subject()

        total_seconds = sum(
            item.get("seconds", 0)
            for item in subject_totals.values()
        )

        total_minutes = total_seconds // 60

        self.subject_distribution_subtitle.configure(
            text=f"{self.app.t('weekly_total')}: {total_minutes}{self.app.t('minute_short')}"
        )

        if total_seconds <= 0:
            empty_label = ctk.CTkLabel(
                self.subject_distribution_frame,
                text=self.app.t("no_subject_stats"),
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=14)
            )
            empty_label.grid(row=0, column=0, padx=4, pady=12, sticky="w")

            if hasattr(self, "subject_donut_chart"):
                self.subject_donut_chart.set_data(
                    data=[],
                    total_minutes=0,
                    center_text=self.app.t("minute_short")
                )

            return

        sorted_subjects = sorted(
            subject_totals.values(),
            key=lambda item: item.get("seconds", 0),
            reverse=True
        )

        subject_names = [
            item.get("name", self.app.t("other_subject"))
            for item in sorted_subjects
        ]

        color_map = self.get_subject_chart_colors(subject_names)

        donut_data = []

        for row_index, item in enumerate(sorted_subjects):
            subject_name = item.get("name", self.app.t("other_subject"))
            subject_color = color_map.get(subject_name, "#A78BFA")

            seconds = item.get("seconds", 0)
            minutes = seconds // 60
            ratio = seconds / total_seconds if total_seconds else 0
            percent = int(round(ratio * 100))

            donut_data.append({
                "subject_name": subject_name,
                "minutes": minutes,
                "color": subject_color
            })

            row = ctk.CTkFrame(
                self.subject_distribution_frame,
                fg_color=COLORS["surface"],
                corner_radius=14
            )
            row.grid(row=row_index, column=0, pady=6, sticky="ew")
            row.grid_columnconfigure(2, weight=1)

            color_dot = ctk.CTkLabel(
                row,
                text="●",
                text_color=subject_color,
                font=ctk.CTkFont(size=15)
            )
            color_dot.grid(
                row=0,
                column=0,
                padx=(16, 8),
                pady=(12, 4),
                sticky="w"
            )

            name_label = ctk.CTkLabel(
                row,
                text=subject_name,
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_label.grid(
                row=0,
                column=1,
                padx=(0, 12),
                pady=(12, 4),
                sticky="w"
            )

            value_label = ctk.CTkLabel(
                row,
                text=f"{minutes}{self.app.t('minute_short')} · {percent}%",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=13)
            )
            value_label.grid(
                row=0,
                column=3,
                padx=(12, 16),
                pady=(12, 4),
                sticky="e"
            )

            progress = ctk.CTkProgressBar(
                row,
                height=10,
                corner_radius=8,
                progress_color=subject_color,
                fg_color=COLORS["card_soft"]
            )
            progress.grid(
                row=1,
                column=0,
                columnspan=4,
                padx=16,
                pady=(0, 14),
                sticky="ew"
            )
            progress.set(ratio)

        if hasattr(self, "subject_donut_chart"):
            self.subject_donut_chart.set_data(
                data=donut_data,
                total_minutes=total_minutes,
                center_text=self.app.t("minute_short")
            )

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("statistics"))
        self.subtitle_label.configure(text=self.app.t("statistics_subtitle"))
        self.breakdown_title.configure(text=self.app.t("focus_breakdown"))
        self.goal_title.configure(text=self.app.t("goal_progress"))
        self.subject_filter_title.configure(text=self.app.t("subject_filter"))
        self.subject_filter_subtitle.configure(text=self.app.t("subject_filter_subtitle"))
        self.refresh_subject_filter_menu()
        self.subject_distribution_title.configure(text=self.app.t("weekly_subject_distribution"))
        self.weekly_title.configure(text=self.app.t("weekly_overview"))
        self.recent_title.configure(text=self.app.t("recent_sessions"))
        self.refresh_stats()

    def get_recent_today_sessions(self, limit=5):
        today_sessions = self.get_today_sessions()

        sorted_sessions = sorted(
            today_sessions,
            key=lambda session: session.get("completed_at", ""),
            reverse=True
        )

        return sorted_sessions[:limit]

    def format_session_time(self, iso_datetime):
        try:
            parsed = datetime.fromisoformat(iso_datetime)
            return parsed.strftime("%H:%M")
        except ValueError:
            return "--:--"

    def render_recent_sessions(self):
        for widget in self.recent_list_frame.winfo_children():
            widget.destroy()

        recent_sessions = self.get_recent_today_sessions(limit=5)

        if not recent_sessions:
            self.render_recent_empty_state()
            return

        for row_index, session in enumerate(recent_sessions):
            item = RecentSessionItem(self.recent_list_frame, self.app, session)
            item.grid(row=row_index, column=0, pady=6, sticky="ew")

    def render_recent_empty_state(self):
        empty_frame = ctk.CTkFrame(
            self.recent_list_frame,
            fg_color=COLORS["surface"],
            corner_radius=16
        )
        empty_frame.grid(row=0, column=0, sticky="ew")
        empty_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            empty_frame,
            text=self.app.t("no_recent_sessions"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        subtitle = ctk.CTkLabel(
            empty_frame,
            text=self.app.t("no_recent_sessions_subtitle"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")

class RecentSessionItem(ctk.CTkFrame):
    def __init__(self, parent, app, session):
        super().__init__(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=16
        )

        self.app = app
        self.session = session

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        source = session.get("source", "study_plan")

        if source == "regular_pomodoro":
            icon_text = "⏱"
            task_title = app.t("regular_pomodoro_session")
            badge_text = app.t("pomodoro_badge")
            badge_color = COLORS["orange"]
        else:
            icon_text = "📘"
            task_title = session.get("task_title") or app.t("default_task_name")
            badge_text = app.t("study_plan_badge")
            badge_color = COLORS["primary"]

        icon = ctk.CTkLabel(
            self,
            text=icon_text,
            width=42,
            height=42,
            fg_color=COLORS["primary_soft"],
            text_color=COLORS["text"],
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        icon.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=14)

        title = ctk.CTkLabel(
            self,
            text=task_title,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title.grid(row=0, column=1, padx=0, pady=(14, 2), sticky="ew")
        badge = ctk.CTkLabel(
            self,
            text=badge_text,
            fg_color=badge_color,
            text_color=COLORS["white"],
            corner_radius=10,
            padx=10,
            pady=4,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        badge.grid(row=0, column=2, padx=(12, 16), pady=(14, 2), sticky="e")

        duration_text = self.format_minutes(session.get("duration_seconds", 0))
        away_text = self.format_minutes(session.get("away_seconds", 0))
        completed_time = self.format_session_time(session.get("completed_at", ""))

        details = ctk.CTkLabel(
            self,
            text=(
                f"{self.app.t('session_duration')}: {duration_text}   ·   "
                f"{self.app.t('session_away')}: {away_text}   ·   "
                f"{completed_time}"
            ),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        details.grid(row=1, column=1, padx=0, pady=(0, 14), sticky="ew")

    def format_minutes(self, seconds):
        minutes = seconds // 60
        return f"{minutes}{self.app.t('minute_short')}"

    def format_session_time(self, iso_datetime):
        try:
            parsed = datetime.fromisoformat(iso_datetime)
            return parsed.strftime("%H:%M")
        except ValueError:
            return "--:--"