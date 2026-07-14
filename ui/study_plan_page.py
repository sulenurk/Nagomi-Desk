import uuid
import customtkinter as ctk
from datetime import datetime
from ui.theme import COLORS
from ui.components import (
    AppCard,
    PageTitle,
    PageSubtitle,
    PrimaryButton,
    SecondaryButton,
    PillButton,
    PriorityBadge,
    SubjectIcon,
    AppEntry,
    MetricCard,
    Tooltip
)

SUBJECT_META = {
    "math": {"icon": "∑"},
    "physics": {"icon": "⚗"},
    "chemistry": {"icon": "🧪"},
    "turkish": {"icon": "📘"},
    "biology": {"icon": "☘"},
    "history": {"icon": "⌛"},
    "geography": {"icon": "🌍"},
    "other": {"icon": "•"},
}


class StudyPlanPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.active_filter = "all_tasks"
        self.editing_task_id = None

        self.subject_options = [
            "math",
            "physics",
            "chemistry",
            "turkish",
            "biology",
            "history",
            "geography",
            "other",
        ]

        self.priority_options = ["low", "medium", "high"]
        self.ensure_subjects_data()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.create_header()
        self.create_summary_cards()
        self.create_filter_bar()
        self.create_action_bar()
        self.create_add_task_card()
        self.create_task_list()
        self.render_tasks()

    def ensure_subjects_data(self):
        subjects = self.app.app_data.setdefault("subjects", [])

        if not subjects:
            subjects.append({
                "id": "subject_other",
                "name": self.app.t("other_subject"),
                "color": COLORS["primary"],
                "is_default": True
            })
            self.app.save_app_data()


    def get_subjects(self):
        self.ensure_subjects_data()
        return self.app.app_data.get("subjects", [])


    def get_subject_names(self):
        return [
            self.app.get_subject_display_name(subject)
            for subject in self.get_subjects()
        ]


    def get_subject_by_name(self, subject_name):
        for subject in self.app.app_data.get("subjects", []):
            if self.app.get_subject_display_name(subject) == subject_name:
                return subject

        return self.get_default_subject()


    def get_subject_by_id(self, subject_id):
        for subject in self.get_subjects():
            if subject.get("id") == subject_id:
                return subject

        return self.get_subjects()[0]

    def create_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30,10), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("study_plan_title"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(self.header, self.app.t("study_plan_subtitle"))
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

        self.start_plan_button = PrimaryButton(
            self.header,
            text=f"▶ {self.app.t('start_plan')}",
            command=self.start_plan,
            width=140
        )
        self.start_plan_button.grid(row=0, column=1, rowspan=2, padx=(0, 150), sticky="e")

        """ self.add_top_button = PrimaryButton(
            self.header,
            text=f"+ {self.app.t('add_task')}",
            command=self.focus_task_name_entry,
            width=130
        )
        self.add_top_button.grid(row=0, column=2, rowspan=2, sticky="e") """
    
    def create_summary_cards(self):
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.grid(row=1, column=0, padx=36, pady=(0, 8), sticky="ew")

        for col in range(4):
            self.summary_frame.grid_columnconfigure(col, weight=1, uniform="summary")

        self.pending_card = MetricCard(
            self.summary_frame,
            title=self.app.t("pending_tasks"),
            value="0"
        )
        self.pending_card.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.active_card = MetricCard(
            self.summary_frame,
            title=self.app.t("active_tasks"),
            value="0"
        )
        self.active_card.grid(row=0, column=1, padx=8, sticky="ew")

        self.completed_card = MetricCard(
            self.summary_frame,
            title=self.app.t("completed_tasks"),
            value="0"
        )
        self.completed_card.grid(row=0, column=2, padx=8, sticky="ew")

        self.total_focus_card = MetricCard(
            self.summary_frame,
            title=self.app.t("total_focus"),
            value="0m"
        )
        self.total_focus_card.grid(row=0, column=3, padx=(8, 0), sticky="ew")
    
    def create_filter_bar(self):
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=2, column=0, padx=36, pady=(16, 12), sticky="w")

        self.filter_buttons = {}

        filters = ["all_tasks", "pending", "active", "completed"]

        for index, filter_key in enumerate(filters):
            button = PillButton(
                self.filter_frame,
                text=self.app.t(filter_key),
                active=(filter_key == self.active_filter),
                command=lambda key=filter_key: self.change_filter(key),
                width=110
            )
            button.grid(row=0, column=index, padx=(0, 10))
            self.filter_buttons[filter_key] = button

    def create_action_bar(self):
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=36, pady=(0, 12), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.clear_completed_button = SecondaryButton(
            self.action_frame,
            text=self.app.t("clear_completed"),
            command=self.clear_completed_tasks,
            width=160
        )
        self.clear_completed_button.grid(row=0, column=1, padx=(8, 0), sticky="e")

        self.reset_all_button = SecondaryButton(
            self.action_frame,
            text=self.app.t("reset_all_tasks"),
            command=self.reset_all_tasks_to_pending,
            width=180
        )
        self.reset_all_button.grid(row=0, column=2, padx=(8, 0), sticky="e")

    def create_task_list(self):
        self.task_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["card_soft"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.task_scroll.grid(row=5, column=0, padx=36, pady=(0, 12), sticky="nsew")
        self.task_scroll.grid_columnconfigure(0, weight=1)

    def get_subjects(self):
        self.ensure_subjects_data()
        subjects = self.app.app_data.setdefault("subjects", [])

        if not subjects:
            subjects.append({
                "id": "subject_other",
                "name": self.app.t("other_subject"),
                "color": COLORS["primary"],
                "is_default": True
            })
            self.app.save_app_data()

        return subjects


    def get_subject_names(self):
        return [
            self.app.get_subject_display_name(subject)
            for subject in self.get_subjects()
        ]


    def get_subject_by_name(self, subject_name):
        for subject in self.get_subjects():
            if subject.get("name") == subject_name:
                return subject

        return self.get_subjects()[0]


    def get_subject_by_id(self, subject_id):
        for subject in self.get_subjects():
            if subject.get("id") == subject_id:
                return subject

        return self.get_subjects()[0]

    def create_add_task_card(self):
        self.add_card = AppCard(self)
        self.add_card.grid(row=4, column=0, padx=36, pady=(8, 30), sticky="ew")
        self.add_card.grid_columnconfigure(1, weight=1)

        self.add_title = ctk.CTkLabel(
            self.add_card,
            text=self.app.t("add_new_task"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.add_title.grid(row=0, column=0, columnspan=7, padx=20, pady=(18, 8), sticky="w")

        self.subject_menu = ctk.CTkOptionMenu(
            self.add_card,
            values=self.get_subject_names(),
            width=135,
            height=42,
            fg_color=COLORS["input"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["input_text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            command=None
        )

        subjects = self.get_subjects()
        self.subject_menu.set(subjects[0].get("name", self.app.t("other_subject")))

        self.subject_menu.grid(
            row=1,
            column=0,
            padx=(20, 8),
            pady=(8, 20),
            sticky="ew"
        )
        self.task_name_entry = AppEntry(
            self.add_card,
            placeholder_text=self.app.t("task_name")
        )
        self.task_name_entry.grid(row=1, column=1, padx=8, pady=(8, 20), sticky="ew")

        self.focus_entry = AppEntry(
            self.add_card,
            placeholder_text=self.app.t("focus_minutes"),
            width=100
        )
        self.focus_entry.insert(0, "25")
        self.focus_entry.grid(row=1, column=2, padx=8, pady=(8, 20))

        self.break_entry = AppEntry(
            self.add_card,
            placeholder_text=self.app.t("break_minutes"),
            width=100
        )
        self.break_entry.insert(0, "5")
        self.break_entry.grid(row=1, column=3, padx=8, pady=(8, 20))

        self.priority_menu = ctk.CTkOptionMenu(
            self.add_card,
            values=[self.app.t(item) for item in self.priority_options],
            width=110,
            height=42,
            fg_color=COLORS["input"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            text_color=COLORS["input_text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"]
        )
        self.priority_menu.set(self.app.t("medium"))
        self.priority_menu.grid(row=1, column=4, padx=8, pady=(8, 20))

        self.add_button = PrimaryButton(
            self.add_card,
            text=self.app.t("add_task"),
            command=self.save_task_from_form,
            width=110
        )
        self.add_button.grid(row=1, column=5, padx=(8, 8), pady=(8, 20))

        self.cancel_edit_button = SecondaryButton(
            self.add_card,
            text=self.app.t("cancel_edit"),
            command=self.cancel_edit,
            width=90
        )
        self.cancel_edit_button.grid(row=1, column=6, padx=(0, 20), pady=(8, 20))
        self.cancel_edit_button.grid_remove()
        
        self.form_status_label = ctk.CTkLabel(
            self.add_card,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.form_status_label.grid(
            row=2,
            column=0,
            columnspan=6,
            padx=20,
            pady=(0, 16),
            sticky="w"
        )

    def focus_task_name_entry(self):
        self.task_name_entry.focus_set()

    def get_key_from_translated_value(self, translated_value, options):
        for key in options:
            if self.app.t(key) == translated_value:
                return key
        return options[0]

    def change_filter(self, filter_key):
        self.active_filter = filter_key

        for key, button in self.filter_buttons.items():
            is_active = key == filter_key
            button.configure(
                fg_color=COLORS["primary_soft"] if is_active else COLORS["surface_light"],
                text_color=COLORS["white"] if is_active else COLORS["muted"]
            )

        self.render_tasks()

    def save_task_from_form(self):
        title = self.task_name_entry.get().strip()
        focus_value = self.focus_entry.get().strip()
        break_value = self.break_entry.get().strip()

        selected_subject = self.get_subject_by_name(self.subject_menu.get())

        if not title:
            title = self.app.t("default_task_name")

        try:
            focus_minutes = int(focus_value)
        except ValueError:
            self.form_status_label.configure(
                text=self.app.t("invalid_focus_minutes"),
                text_color=COLORS["red"]
            )
            return

        try:
            break_minutes = int(break_value)
        except ValueError:
            self.form_status_label.configure(
                text=self.app.t("invalid_break_minutes"),
                text_color=COLORS["red"]
            )
            return

        if focus_minutes <= 0:
            self.form_status_label.configure(
                text=self.app.t("invalid_focus_minutes"),
                text_color=COLORS["red"]
            )
            return

        if break_minutes < 0:
            self.form_status_label.configure(
                text=self.app.t("invalid_break_minutes"),
                text_color=COLORS["red"]
            )
            return

        selected_priority = self.get_key_from_translated_value(
            self.priority_menu.get(),
            self.priority_options
        )

        if self.editing_task_id:
            self.update_existing_task(
                task_id=self.editing_task_id,
                subject=selected_subject,
                title=title,
                focus_minutes=focus_minutes,
                break_minutes=break_minutes,
                priority=selected_priority
            )
        else:
            self.create_new_task(
                subject=selected_subject,
                title=title,
                focus_minutes=focus_minutes,
                break_minutes=break_minutes,
                priority=selected_priority
            )

    def create_new_task(self, subject, title, focus_minutes, break_minutes, priority):
        new_task = {
            "id": f"task_{uuid.uuid4().hex[:8]}",
            "subject_id": subject.get("id", "subject_other"),
            "subject_name": self.app.get_subject_display_name(subject),
            "title": title,
            "focus_minutes": focus_minutes,
            "break_minutes": break_minutes,
            "priority": priority,
            "status": "pending"
        }

        self.app.app_data.setdefault("tasks", []).append(new_task)
        self.app.save_app_data()

        self.clear_task_form()

        self.form_status_label.configure(
            text=self.app.t("task_added"),
            text_color=COLORS["green"]
        )

        self.after(2000, lambda: self.form_status_label.configure(text=""))
        self.render_tasks()

    def sync_task_sessions(self, task):
        for session in self.app.app_data.get("sessions", []):
            if session.get("task_id") == task.get("id"):
                session["task_title"] = task.get("title", self.app.t("default_task_name"))
                session["subject_id"] = task.get("subject_id", "subject_other")
                session["subject_name"] = task.get("subject_name", self.app.t("other_subject"))
                session["duration_seconds"] = task.get("focus_minutes", 0) * 60

    def update_existing_task(self, task_id, subject, title, focus_minutes, break_minutes, priority):
        updated_task = None

        for task in self.app.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["subject_id"] = subject.get("id", "subject_other")
                task["subject_name"] = self.app.get_subject_display_name(subject),
                task["title"] = title
                task["focus_minutes"] = focus_minutes
                task["break_minutes"] = break_minutes
                task["priority"] = priority
                updated_task = task
                break

        if updated_task:
            self.sync_task_sessions(updated_task)

        self.app.save_app_data()

        active_task_id = self.app.app_data.get("active_task_id")
        if active_task_id == task_id:
            self.app.focus_page.load_active_task()

        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_stats()

        self.cancel_edit()

        self.form_status_label.configure(
            text=self.app.t("task_updated"),
            text_color=COLORS["green"]
        )

        self.after(2000, lambda: self.form_status_label.configure(text=""))
        self.render_tasks()

    def clear_task_form(self):
        self.task_name_entry.delete(0, "end")
        self.focus_entry.delete(0, "end")
        self.focus_entry.insert(0, "25")
        self.break_entry.delete(0, "end")
        self.break_entry.insert(0, "5")
        subjects = self.get_subjects()
        self.subject_menu.configure(values=self.get_subject_names())
        self.subject_menu.set(subjects[0].get("name", self.app.t("other_subject")))
        self.priority_menu.set(self.app.t("medium"))

    def cancel_edit(self):
        self.editing_task_id = None
        self.clear_task_form()
        self.add_title.configure(text=self.app.t("add_new_task"))
        self.add_button.configure(text=self.app.t("add_task"))
        self.cancel_edit_button.grid_remove()            
    
    def render_empty_state(self):
        empty_card = AppCard(self.task_scroll)
        empty_card.grid(row=0, column=0, padx=4, pady=20, sticky="ew")
        empty_card.grid_columnconfigure(0, weight=1)

        icon_label = ctk.CTkLabel(
            empty_card,
            text="✦",
            text_color=COLORS["primary"],
            font=ctk.CTkFont(size=42, weight="bold")
        )
        icon_label.grid(row=0, column=0, pady=(28, 8))

        title_label = ctk.CTkLabel(
            empty_card,
            text=self.app.t("empty_tasks_title"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=1, column=0, pady=(0, 6))

        subtitle_label = ctk.CTkLabel(
            empty_card,
            text=self.app.t("empty_tasks_subtitle"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=14),
            wraplength=420,
            justify="center"
        )
        subtitle_label.grid(row=2, column=0, padx=30, pady=(0, 20))

        add_button = PrimaryButton(
            empty_card,
            text=f"+ {self.app.t('add_task')}",
            command=self.focus_task_name_entry,
            width=150
        )
        add_button.grid(row=3, column=0, pady=(0, 28))

    def render_tasks(self):
        self.update_summary_cards()

        for widget in self.task_scroll.winfo_children():
            widget.destroy()

        tasks = self.app.app_data.get("tasks", [])
        active_task_id = self.app.app_data.get("active_task_id")

        if self.active_filter == "completed":
            tasks = [
                task for task in tasks
                if task.get("status") == "completed"
                and not task.get("hidden_from_completed", False)
            ]

        elif self.active_filter == "pending":
            tasks = [
                task for task in tasks
                if task.get("status") != "completed"
                and task.get("id") != active_task_id
                and not task.get("hidden_from_plan", False)
            ]

        elif self.active_filter == "active":
            tasks = [
                task for task in tasks
                if task.get("id") == active_task_id
                and task.get("status") != "completed"
                and not task.get("hidden_from_plan", False)
            ]

        else:
            tasks = [
                task for task in tasks
                if not task.get("hidden_from_plan", False)
            ]

        if not tasks:
            self.render_empty_state()
            return

        for row_index, task in enumerate(tasks):
            is_active = task.get("id") == self.app.app_data.get("active_task_id")
            is_completed = task.get("status") == "completed"

            card = TaskCard(
                self.task_scroll,
                self.app,
                task,
                is_active=is_active,
                is_completed=is_completed,
                on_start=self.start_task,
                on_edit=self.edit_task,
                on_delete=self.delete_task,
                on_complete=self.complete_task,
                on_drag_start=self.drag_start,
                on_drag_release=self.drag_release,
                on_duplicate=self.duplicate_task,
                on_move_to_pending=self.move_completed_task_to_pending
            )

            card.grid(row=row_index, column=0, pady=7, sticky="ew")

    def delete_task(self, task_id):
        tasks = self.app.app_data.get("tasks", [])
        active_task_id = self.app.app_data.get("active_task_id")

        task_to_delete = None

        for task in tasks:
            if task.get("id") == task_id:
                task_to_delete = task
                break

        if not task_to_delete:
            return

        if task_to_delete.get("status") == "completed":
            task_to_delete["hidden_from_plan"] = True

        else:
            self.app.app_data["tasks"] = [
                task for task in tasks
                if task.get("id") != task_id
            ]

            if active_task_id == task_id:
                self.app.app_data["active_task_id"] = None
                self.app.app_data["queue_mode_active"] = False
                self.app.app_data["queue_task_ids"] = []

        existing_task_ids = {
            task.get("id")
            for task in self.app.app_data.get("tasks", [])
        }

        self.app.app_data["queue_task_ids"] = [
            item_id for item_id in self.app.app_data.get("queue_task_ids", [])
            if item_id in existing_task_ids
        ]

        if not self.app.app_data.get("tasks"):
            self.app.app_data["active_task_id"] = None
            self.app.app_data["queue_mode_active"] = False
            self.app.app_data["queue_task_ids"] = []

        self.app.save_app_data()

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.load_active_task()
            self.app.focus_page.update_queue_progress()
            self.app.focus_page.refresh_queue_progress_visibility()

        self.render_tasks()

    def log_manual_completion_session(self, task):
        existing_sessions = self.app.app_data.setdefault("sessions", [])

        for session in existing_sessions:
            if (
                session.get("task_id") == task.get("id")
                and session.get("source") == "study_plan"
            ):
                session["task_title"] = task.get("title", self.app.t("default_task_name"))
                session["subject_id"] = task.get("subject_id", "subject_other")
                session["subject_name"] = task.get("subject_name", self.app.t("other_subject"))
                session["duration_seconds"] = task.get("focus_minutes", 0) * 60
                session["mode"] = "focus"
                return

        session = {
            "id": f"session_{uuid.uuid4().hex[:8]}",
            "task_id": task.get("id"),
            "task_title": task.get("title", self.app.t("default_task_name")),
            "subject_id": task.get("subject_id", "subject_other"),
            "subject_name": task.get("subject_name", self.app.t("other_subject")),
            "mode": "focus",
            "source": "study_plan",
            "duration_seconds": task.get("focus_minutes", 0) * 60,
            "away_seconds": 0,
            "completed_at": datetime.now().isoformat(timespec="seconds")
        }

        existing_sessions.append(session)

    def complete_task(self, task_id):
        completed_task = None
        was_active_task = self.app.app_data.get("active_task_id") == task_id

        for task in self.app.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat(timespec="seconds")
                task["hidden_from_plan"] = False
                task["hidden_from_completed"] = False
                completed_task = task
                break

        if completed_task:
            self.log_manual_completion_session(completed_task)

        if was_active_task:
            moved_to_next = self.app.move_to_next_queue_task()

            if not moved_to_next:
                self.app.app_data["active_task_id"] = None
                self.app.app_data["queue_mode_active"] = False
                self.app.app_data["queue_task_ids"] = []

        self.app.save_app_data()

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.reset_timer()
            self.app.focus_page.load_active_task()
            self.app.focus_page.update_queue_progress()
            self.app.focus_page.refresh_queue_progress_visibility()

        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_stats()

        self.render_tasks()

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("study_plan_title"))
        self.subtitle_label.configure(text=self.app.t("study_plan_subtitle"))

        self.add_title.configure(text=self.app.t("add_new_task"))
        self.task_name_entry.configure(placeholder_text=self.app.t("task_name"))
        self.focus_entry.configure(placeholder_text=self.app.t("focus_minutes"))
        self.break_entry.configure(placeholder_text=self.app.t("break_minutes"))
        self.add_button.configure(text=self.app.t("add_task"))

        self.pending_card.title_label.configure(text=self.app.t("pending_tasks"))
        
        self.active_card.title_label.configure(text=self.app.t("active_tasks"))
        
        self.completed_card.title_label.configure(text=self.app.t("completed_tasks"))
        
        self.total_focus_card.title_label.configure(text=self.app.t("total_focus"))
       
        self.update_summary_cards()

        for key, button in self.filter_buttons.items():
            button.configure(text=self.app.t(key))

        current_subject = self.subject_menu.get()
        subject_names = self.get_subject_names()

        self.subject_menu.configure(values=subject_names)

        if current_subject in subject_names:
            self.subject_menu.set(current_subject)
        else:
            self.subject_menu.set(subject_names[0])

        self.priority_menu.configure(values=[self.app.t(item) for item in self.priority_options])

        self.render_tasks()

        self.start_plan_button.configure(text=f"▶ {self.app.t('start_plan')}")
        self.clear_completed_button.configure(text=self.app.t("clear_completed"))
        self.reset_all_button.configure(text=self.app.t("reset_all_tasks"))
        self.cancel_edit_button.configure(text=self.app.t("cancel_edit"))

        if self.editing_task_id:
            self.add_title.configure(text=self.app.t("update_task"))
            self.add_button.configure(text=self.app.t("update_task"))
        else:
            self.add_title.configure(text=self.app.t("add_new_task"))
            self.add_button.configure(text=self.app.t("add_task"))

    def start_task(self, task_id):
        self.app.set_active_task(task_id)
        self.render_tasks()

    def start_plan(self):
        started = self.app.start_task_queue()

        if started:
            self.form_status_label.configure(
                text=self.app.t("queue_started"),
                text_color=COLORS["green"]
            )
        else:
            self.form_status_label.configure(
                text=self.app.t("no_pending_tasks"),
                text_color=COLORS["red"]
            )

    def edit_task(self, task_id):
        task = None

        for item in self.app.app_data.get("tasks", []):
            if item.get("id") == task_id:
                task = item
                break

        if not task:
            return

        self.editing_task_id = task_id

        subject_id = task.get("subject_id")

        if subject_id:
            subject = self.get_subject_by_id(subject_id)
        else:
            old_subject_name = self.app.t(task.get("subject", "other_subject"))
            subject = self.get_subject_by_name(old_subject_name)

        self.subject_menu.configure(values=self.get_subject_names())
        self.subject_menu.set(self.app.get_subject_display_name(subject))

        self.task_name_entry.delete(0, "end")
        self.task_name_entry.insert(0, task.get("title", ""))

        self.focus_entry.delete(0, "end")
        self.focus_entry.insert(0, str(task.get("focus_minutes", 25)))

        self.break_entry.delete(0, "end")
        self.break_entry.insert(0, str(task.get("break_minutes", 5)))

        self.priority_menu.set(self.app.t(task.get("priority", "medium")))

        self.add_title.configure(text=self.app.t("update_task"))
        self.add_button.configure(text=self.app.t("update_task"))
        self.cancel_edit_button.grid()
        self.task_name_entry.focus_set()

    def drag_start(self, task_id):
        self.dragged_task_id = task_id

    def drag_release(self, task_id, event):
        if not getattr(self, "dragged_task_id", None):
            return

        target_widget = self.winfo_containing(event.x_root, event.y_root)

        target_task_id = None

        while target_widget:
            if hasattr(target_widget, "task"):
                target_task_id = target_widget.task.get("id")
                break
            target_widget = target_widget.master

        if target_task_id and target_task_id != self.dragged_task_id:
            self.reorder_tasks(self.dragged_task_id, target_task_id)

        self.dragged_task_id = None

    def reorder_tasks(self, dragged_task_id, target_task_id):
        tasks = self.app.app_data.get("tasks", [])

        dragged_index = None
        target_index = None

        for index, task in enumerate(tasks):
            if task.get("id") == dragged_task_id:
                dragged_index = index
            if task.get("id") == target_task_id:
                target_index = index

        if dragged_index is None or target_index is None:
            return

        dragged_task = tasks.pop(dragged_index)
        tasks.insert(target_index, dragged_task)

        self.app.save_app_data()
        self.render_tasks()

    def update_summary_cards(self):
        tasks = self.app.app_data.get("tasks", [])
        active_task_id = self.app.app_data.get("active_task_id")

        visible_tasks = [
            task for task in tasks
            if not task.get("hidden_from_plan", False)
        ]

        completed_tasks = [
            task for task in tasks
            if task.get("status") == "completed"
        ]

        active_tasks = [
            task for task in visible_tasks
            if task.get("id") == active_task_id
            and task.get("status") != "completed"
        ]

        pending_tasks = [
            task for task in visible_tasks
            if task.get("status") != "completed"
            and task.get("id") != active_task_id
        ]

        total_focus_minutes = sum(
            task.get("focus_minutes", 0)
            for task in visible_tasks
            if task.get("status") != "completed"
        )

        self.pending_card.value_label.configure(text=str(len(pending_tasks)))
        self.active_card.value_label.configure(text=str(len(active_tasks)))
        self.completed_card.value_label.configure(text=str(len(completed_tasks)))
        self.total_focus_card.value_label.configure(text=f"{total_focus_minutes}m")

    def clear_completed_tasks(self):
        for task in self.app.app_data.get("tasks", []):
            if task.get("status") == "completed":
                task["hidden_from_plan"] = True
                task["hidden_from_completed"] = True

        self.app.save_app_data()

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.load_active_task()
            self.app.focus_page.update_queue_progress()
            self.app.focus_page.refresh_queue_progress_visibility()

        self.form_status_label.configure(
            text=self.app.t("completed_tasks_cleared"),
            text_color=COLORS["green"]
        )

        self.after(2000, lambda: self.form_status_label.configure(text=""))
        self.render_tasks()

    def remove_task_sessions(self, task_id):
        self.app.app_data["sessions"] = [
            session for session in self.app.app_data.get("sessions", [])
            if session.get("task_id") != task_id
        ]

    def move_completed_task_to_pending(self, task_id):
        moved_task = None

        for task in self.app.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "pending"
                task["hidden_from_plan"] = False
                task["hidden_from_completed"] = False
                task.pop("completed_at", None)
                moved_task = task
                break

        if not moved_task:
            return

        self.remove_task_sessions(task_id)

        self.app.save_app_data()

        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_stats()

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.update_queue_progress()
            self.app.focus_page.refresh_queue_progress_visibility()

        self.render_tasks()

    def reset_all_tasks_to_pending(self):
        for task in self.app.app_data.get("tasks", []):
            task["status"] = "pending"
            task["hidden_from_plan"] = False

        self.app.app_data["active_task_id"] = None
        self.app.app_data["queue_mode_active"] = False
        self.app.app_data["queue_task_ids"] = []

        self.app.save_app_data()

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.reset_timer()
            self.app.focus_page.load_active_task()
            self.app.focus_page.update_queue_progress()

        self.form_status_label.configure(
            text=self.app.t("all_tasks_reset"),
            text_color=COLORS["green"]
        )

        self.render_tasks()
    
    def duplicate_task(self, task_id):
        tasks = self.app.app_data.setdefault("tasks", [])

        original_index = None
        original_task = None

        for index, task in enumerate(tasks):
            if task.get("id") == task_id:
                original_index = index
                original_task = task
                break

        if original_task is None:
            return

        if original_task.get("status") == "completed":
            return

        duplicated_task = original_task.copy()
        duplicated_task["id"] = f"task_{uuid.uuid4().hex[:8]}"
        duplicated_task["status"] = "pending"
        duplicated_task["hidden_from_plan"] = False
        duplicated_task["hidden_from_completed"] = False
        duplicated_task.pop("completed_at", None)

        tasks.insert(original_index + 1, duplicated_task)

        self.app.save_app_data()
        self.render_tasks()

    def refresh_subject_menu(self):
        if not hasattr(self, "subject_menu"):
            return

        current_subject = self.subject_menu.get()
        subject_names = self.get_subject_names()

        self.subject_menu.configure(values=subject_names)

        if current_subject in subject_names:
            self.subject_menu.set(current_subject)
        elif subject_names:
            self.subject_menu.set(subject_names[0])

class TaskCard(AppCard):
    def __init__(
        self,
        parent,
        app,
        task,
        is_active=False,
        is_completed=False,
        on_start=None,
        on_edit=None,
        on_delete=None,
        on_complete=None,
        on_duplicate=None,
        on_move_to_pending=None,
        on_drag_start=None,
        on_drag_release=None
    ):
        self.on_edit = on_edit
        self.on_drag_start = on_drag_start
        self.on_drag_release = on_drag_release

        border_color = COLORS["primary"] if is_active else COLORS["card_border"]
        fg_color = COLORS["surface"] if is_completed else COLORS["card"]

        ctk.CTkFrame.__init__(
            self,
            parent,
            fg_color=fg_color,
            corner_radius=22,
            border_width=2 if is_active else 1,
            border_color=border_color
        )

        self.app = app
        self.task = task
        self.is_active = is_active
        self.is_completed = is_completed
        self.on_start = on_start
        self.on_delete = on_delete
        self.on_complete = on_complete
        self.on_duplicate = on_duplicate
        self.on_move_to_pending = on_move_to_pending

        self.grid_columnconfigure(1, weight=1)

        subject_name = task.get("subject_name")

        if not subject_name:
            old_subject_key = task.get("subject", "other")
            subject_name = self.app.t(old_subject_key)

        subject_key = task.get("subject", "other")
        subject_meta = SUBJECT_META.get(subject_key, SUBJECT_META["other"])
        subject_color = self.app.get_subject_color(task.get("subject_id"))

        self.icon = SubjectIcon(
            self,
            subject_key=subject_key,
            icon_text=subject_meta["icon"],
            color=subject_color
        )
        self.icon.grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=16)

        title_text = f"{subject_name} - {task.get('title', '')}"

        self.title = ctk.CTkLabel(
            self,
            text=title_text,
            text_color=COLORS["muted"] if self.is_completed else COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.title.grid(row=0, column=1, padx=0, pady=(16, 2), sticky="ew")

        detail_text = (
            f"◷ {task.get('focus_minutes', 0)}{self.app.t('minute_short')} {self.app.t('focus_label_short')}   "
            f"○ {task.get('break_minutes', 0)}{self.app.t('minute_short')} {self.app.t('break_label_short')}"
        )

        self.details = ctk.CTkLabel(
            self,
            text=detail_text,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.details.grid(row=1, column=1, padx=0, pady=(0, 16), sticky="ew")

        self.priority = PriorityBadge(self, task.get("priority", "medium"))
        self.priority.grid(row=0, column=2, rowspan=2, padx=(12, 8), pady=20)

        if self.is_completed:
            status_text = self.app.t("completed_status_label")
            status_color = COLORS["green"]
        elif self.is_active:
            status_text = self.app.t("active_status")
            status_color = COLORS["primary"]
        else:
            status_text = self.app.t("pending_status")
            status_color = COLORS["card_soft"]

        self.status_badge = ctk.CTkLabel(
            self,
            text=status_text,
            fg_color=status_color,
            text_color=COLORS["white"],
            corner_radius=10,
            padx=10,
            pady=5,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.status_badge.grid(row=0, column=3, rowspan=2, padx=(0, 8), pady=20)

        self.start_button = SecondaryButton(
            self,
            text=f"▶ {self.app.t('start_task')}",
            command=lambda: self.on_start(task.get("id")) if self.on_start else None,
            width=92
        )
        self.start_button.grid(row=0, column=4, rowspan=2, padx=(0, 8), pady=20)

        if self.is_completed:
            self.secondary_action_button = SecondaryButton(
                self,
                text="↺",
                command=lambda: self.on_move_to_pending(task.get("id")) if self.on_move_to_pending else None,
                width=44
            )
        else:
            self.secondary_action_button = SecondaryButton(
                self,
                text="⧉",
                command=lambda: self.on_duplicate(task.get("id")) if self.on_duplicate else None,
                width=44
            )

        self.secondary_action_button.grid(row=0, column=5, rowspan=2, padx=(0, 8), pady=20)

        self.edit_button = SecondaryButton(
            self,
            text="✎",
            command=lambda: self.on_edit(task.get("id")) if self.on_edit else None,
            width=44
        )
        self.edit_button.grid(row=0, column=6, rowspan=2, padx=(0, 8), pady=20)

        self.complete_button = SecondaryButton(
            self,
            text="✓",
            command=lambda: self.on_complete(task.get("id")) if self.on_complete else None,
            width=44
        )
        self.complete_button.grid(row=0, column=7, rowspan=2, padx=(0, 8), pady=20)

        self.delete_button = SecondaryButton(
            self,
            text="×",
            command=lambda: self.on_delete(task.get("id")) if self.on_delete else None,
            width=44
        )
        self.delete_button.grid(row=0, column=8, rowspan=2, padx=(0, 8), pady=20)

        self.drag_handle = ctk.CTkLabel(
            self,
            text="☰",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=18, weight="bold"),
            cursor="hand2"
        )
        self.drag_handle.grid(row=0, column=9, rowspan=2, padx=(0, 18), pady=20)

        Tooltip(self.start_button, self.app.t("tooltip_start_task"))

        if self.is_completed:
            Tooltip(self.secondary_action_button, self.app.t("tooltip_move_to_pending"))
        else:
            Tooltip(self.secondary_action_button, self.app.t("tooltip_duplicate_task"))

        Tooltip(self.edit_button, self.app.t("tooltip_edit_task"))
        Tooltip(self.complete_button, self.app.t("tooltip_complete_task"))

        delete_tooltip_text = (
            self.app.t("tooltip_remove_completed_task")
            if self.is_completed
            else self.app.t("tooltip_delete_task")
        )

        Tooltip(self.delete_button, delete_tooltip_text)
        Tooltip(self.drag_handle, self.app.t("tooltip_drag_task"))

        if self.on_drag_start:
            self.drag_handle.bind(
                "<Button-1>",
                self.handle_drag_start
            )

        if self.on_drag_release:
            self.drag_handle.bind(
                "<ButtonRelease-1>",
                self.handle_drag_release
            )

        if self.is_active:
            self.start_button.configure(
                state="disabled",
                fg_color=COLORS["surface"],
                text_color=COLORS["muted"]
            )

            self.edit_button.configure(
                state="disabled",
                fg_color=COLORS["surface"],
                text_color=COLORS["muted"]
            )

            self.secondary_action_button.configure(
                state="disabled",
                fg_color=COLORS["surface"],
                text_color=COLORS["muted"]
            )

        if self.is_completed:
            self.start_button.configure(
                state="disabled",
                fg_color=COLORS["surface"],
                text_color=COLORS["muted"]
            )

            self.complete_button.configure(
                state="disabled",
                fg_color=COLORS["surface"],
                text_color=COLORS["muted"]
            )

            self.drag_handle.configure(
                text_color=COLORS["surface"],
                cursor=""
            )

            self.drag_handle.unbind("<Button-1>")
            self.drag_handle.unbind("<ButtonRelease-1>")

    def set_dragging_style(self):
        if self.is_completed:
            return

        self.configure(
            fg_color=COLORS["surface"],
            border_width=2,
            border_color=COLORS["primary"]
        )

        self.title.configure(text_color=COLORS["muted"])
        self.details.configure(text_color=COLORS["muted"])

        self.drag_handle.configure(
            text_color=COLORS["primary"],
            font=ctk.CTkFont(size=21, weight="bold")
        )


    def reset_dragging_style(self):
        if self.is_completed:
            return

        border_color = COLORS["primary"] if self.is_active else COLORS["card_border"]
        fg_color = COLORS["surface"] if self.is_completed else COLORS["card"]

        self.configure(
            fg_color=fg_color,
            border_width=2 if self.is_active else 1,
            border_color=border_color
        )

        self.title.configure(
            text_color=COLORS["muted"] if self.is_completed else COLORS["text"]
        )

        self.details.configure(text_color=COLORS["muted"])

        self.drag_handle.configure(
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=18, weight="bold")
        )


    def handle_drag_start(self, event):
        if self.is_completed:
            return

        self.set_dragging_style()

        if self.on_drag_start:
            self.on_drag_start(self.task.get("id"))


    def handle_drag_release(self, event):
        if self.is_completed:
            return

        self.reset_dragging_style()

        if self.on_drag_release:
            self.on_drag_release(self.task.get("id"), event)
