import json
import customtkinter as ctk
from pathlib import Path
from ui.pomodoro_page import PomodoroPage
from ui.statistics_page import StatisticsPage
from ui.focus_page import FocusPage
from ui.study_plan_page import StudyPlanPage
from ui.subjects_page import SubjectsPage
from ui.settings_page import SettingsPage
from ui.theme import COLORS, SUBJECT_COLOR_PALETTE, apply_color_palette

class FocusFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.base_path = Path(__file__).resolve().parent.parent
        self.data_path = self.base_path / "data" / "app_data.json"

        self.app_data = self.load_app_data()
        self.ensure_app_data_defaults()
        self.apply_saved_theme()
        self.language = self.app_data.get("language", "en")
        self.translations = self.load_translations()

        self.active_page = "pomodoro"

        self.title(self.t("app_name"))
        self.geometry("1000x650")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg"])

        ctk.set_appearance_mode(self.app_data["settings"].get("appearance_mode", "dark"))
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()

        self.show_pomodoro_page()

    def ensure_app_data_defaults(self):
        self.app_data.setdefault("language", "en")

        self.app_data.setdefault("active_task_id", None)
        self.app_data.setdefault("queue_mode_active", False)
        self.app_data.setdefault("queue_task_ids", [])
        self.app_data.setdefault("last_queue_state", None)

        settings = self.app_data.setdefault("settings", {})

        default_settings = {
            "auto_start_break": False,
            "auto_start_focus": False,
            "sound_enabled": True,
            "daily_focus_goal_minutes": 300,
            "regular_focus_minutes": 25,
            "regular_short_break_minutes": 5,
            "regular_long_break_minutes": 15,
            "regular_long_break_after": 4,
            "regular_focus_count": 4,
            "show_queue_progress": True,
            "show_cumulative_away_time": True,
            "week_start_day": "monday",
            "appearance_mode": "dark",
            "color_palette": "purple"
        }

        for key, value in default_settings.items():
            settings.setdefault(key, value)

        self.app_data.setdefault("tasks", [])
        self.app_data.setdefault("sessions", [])

        subjects = self.app_data.setdefault("subjects", [])

        default_subject = None

        for subject in subjects:
            if subject.get("id") == "subject_other" or subject.get("is_default"):
                default_subject = subject
                break

        if default_subject is None:
            subjects.insert(0, {
                "id": "subject_other",
                "name_key": "other_subject",
                "color": "#A78BFA",
                "is_default": True
            })
        else:
            default_subject["id"] = "subject_other"
            default_subject["name_key"] = "other_subject"
            default_subject["is_default"] = True
            default_subject.setdefault("color", "#A78BFA")
            default_subject.pop("name", None)

        for task in self.app_data.get("tasks", []):
            task.setdefault("status", "pending")
            task.setdefault("hidden_from_plan", False)
            task.setdefault("hidden_from_completed", False)

        # Older data did not guarantee a color for every subject.  Keep any
        # existing choice intact and assign a stable palette color only when
        # one is missing.
        for index, subject in enumerate(subjects):
            subject.setdefault("color", SUBJECT_COLOR_PALETTE[index % len(SUBJECT_COLOR_PALETTE)])

        self.save_app_data()

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
    
    def get_subject_display_name(self, subject):
        if not subject:
            return self.t("other_subject")

        if subject.get("is_default") or subject.get("id") == "subject_other":
            return self.t(subject.get("name_key", "other_subject"))

        return subject.get("name", self.t("other_subject"))

    def get_subject_by_id(self, subject_id):
        for subject in self.app_data.get("subjects", []):
            if subject.get("id") == subject_id:
                return subject
        return next(
            (subject for subject in self.app_data.get("subjects", []) if subject.get("is_default")),
            None
        )

    def get_subject_color(self, subject_id=None, fallback=None):
        subject = self.get_subject_by_id(subject_id)
        if subject:
            return subject.get("color", COLORS["primary"])
        return fallback or COLORS["primary"]

    def apply_saved_theme(self):
        settings = self.app_data.setdefault("settings", {})
        apply_color_palette(
            settings.get("color_palette", "purple"),
            settings.get("appearance_mode", "dark")
        )

    def apply_theme(self, palette_key=None, appearance_mode=None):
        settings = self.app_data.setdefault("settings", {})
        if palette_key:
            settings["color_palette"] = palette_key
        if appearance_mode:
            settings["appearance_mode"] = appearance_mode

        self.apply_saved_theme()
        ctk.set_appearance_mode(settings["appearance_mode"])
        self.configure(fg_color=COLORS["bg"])
        self.save_app_data()

        # Widget colors are set at creation time in CustomTkinter. Rebuild the
        # shell so the new palette is applied consistently everywhere.
        active_page = self.active_page
        timer_states = {}
        # Stop the old page timers before their widgets are replaced; their
        # scheduled callbacks will then exit without touching destroyed UI.
        for page_name in ("focus_page", "pomodoro_page"):
            page = getattr(self, page_name, None)
            if page is not None:
                timer_states[page_name] = {
                    "is_running": page.is_running,
                    "is_paused": page.is_paused,
                    "current_mode": page.current_mode,
                    "remaining_seconds": page.remaining_seconds,
                }
                page.is_running = False
                page.is_paused = False
        self.sidebar.destroy()
        self.page_container.destroy()
        self.create_sidebar()
        self.create_pages()
        self.restore_timer_state(timer_states)
        self.show_page(active_page)

    def restore_timer_state(self, timer_states):
        for page_name, state in timer_states.items():
            page = getattr(self, page_name)
            page.current_mode = state["current_mode"]
            page.remaining_seconds = state["remaining_seconds"]
            page.is_paused = state["is_paused"]
            page.is_running = state["is_running"]
            if page_name == "focus_page":
                page.timer_label.configure(text=page.format_time(page.remaining_seconds))
                page.update_mode_ui()
            else:
                page.update_timer_label()
                page.update_mode_ui()
            if page.is_running:
                page.count_down()

    def show_page(self, page):
        {
            "pomodoro": self.show_pomodoro_page,
            "study": self.show_todo_page,
            "focus": self.show_focus_page,
            "subjects": self.show_subjects_page,
            "statistics": self.show_statistics_page,
            "settings": self.show_settings_page,
        }.get(page, self.show_pomodoro_page)()

    def toggle_appearance_mode(self):
        current = self.app_data["settings"].get("appearance_mode", "dark")
        self.apply_theme(appearance_mode="light" if current == "dark" else "dark")

    def toggle_sound(self):
        settings = self.app_data.setdefault("settings", {})
        settings["sound_enabled"] = not settings.get("sound_enabled", True)
        self.save_app_data()
        self.update_quick_actions()
        if hasattr(self, "settings_page"):
            self.settings_page.load_settings()

    def play_alarm(self):
        if not self.app_data.get("settings", {}).get("sound_enabled", True):
            return
        self.bell()
        self.after(180, self.bell)
    
    def get_language_options(self):
        return {
            "tr": "Türkçe",
            "en": "English"
        }

    def get_language_display_name(self, language_code):
        return self.get_language_options().get(language_code, language_code)


    def get_language_code_from_display_name(self, display_name):
        for code, name in self.get_language_options().items():
            if name == display_name:
                return code

        return self.language

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=self.t("app_name"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.pomodoro_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("regular_pomodoro"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_pomodoro_page
        )
        self.pomodoro_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.todo_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("study_plan"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_todo_page
        )
        self.todo_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.focus_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("focus_timer"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_focus_page
        )
        self.focus_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.subjects_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("subjects"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_subjects_page
        )
        self.subjects_button.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.statistics_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("statistics"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_statistics_page
        )
        self.statistics_button.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text=self.t("settings"),
            height=42,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["surface_light"],
            anchor="w",
            command=self.show_settings_page
        )
        self.settings_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # 1. Ortak bir alt çerçeve oluşturuyoruz
        self.bottom_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        # sticky değerini "ew" yerine "ews" veya "s" yaparak en alta yaslıyoruz:
        self.bottom_container.grid(row=7, column=0, padx=20, pady=(0, 30), sticky="ews")

        # 2. Butonların çerçevesini bu yeni ortak çerçevenin içine koyuyoruz (row=0)
        self.quick_actions = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.quick_actions.grid(row=0, column=0, sticky="ew", pady=(0, 8)) # pady=(0, 8) ile butonların altına 8px boşluk verdik

        self.quick_actions.grid_columnconfigure((0, 1), weight=1)

        # --- Buton tanımlamaların (Aynen kalıyor, sadece parent'ı self.quick_actions) ---
        self.mode_button = ctk.CTkButton(
            self.quick_actions, text="", width=42, height=42, corner_radius=21,
            command=self.toggle_appearance_mode, fg_color=COLORS["card_soft"],
            hover_color=COLORS["primary_soft"], text_color=COLORS["text"]
        )
        self.mode_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.sound_button = ctk.CTkButton(
            self.quick_actions, text="", width=42, height=42, corner_radius=21,
            command=self.toggle_sound, fg_color=COLORS["card_soft"],
            hover_color=COLORS["primary_soft"], text_color=COLORS["text"]
        )
        self.sound_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self.update_quick_actions()
        # -----------------------------------------------------------------

        # 3. Dil menüsünü de aynı ortak çerçevenin içine koyuyoruz (row=1)
        language_options = self.get_language_options()

        self.language_menu = ctk.CTkOptionMenu(
            self.bottom_container, # Parent artık self.bottom_container
            values=list(language_options.values()),
            fg_color=COLORS["card_soft"],
            button_color=COLORS["surface_light"],
            button_hover_color=COLORS["primary_soft"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface"],
            dropdown_text_color=COLORS["text"],
            command=self.change_language
        )
        self.language_menu.set(self.get_language_display_name(self.language))
        # Dil menüsünün üst boşluğunu (pady) burada kontrol edebilirsin:
        self.language_menu.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def hide_sidebar(self):
        self.sidebar.grid_remove()

    def show_sidebar(self):
        self.sidebar.grid()

    def create_pages(self):
        self.page_container = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg"])
        self.page_container.grid(row=0, column=1, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.focus_page = FocusPage(self.page_container, self)
        self.todo_page = StudyPlanPage(self.page_container, self)
        self.pomodoro_page = PomodoroPage(self.page_container, self)
        self.subjects_page = SubjectsPage(self.page_container, self)
        self.settings_page = SettingsPage(self.page_container, self)
        self.statistics_page = StatisticsPage(self.page_container, self)
        
        self.focus_page.grid(row=0, column=0, sticky="nsew")
        self.todo_page.grid(row=0, column=0, sticky="nsew")
        self.pomodoro_page.grid(row=0, column=0, sticky="nsew")
        self.subjects_page.grid(row=0, column=0, sticky="nsew")
        self.statistics_page.grid(row=0, column=0, sticky="nsew")
        self.settings_page.grid(row=0, column=0, sticky="nsew")

    def update_quick_actions(self):
        if not hasattr(self, "mode_button"):
            return
        mode = self.app_data["settings"].get("appearance_mode", "dark")
        sound_on = self.app_data["settings"].get("sound_enabled", True)
        self.mode_button.configure(text="☀" if mode == "dark" else "☾")
        self.sound_button.configure(text="🔔" if sound_on else "🔕")

    def show_focus_page(self):
        self.active_page = "focus"
        self.update_sidebar_active_state()
        self.focus_page.tkraise()
        if hasattr(self.focus_page, "refresh_page"):
            self.focus_page.refresh_page()
        elif hasattr(self.focus_page, "refresh_texts"):
            self.focus_page.refresh_texts()

    def show_todo_page(self):
        self.active_page = "study"
        self.update_sidebar_active_state()

        if hasattr(self.todo_page, "refresh_subject_menu"):
            self.todo_page.refresh_subject_menu()

        if hasattr(self.todo_page, "render_tasks"):
            self.todo_page.render_tasks()

        self.todo_page.tkraise()

    def show_pomodoro_page(self):
        self.active_page = "pomodoro"
        self.update_sidebar_active_state()
        self.pomodoro_page.tkraise()

        if hasattr(self, "pomodoro_page"):
            self.pomodoro_page.update_auto_start_info()

    def show_subjects_page(self):
        self.active_page = "subjects"
        self.update_sidebar_active_state()
        self.subjects_page.tkraise()

        if hasattr(self.subjects_page, "refresh_texts"):
            self.subjects_page.refresh_texts()

        if hasattr(self.subjects_page, "focus_subject_entry"):
            self.subjects_page.focus_subject_entry()

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
        language_code = self.get_language_code_from_display_name(selected_language)

        self.language = language_code
        self.app_data["language"] = language_code
        self.save_app_data()

        self.translations = self.load_translations()
        self.refresh_texts()

    def refresh_texts(self):
        self.title(self.t("app_name"))

        self.logo_label.configure(text=self.t("app_name"))
        self.focus_button.configure(text=self.t("focus_timer"))
        self.todo_button.configure(text=self.t("study_plan"))
        self.pomodoro_button.configure(text=self.t("regular_pomodoro"))
        self.subjects_button.configure(text=self.t("subjects"))
        self.statistics_button.configure(text=self.t("statistics"))
        self.settings_button.configure(text=self.t("settings"))

        if hasattr(self, "language_menu"):
            self.language_menu.configure(values=list(self.get_language_options().values()))
            self.language_menu.set(self.get_language_display_name(self.language))
            
        self.focus_page.refresh_texts()
        self.todo_page.refresh_texts()
        self.pomodoro_page.refresh_texts()
        self.subjects_page.refresh_texts()
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
        self.app_data["last_queue_state"] = None
        self.save_app_data()

        if hasattr(self, "focus_page"):
            self.focus_page.load_active_task()
            self.focus_page.update_queue_progress()
            self.focus_page.refresh_queue_progress_visibility()

            if hasattr(self.focus_page, "clear_status_message"):
                self.focus_page.clear_status_message()

        if hasattr(self, "todo_page"):
            self.todo_page.render_tasks()

        self.show_focus_page()

    def update_sidebar_active_state(self):
        buttons = {
            "focus": self.focus_button,
            "study": self.todo_button,
            "pomodoro": self.pomodoro_button,
            "subjects": self.subjects_button,
            "statistics": self.statistics_button,
            "settings": self.settings_button,
        }

        for page_name, button in buttons.items():
            if page_name == self.active_page:
                button.configure(
                    fg_color=COLORS["primary_soft"],
                    hover_color=COLORS["primary_soft"],
                    text_color=COLORS["white"]
                )
            else:
                button.configure(
                    fg_color=COLORS["card_soft"],
                    hover_color=COLORS["surface_light"],
                    text_color=COLORS["soft"]
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
        self.app_data["last_queue_state"] = None
        self.save_app_data()

        if hasattr(self, "focus_page"):
            self.focus_page.load_active_task()
            self.focus_page.update_queue_progress()
            self.focus_page.refresh_queue_progress_visibility()

            if hasattr(self.focus_page, "clear_status_message"):
                self.focus_page.clear_status_message()

        if hasattr(self, "todo_page"):
            self.todo_page.render_tasks()

        if hasattr(self, "focus_page"):
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
                    self.focus_page.refresh_queue_progress_visibility()

                if hasattr(self, "todo_page"):
                    self.todo_page.render_tasks()

                return True
        self.app_data["queue_mode_active"] = False
        self.app_data["queue_task_ids"] = []
        self.app_data["active_task_id"] = None
        self.app_data["last_queue_state"] = "completed"
        self.save_app_data()

        if hasattr(self, "focus_page"):
            self.focus_page.load_active_task()
            self.focus_page.update_queue_progress()

        return False
