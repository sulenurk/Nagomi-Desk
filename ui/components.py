import customtkinter as ctk

from ui.theme import COLORS, PRIORITY_COLORS, SUBJECT_COLORS


class AppCard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["card_border"],
            **kwargs
        )


class PageTitle(ctk.CTkLabel):
    def __init__(self, parent, text):
        super().__init__(
            parent,
            text=text,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=28, weight="bold")
        )


class PageSubtitle(ctk.CTkLabel):
    def __init__(self, parent, text):
        super().__init__(
            parent,
            text=text,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=14)
        )


class PrimaryButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, width=120, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=42,
            corner_radius=14,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=14, weight="bold"),
            **kwargs
        )


class SecondaryButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, width=120, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=38,
            corner_radius=14,
            fg_color=COLORS["card_soft"],
            hover_color="#334155",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
            **kwargs
        )


class SidebarButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, active=False, **kwargs):
        fg = COLORS["primary_soft"] if active else "transparent"
        hover = COLORS["primary_soft"] if active else COLORS["card_soft"]

        super().__init__(
            parent,
            text=text,
            command=command,
            height=44,
            corner_radius=14,
            fg_color=fg,
            hover_color=hover,
            text_color=COLORS["text"],
            anchor="w",
            font=ctk.CTkFont(size=14),
            **kwargs
        )


class PillButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, active=False, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            height=34,
            corner_radius=14,
            fg_color=COLORS["primary_soft"] if active else COLORS["surface_light"],
            hover_color=COLORS["primary_soft"],
            text_color=COLORS["white"] if active else COLORS["muted"],
            font=ctk.CTkFont(size=12, weight="bold"),
            **kwargs
        )


class PriorityBadge(ctk.CTkLabel):
    def __init__(self, parent, priority):
        color = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["medium"])
        text = priority.capitalize()

        super().__init__(
            parent,
            text=text,
            fg_color=color,
            text_color=COLORS["white"],
            corner_radius=10,
            padx=12,
            pady=5,
            font=ctk.CTkFont(size=12, weight="bold")
        )


class SubjectIcon(ctk.CTkLabel):
    def __init__(self, parent, subject_key=None, icon_text="•", color=None):
        color = color or SUBJECT_COLORS.get(subject_key, SUBJECT_COLORS["default"])

        super().__init__(
            parent,
            text=icon_text,
            width=42,
            height=42,
            fg_color=color,
            text_color=COLORS["white"],
            corner_radius=12,
            font=ctk.CTkFont(size=18, weight="bold")
        )


class AppEntry(ctk.CTkEntry):
    def __init__(self, parent, placeholder_text="", **kwargs):
        super().__init__(
            parent,
            placeholder_text=placeholder_text,
            height=42,
            corner_radius=12,
            fg_color=COLORS["input"],
            text_color=COLORS["input_text"],
            placeholder_text_color="#6B7280",
            border_width=1,
            border_color=COLORS["card_border"],
            font=ctk.CTkFont(size=13),
            **kwargs
        )

class MetricCard(AppCard):
    def __init__(self, parent, title, value, accent_color=None, **kwargs):
        super().__init__(parent, **kwargs)

        if accent_color is None:
            accent_color = COLORS["primary"]

        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=18, pady=(18, 4), sticky="w")

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=accent_color,
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.value_label.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

    def update(self, title=None, value=None):
        if title is not None:
            self.title_label.configure(text=title)

        if value is not None:
            self.value_label.configure(text=value)

class Tooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None

        self.widget.bind("<Enter>", self.schedule_show, add="+")
        self.widget.bind("<Leave>", self.hide, add="+")
        self.widget.bind("<ButtonPress>", self.hide, add="+")

    def schedule_show(self, event=None):
        self.cancel_scheduled_show()
        self.after_id = self.widget.after(self.delay, self.show)

    def cancel_scheduled_show(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def show(self):
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes("-topmost", True)

        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
            corner_radius=8,
            padx=10,
            pady=6,
            font=ctk.CTkFont(size=12)
        )
        label.pack()

    def hide(self, event=None):
        self.cancel_scheduled_show()

        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
