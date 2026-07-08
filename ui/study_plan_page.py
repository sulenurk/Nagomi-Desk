import uuid
import customtkinter as ctk

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

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_header()
        self.create_filter_bar()
        self.create_task_list()
        self.create_add_task_card()

        self.render_tasks()

    def create_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 10), sticky="ew")
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
        self.start_plan_button.grid(row=0, column=1, rowspan=2, padx=(0, 12), sticky="e")

        self.add_top_button = PrimaryButton(
            self.header,
            text=f"+ {self.app.t('add_task')}",
            command=self.focus_task_name_entry,
            width=130
        )
        self.add_top_button.grid(row=0, column=2, rowspan=2, sticky="e")
    def create_filter_bar(self):
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, padx=36, pady=(16, 12), sticky="w")

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

    def create_task_list(self):
        self.task_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["card_soft"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.task_scroll.grid(row=2, column=0, padx=36, pady=(0, 12), sticky="nsew")
        self.task_scroll.grid_columnconfigure(0, weight=1)

    def create_add_task_card(self):
        self.add_card = AppCard(self)
        self.add_card.grid(row=3, column=0, padx=36, pady=(8, 30), sticky="ew")
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
            values=[self.app.t(item) for item in self.subject_options],
            width=135,
            height=42,
            fg_color=COLORS["input"],
            button_color="#DDD6FE",
            button_hover_color="#C4B5FD",
            text_color=COLORS["input_text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            command=None
        )
        self.subject_menu.set(self.app.t("math"))
        self.subject_menu.grid(row=1, column=0, padx=(20, 8), pady=(8, 20), sticky="ew")

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
            button_color="#DDD6FE",
            button_hover_color="#C4B5FD",
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
                text_color=COLORS["text"] if is_active else COLORS["muted"]
            )

        self.render_tasks()

    def save_task_from_form(self):
        title = self.task_name_entry.get().strip()
        focus_value = self.focus_entry.get().strip()
        break_value = self.break_entry.get().strip()

        selected_subject = self.get_key_from_translated_value(
            self.subject_menu.get(),
            self.subject_options
        )

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
            "subject": subject,
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

    def update_existing_task(self, task_id, subject, title, focus_minutes, break_minutes, priority):
        for task in self.app.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["subject"] = subject
                task["title"] = title
                task["focus_minutes"] = focus_minutes
                task["break_minutes"] = break_minutes
                task["priority"] = priority
                break

        self.app.save_app_data()

        active_task_id = self.app.app_data.get("active_task_id")
        if active_task_id == task_id:
            self.app.focus_page.load_active_task()

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
        self.subject_menu.set(self.app.t("math"))
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
        for widget in self.task_scroll.winfo_children():
            widget.destroy()

        tasks = self.app.app_data.get("tasks", [])
        active_task_id = self.app.app_data.get("active_task_id")

        if self.active_filter == "completed":
            tasks = [
                task for task in tasks
                if task.get("status") == "completed"
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
                on_drag_release=self.drag_release
                )

            card.grid(row=row_index, column=0, pady=7, sticky="ew")

    def delete_task(self, task_id):
        tasks = self.app.app_data.get("tasks", [])

        task_to_delete = None

        for task in tasks:
            if task.get("id") == task_id:
                task_to_delete = task
                break

        if not task_to_delete:
            return

        active_task_id = self.app.app_data.get("active_task_id")

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

    def complete_task(self, task_id):
        for task in self.app.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "completed"

        self.app.save_app_data()
        self.render_tasks()

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("study_plan_title"))
        self.subtitle_label.configure(text=self.app.t("study_plan_subtitle"))
        self.add_top_button.configure(text=f"+ {self.app.t('add_task')}")
        self.add_title.configure(text=self.app.t("add_new_task"))
        self.task_name_entry.configure(placeholder_text=self.app.t("task_name"))
        self.focus_entry.configure(placeholder_text=self.app.t("focus_minutes"))
        self.break_entry.configure(placeholder_text=self.app.t("break_minutes"))
        self.add_button.configure(text=self.app.t("add_task"))

        for key, button in self.filter_buttons.items():
            button.configure(text=self.app.t(key))

        self.subject_menu.configure(values=[self.app.t(item) for item in self.subject_options])
        self.priority_menu.configure(values=[self.app.t(item) for item in self.priority_options])

        self.render_tasks()

        self.start_plan_button.configure(text=f"▶ {self.app.t('start_plan')}")
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

        self.subject_menu.set(self.app.t(task.get("subject", "math")))

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

        self.grid_columnconfigure(1, weight=1)

        subject = task.get("subject", "other")
        subject_meta = SUBJECT_META.get(subject, SUBJECT_META["other"])

        self.icon = SubjectIcon(
            self,
            subject_key=subject,
            icon_text=subject_meta["icon"]
        )
        self.icon.grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=16)

        title_text = f"{self.app.t(subject)} - {task.get('title', '')}"

        self.title = ctk.CTkLabel(
            self,
            text=title_text,
            text_color=COLORS["muted"] if self.is_completed else COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.title.grid(row=0, column=1, padx=0, pady=(16, 2), sticky="ew")

        detail_text = (
            f"◷ {task.get('focus_minutes', 0)} {self.app.t('focus_minutes')}   "
            f"○ {task.get('break_minutes', 0)} {self.app.t('break_minutes')}"
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
            command=lambda: self.on_start(task.get("id")),
            width=92
        )
        self.start_button.grid(row=0, column=4, rowspan=2, padx=(0, 8), pady=20)
        
        self.edit_button = SecondaryButton(
            self,
            text="✎",
            command=lambda: self.on_edit(task.get("id")),
            width=44
        )
        self.edit_button.grid(row=0, column=5, rowspan=2, padx=(0, 8), pady=20)

        self.complete_button = SecondaryButton(
            self,
            text="✓",
            command=lambda: self.on_complete(task.get("id")),
            width=44
        )
        self.complete_button.grid(row=0, column=6, rowspan=2, padx=(0, 8), pady=20)
        self.delete_button = SecondaryButton(
            self,
            text="×",
            command=lambda: self.on_delete(task.get("id")),
            width=44
        )
        self.delete_button.grid(row=0, column=7, rowspan=2, padx=(0, 18), pady=20)

        self.drag_handle = ctk.CTkLabel(
            self,
            text="☰",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=18, weight="bold"),
            cursor="hand2"
        )
        self.drag_handle.grid(row=0, column=8, rowspan=2, padx=(0, 18), pady=20)

        self.drag_handle.bind("<Button-1>", lambda event: self.on_drag_start(task.get("id")))
        self.drag_handle.bind("<ButtonRelease-1>", lambda event: self.on_drag_release(task.get("id"), event))

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

    