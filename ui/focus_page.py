from datetime import datetime
import uuid
import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, PrimaryButton, SecondaryButton


class FocusPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.is_running = False
        self.is_paused = False

        self.current_mode = "focus"  # focus or break
        self.is_waiting_for_next = False

        self.focus_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.remaining_seconds = self.focus_seconds
        self.away_seconds = 0
        self.session_away_seconds = 0
        self.session_elapsed_seconds = 0
        self.cumulative_away_seconds_today = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_header()
        self.create_content()

        self.load_active_task()
        self.update_total_focus_label()
        self.update_away_metric()
        self.refresh_away_card_visibility()
        self.update_queue_progress()
        self.refresh_queue_progress_visibility()

    def create_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 12), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("focus_timer"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(
            self.header,
            self.app.t("focus_subtitle")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

    def create_content(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=36, pady=(4, 30), sticky="nsew")
        self.content.grid_columnconfigure(0, weight=3)
        self.content.grid_columnconfigure(1, weight=2)
        self.content.grid_rowconfigure(0, weight=1)

        self.create_timer_card()
        self.create_side_panel()

    def create_timer_card(self):
        self.timer_card = AppCard(self.content)
        self.timer_card.grid(row=0, column=0, padx=(0, 16), sticky="nsew")
        self.timer_card.grid_columnconfigure(0, weight=1)
        self.timer_card.grid_rowconfigure(4, weight=1)

        self.status_pill = ctk.CTkLabel(
            self.timer_card,
            text=self.app.t("focus_mode"),
            fg_color=COLORS["primary_soft"],
            text_color=COLORS["text"],
            corner_radius=18,
            padx=18,
            pady=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_pill.grid(row=0, column=0, pady=(34, 18))

        self.timer_label = ctk.CTkLabel(
            self.timer_card,
            text=self.format_time(self.remaining_seconds),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=92, weight="bold")
        )
        self.timer_label.grid(row=1, column=0, pady=(8, 4))

        self.timer_hint_label = ctk.CTkLabel(
            self.timer_card,
            text=self.app.t("one_session_at_a_time"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=14)
        )
        self.timer_hint_label.grid(row=2, column=0, pady=(0, 22))

        self.button_frame = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        self.button_frame.grid(row=3, column=0, pady=(8, 34))

        self.start_button = PrimaryButton(
            self.button_frame,
            text=self.app.t("start"),
            command=self.start_timer,
            width=140
        )
        self.start_button.grid(row=0, column=0, padx=8)

        self.pause_button = SecondaryButton(
            self.button_frame,
            text=self.app.t("pause"),
            command=self.pause_timer,
            width=130
        )
        self.pause_button.grid(row=0, column=1, padx=8)

        self.reset_button = SecondaryButton(
            self.button_frame,
            text=self.app.t("reset"),
            command=self.reset_timer,
            width=130
        )
        self.reset_button.grid(row=0, column=2, padx=8)

        self.away_warning_label = ctk.CTkLabel(
            self.timer_card,
            text="",
            text_color=COLORS["orange"],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.away_warning_label.grid(row=4, column=0, pady=(0, 30), sticky="s")

        self.current_task_bar = ctk.CTkFrame(
            self.timer_card,
            fg_color=COLORS["surface"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self.current_task_bar.grid(row=5, column=0, padx=32, pady=(0, 30), sticky="ew")
        self.current_task_bar.grid_columnconfigure(1, weight=1)

        self.current_task_icon = ctk.CTkLabel(
            self.current_task_bar,
            text="📘",
            width=42,
            height=42,
            fg_color=COLORS["primary_soft"],
            text_color=COLORS["text"],
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.current_task_icon.grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=14)

        self.current_task_title = ctk.CTkLabel(
            self.current_task_bar,
            text=self.app.t("no_active_task"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.current_task_title.grid(row=0, column=1, padx=0, pady=(14, 2), sticky="ew")

        self.current_task_detail = ctk.CTkLabel(
            self.current_task_bar,
            text=self.app.t("no_task_selected"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.current_task_detail.grid(row=1, column=1, padx=0, pady=(0, 14), sticky="ew")

        self.task_progress = ctk.CTkProgressBar(
            self.current_task_bar,
            height=8,
            corner_radius=4,
            progress_color=COLORS["primary"],
            fg_color=COLORS["card_soft"]
        )
        self.task_progress.grid(row=0, column=2, rowspan=2, padx=(14, 10), sticky="ew")
        self.task_progress.set(0)

        self.task_progress_label = ctk.CTkLabel(
            self.current_task_bar,
            text="0%",
            text_color=COLORS["soft"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.task_progress_label.grid(row=0, column=3, rowspan=2, padx=(0, 18), pady=14)        

    def create_side_panel(self):
        self.side_panel = ctk.CTkFrame(self.content, fg_color="transparent")
        self.side_panel.grid(row=0, column=1, sticky="nsew")
        self.side_panel.grid_columnconfigure(0, weight=1)

        self.active_task_card = AppCard(self.side_panel)
        self.active_task_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.active_task_card.grid_columnconfigure(0, weight=1)

        self.active_task_heading = ctk.CTkLabel(
            self.active_task_card,
            text=self.app.t("active_task"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.active_task_heading.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.active_task_label = ctk.CTkLabel(
            self.active_task_card,
            text=self.app.t("no_active_task"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
            wraplength=280,
            justify="left"
        )
        self.active_task_label.grid(row=1, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.active_task_detail_label = ctk.CTkLabel(
            self.active_task_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.active_task_detail_label.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="w")

        self.total_focus_card = AppCard(self.side_panel)
        self.total_focus_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.total_focus_card.grid_columnconfigure(0, weight=1)

        self.total_focus_title = ctk.CTkLabel(
            self.total_focus_card,
            text=self.app.t("total_focus_today"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.total_focus_title.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.total_focus_value = ctk.CTkLabel(
            self.total_focus_card,
            text="00:00",
            text_color=COLORS["green"],
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.total_focus_value.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")

        self.away_card = AppCard(self.side_panel)
        self.away_card.grid(row=2, column=0, sticky="ew")
        self.away_card.grid_columnconfigure(0, weight=1)

        self.queue_card = AppCard(self.side_panel)
        self.queue_card.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.queue_card.grid_columnconfigure(0, weight=1)

        self.queue_title = ctk.CTkLabel(
            self.queue_card,
            text=self.app.t("study_queue"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.queue_title.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.queue_value = ctk.CTkLabel(
            self.queue_card,
            text="0 / 0",
            text_color=COLORS["primary"],
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.queue_value.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        self.queue_detail = ctk.CTkLabel(
            self.queue_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        self.queue_detail.grid(row=2, column=0, padx=20, pady=(0, 14), sticky="w")

        self.stop_plan_button = SecondaryButton(
            self.queue_card,
            text=self.app.t("stop_plan"),
            command=self.stop_plan,
            width=140
        )
        self.stop_plan_button.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="w")

        self.away_title = ctk.CTkLabel(
            self.away_card,
            text=self.app.t("away_time"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.away_title.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.away_value = ctk.CTkLabel(
            self.away_card,
            text="--:--",
            text_color=COLORS["orange"],
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.away_value.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")

    def format_time(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def format_hours_minutes(self, seconds):
        total_minutes = seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def load_active_task(self):
        task = self.app.get_active_task()

        if not task:
            self.active_task_label.configure(text=self.app.t("no_active_task"))
            self.active_task_detail_label.configure(text="")

            self.current_task_title.configure(text=self.app.t("no_active_task"))
            self.current_task_detail.configure(text=self.app.t("no_task_selected"))

            self.focus_seconds = 25 * 60
            self.break_seconds = 5 * 60

            if not self.is_running and not self.is_paused:
                self.current_mode = "focus"
                self.remaining_seconds = self.focus_seconds
                self.away_seconds = 0
                self.session_away_seconds = 0
                self.timer_label.configure(text=self.format_time(self.remaining_seconds))
                self.start_button.configure(state="disabled")
                self.task_progress.set(0)
                self.task_progress_label.configure(text="0%")

            return

        subject = self.app.t(task.get("subject", "other"))
        title = task.get("title", "")
        focus_minutes = task.get("focus_minutes", 25)
        break_minutes = task.get("break_minutes", 5)

        self.active_task_label.configure(text=f"{subject} · {title}")
        self.active_task_detail_label.configure(
            text=f"{focus_minutes} {self.app.t('focus_minutes')} · "
                 f"{break_minutes} {self.app.t('break_minutes')}"
        )

        self.current_task_title.configure(text=f"{subject} · {title}")
        self.current_task_detail.configure(
            text=f"{focus_minutes} {self.app.t('focus_minutes')} · "
                 f"{break_minutes} {self.app.t('break_minutes')}"
        )

        self.focus_seconds = focus_minutes * 60
        self.break_seconds = break_minutes * 60

        if not self.is_running and not self.is_paused:
            self.current_mode = "focus"
            self.remaining_seconds = self.focus_seconds
            self.timer_label.configure(text=self.format_time(self.remaining_seconds))
            self.start_button.configure(state="normal")
            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["text"]
            )

        self.update_current_task_progress()

    def start_timer(self):
        if self.is_paused:
            self.is_paused = False
            self.away_seconds = 0
            self.away_warning_label.configure(text="")
            self.update_away_metric()

            self.start_button.configure(text=self.app.t("start"))
            self.update_mode_ui()

        if not self.is_running:
            self.is_running = True
            self.is_waiting_for_next = False
            self.count_down()

    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = True

            self.start_button.configure(text=self.app.t("resume"))
            self.status_pill.configure(
                text=self.app.t("paused"),
                fg_color="#92400E",
                text_color="#FEF3C7"
            )

            self.update_away_timer()

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.is_waiting_for_next = False
        self.away_seconds = 0
        self.session_away_seconds = 0
        self.current_mode = "focus"

        task = self.app.get_active_task()
        if task:
            self.focus_seconds = task.get("focus_minutes", 25) * 60
            self.break_seconds = task.get("break_minutes", 5) * 60
        else:
            self.focus_seconds = 25 * 60
            self.break_seconds = 5 * 60

        self.remaining_seconds = self.focus_seconds

        self.timer_label.configure(text=self.format_time(self.remaining_seconds))
        self.away_warning_label.configure(text="")
        self.start_button.configure(text=self.app.t("start"))

        self.update_mode_ui()
        self.update_away_metric()

    def get_current_mode_total_seconds(self):
        if self.current_mode == "focus":
            return self.focus_seconds
        return self.break_seconds

    def switch_to_break_ready(self):
        self.current_mode = "break"
        self.remaining_seconds = self.break_seconds
        self.update_current_task_progress()
        self.is_waiting_for_next = True
        self.timer_label.configure(text=self.format_time(self.remaining_seconds))
        self.away_warning_label.configure(text=self.app.t("break_ready"))
        self.start_button.configure(text=self.app.t("start_break"))
        self.task_progress.set(0)
        self.task_progress_label.configure(text="0%")
        
        self.update_mode_ui()

        auto_start_break = self.app.app_data.get("settings", {}).get("auto_start_break", False)
        if auto_start_break:
            self.start_timer()

    def switch_to_focus_ready(self):
        self.current_mode = "focus"
        self.remaining_seconds = self.focus_seconds
        self.is_waiting_for_next = True
        self.timer_label.configure(text=self.format_time(self.remaining_seconds))
        self.away_warning_label.configure(text=self.app.t("focus_ready"))
        self.start_button.configure(text=self.app.t("start_focus"))

        self.task_progress.set(0)
        self.task_progress_label.configure(text="0%")
        self.update_current_task_progress()

        self.update_mode_ui()

        auto_start_focus = self.app.app_data.get("settings", {}).get("auto_start_focus", False)
        if auto_start_focus:
            self.start_timer()

    def update_mode_ui(self):
        if self.current_mode == "focus":
            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["text"]
            )
        else:
            self.status_pill.configure(
                text=self.app.t("break_mode"),
                fg_color="#065F46",
                text_color="#D1FAE5"
            )

    def count_down(self):
        if self.is_running and self.remaining_seconds > 0:
            self.timer_label.configure(text=self.format_time(self.remaining_seconds))
            self.update_current_task_progress()
            self.remaining_seconds -= 1
            self.after(1000, self.count_down)

        elif self.is_running and self.remaining_seconds <= 0:
            self.update_current_task_progress()
            self.is_running = False
            self.timer_label.configure(text="00:00")

            if self.current_mode == "focus":
                self.away_warning_label.configure(text=self.app.t("focus_completed"))

                self.update_queue_progress()

                self.status_pill.configure(
                    text=self.app.t("completed_status"),
                    fg_color="#065F46",
                    text_color="#D1FAE5"
                )

                active_task = self.app.get_active_task()
                active_task_id = active_task.get("id") if active_task else None

                self.app.app_data["total_focus_seconds_today"] = (
                    self.app.app_data.get("total_focus_seconds_today", 0)
                    + self.focus_seconds
                )

                self.log_focus_session()

                if self.app.app_data.get("queue_mode_active", False):
                    self.app.mark_task_completed(active_task_id)

                self.app.save_app_data()
                self.update_total_focus_label()

                if hasattr(self.app, "statistics_page"):
                    self.app.statistics_page.refresh_stats()

                self.session_away_seconds = 0
                self.away_seconds = 0
                self.update_away_metric()

                self.switch_to_break_ready()

            else:
                self.away_warning_label.configure(text=self.app.t("break_completed"))

                if self.app.app_data.get("queue_mode_active", False):
                    moved_to_next_task = self.app.move_to_next_queue_task()

                    if moved_to_next_task:
                        self.away_warning_label.configure(text=self.app.t("focus_ready"))
                        self.switch_to_focus_ready()
                    else:
                        self.is_running = False
                        self.is_paused = False
                        self.is_waiting_for_next = False
                        self.current_mode = "focus"

                        self.app.app_data["active_task_id"] = None
                        self.app.app_data["queue_mode_active"] = False
                        self.app.app_data["queue_task_ids"] = []
                        self.app.save_app_data()

                        self.load_active_task()
                        self.update_queue_progress()

                        self.timer_label.configure(text=self.format_time(self.remaining_seconds))
                        self.start_button.configure(text=self.app.t("start"))
                        self.status_pill.configure(
                            text=self.app.t("focus_mode"),
                            fg_color=COLORS["primary_soft"],
                            text_color=COLORS["text"]
                        )
                        self.away_warning_label.configure(text=self.app.t("queue_completed"))
                else:
                    self.switch_to_focus_ready()
                    
    def update_away_timer(self):
        if self.is_paused:
            self.away_seconds += 1
            self.session_away_seconds += 1

            if self.away_seconds < 60:
                text = self.app.t(
                    "away_message_seconds",
                    seconds=self.away_seconds
                )
            else:
                away_minutes = self.away_seconds // 60
                text = self.app.t(
                    "away_message_minutes",
                    minutes=away_minutes
                )

            self.away_warning_label.configure(text=text)
            self.update_away_metric()

            self.after(1000, self.update_away_timer)
            
    def update_total_focus_label(self):
        total_seconds = self.app.app_data.get("total_focus_seconds_today", 0)
        self.total_focus_value.configure(text=self.format_hours_minutes(total_seconds))

    def update_away_metric(self):
        cumulative_away = self.get_cumulative_away_seconds_today()

        if cumulative_away <= 0:
            self.away_value.configure(text="--:--")
        else:
            self.away_value.configure(text=self.format_time(cumulative_away))

    def refresh_texts(self):
        self.subtitle_label.configure(text=self.app.t("focus_subtitle"))
        self.title_label.configure(text=self.app.t("focus_timer"))
        self.active_task_heading.configure(text=self.app.t("active_task"))
        self.total_focus_title.configure(text=self.app.t("total_focus_today"))
        self.away_title.configure(text=self.app.t("away_time"))
        self.timer_hint_label.configure(text=self.app.t("one_session_at_a_time"))

        self.queue_title.configure(text=self.app.t("study_queue"))
        self.stop_plan_button.configure(text=self.app.t("stop_plan"))

        if not self.app.get_active_task():
            self.current_task_title.configure(text=self.app.t("no_active_task"))
            self.current_task_detail.configure(text=self.app.t("no_task_selected"))


        if self.is_paused:
            self.status_pill.configure(text=self.app.t("paused"))
            self.start_button.configure(text=self.app.t("resume"))

            if self.away_seconds < 60:
                self.away_warning_label.configure(
                    text=f"{self.away_seconds} sn'dir uzaktasın."
                )
            else:
                away_minutes = self.away_seconds // 60
                self.away_warning_label.configure(
                    text=self.app.t("away_message", minutes=away_minutes)
                )
        else:
            self.update_mode_ui()

            if self.is_waiting_for_next:
                if self.current_mode == "break":
                    self.start_button.configure(text=self.app.t("start_break"))
                else:
                    self.start_button.configure(text=self.app.t("start_focus"))
            else:
                self.start_button.configure(text=self.app.t("start"))

        self.pause_button.configure(text=self.app.t("pause"))
        self.reset_button.configure(text=self.app.t("reset"))

        if not self.is_running and not self.is_paused:
            self.load_active_task()

        self.update_queue_progress()
        self.refresh_queue_progress_visibility()
        self.update_total_focus_label()
        self.update_away_metric()
        self.refresh_away_card_visibility()

    def log_focus_session(self):
        task = self.app.get_active_task()

        if not task:
            return

        session = {
            "id": f"session_{uuid.uuid4().hex[:8]}",
            "task_id": task.get("id") if task else None,
            "task_title": task.get("title") if task else None,
            "subject_id": task.get("subject_id", "subject_other"),
            "subject_name": task.get("subject_name", self.app.t("other_subject")),
            "mode": "focus",
            "source": "study_plan",
            "duration_seconds": self.focus_seconds,
            "away_seconds": self.session_away_seconds,
            "completed_at": datetime.now().isoformat(timespec="seconds")
        }

        self.app.app_data.setdefault("sessions", []).append(session)

    def stop_plan(self):
        self.app.stop_task_queue()
        self.away_warning_label.configure(text=self.app.t("plan_stopped"))

    def get_queue_counts(self):
        tasks = self.app.app_data.get("tasks", [])
        queue_task_ids = self.app.app_data.get("queue_task_ids", [])
        queue_active = self.app.app_data.get("queue_mode_active", False)

        tasks_by_id = {
            task.get("id"): task
            for task in tasks
        }

        if queue_active and queue_task_ids:
            queue_tasks = [
                tasks_by_id[task_id]
                for task_id in queue_task_ids
                if task_id in tasks_by_id
            ]

            total_tasks = len(queue_tasks)
            completed_tasks = len([
                task for task in queue_tasks
                if task.get("status") == "completed"
            ])
            pending_tasks = total_tasks - completed_tasks

            return total_tasks, completed_tasks, pending_tasks

        pending_tasks_list = [
            task for task in tasks
            if task.get("status") != "completed"
        ]

        total_tasks = len(pending_tasks_list)
        completed_tasks = 0
        pending_tasks = total_tasks

        return total_tasks, completed_tasks, pending_tasks
    
    def update_queue_progress(self):
        total_tasks, completed_tasks, pending_tasks = self.get_queue_counts()

        self.queue_value.configure(text=f"{completed_tasks} / {total_tasks}")

        if total_tasks == 0:
            self.queue_detail.configure(text=self.app.t("no_pending_tasks"))
        else:
            self.queue_detail.configure(
                text=f"{pending_tasks} {self.app.t('pending_label_short')}"
            )

        queue_active = self.app.app_data.get("queue_mode_active", False)

        if queue_active:
            self.stop_plan_button.configure(state="normal")
        else:
            self.stop_plan_button.configure(state="disabled")

    def refresh_queue_progress_visibility(self):
        show_queue = self.app.app_data.get("settings", {}).get("show_queue_progress", True)

        if show_queue:
            self.queue_card.grid()
        else:
            self.queue_card.grid_remove()

    def update_current_task_progress(self):
        task = self.app.get_active_task()

        if not task:
            self.task_progress.set(0)
            self.task_progress_label.configure(text="0%")
            self.update_current_task_bar_text()
            return

        total = self.get_current_mode_total_seconds()

        if total <= 0:
            progress = 0
        else:
            elapsed = max(total - self.remaining_seconds, 0)
            progress = min(elapsed / total, 1)

        self.task_progress.set(progress)
        self.task_progress_label.configure(text=f"{int(progress * 100)}%")
        self.update_current_task_bar_text()

    def get_cumulative_away_seconds_today(self):
        from datetime import date

        today_str = date.today().isoformat()
        today_sessions = []

        for session in self.app.app_data.get("sessions", []):
            completed_at = session.get("completed_at", "")

            if (
                completed_at.startswith(today_str)
                and session.get("mode") == "focus"
            ):
                today_sessions.append(session)

        completed_away = sum(
            session.get("away_seconds", 0)
            for session in today_sessions
        )

        return completed_away + self.session_away_seconds
    
    def update_current_task_bar_text(self):
        task = self.app.get_active_task()

        if not task:
            self.current_task_title.configure(text=self.app.t("no_active_task"))
            self.current_task_detail.configure(text=self.app.t("no_task_selected"))
            return

        subject = self.app.t(task.get("subject", "other"))
        title = task.get("title", "")

        total = self.get_current_mode_total_seconds()
        elapsed = max(total - self.remaining_seconds, 0)

        elapsed_minutes = elapsed // 60
        total_minutes = total // 60

        if self.current_mode == "focus":
            self.current_task_title.configure(
                text=f"{subject} · {title}"
            )
            self.current_task_detail.configure(
                text=f"{elapsed_minutes} / {total_minutes} {self.app.t('minutes_short')} · "
                     f"{self.app.t('focus_mode')}"
            )
        else:
            self.current_task_title.configure(
                text=f"{self.app.t('break_mode')} · {subject}"
            )
            self.current_task_detail.configure(
                text=f"{elapsed_minutes} / {total_minutes} {self.app.t('minutes_short')} · "
                     f"{self.app.t('break_mode')}"
            )

    def refresh_away_card_visibility(self):
        show_away = self.app.app_data.get("settings", {}).get(
            "show_cumulative_away_time",
            True
        )

        if show_away:
            self.away_card.grid()
        else:
            self.away_card.grid_remove()

    def refresh_page(self):
        self.load_active_task()
        self.update_total_focus_label()
        self.update_away_metric()
        self.refresh_away_card_visibility()
        self.update_queue_progress()
        self.refresh_queue_progress_visibility()