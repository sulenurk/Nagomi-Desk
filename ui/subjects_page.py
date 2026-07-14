import uuid
import customtkinter as ctk

from ui.theme import COLORS, SUBJECT_COLOR_PALETTE
from ui.components import AppCard, PageTitle, PageSubtitle, PrimaryButton, SecondaryButton, AppEntry


class SubjectsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.ensure_subjects_data()

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["card_soft"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.selected_color = self.get_next_subject_color()
        self.create_add_card()
        self.create_subjects_list()

        self.render_subjects()

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

    def create_header(self):
        self.header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 12), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("subjects"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(
            self.header,
            self.app.t("subjects_subtitle")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

    def create_add_card(self):
        self.add_card = AppCard(self.scroll)
        self.add_card.grid(row=1, column=0, padx=36, pady=(12, 12), sticky="ew")
        self.add_card.grid_columnconfigure(0, weight=1)

        self.add_title = ctk.CTkLabel(
            self.add_card,
            text=self.app.t("add_subject"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.add_title.grid(row=0, column=0, padx=22, pady=(20, 8), sticky="w")

        self.subject_name_entry = AppEntry(
            self.add_card,
            placeholder_text=self.app.t("subject_name_placeholder")
        )
        self.subject_name_entry.grid(row=1, column=0, padx=22, pady=(4, 10), sticky="ew")

        self.subject_name_entry.bind(
            "<Return>",
            lambda event: self.add_subject()
        )

        self.add_button = PrimaryButton(
            self.add_card,
            text=self.app.t("add_subject"),
            command=self.add_subject,
            width=180
        )
        self.add_button.grid(row=1, column=1, padx=(0, 22), pady=(4, 10), sticky="e")

        self.color_picker = ctk.CTkFrame(self.add_card, fg_color="transparent")
        self.color_picker.grid(row=2, column=0, columnspan=2, padx=22, pady=(0, 20), sticky="w")

        self.color_picker_label = ctk.CTkLabel(
            self.color_picker,
            text=self.app.t("subject_color"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.color_picker_label.grid(row=0, column=0, padx=(0, 10))

        self.color_buttons = []
        for index, color in enumerate(SUBJECT_COLOR_PALETTE):
            button = ctk.CTkButton(
                self.color_picker,
                text="",
                width=28,
                height=28,
                corner_radius=14,
                fg_color=color,
                hover_color=color,
                border_width=0,
                command=lambda value=color: self.select_color(value)
            )
            button.grid(row=0, column=index + 1, padx=3)
            self.color_buttons.append((color, button))

        self.update_color_picker()

    def get_next_subject_color(self):
        used_colors = {subject.get("color") for subject in self.app.app_data.get("subjects", [])}
        return next(
            (color for color in SUBJECT_COLOR_PALETTE if color not in used_colors),
            SUBJECT_COLOR_PALETTE[len(self.app.app_data.get("subjects", [])) % len(SUBJECT_COLOR_PALETTE)]
        )

    def select_color(self, color):
        self.selected_color = color
        self.update_color_picker()

    def update_color_picker(self):
        for color, button in self.color_buttons:
            button.configure(
                border_width=3 if color == self.selected_color else 0,
                border_color=COLORS["white"] if color == self.selected_color else color
            )

    def create_subjects_list(self):
        self.list_card = AppCard(self.scroll)
        self.list_card.grid(row=2, column=0, padx=36, pady=(8, 30), sticky="ew")
        self.list_card.grid_columnconfigure(0, weight=1)

        self.list_title = ctk.CTkLabel(
            self.list_card,
            text=self.app.t("subject_list"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.list_title.grid(row=0, column=0, padx=22, pady=(20, 12), sticky="w")

        self.subjects_frame = ctk.CTkFrame(
            self.list_card,
            fg_color="transparent"
        )
        self.subjects_frame.grid(row=1, column=0, padx=22, pady=(0, 22), sticky="ew")
        self.subjects_frame.grid_columnconfigure(0, weight=1)

    def add_subject(self):
        name = self.subject_name_entry.get().strip()

        if not name:
            self.focus_subject_entry()
            return

        subjects = self.app.app_data.setdefault("subjects", [])

        new_subject = {
            "id": f"subject_{uuid.uuid4().hex[:8]}",
            "name": name,
            "color": self.selected_color,
            "is_default": False
        }

        subjects.append(new_subject)
        self.app.save_app_data()

        self.subject_name_entry.delete(0, "end")
        self.selected_color = self.get_next_subject_color()
        self.update_color_picker()
        self.render_subjects()
        self.focus_subject_entry()

        if hasattr(self.app, "todo_page"):
            self.app.todo_page.refresh_subject_menu()

        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_subject_filter_menu()

    def delete_subject(self, subject_id):
        subjects = self.app.app_data.get("subjects", [])

        subject = next(
            (item for item in subjects if item.get("id") == subject_id),
            None
        )

        if not subject:
            return

        if subject.get("is_default"):
            return

        self.app.app_data["subjects"] = [
            item for item in subjects
            if item.get("id") != subject_id
        ]

        self.reassign_deleted_subject_tasks(subject_id)
        self.reassign_deleted_subject_sessions(subject_id)

        self.app.save_app_data()
        self.render_subjects()

        if hasattr(self.app, "todo_page"):
            self.app.todo_page.refresh_subject_menu()

        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_subject_filter_menu()

    def reassign_deleted_subject_tasks(self, deleted_subject_id):
        for task in self.app.app_data.get("tasks", []):
            if task.get("subject_id") == deleted_subject_id:
                task["subject_id"] = "subject_other"
                task["subject_name"] = self.app.t("other_subject")

    def reassign_deleted_subject_sessions(self, deleted_subject_id):
        for session in self.app.app_data.get("sessions", []):
            if session.get("subject_id") == deleted_subject_id:
                session["subject_id"] = "subject_other"
                session["subject_name"] = self.app.t("other_subject")

    def render_subjects(self):
        for widget in self.subjects_frame.winfo_children():
            widget.destroy()

        subjects = self.app.app_data.get("subjects", [])

        if not subjects:
            self.ensure_subjects_data()
            subjects = self.app.app_data.get("subjects", [])

        for row_index, subject in enumerate(subjects):
            item = SubjectItem(
                self.subjects_frame,
                self.app,
                subject,
                on_delete=self.delete_subject,
                on_color_change=self.change_subject_color
            )
            item.grid(row=row_index, column=0, pady=6, sticky="ew")

    def focus_subject_entry(self):
        self.after(100, self.subject_name_entry.focus_set)

    def change_subject_color(self, subject_id, color):
        subject = next((item for item in self.app.app_data.get("subjects", []) if item.get("id") == subject_id), None)
        if not subject or subject.get("color") == color:
            return
        subject["color"] = color
        self.app.save_app_data()
        self.render_subjects()
        if hasattr(self.app, "focus_page"):
            self.app.focus_page.load_active_task()
        if hasattr(self.app, "statistics_page"):
            self.app.statistics_page.refresh_stats()

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("subjects"))
        self.subtitle_label.configure(text=self.app.t("subjects_subtitle"))
        self.add_title.configure(text=self.app.t("add_subject"))
        self.subject_name_entry.configure(placeholder_text=self.app.t("subject_name_placeholder"))
        self.add_button.configure(text=self.app.t("add_subject"))
        self.color_picker_label.configure(text=self.app.t("subject_color"))
        self.list_title.configure(text=self.app.t("subject_list"))
        self.render_subjects()

class SubjectItem(ctk.CTkFrame):
    def __init__(self, parent, app, subject, on_delete, on_color_change):
        super().__init__(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=16
        )

        self.app = app
        self.subject = subject
        self.on_delete = on_delete
        self.on_color_change = on_color_change

        self.grid_columnconfigure(1, weight=1)

        subject_color = subject.get("color", COLORS["primary"])
        color_dot = ctk.CTkLabel(
            self,
            text="●",
            text_color=subject_color,
            font=ctk.CTkFont(size=18)
        )
        color_dot.grid(row=0, column=0, padx=(18, 10), pady=16)

        if subject.get("is_default"):
            subject_name = app.t("other_subject")
        else:
            subject_name = subject.get("name", app.t("other_subject"))

        name_label = ctk.CTkLabel(
            self,
            text=subject_name,
            #text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=1, padx=0, pady=16, sticky="ew")

        color_menu = ctk.CTkOptionMenu(
            self,
            values=SUBJECT_COLOR_PALETTE,
            command=lambda color: self.on_color_change(subject.get("id"), color),
            width=92,
            height=30,
            fg_color=subject_color,
            button_color=subject_color,
            button_hover_color=subject_color,
            text_color=COLORS["white"],
            dropdown_fg_color=COLORS["surface"],
            #dropdown_text_color=COLORS["text"]
        )
        color_menu.set(subject_color)
        color_menu.grid(row=0, column=2, padx=(12, 0), pady=12, sticky="e")

        if subject.get("is_default"):
            badge = ctk.CTkLabel(
                self,
                text=app.t("default_subject"),
                fg_color=COLORS["primary"],
                text_color=COLORS["text"],
                corner_radius=10,
                padx=10,
                pady=4,
                font=ctk.CTkFont(size=11, weight="bold")
            )
            badge.grid(row=0, column=3, padx=(12, 18), pady=16, sticky="e")
        else:
            delete_button = SecondaryButton(
                self,
                text=self.app.t("delete"),
                command=lambda: self.on_delete(subject.get("id")),
                width=90
            )
            delete_button.grid(row=0, column=3, padx=(12, 18), pady=12, sticky="e")
