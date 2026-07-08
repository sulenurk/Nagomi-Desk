import json
import customtkinter as ctk
from pathlib import Path
from ui.pomodoro_page import PomodoroPage
from ui.statistics_page import StatisticsPage
from ui.focus_page import FocusPage
from ui.study_plan_page import StudyPlanPage
from ui.settings_page import SettingsPage

class FocusFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.base_path = Path(__file__).resolve().parent.parent
        self.data_path = self.base_path / "data" / "app_data.json"

        self.app_data = self.load_app_data()
        self.language = self.app_data.get("language", "tr")
        self.translations = self.load_translations()

        self.active_page = "focus"

        self.title(self.t("app_name"))
        self.geometry("1000x650")
        self.minsize(900, 600)
        self.configure(fg_color="#020617")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()

        self.show_focus_page()

    def load_app_data(self):
        with open(self.data_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_app_data(self):
        with open(self.data_path, "w", encoding="utf-8") as file:
            json.dump(self.app_data, file, indent=2, ensure_ascii=False)

    def load_translations(self):
        import json
        import os

        translations = {}

        for language in ["tr", "en"]:
            file_path = os.path.join("locales", f"{language}.json")

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    translations[language] = json.load(file)

            except FileNotFoundError:
                print(f"[TRANSLATION ERROR] Missing file: {file_path}")
                translations[language] = {}

            except json.JSONDecodeError as error:
                print(f"[TRANSLATION ERROR] Invalid JSON in {file_path}")
                print(f"Line: {error.lineno}, Column: {error.colno}")
                print(f"Message: {error.msg}")
                translations[language] = {}

        return translations

    def t(self, key, **kwargs):
        language = self.app_data.get("language", "tr")

        text = self.translations.get(language, {}).get(key)

        if text is None:
            text = self.translations.get("en", {}).get(key, key)

        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text

        return text

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
    self,
    width=230,
    corner_radius=0,
    fg_color="#030712"
)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=self.t("app_name"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.focus_button = ctk.CTkButton(
    self.sidebar,
    text=self.t("focus_timer"),
    height=42,
    corner_radius=14,
    fg_color="#1E293B",
    hover_color="#334155",
    anchor="w",
    command=self.show_focus_page
)
        self.focus_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.todo_button = ctk.CTkButton(
    self.sidebar,
    text=self.t("study_plan"),
    height=42,
    corner_radius=14,
    fg_color="#1E293B",
    hover_color="#334155",
    anchor="w",
    command=self.show_todo_page
)
        self.todo_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.pomodoro_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("regular_pomodoro"),
            height=42,
            corner_radius=14,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            command=self.show_pomodoro_page
        )
        self.pomodoro_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.statistics_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("statistics"),
            height=42,
            corner_radius=14,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            command=self.show_statistics_page
        )
        self.statistics_button.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("settings"),
            height=42,
            corner_radius=14,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            command=self.show_settings_page
        )
        self.settings_button.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.language_label = ctk.CTkLabel(
            self.sidebar,
            text=self.t("language")
        )
        self.language_label.grid(row=7, column=0, padx=20, pady=(20, 5))

        self.language_menu = ctk.CTkOptionMenu(
    self.sidebar,
    values=["tr", "en"],
    fg_color="#1E293B",
    button_color="#334155",
    button_hover_color="#475569",
    command=self.change_language
)
        self.language_menu.set(self.language)
        self.language_menu.grid(row=8, column=0, padx=20, pady=(0, 30), sticky="ew")

    def create_pages(self):
        self.page_container = ctk.CTkFrame(self, corner_radius=0)
        self.page_container.grid(row=0, column=1, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.focus_page = FocusPage(self.page_container, self)
        self.todo_page = StudyPlanPage(self.page_container, self)
        self.pomodoro_page = PomodoroPage(self.page_container, self)
        self.settings_page = SettingsPage(self.page_container, self)
        self.statistics_page = StatisticsPage(self.page_container, self)
        
        self.focus_page.grid(row=0, column=0, sticky="nsew")
        self.todo_page.grid(row=0, column=0, sticky="nsew")
        self.pomodoro_page.grid(row=0, column=0, sticky="nsew")
        self.statistics_page.grid(row=0, column=0, sticky="nsew")
        self.settings_page.grid(row=0, column=0, sticky="nsew")

    def show_focus_page(self):
        self.active_page = "focus"
        self.update_sidebar_active_state()
        self.focus_page.tkraise()

    def show_todo_page(self):
        self.active_page = "study"
        self.update_sidebar_active_state()
        self.todo_page.tkraise()

    def show_pomodoro_page(self):
        self.active_page = "pomodoro"
        self.update_sidebar_active_state()
        self.pomodoro_page.tkraise()

    def show_statistics_page(self):
        self.active_page = "statistics"
        self.update_sidebar_active_state()
        self.statistics_page.refresh_stats()
        self.statistics_page.tkraise()

    def show_settings_page(self):
        self.active_page = "settings"
        self.update_sidebar_active_state()
        self.settings_page.tkraise()

    def change_language(self, selected_language):
        self.language = selected_language
        self.app_data["language"] = selected_language
        self.save_app_data()

        self.translations = self.load_translations()
        self.refresh_texts()

    def refresh_texts(self):
        self.title(self.t("app_name"))

        self.logo_label.configure(text=self.t("app_name"))
        self.focus_button.configure(text=self.t("focus_timer"))
        self.todo_button.configure(text=self.t("study_plan"))
        self.pomodoro_button.configure(text=self.t("regular_pomodoro"))
        self.statistics_button.configure(text=self.t("statistics"))
        self.settings_button.configure(text=self.t("settings"))
        self.language_label.configure(text=self.t("language"))

        self.focus_page.refresh_texts()
        self.todo_page.refresh_texts()
        self.pomodoro_page.refresh_texts()
        self.statistics_page.refresh_texts()
        self.settings_page.refresh_texts()

    def get_active_task(self):
        active_task_id = self.app_data.get("active_task_id")

        if not active_task_id:
            return None

        for task in self.app_data.get("tasks", []):
            if task.get("id") == active_task_id:
                return task

        return None

    def set_active_task(self, task_id):
        self.app_data["active_task_id"] = task_id
        self.save_app_data()

        self.focus_page.load_active_task()
        self.show_focus_page()

    def update_sidebar_active_state(self):
        buttons = {
            "focus": self.focus_button,
            "study": self.todo_button,
            "pomodoro": self.pomodoro_button,
            "statistics": self.statistics_button,
            "settings": self.settings_button,
        }

        for page_name, button in buttons.items():
            if page_name == self.active_page:
                button.configure(
                    fg_color="#312E81",
                    hover_color="#312E81",
                    text_color="#F8FAFC"
                )
            else:
                button.configure(
                    fg_color="#1E293B",
                    hover_color="#334155",
                    text_color="#CBD5E1"
                )
    
    def get_pending_tasks(self):
        return [
            task for task in self.app_data.get("tasks", [])
            if task.get("status") != "completed"
        ]

    def start_task_queue(self):
        pending_tasks = self.get_pending_tasks()

        if not pending_tasks:
            return False

        queue_task_ids = [task.get("id") for task in pending_tasks]

        self.app_data["queue_mode_active"] = True
        self.app_data["queue_task_ids"] = queue_task_ids
        self.app_data["active_task_id"] = queue_task_ids[0]
        self.save_app_data()

        self.focus_page.load_active_task()
        self.focus_page.update_queue_progress()
        self.focus_page.refresh_queue_progress_visibility()
        self.show_focus_page()

        return True

    def stop_task_queue(self):
        self.app_data["queue_mode_active"] = False
        self.app_data["queue_task_ids"] = []
        self.app_data["active_task_id"] = None
        self.save_app_data()

        if hasattr(self, "focus_page"):
            self.focus_page.reset_timer()
            self.focus_page.load_active_task()
            self.focus_page.update_queue_progress()
            self.focus_page.refresh_queue_progress_visibility()

        if hasattr(self, "todo_page"):
            self.todo_page.render_tasks()

    def mark_task_completed(self, task_id):
        if not task_id:
            return

        for task in self.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "completed"
                break

        self.save_app_data()

        if hasattr(self, "todo_page"):
            self.todo_page.render_tasks()

        if hasattr(self, "focus_page"):
            self.focus_page.update_queue_progress()

    def move_to_next_queue_task(self):
        if not self.app_data.get("queue_mode_active", False):
            return False

        queue_task_ids = self.app_data.get("queue_task_ids", [])
        tasks = self.app_data.get("tasks", [])

        tasks_by_id = {
            task.get("id"): task
            for task in tasks
        }

        for task_id in queue_task_ids:
            task = tasks_by_id.get(task_id)

            if task and task.get("status") != "completed":
                self.app_data["active_task_id"] = task_id
                self.save_app_data()

                if hasattr(self, "focus_page"):
                    self.focus_page.load_active_task()
                    self.focus_page.update_queue_progress()

                return True

        self.app_data["queue_mode_active"] = False
        self.app_data["queue_task_ids"] = []
        self.app_data["active_task_id"] = None
        self.save_app_data()

        if hasattr(self, "focus_page"):
            self.focus_page.load_active_task()
            self.focus_page.update_queue_progress()

        return False
    
    def mark_task_completed(self, task_id):
        if not task_id:
            return

        for task in self.app_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "completed"
                break

        self.save_app_data()

        if hasattr(self, "todo_page"):
            self.todo_page.render_tasks()