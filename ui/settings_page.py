import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, PrimaryButton, AppEntry


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_settings_card()
        self.load_settings()

    def create_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=36, pady=(30, 12), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = PageTitle(self.header, self.app.t("settings"))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = PageSubtitle(
            self.header,
            self.app.t("settings_subtitle")
        )
        self.subtitle_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

    def create_settings_card(self):
        self.settings_card = AppCard(self)
        self.settings_card.grid(row=1, column=0, padx=36, pady=(12, 30), sticky="ew")
        self.settings_card.grid_columnconfigure(0, weight=1)

        self.auto_break_frame = self.create_setting_row(
            row=0,
            title_key="auto_start_break",
            description_key="auto_start_break_desc"
        )

        self.auto_break_switch = ctk.CTkSwitch(
            self.auto_break_frame,
            text="",
            progress_color=COLORS["primary"],
            button_color=COLORS["text"],
            button_hover_color=COLORS["soft"],
            command=self.save_settings
        )
        self.auto_break_switch.grid(row=0, column=1, rowspan=2, padx=20, pady=18)

        self.auto_focus_frame = self.create_setting_row(
            row=1,
            title_key="auto_start_focus",
            description_key="auto_start_focus_desc"
        )

        self.auto_focus_switch = ctk.CTkSwitch(
            self.auto_focus_frame,
            text="",
            progress_color=COLORS["primary"],
            button_color=COLORS["text"],
            button_hover_color=COLORS["soft"],
            command=self.save_settings
        )
        self.auto_focus_switch.grid(row=0, column=1, rowspan=2, padx=20, pady=18)

        self.sound_frame = self.create_setting_row(
            row=2,
            title_key="sound_notification",
            description_key="sound_notification_desc"
        )

        self.sound_switch = ctk.CTkSwitch(
            self.sound_frame,
            text="",
            progress_color=COLORS["primary"],
            button_color=COLORS["text"],
            button_hover_color=COLORS["soft"],
            command=self.save_settings
        )
        self.sound_switch.grid(row=0, column=1, rowspan=2, padx=20, pady=18)

        self.queue_progress_frame = self.create_setting_row(
            row=3,
            title_key="show_queue_progress",
            description_key="show_queue_progress_desc"
        )

        self.queue_progress_switch = ctk.CTkSwitch(
            self.queue_progress_frame,
            text="",
            progress_color=COLORS["primary"],
            button_color=COLORS["text"],
            button_hover_color=COLORS["soft"],
            command=self.save_settings
        )
        self.queue_progress_switch.grid(row=0, column=1, rowspan=2, padx=20, pady=18)

        self.goal_frame = ctk.CTkFrame(
            self.settings_card,
            fg_color="transparent"
        )
        self.goal_frame.grid(row=4, column=0, padx=20, pady=(8, 20), sticky="ew")
        self.goal_frame.grid_columnconfigure(0, weight=1)

        self.goal_title = ctk.CTkLabel(
            self.goal_frame,
            text=self.app.t("daily_focus_goal"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.goal_title.grid(row=0, column=0, sticky="w")

        self.goal_desc = ctk.CTkLabel(
            self.goal_frame,
            text=self.app.t("daily_focus_goal_desc"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13)
        )
        self.goal_desc.grid(row=1, column=0, pady=(4, 0), sticky="w")

        self.goal_entry = AppEntry(
            self.goal_frame,
            placeholder_text=self.app.t("minutes_short"),
            width=120
        )
        self.goal_entry.grid(row=0, column=1, rowspan=2, padx=(20, 10), sticky="e")

        self.save_button = PrimaryButton(
            self.goal_frame,
            text=self.app.t("save"),
            command=self.save_settings,
            width=100
        )
        self.save_button.grid(row=0, column=2, rowspan=2, sticky="e")

        self.status_label = ctk.CTkLabel(
            self.settings_card,
            text="",
            text_color=COLORS["green"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_label.grid(row=5, column=0, padx=20, pady=(0, 18), sticky="w")

    def create_setting_row(self, row, title_key, description_key):
        frame = ctk.CTkFrame(
            self.settings_card,
            fg_color=COLORS["surface"],
            corner_radius=18
        )
        frame.grid(row=row, column=0, padx=20, pady=(18 if row == 0 else 8, 8), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text=self.app.t(title_key),
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        title.grid(row=0, column=0, padx=18, pady=(16, 2), sticky="w")

        desc = ctk.CTkLabel(
            frame,
            text=self.app.t(description_key),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            wraplength=520,
            justify="left"
        )
        desc.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        frame.title_label = title
        frame.desc_label = desc
        frame.title_key = title_key
        frame.description_key = description_key

        return frame

    def get_settings(self):
        return self.app.app_data.setdefault("settings", {})

    def load_settings(self):
        settings = self.get_settings()

        if settings.get("auto_start_break", False):
            self.auto_break_switch.select()
        else:
            self.auto_break_switch.deselect()

        if settings.get("auto_start_focus", False):
            self.auto_focus_switch.select()
        else:
            self.auto_focus_switch.deselect()

        if settings.get("sound_enabled", True):
            self.sound_switch.select()
        else:
            self.sound_switch.deselect()
        
        if settings.get("show_queue_progress", True):
            self.queue_progress_switch.select()
        else:
            self.queue_progress_switch.deselect()

        goal = settings.get("daily_focus_goal_minutes", 300)
        self.goal_entry.delete(0, "end")
        self.goal_entry.insert(0, str(goal))

    def save_settings(self):
        settings = self.get_settings()

        settings["auto_start_break"] = bool(self.auto_break_switch.get())
        settings["auto_start_focus"] = bool(self.auto_focus_switch.get())
        settings["sound_enabled"] = bool(self.sound_switch.get())

        goal_value = self.goal_entry.get().strip()

        try:
            goal_minutes = int(goal_value)
            if goal_minutes > 0:
                settings["daily_focus_goal_minutes"] = goal_minutes
        except ValueError:
            pass

        settings["show_queue_progress"] = bool(self.queue_progress_switch.get())

        if hasattr(self.app, "focus_page"):
            self.app.focus_page.refresh_queue_progress_visibility()

        self.app.save_app_data()
        self.status_label.configure(text=self.app.t("settings_saved"))

        self.after(2000, lambda: self.status_label.configure(text=""))

    def refresh_texts(self):
        self.title_label.configure(text=self.app.t("settings"))
        self.subtitle_label.configure(text=self.app.t("settings_subtitle"))

        for frame in [
            self.auto_break_frame,
            self.auto_focus_frame,
            self.sound_frame,
            self.queue_progress_frame
        ]:
            frame.title_label.configure(text=self.app.t(frame.title_key))
            frame.desc_label.configure(text=self.app.t(frame.description_key))

        self.goal_title.configure(text=self.app.t("daily_focus_goal"))
        self.goal_desc.configure(text=self.app.t("daily_focus_goal_desc"))
        self.goal_entry.configure(placeholder_text=self.app.t("minutes_short"))
        self.save_button.configure(text=self.app.t("save"))