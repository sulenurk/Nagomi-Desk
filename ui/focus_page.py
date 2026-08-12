from datetime import datetime
import uuid
import customtkinter as ctk

from ui.theme import COLORS
from ui.components import AppCard, PageTitle, PageSubtitle, PrimaryButton, SecondaryButton, Tooltip, FullscreenSecondaryButton, FullscreenPrimaryButton


class FocusPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        self.is_running = False
        self.is_paused = False

        self.current_mode = "focus"  # focus or break
        self.is_waiting_for_next = False

        self.is_extra_time = False
        self.extra_time_seconds = 0
        self.is_waiting_for_completion_choice = False
        
        self.fullscreen_mode = False
        self.fullscreen_frame = None
        self.fullscreen_timer_label = None
        self.fullscreen_task_label = None
        self.fullscreen_subject_label = None
        self.fullscreen_alarm_frame = None
        self.fullscreen_start_button = None
        self.fullscreen_status_label = None
        self.fullscreen_button_frame = None
        self.fullscreen_exit_button = None
        self.fullscreen_extra_time_button = None
        self.fullscreen_finish_extra_time_button = None

        self.skip_break_button = None
        self.fullscreen_skip_break_button = None

        self.previous_geometry = None
        self.previous_window_state = None

        self.fullscreen_resize_bind_id = None
        self.fullscreen_resize_after_id = None

        self.stop_alarm_button = None
        self.fullscreen_stop_alarm_button = None

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

    def toggle_fullscreen(self):

        if self.fullscreen_mode:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):

        self.fullscreen_mode = True

        root = self.app

        # Eski pencere boyutunu ve durumunu sakla.
        self.previous_geometry = root.geometry()
        self.previous_window_state = root.state()

        # Gerçek fullscreen yerine çerçeveli büyütülmüş görünüm.
        root.attributes("-fullscreen", False)
        root.state("zoomed")
        root.minsize(220, 150)

        # mevcut arayüzü gizle
        self.header.grid_remove()
        self.content.grid_remove()
        self.app.hide_sidebar()
        

        self.create_fullscreen_view() 
        self.load_active_task()   

        self.app.update_minimal_always_on_top()

        self.fullscreen_resize_bind_id = root.bind(
            "<Configure>",
            self._schedule_fullscreen_resize,
            add="+"
        )

        root.after_idle(self.resize_fullscreen_view)

        root.bind(
            "<Escape>",
            lambda event: self.exit_fullscreen()
        )

    def exit_fullscreen(self):

        self.fullscreen_mode = False

        self.app.update_minimal_always_on_top()

        if self.fullscreen_resize_after_id is not None:
            try:
                self.app.after_cancel(
                    self.fullscreen_resize_after_id
                )
            except Exception:
                pass

            self.fullscreen_resize_after_id = None

        if self.fullscreen_resize_bind_id is not None:
            try:
                self.app.unbind(
                    "<Configure>",
                    self.fullscreen_resize_bind_id
                )
            except Exception:
                pass

            self.fullscreen_resize_bind_id = None

        self.app.unbind("<Escape>")

        root = self.app
        root.attributes("-fullscreen", False)

        if self.previous_window_state == "zoomed":
            root.state("zoomed")
        else:
            root.state("normal")

            if self.previous_geometry:
                root.geometry(self.previous_geometry)

        if self.fullscreen_frame:
            self.fullscreen_frame.destroy()
            self.fullscreen_alarm_frame = None
            self.fullscreen_stop_alarm_button = None

            if (
                getattr(self.app, "alarm_active", False)
                and getattr(self.app, "alarm_source", None) == "focus"
            ):
                self.show_normal_alarm_button()
            
            self.fullscreen_frame = None

        self.fullscreen_start_button = None
        self.fullscreen_timer_label = None
        self.fullscreen_status_label = None
        self.fullscreen_task_label = None
        self.fullscreen_button_frame = None
        self.fullscreen_exit_button = None
        self.fullscreen_alarm_frame = None
        self.fullscreen_stop_alarm_button = None

        self.header.grid()
        self.content.grid()
        root.minsize(1100, 700)
        self.app.show_sidebar()

    def update_fullscreen_task_info(self):

        if not self.fullscreen_task_label:
            return

        task = self.app.get_active_task()

        if not task:

            self.fullscreen_task_label.configure(
                text=self.app.t("no_active_task")
            )

            return


        subject = task.get("subject_name")

        if not subject:
            subject = self.app.t(
                task.get("subject", "other")
            )


        title = task.get("task_name") or task.get("title", "")


        self.fullscreen_task_label.configure(
            text=f"{subject} · {title}"
        )

    def _schedule_fullscreen_resize(self, event=None):
        if not self.fullscreen_mode:
            return

        if event is not None and event.widget != self.app:
            return

        if self.fullscreen_resize_after_id is not None:
            return

        self.fullscreen_resize_after_id = self.app.after_idle(
            self.resize_fullscreen_view
        )

    def resize_fullscreen_view(self):
        self.fullscreen_resize_after_id = None

        if not self.fullscreen_mode:
            return

        if (
            self.fullscreen_frame is None
            or not self.fullscreen_frame.winfo_exists()
        ):
            return

        window_width = max(
            self.app.winfo_width(),
            1
        )

        window_height = max(
            self.app.winfo_height(),
            1
        )

        compact_mode = (
            window_width < 420
            or window_height < 300
        )

        tiny_mode = (
            window_width < 280
            or window_height < 190
        )

        width_scale = window_width / 1360
        height_scale = window_height / 820

        scale = min(
            width_scale,
            height_scale
        )

        scale = max(
            0.20,
            min(scale, 1.55)
        )

        timer_font_size = max(
            28,
            min(int(280 * scale), 430)
        )

        status_font_size = max(
            11,
            min(int(28 * scale), 40)
        )

        task_font_size = max(
            9,
            min(int(20 * scale), 28)
        )

        primary_button_width = max(
            64,
            min(int(150 * scale), 190)
        )

        primary_button_height = max(
            30,
            min(int(54 * scale), 68)
        )

        secondary_button_size = max(
            26,
            min(int(54 * scale), 78)
        )

        button_font_size = max(
            10,
            min(int(18 * scale), 24)
        )

        horizontal_padding = max(
            3,
            min(int(10 * scale), 16)
        )

        # Başlık ve görev bilgisi
        if compact_mode:
            self.fullscreen_status_label.grid_remove()
            self.fullscreen_task_label.grid_remove()
        else:
            self.fullscreen_status_label.grid(
                row=1,
                column=0,
                pady=(8, 16)
            )

            self.fullscreen_task_label.grid(
                row=5,
                column=0,
                pady=(6, 10),
                sticky="n"
            )

        # Fontlar
        self.fullscreen_timer_label.configure(
            font=ctk.CTkFont(
                size=timer_font_size,
                weight="bold"
            )
        )

        self.fullscreen_status_label.configure(
            font=ctk.CTkFont(
                size=status_font_size,
                weight="bold"
            )
        )

        self.fullscreen_task_label.configure(
            font=ctk.CTkFont(
                size=task_font_size,
                weight="bold"
            )
        )

        # Start/Pause butonu
        if tiny_mode:
            start_width = 58
            start_height = 26
            start_font_size = 9

        elif compact_mode:
            start_width = max(
                78,
                min(int(120 * scale), 110)
            )

            start_height = max(
                30,
                min(int(46 * scale), 42)
            )

            start_font_size = max(
                10,
                min(int(15 * scale), 14)
            )

        else:
            start_width = primary_button_width
            start_height = primary_button_height
            start_font_size = button_font_size

        self.fullscreen_start_button.configure(
            width=start_width,
            height=start_height,
            corner_radius=max(
                10,
                start_height // 3
            ),
            font=ctk.CTkFont(
                size=start_font_size,
                weight="bold"
            )
        )

        # Çıkış butonu
        self.fullscreen_exit_button.configure(
            width=secondary_button_size,
            height=secondary_button_size,
            corner_radius=secondary_button_size // 2,
            font=ctk.CTkFont(
                size=button_font_size,
                weight="bold"
            )
        )

        if (
            self.is_waiting_for_completion_choice
            or self.is_extra_time
        ):
            self.fullscreen_start_button.grid_remove()
        else:
            self.fullscreen_start_button.grid(
                row=0,
                column=0,
                padx=3 if tiny_mode else horizontal_padding
            )

        self.fullscreen_exit_button.grid_configure(
            row=0,
            column=2,
            padx=3 if tiny_mode else horizontal_padding
        )

        # Skip Break butonu
        if (
            self.fullscreen_skip_break_button is not None
            and self.fullscreen_skip_break_button.winfo_exists()
        ):
            if tiny_mode:
                skip_width = 72
                skip_height = 24
                skip_font_size = 8

            elif compact_mode:
                skip_width = max(
                    90,
                    min(int(150 * scale), 140)
                )

                skip_height = max(
                    26,
                    min(int(40 * scale), 36)
                )

                skip_font_size = max(
                    9,
                    min(int(12 * scale), 12)
                )

            else:
                skip_width = max(
                    110,
                    min(int(150 * scale), 180)
                )

                skip_height = max(
                    32,
                    min(int(46 * scale), 52)
                )

                skip_font_size = max(
                    10,
                    min(int(14 * scale), 16)
                )

            self.fullscreen_skip_break_button.configure(
                width=skip_width,
                height=skip_height,
                corner_radius=max(
                    8,
                    skip_height // 3
                ),
                font=ctk.CTkFont(
                    size=skip_font_size,
                    weight="bold"
                )
            )

        # Timer ve butonların dikey yerleşimi
        if tiny_mode:
            self.fullscreen_timer_label.grid_configure(
                pady=(30, 4)
            )

            self.fullscreen_button_frame.grid_configure(
                pady=(0, 2)
            )

        else:
            timer_bottom_padding = max(
                4,
                min(int(30 * scale), 40)
            )

            button_bottom_padding = max(
                2,
                min(int(18 * scale), 24)
            )

            self.fullscreen_timer_label.grid_configure(
                pady=(0, timer_bottom_padding)
            )

            self.fullscreen_button_frame.grid_configure(
                pady=(0, button_bottom_padding)
            )

        # Alarm alanı
        if (
            self.fullscreen_alarm_frame is not None
            and self.fullscreen_alarm_frame.winfo_exists()
        ):
            if tiny_mode:
                alarm_frame_height = 30
                alarm_frame_padx = 4
                alarm_frame_pady = (2, 2)

            elif compact_mode:
                alarm_frame_height = 44
                alarm_frame_padx = 12
                alarm_frame_pady = (4, 4)

            else:
                alarm_frame_height = max(
                    46,
                    min(int(54 * scale), 64)
                )

                alarm_frame_padx = 40
                alarm_frame_pady = (6, 6)

            self.fullscreen_alarm_frame.configure(
                height=alarm_frame_height
            )

            self.fullscreen_alarm_frame.grid_configure(
                padx=alarm_frame_padx,
                pady=alarm_frame_pady
            )

            self.fullscreen_alarm_frame.grid_propagate(False)

        # Stop alarm butonu
        alarm_button = self.fullscreen_stop_alarm_button

        if (
            alarm_button is not None
            and alarm_button.winfo_exists()
        ):
            if tiny_mode:
                alarm_button_width = 72
                alarm_button_height = 24
                alarm_button_font_size = 8

            elif compact_mode:
                alarm_button_width = max(
                    90,
                    min(int(180 * scale), 150)
                )

                alarm_button_height = max(
                    26,
                    min(int(40 * scale), 36)
                )

                alarm_button_font_size = max(
                    9,
                    min(int(12 * scale), 12)
                )

            else:
                alarm_button_width = max(
                    120,
                    min(int(210 * scale), 230)
                )

                alarm_button_height = max(
                    32,
                    min(int(46 * scale), 52)
                )

                alarm_button_font_size = max(
                    10,
                    min(int(14 * scale), 16)
                )

            alarm_button.configure(
                width=alarm_button_width,
                height=alarm_button_height,
                corner_radius=max(
                    8,
                    alarm_button_height // 3
                ),
                font=ctk.CTkFont(
                    size=alarm_button_font_size,
                    weight="bold"
                )
            )

            for button in (
                self.fullscreen_extra_time_button,
                self.fullscreen_finish_extra_time_button,
            ):
                if (
                    button is not None
                    and button.winfo_exists()
                ):
                    button.configure(
                        width=alarm_button_width,
                        height=alarm_button_height,
                        corner_radius=max(
                            8,
                            alarm_button_height // 3
                        ),
                        font=ctk.CTkFont(
                            size=alarm_button_font_size,
                            weight="bold"
                        )
                    )

            if (
                getattr(self.app, "alarm_active", False)
                and getattr(self.app, "alarm_source", None) == "focus"
            ):
                if self.is_waiting_for_completion_choice:
                    alarm_button.grid(
                        row=0,
                        column=0,
                        columnspan=1,
                        padx=4 if tiny_mode else 8,
                        pady=4
                    )
                else:
                    alarm_button.grid(
                        row=0,
                        column=0,
                        columnspan=2,
                        padx=4 if tiny_mode else 8,
                        pady=4
                    )
            else:
                alarm_button.grid_remove()

    def create_fullscreen_view(self):
        self.fullscreen_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg"]
        )

        self.fullscreen_frame.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        self.fullscreen_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self.fullscreen_frame.grid_rowconfigure(
            0,
            weight=1
        )

        self.fullscreen_frame.grid_rowconfigure(
            5,
            weight=0
        )

        self.fullscreen_frame.grid_rowconfigure(
            6,
            weight=1
        )


        # ÜST BOŞLUK
        self.fullscreen_top_spacer = ctk.CTkFrame(
            self.fullscreen_frame,
            fg_color="transparent"
        )

        self.fullscreen_top_spacer.grid(
            row=0,
            column=0,
            sticky="nsew"
        )


        # STATUS
        status_text = (
            self.app.t("extra_time")
            if self.is_extra_time
            else (
                self.app.t("break_mode")
                if self.current_mode == "break"
                else self.app.t("focus_mode")
            )
        )

        self.fullscreen_status_label = ctk.CTkLabel(
            self.fullscreen_frame,
            text=status_text,
            text_color=COLORS["primary"],
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        self.fullscreen_status_label.grid(
            row=1,
            column=0,
            pady=(8, 20)
        )


        # TIMER
        if self.is_extra_time:
            timer_text = self.format_time(
                self.extra_time_seconds
            )
        else:
            timer_text = self.format_time(
                self.remaining_seconds
            )

        self.fullscreen_timer_label = ctk.CTkLabel(
            self.fullscreen_frame,
            text=timer_text,
            text_color=COLORS["text"],
            font=ctk.CTkFont(
                size=150,
                weight="bold"
            )
        )

        self.fullscreen_timer_label.grid(
            row=2,
            column=0,
            pady=(0, 30)
        )


        # ANA BUTON FRAME
        self.fullscreen_button_frame = ctk.CTkFrame(
            self.fullscreen_frame,
            fg_color="transparent"
        )

        self.fullscreen_button_frame.grid(
            row=3,
            column=0,
            pady=(0, 18)
        )


        # START / PAUSE BUTTON
        if self.is_running:
            fullscreen_text = self.app.t("pause")
            fullscreen_command = self.pause_timer

        elif self.is_waiting_for_next:
            if self.current_mode == "break":
                fullscreen_text = self.app.t("start_break")
            else:
                fullscreen_text = self.app.t("start_focus")

            fullscreen_command = self.start_timer

        else:
            fullscreen_text = self.app.t("start")
            fullscreen_command = self.start_timer


        self.fullscreen_start_button = FullscreenPrimaryButton(
            self.fullscreen_button_frame,
            text=fullscreen_text,
            command=fullscreen_command
        )

        self.fullscreen_start_button.grid(
            row=0,
            column=0,
            padx=10
        )

        self.fullscreen_skip_break_button = FullscreenSecondaryButton(
            self.fullscreen_button_frame,
            text=self.app.t("skip_break"),
            command=self.skip_break
        )

        self.fullscreen_skip_break_button.grid(
            row=0,
            column=1,
            padx=10
        )

        if self.current_mode != "break":
            self.fullscreen_skip_break_button.grid_remove()

        # FULLSCREEN EXIT BUTTON
        self.fullscreen_exit_button = FullscreenSecondaryButton(
            self.fullscreen_button_frame,
            text="✕",
            command=self.exit_fullscreen
        )

        self.fullscreen_exit_button.grid(
            row=0,
            column=2,
            padx=10
        )

        Tooltip(
            self.fullscreen_exit_button,
            self.app.t("tooltip_exit_fullscreen")
        )


        # ALARM / EXTRA TIME FRAME
        self.fullscreen_alarm_frame = ctk.CTkFrame(
            self.fullscreen_frame,
            fg_color="transparent",
            height=64
        )

        self.fullscreen_alarm_frame.grid(
            row=4,
            column=0,
            padx=40,
            pady=0,
            sticky="ew"
        )

        self.fullscreen_alarm_frame.grid_columnconfigure(
            0,
            weight=0
        )

        self.fullscreen_alarm_frame.grid_columnconfigure(
            1,
            weight=0
        )

        self.fullscreen_alarm_frame.grid_anchor("center")

        self.fullscreen_alarm_frame.grid_rowconfigure(
            0,
            weight=1
        )

        self.fullscreen_alarm_frame.grid_propagate(False)


        # TASK LABEL
        self.fullscreen_task_label = ctk.CTkLabel(
            self.fullscreen_frame,
            text="",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        self.fullscreen_task_label.grid(
            row=5,
            column=0,
            pady=(6, 10),
            sticky="n"
        )


        # ALT BOŞLUK
        self.fullscreen_bottom_spacer = ctk.CTkFrame(
            self.fullscreen_frame,
            fg_color="transparent"
        )

        self.fullscreen_bottom_spacer.grid(
            row=6,
            column=0,
            sticky="nsew"
        )


        # -------------------------------------------------
        # CURRENT TIMER STATE'E GÖRE FULLSCREEN CONTROLS
        # -------------------------------------------------

        if self.is_waiting_for_completion_choice:

            # Focus bitti:
            # Stop Alarm + Extra Time
            self.show_fullscreen_alarm_button()

            self.fullscreen_start_button.grid_remove()


        elif self.is_extra_time:

            # Extra Time aktif:
            # yalnızca Finish
            self.fullscreen_start_button.grid_remove()

            if (
                self.fullscreen_finish_extra_time_button is None
                or not self.fullscreen_finish_extra_time_button.winfo_exists()
            ):
                self.fullscreen_finish_extra_time_button = ctk.CTkButton(
                    self.fullscreen_alarm_frame,
                    text=self.app.t("finish"),
                    command=self.finish_extra_time,
                    width=220,
                    height=50,
                    corner_radius=16,
                    fg_color=COLORS["green"],
                    text_color=COLORS["white"],
                    font=ctk.CTkFont(
                        size=15,
                        weight="bold"
                    )
                )

            self.fullscreen_finish_extra_time_button.grid(
                row=0,
                column=0,
                columnspan=2,
                padx=8,
                pady=4
            )


        elif (
            getattr(self.app, "alarm_active", False)
            and getattr(
                self.app,
                "alarm_source",
                None
            ) == "focus"
        ):

            # Normal alarm state
            self.show_fullscreen_alarm_button()


        # TASK INFO
        self.update_fullscreen_task_info()


        # RESPONSIVE RESIZE
        self.app.after_idle(
            self.resize_fullscreen_view
        )

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

        self.fullscreen_button = SecondaryButton(
            self.header,
            text="⛶",
            command=self.toggle_fullscreen,
            width=50
        )

        self.fullscreen_button.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(20, 0),
            sticky="e"
        )

        Tooltip(
            self.fullscreen_button,
            self.app.t("tooltip_fullscreen")
        )

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
            text_color=COLORS["white"],
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

        """ self.pause_button = SecondaryButton(
            self.button_frame,
            text=self.app.t("pause"),
            command=self.pause_timer,
            width=130
        )
        self.pause_button.grid(row=0, column=1, padx=8) """

        self.reset_button = SecondaryButton(
            self.button_frame,
            text=self.app.t("reset"),
            command=self.reset_timer,
            width=130
        )
        self.reset_button.grid(row=0, column=2, padx=8)

        self.skip_break_button = SecondaryButton(
            self.button_frame,
            text=self.app.t("skip_break"),
            command=self.skip_break,
            width=130
        )

        self.skip_break_button.grid(
            row=0,
            column=1,
            padx=8
        )

        self.skip_break_button.grid_remove()

        self.stop_alarm_button = ctk.CTkButton(
            self.button_frame,
            text=f"🔕 {self.app.t('stop_alarm')}",
            command=self.dismiss_alarm,
            width=180,
            height=40,
            corner_radius=12,
            fg_color=COLORS["red"],
            hover_color="#DC2626",
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=14, weight="bold")
        )

        self.stop_alarm_button.grid(
            row=1,
            column=0,
            pady=(16, 0),
            padx=(0, 8)
        )

        self.stop_alarm_button.grid_remove()

        self.extra_time_button = ctk.CTkButton(
            self.button_frame,
            text=f"+ {self.app.t('extra_time')}",
            command=self.start_extra_time,
            width=180,
            height=40,
            corner_radius=12,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=14, weight="bold")
        )

        self.extra_time_button.grid(
            row=1,
            column=1,
            pady=(16, 0),
            padx=(8, 0)
        )

        self.extra_time_button.grid_remove()


        self.finish_extra_time_button = ctk.CTkButton(
            self.button_frame,
            text=self.app.t("finish"),
            command=self.finish_extra_time,
            width=180,
            height=40,
            corner_radius=12,
            fg_color=COLORS["green"],
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=14, weight="bold")
        )

        self.finish_extra_time_button.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=(16, 0)
        )

        self.finish_extra_time_button.grid_remove()

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
            text="",
            width=42,
            height=42,
            fg_color=COLORS["primary_soft"],
            text_color=COLORS["white"],
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

        # AUTO START CARD
        self.auto_start_card = AppCard(self.side_panel)
        self.auto_start_card.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(16, 0)
        )

        self.auto_start_card.grid_columnconfigure(
            0,
            weight=1
        )

        self.auto_start_title = ctk.CTkLabel(
            self.auto_start_card,
            text=self.app.t("auto_start"),
            text_color=COLORS["text"],
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            anchor="w"
        )

        self.auto_start_title.grid(
            row=0,
            column=0,
            padx=(24, 12),
            pady=(22, 4),
            sticky="w"
        )

        self.auto_start_description = ctk.CTkLabel(
            self.auto_start_card,
            text=self.app.t("pomodoro_auto_start_all"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w",
            justify="left",
            wraplength=210
        )

        self.auto_start_description.grid(
            row=1,
            column=0,
            padx=(24, 12),
            pady=(0, 22),
            sticky="w"
        )

        self.auto_start_switch = ctk.CTkSwitch(
            self.auto_start_card,
            text="",
            command=self.toggle_auto_start,
            width=48,
            progress_color=COLORS["primary"],
            button_color=COLORS["white"],
            button_hover_color=COLORS["white"]
        )

        self.auto_start_switch.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(12, 24),
            pady=20,
            sticky="e"
        )


        self.queue_card = AppCard(self.side_panel)
        self.queue_card.grid(row=4, column=0, sticky="ew", pady=(16, 0))
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

        self.load_auto_start_switch()

    def load_auto_start_switch(self):
        settings = self.app.app_data.setdefault(
            "settings",
            {}
        )

        auto_start_focus = settings.get(
            "auto_start_focus",
            False
        )

        auto_start_break = settings.get(
            "auto_start_break",
            False
        )

        # Switch yalnızca ikisi de açıksa ON görünür.
        if auto_start_focus and auto_start_break:
            self.auto_start_switch.select()
        else:
            self.auto_start_switch.deselect()

    def toggle_auto_start(self):
        is_enabled = bool(
            self.auto_start_switch.get()
        )

        settings = self.app.app_data.setdefault(
            "settings",
            {}
        )

        # Tek switch, iki modu birlikte yönetir.
        settings["auto_start_focus"] = is_enabled
        settings["auto_start_break"] = is_enabled

        self.app.save_app_data()

    def format_time(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def format_hours_minutes(self, seconds):
        total_minutes = seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    def get_focus_empty_state_texts(self):
        last_queue_state = self.app.app_data.get("last_queue_state")
        pending_tasks = self.app.get_pending_tasks() if hasattr(self.app, "get_pending_tasks") else []

        if last_queue_state == "completed":
            return (
                self.app.t("plan_completed"),
                self.app.t("plan_completed_desc")
            )

        if not pending_tasks:
            return (
                self.app.t("no_active_task"),
                self.app.t("empty_study_plan_desc")
            )

        return (
            self.app.t("no_active_task"),
            self.app.t("select_or_start_task_desc")
        )

    def load_active_task(self):
        task = self.app.get_active_task()

        if self.is_waiting_for_completion_choice:
            self.timer_label.configure(text="00:00")

            self.status_pill.configure(
                text=self.app.t("completed_status"),
                fg_color="#065F46",
                text_color="#D1FAE5"
            )

            self.show_completion_choice_controls()
            self.update_fullscreen_task_info()
            return

        if not task:
            empty_title, empty_detail = self.get_focus_empty_state_texts()

            self.active_task_label.configure(text=empty_title)
            self.active_task_detail_label.configure(text=empty_detail)

            self.current_task_title.configure(text=empty_title)
            self.current_task_detail.configure(text=empty_detail)

            self.current_task_icon.configure(
                fg_color=COLORS["primary_soft"]
            )

            self.task_progress.configure(
                progress_color=COLORS["primary"]
            )

            last_queue_state = self.app.app_data.get("last_queue_state")

            if last_queue_state == "completed":
                self.focus_seconds = 0
                self.break_seconds = 0
            else:
                self.focus_seconds = 25 * 60
                self.break_seconds = 5 * 60

            if (
                not self.is_running
                and not self.is_paused
                and not self.is_waiting_for_next
                and not self.is_waiting_for_completion_choice
                and not self.is_extra_time
            ):
                self.current_mode = "focus"

                if last_queue_state == "completed":
                    self.remaining_seconds = 0
                else:
                    self.remaining_seconds = self.focus_seconds

                self.away_seconds = 0
                self.session_away_seconds = 0

                self.timer_label.configure(
                    text=self.format_time(self.remaining_seconds)
                )

                if self.fullscreen_timer_label:
                    self.fullscreen_timer_label.configure(
                        text=self.format_time(self.remaining_seconds)
                    )

                self.start_button.configure(
                    state="disabled",
                    command=self.start_timer
                )

                self.status_pill.configure(
                    text=self.app.t("waiting_status"),
                    fg_color=COLORS["card_soft"],
                    text_color=COLORS["muted"]
                )

                self.task_progress.set(0)
                self.task_progress_label.configure(
                    text="0%"
                )

            self.update_fullscreen_task_info()

            self.update_total_focus_label()
            self.update_queue_progress()
            self.refresh_queue_progress_visibility()

            return


        subject = task.get("subject_name")

        if not subject:
            subject = self.app.t(
                task.get("subject", "other")
            )

        title = task.get("task_name") or task.get("title", "")

        subject_color = self.app.get_subject_color(
            task.get("subject_id")
        )

        focus_minutes = task.get(
            "focus_minutes",
            25
        )

        break_minutes = task.get(
            "break_minutes",
            5
        )


        task_title_text = f"{subject} · {title}"


        detail_text = (
            f"{focus_minutes}{self.app.t('minute_short')} "
            f"{self.app.t('focus_label_short')} · "
            f"{break_minutes}{self.app.t('minute_short')} "
            f"{self.app.t('break_label_short')}"
        )


        self.active_task_label.configure(
            text=task_title_text
        )

        self.active_task_detail_label.configure(
            text=detail_text
        )


        self.current_task_title.configure(
            text=task_title_text
        )

        self.current_task_detail.configure(
            text=detail_text
        )


        self.current_task_icon.configure(
            fg_color=subject_color
        )

        self.task_progress.configure(
            progress_color=subject_color
        )


        self.focus_seconds = focus_minutes * 60
        self.break_seconds = break_minutes * 60


        if (
            not self.is_running
            and not self.is_paused
            and not self.is_waiting_for_next
            and not self.is_waiting_for_completion_choice
            and not self.is_extra_time
        ):

            self.current_mode = "focus"

            self.remaining_seconds = self.focus_seconds

            self.timer_label.configure(
                text=self.format_time(
                    self.remaining_seconds
                )
            )

            if self.fullscreen_timer_label:
                self.fullscreen_timer_label.configure(
                    text=self.format_time(
                        self.remaining_seconds
                    )
                )


            self.start_button.configure(
                state="normal",
                command=self.start_timer
            )


            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["white"]
            )


        self.update_fullscreen_task_info()

        self.update_current_task_progress()
        self.update_total_focus_label()
        self.update_queue_progress()
        self.refresh_queue_progress_visibility()

    def start_timer(self, manual_start=True):
        if (
            manual_start
            and getattr(self.app, "alarm_active", False)
            and getattr(self.app, "alarm_source", None) == "focus"
        ):
            self.dismiss_alarm()

        # Aktif görev yoksa timer başlatma.
        if not self.app.get_active_task():
            return

        # Zaten çalışıyorsa ikinci bir countdown zinciri oluşturma.
        if self.is_running:
            return

        self.is_paused = False
        self.is_running = True
        self.is_waiting_for_next = False

        self.away_seconds = 0
        self.away_warning_label.configure(text="")
        self.update_away_metric()
        self.update_mode_ui()
        self._set_timer_controls_running()

        if self.current_mode == "break":
            if (
                self.skip_break_button is not None
                and self.skip_break_button.winfo_exists()
            ):
                self.skip_break_button.grid(
                    row=0,
                    column=1,
                    padx=8
                )

            if (
                self.fullscreen_skip_break_button is not None
                and self.fullscreen_skip_break_button.winfo_exists()
            ):
                self.fullscreen_skip_break_button.grid(
                    row=0,
                    column=1,
                    padx=10
                )

        self.count_down()

    def pause_timer(self):
        if not self.is_running:
            return

        self.is_running = False
        self.is_paused = True

        self._set_timer_controls_ready(
            text_key="resume"
        )

        self.status_pill.configure(
            text=self.app.t("paused"),
            fg_color="#92400E",
            text_color="#FEF3C7"
        )

        self.update_away_timer()

    def reset_timer(self):
        self.dismiss_alarm()

        self.is_running = False
        self.is_paused = False
        self.is_waiting_for_next = False
        self.away_seconds = 0
        self.session_away_seconds = 0
        self.current_mode = "focus"

        self.hide_skip_break_controls()

        task = self.app.get_active_task()

        if task:
            self.focus_seconds = task.get("focus_minutes", 25) * 60
            self.break_seconds = task.get("break_minutes", 5) * 60
        else:
            self.focus_seconds = 25 * 60
            self.break_seconds = 5 * 60

        self.remaining_seconds = self.focus_seconds

        self.timer_label.configure(
            text=self.format_time(self.remaining_seconds)
        )

        fullscreen_timer_label = getattr(
            self,
            "fullscreen_timer_label",
            None
        )

        if (
            fullscreen_timer_label is not None
            and fullscreen_timer_label.winfo_exists()
        ):
            fullscreen_timer_label.configure(
                text=self.format_time(self.remaining_seconds)
            )

        self.away_warning_label.configure(text="")
        self._set_timer_controls_ready(text_key="start")
        self.update_mode_ui()
        self.update_away_metric()
        self.update_current_task_progress()

    def _set_timer_controls_running(self):
        self.start_button.configure(
            text=self.app.t("pause"),
            command=self.pause_timer
        )

        fullscreen_start_button = getattr(
            self,
            "fullscreen_start_button",
            None
        )

        if (
            fullscreen_start_button is not None
            and fullscreen_start_button.winfo_exists()
        ):
            fullscreen_start_button.configure(
                text=self.app.t("pause"),
                command=self.pause_timer
            )

    def _set_timer_controls_ready(self, text_key="start"):
        self.start_button.configure(
            text=self.app.t(text_key),
            command=self.start_timer
        )

        fullscreen_start_button = getattr(
            self,
            "fullscreen_start_button",
            None
        )

        if (
            fullscreen_start_button is not None
            and fullscreen_start_button.winfo_exists()
        ):
            fullscreen_start_button.configure(
                text=self.app.t(text_key),
                command=self.start_timer
            )

            # Completion choice veya Extra Time sırasında
            # normal Start/Resume butonunu gösterme.
            if (
                not self.is_waiting_for_completion_choice
                and not self.is_extra_time
            ):
                fullscreen_start_button.grid(
                    row=0,
                    column=0,
                    padx=10
                )
            else:
                fullscreen_start_button.grid_remove()


    def get_current_mode_total_seconds(self):
        if self.current_mode == "focus":
            return self.focus_seconds
        return self.break_seconds

    def skip_break(self):
        if self.current_mode != "break":
            return

        # Çalışan break countdown'unu durdur.
        self.is_running = False
        self.is_paused = False
        self.is_waiting_for_next = False

        # Eğer break alarmı bir nedenle aktifse kapat.
        self.app.stop_alarm()

        # Skip butonlarını gizle.
        if (
            self.skip_break_button is not None
            and self.skip_break_button.winfo_exists()
        ):
            self.skip_break_button.grid_remove()

        if (
            self.fullscreen_skip_break_button is not None
            and self.fullscreen_skip_break_button.winfo_exists()
        ):
            self.fullscreen_skip_break_button.grid_remove()

        # Queue kullanılıyorsa normal break tamamlanmış gibi
        # sıradaki göreve geç.
        if self.app.app_data.get(
            "queue_mode_active",
            False
        ):
            moved_to_next_task = (
                self.app.move_to_next_queue_task()
            )

            if moved_to_next_task:
                self.switch_to_focus_ready()
                return

            # Queue tamamen bittiyse
            self.current_mode = "focus"

            self.app.app_data["active_task_id"] = None
            self.app.app_data["queue_mode_active"] = False
            self.app.app_data["queue_task_ids"] = []
            self.app.save_app_data()

            self.load_active_task()
            self.update_queue_progress()

            self._set_timer_controls_ready(
                text_key="start"
            )

            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["white"]
            )

            self.away_warning_label.configure(
                text=self.app.t("queue_completed")
            )

            return

        # Queue yoksa doğrudan yeni focus'a hazırlan.
        self.switch_to_focus_ready()

    def switch_to_break_ready(self):
        self.current_mode = "break"
        self.remaining_seconds = self.break_seconds
        self.is_waiting_for_next = True

        self.timer_label.configure(
            text=self.format_time(self.remaining_seconds)
        )

        fullscreen_timer_label = getattr(
            self,
            "fullscreen_timer_label",
            None
        )

        if (
            fullscreen_timer_label is not None
            and fullscreen_timer_label.winfo_exists()
        ):
            fullscreen_timer_label.configure(
                text=self.format_time(self.remaining_seconds)
            )

        self.away_warning_label.configure(
            text=self.app.t("break_ready")
        )

        self._set_timer_controls_ready(
            text_key="start_break"
        )

        if (
            self.skip_break_button is not None
            and self.skip_break_button.winfo_exists()
        ):
            self.skip_break_button.grid(
                row=0,
                column=1,
                padx=8
            )

        if (
            self.fullscreen_skip_break_button is not None
            and self.fullscreen_skip_break_button.winfo_exists()
        ):
            self.fullscreen_skip_break_button.grid(
                row=0,
                column=1,
                padx=10
            )

        self.task_progress.set(0)
        self.task_progress_label.configure(text="0%")
        self.update_mode_ui()

        fullscreen_status_label = getattr(
            self,
            "fullscreen_status_label",
            None
        )

        if (
            fullscreen_status_label is not None
            and fullscreen_status_label.winfo_exists()
        ):
            fullscreen_status_label.configure(
                text=self.app.t("break_mode")
            )

        auto_start_break = self.app.app_data.get(
            "settings",
            {}
        ).get(
            "auto_start_break",
            False
        )

        if auto_start_break:
            self.start_timer(manual_start=False)

    def switch_to_focus_ready(self):
        self.current_mode = "focus"
        self.remaining_seconds = self.focus_seconds
        self.is_waiting_for_next = True

        self.timer_label.configure(
            text=self.format_time(self.remaining_seconds)
        )

        if (
            self.skip_break_button is not None
            and self.skip_break_button.winfo_exists()
        ):
            self.skip_break_button.grid_remove()

        if (
            self.fullscreen_skip_break_button is not None
            and self.fullscreen_skip_break_button.winfo_exists()
        ):
            self.fullscreen_skip_break_button.grid_remove()

        fullscreen_timer_label = getattr(
            self,
            "fullscreen_timer_label",
            None
        )

        if (
            fullscreen_timer_label is not None
            and fullscreen_timer_label.winfo_exists()
        ):
            fullscreen_timer_label.configure(
                text=self.format_time(self.remaining_seconds)
            )

        self.away_warning_label.configure(
            text=self.app.t("focus_ready")
        )

        self._set_timer_controls_ready(
            text_key="start_focus"
        )

        self.task_progress.set(0)
        self.task_progress_label.configure(text="0%")
        self.update_current_task_progress()
        self.update_mode_ui()

        fullscreen_status_label = getattr(
            self,
            "fullscreen_status_label",
            None
        )

        if (
            fullscreen_status_label is not None
            and fullscreen_status_label.winfo_exists()
        ):
            fullscreen_status_label.configure(
                text=self.app.t("focus_mode")
            )

        auto_start_focus = self.app.app_data.get(
            "settings",
            {}
        ).get(
            "auto_start_focus",
            False
        )

        if auto_start_focus:
            self.start_timer(manual_start=False)

    def update_mode_ui(self):
        if self.current_mode == "focus":
            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["white"]
            )
        else:
            self.status_pill.configure(
                text=self.app.t("break_mode"),
                fg_color="#065F46",
                text_color="#D1FAE5"
            )

    def count_down(self):
        if not self.is_running:
            return

        if self.remaining_seconds > 0:
            time_text = self.format_time(
                self.remaining_seconds
            )

            self.timer_label.configure(
                text=time_text
            )

            fullscreen_timer_label = getattr(
                self,
                "fullscreen_timer_label",
                None
            )

            if (
                fullscreen_timer_label is not None
                and fullscreen_timer_label.winfo_exists()
            ):
                fullscreen_timer_label.configure(
                    text=time_text
                )

            self.update_current_task_progress()
            self.remaining_seconds -= 1
            self.after(1000, self.count_down)
            return

        self.update_current_task_progress()
        self.is_running = False
        self.is_paused = False

        self.timer_label.configure(
            text="00:00"
        )

        fullscreen_timer_label = getattr(
            self,
            "fullscreen_timer_label",
            None
        )

        if (
            fullscreen_timer_label is not None
            and fullscreen_timer_label.winfo_exists()
        ):
            fullscreen_timer_label.configure(
                text="00:00"
            )

        self.start_alarm()

        if self.current_mode == "focus":
            self.away_warning_label.configure(
                text=self.app.t("focus_completed")
            )

            self.status_pill.configure(
                text=self.app.t("completed_status"),
                fg_color="#065F46",
                text_color="#D1FAE5"
            )

            settings = self.app.app_data.get(
                "settings",
                {}
            )

            extra_time_enabled = settings.get(
                "extra_time_enabled",
                False
            )

            auto_start_break = settings.get(
                "auto_start_break",
                False
            )

            # Auto Start açıksa Extra Time seçimini atla.
            # Focus session'ı tamamla ve doğrudan break'e geç.
            if auto_start_break:
                self.is_waiting_for_completion_choice = False
                self.is_extra_time = False
                self.extra_time_seconds = 0

                self.hide_completion_choice_controls()

                # Focus session'ını kapat.
                # Bu fonksiyon Break'e geçecek ve Auto Start
                # açıksa break countdown'unu başlatacak.
                self.finalize_focus_session()

                # Alarm hâlâ çalıyorsa Stop Alarm butonu görünmeli.
                if getattr(self.app, "alarm_active", False):
                    self.show_alarm_controls()

                return

            # Auto Start kapalıysa ve Extra Time açıksa
            # kullanıcı karar versin.
            if extra_time_enabled:
                self.is_waiting_for_completion_choice = True
                self.is_extra_time = False
                self.extra_time_seconds = 0

                self.show_completion_choice_controls()
                return

            # Ne Auto Start ne de Extra Time seçimi gerekiyorsa
            # normal şekilde break-ready ekranına geç.
            self.finalize_focus_session()
            return

        self.away_warning_label.configure(
            text=self.app.t("break_completed")
        )

        if self.app.app_data.get(
            "queue_mode_active",
            False
        ):
            moved_to_next_task = (
                self.app.move_to_next_queue_task()
            )

            if moved_to_next_task:
                self.switch_to_focus_ready()
                return

            self.is_running = False
            self.is_paused = False
            self.is_waiting_for_next = False
            self.current_mode = "focus"
            self.hide_skip_break_controls()

            self.app.app_data["active_task_id"] = None
            self.app.app_data["queue_mode_active"] = False
            self.app.app_data["queue_task_ids"] = []
            self.app.save_app_data()

            self.load_active_task()
            self.update_queue_progress()
            self._set_timer_controls_ready(
                text_key="start"
            )

            self.status_pill.configure(
                text=self.app.t("focus_mode"),
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["white"]
            )

            self.away_warning_label.configure(
                text=self.app.t("queue_completed")
            )
            return

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

        self.auto_start_title.configure(
            text=self.app.t("auto_start")
        )

        self.auto_start_description.configure(
            text=self.app.t("pomodoro_auto_start_all")
        )

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

        self.reset_button.configure(text=self.app.t("reset"))

        if (
            not self.is_running
            and not self.is_paused
            and not self.is_waiting_for_next
            and not self.is_waiting_for_completion_choice
            and not self.is_extra_time
        ):
            self.load_active_task()

        self.update_queue_progress()
        self.refresh_queue_progress_visibility()
        self.update_total_focus_label()
        self.load_auto_start_switch()
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
            "planned_seconds": self.focus_seconds,
            "extra_time_seconds": self.extra_time_seconds,
            "duration_seconds": (
                self.focus_seconds
                + self.extra_time_seconds
            ),
            "away_seconds": self.session_away_seconds,
            "completed_at": datetime.now().isoformat(timespec="seconds")
        }

        self.app.app_data.setdefault("sessions", []).append(session)
    
    def clear_status_message(self):
        self.away_warning_label.configure(text="")

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

        subject = task.get("subject_name")

        if not subject:
            subject = self.app.t(task.get("subject", "other"))

        title = task.get("title", "")
        focus_minutes = task.get("focus_minutes", 25)
        break_minutes = task.get("break_minutes", 5)

        self.current_task_title.configure(
            text=f"{subject} · {title}"
        )

        self.current_task_detail.configure(
            text=(
                f"{focus_minutes}{self.app.t('minute_short')} {self.app.t('focus_label_short')} · "
                f"{break_minutes}{self.app.t('minute_short')} {self.app.t('break_label_short')}"
            )
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
        self.load_auto_start_switch()
        self.update_queue_progress()
        self.refresh_queue_progress_visibility()

    def start_alarm(self):
        self.app.play_alarm("focus")

    def show_completion_choice_controls(self):

        # -------------------------
        # NORMAL VIEW
        # -------------------------

        self.start_button.grid_remove()
        self.reset_button.grid_remove()

        self.stop_alarm_button.configure(
            text=self.app.t("continue_to_break"),
            command=self.continue_to_break
        )

        self.stop_alarm_button.grid(
            row=1,
            column=0,
            columnspan=1,
            pady=(16, 0),
            padx=(0, 8)
        )

        self.extra_time_button.grid(
            row=1,
            column=1,
            columnspan=1,
            pady=(16, 0),
            padx=(8, 0)
        )

        self.finish_extra_time_button.grid_remove()


        # -------------------------
        # FULLSCREEN VIEW
        # -------------------------

        if not self.fullscreen_mode:
            return

        if (
            self.fullscreen_start_button is not None
            and self.fullscreen_start_button.winfo_exists()
        ):
            self.fullscreen_start_button.grid_remove()

        self.show_fullscreen_alarm_button()


    def hide_completion_choice_controls(self):
        self.stop_alarm_button.grid_remove()
        self.extra_time_button.grid_remove()
        self.finish_extra_time_button.grid_remove()

        if (
            self.fullscreen_stop_alarm_button is not None
            and self.fullscreen_stop_alarm_button.winfo_exists()
        ):
            self.fullscreen_stop_alarm_button.grid_remove()

        if (
            self.fullscreen_extra_time_button is not None
            and self.fullscreen_extra_time_button.winfo_exists()
        ):
            self.fullscreen_extra_time_button.grid_remove()

        if (
            self.fullscreen_finish_extra_time_button is not None
            and self.fullscreen_finish_extra_time_button.winfo_exists()
        ):
            self.fullscreen_finish_extra_time_button.grid_remove()


    def restore_normal_timer_controls(self):
        self.start_button.grid(
            row=0,
            column=0,
            padx=8
        )

        self.reset_button.grid(
            row=0,
            column=2,
            padx=8
        )

    def start_extra_time(self):
        if not self.is_waiting_for_completion_choice:
            return

        self.app.stop_alarm()

        self.is_waiting_for_completion_choice = False
        self.is_extra_time = True
        self.extra_time_seconds = 0

        self.stop_alarm_button.grid_remove()
        self.extra_time_button.grid_remove()

        if (
            self.fullscreen_stop_alarm_button is not None
            and self.fullscreen_stop_alarm_button.winfo_exists()
        ):
            self.fullscreen_stop_alarm_button.grid_remove()

        if (
            self.fullscreen_extra_time_button is not None
            and self.fullscreen_extra_time_button.winfo_exists()
        ):
            self.fullscreen_extra_time_button.grid_remove()

        self.finish_extra_time_button.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=(16, 0)
        )

        if (
            self.fullscreen_mode
            and self.fullscreen_alarm_frame is not None
            and self.fullscreen_alarm_frame.winfo_exists()
        ):
            if (
                self.fullscreen_finish_extra_time_button is None
                or not self.fullscreen_finish_extra_time_button.winfo_exists()
            ):
                self.fullscreen_finish_extra_time_button = ctk.CTkButton(
                    self.fullscreen_alarm_frame,
                    text=self.app.t("finish"),
                    command=self.finish_extra_time,
                    width=220,
                    height=50,
                    corner_radius=16,
                    fg_color=COLORS["green"],
                    text_color=COLORS["white"],
                    font=ctk.CTkFont(
                        size=15,
                        weight="bold"
                    )
                )

            self.fullscreen_finish_extra_time_button.grid(
                row=0,
                column=0,
                columnspan=2,
                padx=8,
                pady=4
            )

        self.timer_label.configure(
            text="00:00"
        )

        self.status_pill.configure(
            text=self.app.t("extra_time"),
            fg_color=COLORS["primary_soft"],
            text_color=COLORS["white"]
        )

        self.count_extra_time()


    def count_extra_time(self):
        if not self.is_extra_time:
            return

        time_text = self.format_time(
            self.extra_time_seconds
        )

        self.timer_label.configure(
            text=time_text
        )

        fullscreen_timer_label = getattr(
            self,
            "fullscreen_timer_label",
            None
        )

        if (
            fullscreen_timer_label is not None
            and fullscreen_timer_label.winfo_exists()
        ):
            fullscreen_timer_label.configure(
                text=time_text
            )

        self.extra_time_seconds += 1

        self.after(
            1000,
            self.count_extra_time
        )


    def finish_extra_time(self):
        if not self.is_extra_time:
            return

        if (
            self.fullscreen_finish_extra_time_button is not None
            and self.fullscreen_finish_extra_time_button.winfo_exists()
        ):
            self.fullscreen_finish_extra_time_button.grid_remove()

        self.is_extra_time = False

        self.finish_extra_time_button.grid_remove()

        self.finalize_focus_session()

    def finalize_focus_session(self):
        active_task = self.app.get_active_task()

        active_task_id = (
            active_task.get("id")
            if active_task
            else None
        )

        total_focus_seconds = (
            self.focus_seconds
            + self.extra_time_seconds
        )

        self.app.app_data["total_focus_seconds_today"] = (
            self.app.app_data.get(
                "total_focus_seconds_today",
                0
            )
            + total_focus_seconds
        )

        self.log_focus_session()

        if self.app.app_data.get(
            "queue_mode_active",
            False
        ):
            self.app.mark_task_completed(
                active_task_id
            )

        self.app.save_app_data()

        self.update_total_focus_label()

        if hasattr(
            self.app,
            "statistics_page"
        ):
            self.app.statistics_page.refresh_stats()

        self.session_away_seconds = 0
        self.away_seconds = 0

        self.update_away_metric()

        self.is_waiting_for_completion_choice = False
        self.is_extra_time = False

        self.hide_completion_choice_controls()
        self.restore_normal_timer_controls()

        self.switch_to_break_ready()

        self.extra_time_seconds = 0

    def continue_to_break(self):
        if not self.is_waiting_for_completion_choice:
            return

        # Alarm çalıyorsa sustur.
        self.app.stop_alarm()

        # Completion choice ekranını kapat.
        self.hide_completion_choice_controls()

        self.is_waiting_for_completion_choice = False
        self.is_extra_time = False

        # Focus session'ını kaydet ve Break Ready durumuna geçir.
        self.finalize_focus_session()

        # Auto Start kapalı olsa bile kullanıcı özellikle
        # "Molaya Geç" dediği için break'i hemen başlat.
        if (
            self.current_mode == "break"
            and not self.is_running
        ):
            self.start_timer(manual_start=False)

    def dismiss_alarm(self):
        self.app.stop_alarm()

        if (
            self.current_mode == "focus"
            and self.is_waiting_for_completion_choice
        ):
            self.hide_completion_choice_controls()
            self.finalize_focus_session()

    def show_alarm_controls(self):
        if self.fullscreen_mode:
            self.hide_normal_alarm_button()
            self.show_fullscreen_alarm_button()
        else:
            self.hide_fullscreen_alarm_button()
            self.show_normal_alarm_button()

    def hide_alarm_controls(self):

        # Focus tamamlandı ve kullanıcı henüz
        # Break / Extra Time kararını vermediyse
        # karar butonlarını gizleme.
        if self.is_waiting_for_completion_choice:
            return

        self.hide_normal_alarm_button()
        self.hide_fullscreen_alarm_button()

    def show_normal_alarm_button(self):

        if (
            self.stop_alarm_button is None
            or not self.stop_alarm_button.winfo_exists()
        ):
            return

        # Bu fonksiyon gerçek alarm susturma hali için.
        self.stop_alarm_button.configure(
            text=f"🔕 {self.app.t('stop_alarm')}",
            command=self.dismiss_alarm
        )

        self.stop_alarm_button.grid(
            row=1,
            column=0,
            columnspan=3,
            padx=8,
            pady=(16, 0)
        )

        self.stop_alarm_button.lift()
        
    def hide_normal_alarm_button(self):

        if (
            self.stop_alarm_button is not None
            and self.stop_alarm_button.winfo_exists()
        ):
            self.stop_alarm_button.grid_remove()

    def hide_skip_break_controls(self):
        if (
            self.skip_break_button is not None
            and self.skip_break_button.winfo_exists()
        ):
            self.skip_break_button.grid_remove()

        if (
            self.fullscreen_skip_break_button is not None
            and self.fullscreen_skip_break_button.winfo_exists()
        ):
            self.fullscreen_skip_break_button.grid_remove()

    def show_fullscreen_alarm_button(self):

        if (
            self.fullscreen_alarm_frame is None
            or not self.fullscreen_alarm_frame.winfo_exists()
        ):
            return

        # SOL BUTON:
        # completion choice sırasında -> Continue to Break
        # normal alarm sırasında -> Stop Alarm
        if (
            self.fullscreen_stop_alarm_button is None
            or not self.fullscreen_stop_alarm_button.winfo_exists()
        ):
            self.fullscreen_stop_alarm_button = ctk.CTkButton(
                self.fullscreen_alarm_frame,
                width=220,
                height=50,
                corner_radius=16,
                text_color=COLORS["white"],
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                )
            )

        # EXTRA TIME
        if (
            self.fullscreen_extra_time_button is None
            or not self.fullscreen_extra_time_button.winfo_exists()
        ):
            self.fullscreen_extra_time_button = ctk.CTkButton(
                self.fullscreen_alarm_frame,
                text=f"+ {self.app.t('extra_time')}",
                command=self.start_extra_time,
                width=220,
                height=50,
                corner_radius=16,
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                text_color=COLORS["white"],
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                )
            )

        # ------------------------------------
        # FOCUS BİTTİ, KULLANICI SEÇİM BEKLİYOR
        # ------------------------------------
        if self.is_waiting_for_completion_choice:

            self.fullscreen_stop_alarm_button.configure(
                text=self.app.t("continue_to_break"),
                command=self.continue_to_break,
                fg_color=COLORS["green"],
                hover_color=COLORS["green"]
            )

            self.fullscreen_stop_alarm_button.grid(
                row=0,
                column=0,
                columnspan=1,
                padx=8,
                pady=4
            )

            self.fullscreen_extra_time_button.grid(
                row=0,
                column=1,
                columnspan=1,
                padx=8,
                pady=4
            )

        # ------------------------------------
        # NORMAL ALARM
        # örn. Auto Start ile break başladı
        # ------------------------------------
        else:

            self.fullscreen_stop_alarm_button.configure(
                text=f"🔕 {self.app.t('stop_alarm')}",
                command=self.dismiss_alarm,
                fg_color=COLORS["red"],
                hover_color="#DC2626"
            )

            self.fullscreen_stop_alarm_button.grid(
                row=0,
                column=0,
                columnspan=2,
                padx=8,
                pady=4
            )

            self.fullscreen_extra_time_button.grid_remove()

        self.app.after_idle(
            self.resize_fullscreen_view
        )


    def hide_fullscreen_alarm_button(self):

        if (
            self.fullscreen_stop_alarm_button is not None
            and self.fullscreen_stop_alarm_button.winfo_exists()
        ):
            self.fullscreen_stop_alarm_button.grid_remove()

        if (
            self.fullscreen_extra_time_button is not None
            and self.fullscreen_extra_time_button.winfo_exists()
        ):
            self.fullscreen_extra_time_button.grid_remove()