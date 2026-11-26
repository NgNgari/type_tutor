import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox


class TypingTrainerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Type Tutor")
        self.root.geometry("1120x780")
        self.root.minsize(960, 560)
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        # Keyboard shortcuts
        self.root.bind("<Escape>", self.confirm_exit)
        self.root.bind("<F11>", self.toggle_live_fullscreen)
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-r>", lambda e: self.restart_session())
        self.root.bind("<Control-h>", self.toggle_recording_mode)
        self.root.bind("<Control-H>", self.toggle_recording_mode)
        self.root.bind("<Control-l>", self.clear_stack)
        self.root.bind("<Control-L>", self.clear_stack)

        # Zoom shortcuts (Ctrl + '+' / '-' / '0')
        self.root.bind("<Control-plus>", lambda e: self.change_font_size(2))
        self.root.bind("<Control-equal>", lambda e: self.change_font_size(2))
        self.root.bind("<Control-KP_Add>", lambda e: self.change_font_size(2))
        self.root.bind("<Control-minus>", lambda e: self.change_font_size(-2))
        self.root.bind("<Control-KP_Subtract>", lambda e: self.change_font_size(-2))
        self.root.bind("<Control-0>", lambda e: self.reset_font_size())
        self.root.bind("<Control-KP_0>", lambda e: self.reset_font_size())

        # State variables
        self.lines = []
        self.stacked_lines = []
        self.current_idx = 0
        self.line_start_time = None
        self.total_time = 0.0
        self.total_chars = 0
        self.correct_keystrokes = 0
        self.total_keystrokes = 0
        self.script_path = None
        self._progress_value = 0.0

        self.drill_mode = tk.BooleanVar(value=True)
        self.target_wpm = tk.IntVar(value=45)
        self.recording_mode = False
        self.dark_theme = True

        # Dynamic font sizes
        self.base_font_size = 20
        self.rec_font_size = 24

        # Anti-flicker / layout stability state
        self._resize_after_id = None
        self._scroll_after_id = None
        self._last_layout_sig = None
        self.active_text_widget = None

        # Color palettes
        self.themes = {
            "dark": {
                "bg": "#151621",
                "bar": "#10111a",
                "deck_back": "#191a28",
                "deck_mid": "#1d1f30",
                "card": "#212336",
                "card_border": "#32354f",
                "card_shadow": "#10111a",
                "card_shadow_edge": "#2a2d45",
                "tile_bg": "#27293e",
                "tile_border": "#3b3f5c",
                "stripe_a": "#89b4fa",
                "stripe_b": "#cba6f7",
                "active_tile_bg": "#22303c",
                "active_border": "#a6e3a1",
                "active_shadow": "#121b22",
                "tele_bg": "#13141f",
                "tele_border": "#313244",
                "input_bg": "#10111a",
                "text": "#cdd6f4",
                "stacked_text": "#dce2f7",
                "active_bullet": "#a6e3a1",
                "active_text": "#ffffff",
                "muted": "#7f849c",
                "accent": "#89b4fa",
                "green": "#a6e3a1",
                "yellow": "#f9e2af",
                "orange": "#fab387",
                "pending": "#fab387",
                "red": "#f38ba8",
                "red_bg": "#452736",
            },
            "light": {
                "bg": "#e9ecf2",
                "bar": "#dce0e8",
                "deck_back": "#dfe3ec",
                "deck_mid": "#eef1f7",
                "card": "#f8f9fc",
                "card_border": "#cbd1df",
                "card_shadow": "#cfd5e3",
                "card_shadow_edge": "#bcc4d6",
                "tile_bg": "#ffffff",
                "tile_border": "#d0d6e4",
                "stripe_a": "#1e66f5",
                "stripe_b": "#8839ef",
                "active_tile_bg": "#edf8f0",
                "active_border": "#40a02b",
                "active_shadow": "#cde5d4",
                "tele_bg": "#e6e9ef",
                "tele_border": "#ccd0da",
                "input_bg": "#ffffff",
                "text": "#4c4f69",
                "stacked_text": "#2c2e3e",
                "active_bullet": "#40a02b",
                "active_text": "#11111b",
                "muted": "#7c7f93",
                "accent": "#1e66f5",
                "green": "#40a02b",
                "yellow": "#df8e1d",
                "orange": "#fe640b",
                "pending": "#c76d16",
                "red": "#d20f39",
                "red_bg": "#fce4ec",
            },
        }

        self.setup_ui()
        self.apply_theme()
        self.rebuild_all_cards(force=True)

    def current_font_size(self):
        return self.rec_font_size if self.recording_mode else self.base_font_size

    def get_safe_target_wpm(self):
        try:
            val = int(self.spin_wpm.get())
            return max(10, min(180, val))
        except (tk.TclError, ValueError):
            return 45

    def setup_ui(self):
        # 1. Top Control Bar (Hidden in Live Screen Mode)
        self.top_frame = tk.Frame(self.root, pady=10, padx=16)
        self.top_frame.grid(row=0, column=0, sticky="ew")

        self.btn_load = tk.Button(
            self.top_frame,
            text="Open Script (Ctrl+O)",
            command=self.load_file,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.btn_load.pack(side="left")

        self.btn_clear = tk.Button(
            self.top_frame,
            text="Clear Screen (Ctrl+L)",
            command=self.clear_stack,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.btn_clear.pack(side="left", padx=(8, 0))

        self.btn_restart = tk.Button(
            self.top_frame,
            text="Restart (Ctrl+R)",
            command=self.restart_session,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled",
        )
        self.btn_restart.pack(side="left", padx=(8, 0))

        self.btn_record = tk.Button(
            self.top_frame,
            text="Live Screen (F11)",
            command=self.toggle_recording_mode,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.btn_record.pack(side="left", padx=(8, 0))

        self.btn_theme = tk.Button(
            self.top_frame,
            text="Light/Dark",
            command=self.toggle_theme,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.btn_theme.pack(side="left", padx=(8, 0))

        # Font Size Zoom Controls
        zoom_frame = tk.Frame(self.top_frame)
        zoom_frame.pack(side="left", padx=(12, 0))
        self.zoom_frame = zoom_frame

        self.btn_zoom_out = tk.Button(
            zoom_frame,
            text="A-",
            command=lambda: self.change_font_size(-2),
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=3,
            relief="flat",
            cursor="hand2",
        )
        self.btn_zoom_out.pack(side="left")

        self.lbl_font_size = tk.Label(
            zoom_frame,
            text=f"{self.base_font_size}pt",
            font=("Segoe UI", 9, "bold"),
            padx=5,
        )
        self.lbl_font_size.pack(side="left")

        self.btn_zoom_in = tk.Button(
            zoom_frame,
            text="A+",
            command=lambda: self.change_font_size(2),
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=3,
            relief="flat",
            cursor="hand2",
        )
        self.btn_zoom_in.pack(side="left")

        # Target WPM Control
        wpm_frame = tk.Frame(self.top_frame)
        wpm_frame.pack(side="left", padx=(14, 0))
        self.wpm_frame = wpm_frame

        self.lbl_target_title = tk.Label(
            wpm_frame, text="Target WPM:", font=("Segoe UI", 9)
        )
        self.lbl_target_title.pack(side="left")

        self.spin_wpm = tk.Spinbox(
            wpm_frame,
            from_=15,
            to=120,
            increment=5,
            textvariable=self.target_wpm,
            width=4,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            command=self.update_pace_indicator,
        )
        self.spin_wpm.pack(side="left", padx=(4, 0))
        self.spin_wpm.bind("<KeyRelease>", lambda e: self.update_pace_indicator())

        self.chk_drill = tk.Checkbutton(
            self.top_frame,
            text="Drill Mode (100%)",
            variable=self.drill_mode,
            font=("Segoe UI", 9),
        )
        self.chk_drill.pack(side="left", padx=12)

        self.lbl_esc = tk.Label(
            self.top_frame,
            text="[Esc] Exit",
            font=("Segoe UI", 9, "italic"),
        )
        self.lbl_esc.pack(side="right")

        # 2. Practice Stats Bar (Hidden in Live Screen Mode)
        self.stats_frame = tk.Frame(self.root, pady=6, padx=24)
        self.stats_frame.grid(row=1, column=0, sticky="ew")

        self.lbl_progress = tk.Label(
            self.stats_frame,
            text="No script loaded",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_progress.pack(side="left")

        self.progress_canvas = tk.Canvas(
            self.stats_frame, height=6, highlightthickness=0, bd=0
        )
        self.progress_canvas.pack(side="left", fill="x", expand=True, padx=16)
        self.progress_canvas.create_rectangle(
            0, 0, 1, 6, tags="track", width=0
        )
        self.progress_canvas.create_rectangle(
            0, 0, 0, 6, tags="fill", width=0
        )
        self.progress_canvas.bind("<Configure>", self._draw_progress)

        self.lbl_progress_percent = tk.Label(
            self.stats_frame,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            width=4,
        )
        self.lbl_progress_percent.pack(side="left")

        self.lbl_pace = tk.Label(
            self.stats_frame,
            text="Pace: Ready (40-50 WPM ideal)",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_pace.pack(side="left", padx=30)

        self.lbl_stats = tk.Label(
            self.stats_frame,
            text="WPM: 0  |  Accuracy: 100%",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_stats.pack(side="right")

        # 3. TOP SCREEN: Stylish Layered Window Deck + Offset Stacked Cards
        self.outer_pad = tk.Frame(self.root, padx=24, pady=6)
        self.outer_pad.grid(row=2, column=0, sticky="nsew")

        # Outer layered deck plates for window depth
        self.deck_layer_back = tk.Frame(self.outer_pad, height=8)
        self.deck_layer_back.pack(fill="x", padx=28)

        self.deck_layer_mid = tk.Frame(self.outer_pad, height=8)
        self.deck_layer_mid.pack(fill="x", padx=14)

        self.stage_card = tk.Frame(self.outer_pad, padx=24, pady=18)
        self.stage_card.pack(fill="both", expand=True)

        # Header inside stage card
        stage_header = tk.Frame(self.stage_card)
        stage_header.pack(fill="x", pady=(0, 12))
        self.stage_header = stage_header

        self.window_dots = tk.Canvas(
            stage_header, width=54, height=14, highlightthickness=0, bd=0
        )
        self.window_dots.pack(side="left", padx=(0, 10))
        self.window_dots.create_oval(2, 3, 11, 12, fill="#f38ba8", outline="")
        self.window_dots.create_oval(18, 3, 27, 12, fill="#f9e2af", outline="")
        self.window_dots.create_oval(34, 3, 43, 12, fill="#a6e3a1", outline="")

        self.lbl_stage_mode = tk.Label(
            stage_header,
            text="PRACTICE PLACE  |  LAYERED SCRIPT DECK",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_stage_mode.pack(side="left")

        # Subtle corner pace dot
        self.pace_dot = tk.Canvas(
            stage_header, width=12, height=12, highlightthickness=0, bd=0
        )
        self.pace_dot.pack(side="right")
        self.dot_oval = self.pace_dot.create_oval(
            2, 2, 10, 10, fill="#6c7086", outline=""
        )

        # Scrollable canvas holding distinct layered cards
        self.cards_canvas = tk.Canvas(
            self.stage_card, highlightthickness=0, bd=0
        )
        self.cards_canvas.pack(fill="both", expand=True)

        self.cards_inner = tk.Frame(self.cards_canvas)
        self.cards_window_id = self.cards_canvas.create_window(
            (0, 0), window=self.cards_inner, anchor="nw"
        )

        self.cards_inner.bind("<Configure>", self._on_inner_configure)
        self.cards_canvas.bind("<Configure>", self._on_canvas_configure)

        # Cross-platform mouse wheel scrolling
        self.cards_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.cards_canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.cards_canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

        # 4. BOTTOM GUIDING TELEPROMPTER
        self.tele_border_frame = tk.Frame(self.root, padx=24, pady=6)
        self.tele_border_frame.grid(row=3, column=0, sticky="ew")

        self.tele_frame = tk.Frame(self.tele_border_frame, padx=22, pady=10)
        self.tele_frame.pack(fill="x")

        tele_header = tk.Frame(self.tele_frame)
        tele_header.pack(fill="x", pady=(0, 4))
        self.tele_header = tele_header

        self.lbl_tele_title = tk.Label(
            tele_header,
            text="SCRIPT GUIDE   |   Tab completes a word   |   Enter submits a line",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_tele_title.pack(side="left")

        self.lbl_tele_shortcuts = tk.Label(
            tele_header,
            text="Ctrl+O Open   |   Ctrl+R Restart   |   F11 Live view",
            font=("Segoe UI", 8, "italic"),
            anchor="e",
        )
        self.lbl_tele_shortcuts.pack(side="right")

        self.txt_target = tk.Text(
            self.tele_frame,
            height=2,
            font=("Consolas", 13),
            wrap="word",
            bd=0,
            highlightthickness=0,
            state="disabled",
        )
        self.txt_target.pack(fill="x")

        self.lbl_next = tk.Label(
            self.tele_frame,
            text="Next line preview will appear here",
            font=("Consolas", 11, "italic"),
            anchor="w",
            pady=2,
        )
        self.lbl_next.pack(fill="x")

        # 5. Typing Input Box
        self.input_container = tk.Frame(self.root, padx=24, pady=6)
        self.input_container.grid(row=4, column=0, sticky="ew")

        self.lbl_input_hint = tk.Label(
            self.input_container,
            text="Type the highlighted line. Tab completes the next word; Enter submits the line.",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_input_hint.pack(fill="x", pady=(0, 4))

        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.on_type)

        self.entry_input = tk.Entry(
            self.input_container,
            textvariable=self.entry_var,
            font=("Consolas", 14),
            relief="flat",
        )
        self.entry_input.pack(fill="x", ipady=8)
        self.entry_input.bind("<Return>", self.check_line)
        self.entry_input.bind("<Tab>", self.autofill_word)

        # 6. Practice Feedback Banner
        self.lbl_feedback = tk.Label(
            self.root,
            text="Open a text script to begin. Your typing will appear in the preview.",
            font=("Segoe UI", 10),
            pady=6,
        )
        self.lbl_feedback.grid(row=5, column=0, sticky="ew")

        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_rowconfigure(4, weight=0)
        self.root.grid_rowconfigure(5, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

    def _on_inner_configure(self, event):
        self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all"))

    def _draw_progress(self, event=None):
        width = self.progress_canvas.winfo_width()
        height = self.progress_canvas.winfo_height()
        fill_width = int(width * self._progress_value)
        self.progress_canvas.coords("track", 0, 0, width, height)
        self.progress_canvas.coords("fill", 0, 0, fill_width, height)

    def _update_progress(self):
        total = len(self.lines)
        completed = min(self.current_idx, total)
        line_progress = 0.0
        if total and completed < total:
            target_length = len(self.lines[completed])
            if target_length:
                line_progress = min(
                    len(self.entry_var.get()) / target_length, 1.0
                )
        self._progress_value = (
            (completed + line_progress) / total if total else 0.0
        )
        if completed < total:
            self._progress_value = min(self._progress_value, 0.99)
        if total and completed == total:
            self.lbl_progress.config(text=f"Complete · {total} lines")
        elif total:
            self.lbl_progress.config(
                text=f"Line {completed + 1} of {total}"
            )
        else:
            self.lbl_progress.config(text="No script loaded")
        self.lbl_progress_percent.config(
            text=f"{round(self._progress_value * 100)}%"
        )
        self._draw_progress()

    def _on_canvas_configure(self, event):
        self.cards_canvas.itemconfig(self.cards_window_id, width=event.width)
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(140, self._handle_debounced_resize)

    def _handle_debounced_resize(self):
        self._resize_after_id = None
        self.rebuild_all_cards(force=False)

    def _on_mousewheel(self, event):
        if event.delta:
            self.cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.cards_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.cards_canvas.yview_scroll(1, "units")

    def _schedule_scroll_bottom(self):
        if self._scroll_after_id is not None:
            self.root.after_cancel(self._scroll_after_id)
        self._scroll_after_id = self.root.after(15, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self._scroll_after_id = None
        self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all"))
        self.cards_canvas.yview_moveto(1.0)

    def apply_theme(self):
        t = self.themes["dark" if self.dark_theme else "light"]
        self.root.configure(bg=t["bg"])
        self.top_frame.configure(bg=t["bar"])
        self.zoom_frame.configure(bg=t["bar"])
        self.wpm_frame.configure(bg=t["bar"])
        self.stats_frame.configure(bg=t["bg"])
        self.outer_pad.configure(bg=t["bg"])

        self.deck_layer_back.configure(
            bg=t["deck_back"], highlightbackground=t["card_border"], highlightthickness=1
        )
        self.deck_layer_mid.configure(
            bg=t["deck_mid"], highlightbackground=t["card_border"], highlightthickness=1
        )
        self.stage_card.configure(
            bg=t["card"], highlightbackground=t["card_border"], highlightthickness=1
        )
        self.stage_header.configure(bg=t["card"])
        self.window_dots.configure(bg=t["card"])
        self.pace_dot.configure(bg=t["card"])
        self.cards_canvas.configure(bg=t["card"])
        self.cards_inner.configure(bg=t["card"])

        self.tele_border_frame.configure(bg=t["bg"])
        self.tele_frame.configure(
            bg=t["tele_bg"], highlightbackground=t["tele_border"], highlightthickness=1
        )
        self.tele_header.configure(bg=t["tele_bg"])
        self.input_container.configure(bg=t["bg"])

        self.btn_load.configure(
            bg=t["accent"], fg="#11111b" if self.dark_theme else "#ffffff"
        )
        self.btn_clear.configure(bg=t["tele_border"], fg=t["text"])
        self.btn_restart.configure(
            bg=t["tele_border"],
            fg=t["text"],
            disabledforeground=t["muted"],
        )
        self.btn_record.configure(
            bg=t["red"] if self.recording_mode else t["green"],
            fg="#11111b" if self.dark_theme else "#ffffff",
            text="Back to Practice (F11)" if self.recording_mode else "Live Screen (F11)",
        )
        self.btn_theme.configure(bg=t["tele_border"], fg=t["text"])
        self.btn_zoom_out.configure(bg=t["tele_border"], fg=t["text"])
        self.btn_zoom_in.configure(bg=t["tele_border"], fg=t["text"])
        self.lbl_font_size.configure(bg=t["bar"], fg=t["text"])

        self.lbl_target_title.configure(bg=t["bar"], fg=t["text"])
        self.spin_wpm.configure(
            bg=t["input_bg"], fg=t["text"], buttonbackground=t["tele_border"]
        )
        self.chk_drill.configure(
            bg=t["bar"],
            fg=t["text"],
            selectcolor=t["input_bg"],
            activebackground=t["bar"],
            activeforeground=t["text"],
        )
        self.lbl_esc.configure(bg=t["bar"], fg=t["muted"])

        self.lbl_progress.configure(bg=t["bg"], fg=t["yellow"])
        self.lbl_progress_percent.configure(bg=t["bg"], fg=t["muted"])
        self.progress_canvas.configure(bg=t["bg"])
        self.progress_canvas.itemconfig("track", fill=t["tele_border"])
        self.progress_canvas.itemconfig("fill", fill=t["green"])
        self.lbl_pace.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_stats.configure(bg=t["bg"], fg=t["green"])

        self.lbl_stage_mode.configure(
            bg=t["card"],
            fg=t["red"] if self.recording_mode else t["muted"],
            text="LIVE SCREEN"
            if self.recording_mode
            else "PRACTICE PLACE  |  LAYERED SCRIPT DECK",
        )

        # Teleprompter styles
        self.lbl_tele_title.configure(bg=t["tele_bg"], fg=t["accent"])
        self.lbl_tele_shortcuts.configure(bg=t["tele_bg"], fg=t["muted"])
        self.txt_target.configure(bg=t["tele_bg"], fg=t["text"])
        self.txt_target.tag_config("correct", foreground=t["green"])
        self.txt_target.tag_config("wrong", foreground=t["red"], background=t["red_bg"])
        self.txt_target.tag_config("pending", foreground=t["pending"])
        self.lbl_next.configure(bg=t["tele_bg"], fg=t["muted"])

        self.lbl_input_hint.configure(bg=t["bg"], fg=t["muted"])
        self.entry_input.configure(
            bg=t["input_bg"],
            fg=t["active_text"],
            insertbackground=t["active_text"],
        )
        self.lbl_feedback.configure(bg=t["bg"], fg=t["accent"])

    def change_font_size(self, delta):
        if self.recording_mode:
            self.rec_font_size = max(14, min(56, self.rec_font_size + delta))
            size = self.rec_font_size
        else:
            self.base_font_size = max(12, min(48, self.base_font_size + delta))
            size = self.base_font_size

        self.lbl_font_size.config(text=f"{size}pt")
        self.apply_theme()
        self.rebuild_all_cards(force=True)

    def reset_font_size(self):
        if self.recording_mode:
            self.rec_font_size = 24
            size = self.rec_font_size
        else:
            self.base_font_size = 20
            size = self.base_font_size

        self.lbl_font_size.config(text=f"{size}pt")
        self.apply_theme()
        self.rebuild_all_cards(force=True)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()
        self.rebuild_all_cards(force=True)

    def toggle_recording_mode(self, event=None):
        """Switches between Practice Place and Live Screen while keeping Teleprompter active."""
        self.recording_mode = not self.recording_mode

        if not self.recording_mode:
            try:
                if self.root.attributes("-fullscreen"):
                    self.root.attributes("-fullscreen", False)
            except tk.TclError:
                pass

        if self.recording_mode:
            self.top_frame.grid_remove()
            self.stats_frame.grid_remove()
            self.lbl_feedback.grid_remove()
            self.lbl_input_hint.pack_forget()
            self.outer_pad.configure(padx=28, pady=8)
            self.stage_card.configure(padx=28, pady=22)
            self.tele_border_frame.configure(padx=28, pady=8)
            self.input_container.configure(padx=28, pady=12)
        else:
            self.top_frame.grid(row=0, column=0, sticky="ew")
            self.stats_frame.grid(row=1, column=0, sticky="ew")
            self.outer_pad.configure(padx=24, pady=6)
            self.stage_card.configure(padx=24, pady=18)
            self.tele_border_frame.configure(padx=24, pady=6)
            self.lbl_input_hint.pack(fill="x", pady=(0, 4), before=self.entry_input)
            self.input_container.configure(padx=24, pady=6)
            self.lbl_feedback.grid(row=5, column=0, sticky="ew")

        self.lbl_font_size.config(text=f"{self.current_font_size()}pt")
        self.apply_theme()
        self.rebuild_all_cards(force=True)
        self.entry_input.config(state="normal")
        self.entry_input.focus_set()

    def toggle_live_fullscreen(self, event=None):
        """Toggle Live Screen together with fullscreen."""
        if not self.recording_mode:
            self.toggle_recording_mode()
            try:
                self.root.attributes("-fullscreen", True)
            except tk.TclError:
                pass
        else:
            try:
                self.root.attributes("-fullscreen", False)
            except tk.TclError:
                pass
            self.toggle_recording_mode()
        return "break"

    def clear_stack(self, event=None):
        """Clears stacked cards on the top screen (Ctrl+L)."""
        self.stacked_lines = []
        self.rebuild_all_cards(force=True)
        self.lbl_feedback.config(
            text="Top screen cleared (Ctrl+L). Ready for next paragraph!"
        )
        self.entry_input.focus_set()

    def _has_unsaved_session(self):
        return bool(
            self.lines
            and (
                self.current_idx > 0
                or self.entry_var.get()
                or self.stacked_lines
                or self.total_keystrokes
            )
        )

    def _reset_session_stats(self):
        self.line_start_time = None
        self.total_time = 0.0
        self.total_chars = 0
        self.correct_keystrokes = 0
        self.total_keystrokes = 0
        self.lbl_stats.config(text="WPM: 0  |  Accuracy: 100%")
        self.update_pace_indicator()

    def restart_session(self, event=None):
        if not self.lines:
            return "break"
        if self._has_unsaved_session() and not messagebox.askyesno(
            "Restart session?",
            "Restart this script from the beginning? Your current progress and stats will be cleared.",
            parent=self.root,
        ):
            return "break"

        self.current_idx = 0
        self.stacked_lines = []
        self._reset_session_stats()
        self.lbl_feedback.config(
            text="Session restarted. Type the highlighted line or press Tab to complete a word."
        )
        self.display_current_line()
        return "break"

    def _create_layered_card(self, parent, bg, border, shadow_bg, shadow_edge, stripe, wrap_px, pad_y=12):
        """Builds a single layered card container with an offset bottom-right depth edge."""
        holder = tk.Frame(parent, bg=self.themes["dark" if self.dark_theme else "light"]["card"])
        holder.pack(fill="x", pady=(0, 12), padx=(0, 6))

        # Offset back layer for bottom-right layered card edge
        shadow_plate = tk.Frame(
            holder,
            bg=shadow_bg,
            highlightbackground=shadow_edge,
            highlightthickness=1,
        )
        shadow_plate.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0, x=6, y=6)

        # Foreground bordered card
        card = tk.Frame(
            holder,
            bg=bg,
            highlightbackground=border,
            highlightthickness=1,
        )
        card.pack(fill="x", padx=(0, 6), pady=(0, 6))

        # Left color accent stripe
        stripe_bar = tk.Frame(card, bg=stripe, width=6)
        stripe_bar.pack(side="left", fill="y")

        body = tk.Frame(card, bg=bg, padx=18, pady=pad_y)
        body.pack(side="left", fill="both", expand=True)

        return body

    def rebuild_all_cards(self, force=False):
        """Builds completed cards once and sets up the active card without flickering."""
        t = self.themes["dark" if self.dark_theme else "light"]
        fs = self.current_font_size()
        canvas_w = self.cards_canvas.winfo_width()
        if canvas_w < 120:
            canvas_w = 880
        wrap_px = max(320, canvas_w - 84)
        has_active_line = bool(self.lines and self.current_idx < len(self.lines))

        sig = (
            tuple(self.stacked_lines),
            has_active_line,
            fs,
            self.dark_theme,
            wrap_px // 20,
        )
        if not force and sig == self._last_layout_sig:
            self.update_active_card_only()
            return
        self._last_layout_sig = sig

        for child in self.cards_inner.winfo_children():
            child.destroy()
        self.active_text_widget = None

        # 1. Render completed paragraphs as static, rock-solid layered cards
        for idx, line in enumerate(self.stacked_lines):
            stripe = t["stripe_a"] if idx % 2 == 0 else t["stripe_b"]
            body = self._create_layered_card(
                parent=self.cards_inner,
                bg=t["tile_bg"],
                border=t["tile_border"],
                shadow_bg=t["card_shadow"],
                shadow_edge=t["card_shadow_edge"],
                stripe=stripe,
                wrap_px=wrap_px,
                pad_y=12,
            )

            lbl = tk.Label(
                body,
                text=line,
                font=("Segoe UI", fs),
                bg=t["tile_bg"],
                fg=t["stacked_text"],
                justify="left",
                anchor="w",
                wraplength=wrap_px,
            )
            lbl.pack(fill="x")

        # 2. Render active typing card (updated in-place on keystrokes)
        if has_active_line:
            body = self._create_layered_card(
                parent=self.cards_inner,
                bg=t["active_tile_bg"],
                border=t["active_border"],
                shadow_bg=t["active_shadow"],
                shadow_edge=t["active_border"],
                stripe=t["active_border"],
                wrap_px=wrap_px,
                pad_y=14,
            )

            txt = tk.Text(
                body,
                font=("Segoe UI", fs, "bold"),
                bg=t["active_tile_bg"],
                fg=t["active_text"],
                wrap="word",
                bd=0,
                highlightthickness=0,
                height=1,
                state="disabled",
                cursor="arrow",
            )
            txt.pack(fill="x")
            txt.tag_config("bullet", foreground=t["active_bullet"])
            txt.tag_config("ok", foreground=t["active_text"])
            txt.tag_config("bad", foreground=t["red"], background=t["red_bg"])
            txt.tag_config("cursor", foreground=t["accent"])
            self.active_text_widget = txt
            self.update_active_card_only()

        elif not self.stacked_lines:
            body = self._create_layered_card(
                parent=self.cards_inner,
                bg=t["tile_bg"],
                border=t["tile_border"],
                shadow_bg=t["card_shadow"],
                shadow_edge=t["card_shadow_edge"],
                stripe=t["stripe_a"],
                wrap_px=wrap_px,
                pad_y=16,
            )
            lbl = tk.Label(
                body,
                text="Welcome to Type Tutor\nOpen a text script to begin. Your progress and stats will appear here as you practice.",
                font=("Segoe UI", fs),
                bg=t["tile_bg"],
                fg=t["muted"],
                justify="left",
                anchor="w",
                wraplength=wrap_px,
            )
            lbl.pack(fill="x")

        self._schedule_scroll_bottom()

    def update_active_card_only(self):
        """Updates ONLY the active card text in-place so stacked cards never blink."""
        if self.active_text_widget is None or not self.active_text_widget.winfo_exists():
            return
        if not self.lines or self.current_idx >= len(self.lines):
            return

        typed = self.entry_var.get()
        target = self.lines[self.current_idx]
        txt = self.active_text_widget

        txt.config(state="normal")
        txt.delete("1.0", tk.END)
        txt.insert(tk.END, "▶  ", "bullet")

        for i, ch in enumerate(typed):
            if i < len(target) and ch == target[i]:
                txt.insert(tk.END, ch, "ok")
            else:
                txt.insert(tk.END, ch, "bad")

        txt.insert(tk.END, " ▌", "cursor")

        # Adjust height smoothly to fit wrapped lines without rebuilding widgets
        try:
            display_lines = txt.count("1.0", "end", "displaylines")
            line_count = display_lines[0] if display_lines else 1
            txt.config(height=max(1, line_count))
        except tk.TclError:
            pass

        txt.config(state="disabled")
        self._schedule_scroll_bottom()

    def autofill_word(self, event=None):
        """Pressing Tab autofills the next word from the target script line."""
        if not self.lines or self.current_idx >= len(self.lines):
            return "break"

        target = self.lines[self.current_idx]
        typed = self.entry_var.get()

        valid_len = 0
        for a, b in zip(target, typed):
            if a == b:
                valid_len += 1
            else:
                break

        clean_prefix = target[:valid_len]
        remaining = target[valid_len:]

        if not remaining:
            return "break"

        idx = 0
        while idx < len(remaining) and remaining[idx] == " ":
            idx += 1
        while idx < len(remaining) and remaining[idx] != " ":
            idx += 1
        if idx < len(remaining) and remaining[idx] == " ":
            idx += 1

        new_text = clean_prefix + remaining[:idx]
        self.entry_var.set(new_text)
        self.entry_input.icursor(tk.END)
        return "break"

    def load_file(self):
        options = {
            "title": "Choose a text script",
            "filetypes": [("Text Files", "*.txt"), ("All Files", "*.*")],
        }
        if self.script_path:
            options["initialdir"] = os.path.dirname(self.script_path)
        file_path = filedialog.askopenfilename(
            **options,
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                lines = [line.rstrip("\r\n") for line in f if line.strip()]
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror(
                "File Error", f"Could not read file:\n{e}\n\nPlease try another file."
            )
            return

        if not lines:
            messagebox.showwarning(
                "Empty File", "That file has no text. Please select another .txt file."
            )
            return

        if self._has_unsaved_session() and not messagebox.askyesno(
            "Replace current session?",
            "Loading a new script will discard your current progress and stats.",
            parent=self.root,
        ):
            return

        self.script_path = file_path
        self.root.title(f"Type Tutor - {os.path.basename(file_path)}")
        self.lines = lines
        self.stacked_lines = []
        self.current_idx = 0
        self._reset_session_stats()
        self.btn_restart.config(state="normal")

        self.lbl_feedback.config(
            text=f"{os.path.basename(file_path)} loaded · {len(lines)} lines. Start typing or press Tab to complete a word.",
        )
        self.display_current_line()

    def display_current_line(self):
        self._update_progress()
        if self.current_idx >= len(self.lines):
            self.finish_session()
            return

        target = self.lines[self.current_idx]

        # Update teleprompter guide line
        self.txt_target.config(state="normal")
        self.txt_target.delete("1.0", tk.END)
        self.txt_target.insert("1.0", target, "pending")
        self.txt_target.config(state="disabled")

        # Update next line preview
        if self.current_idx + 1 < len(self.lines):
            next_preview = self.lines[self.current_idx + 1]
            if len(next_preview) > 95:
                next_preview = next_preview[:92] + "..."
            self.lbl_next.config(text=f"Next: > {next_preview}")
        else:
            self.lbl_next.config(text="Next: > (End of script)")

        self.entry_var.set("")
        self.entry_input.config(state="normal")
        self.entry_input.focus_set()
        self.line_start_time = None
        self.rebuild_all_cards(force=True)

    def on_type(self, *args):
        if not self.lines or self.current_idx >= len(self.lines):
            return

        typed = self.entry_var.get()
        target = self.lines[self.current_idx]
        self._update_progress()

        if self.line_start_time is None and len(typed) > 0:
            self.line_start_time = time.perf_counter()

        # Update ONLY active card in-place (zero blinking!)
        self.update_active_card_only()

        # Update teleprompter guide highlighting
        self.txt_target.config(state="normal")
        self.txt_target.delete("1.0", tk.END)

        for i, char in enumerate(target):
            if i < len(typed):
                if typed[i] == char:
                    self.txt_target.insert(tk.END, char, "correct")
                else:
                    self.txt_target.insert(tk.END, char, "wrong")
            else:
                self.txt_target.insert(tk.END, char, "pending")

        if len(typed) > len(target):
            self.txt_target.insert(tk.END, typed[len(target) :], "wrong")

        self.txt_target.config(state="disabled")

    def update_pace_indicator(self, current_wpm=None):
        t = self.themes["dark" if self.dark_theme else "light"]
        goal = self.get_safe_target_wpm()
        low = max(10, goal - 5)
        high = goal + 5

        if current_wpm is None:
            self.lbl_pace.config(
                text=f"Pace: Ready ({low}-{high} WPM ideal)", fg=t["accent"]
            )
            self.pace_dot.itemconfig(self.dot_oval, fill="#6c7086")
            return

        if low <= current_wpm <= high:
            self.lbl_pace.config(
                text=f"Pace: ON TARGET ({low}-{high} WPM)", fg=t["green"]
            )
            self.pace_dot.itemconfig(self.dot_oval, fill=t["green"])
        elif current_wpm < low:
            self.lbl_pace.config(
                text=f"Pace: Too Slow (Aim {low}-{high} WPM)", fg=t["yellow"]
            )
            self.pace_dot.itemconfig(self.dot_oval, fill=t["yellow"])
        else:
            self.lbl_pace.config(
                text=f"Pace: Too Fast (Aim {low}-{high} WPM)", fg=t["orange"]
            )
            self.pace_dot.itemconfig(self.dot_oval, fill=t["orange"])

    def check_line(self, event=None):
        if not self.lines or self.current_idx >= len(self.lines):
            return

        typed = self.entry_var.get()
        target = self.lines[self.current_idx]

        if not typed:
            return

        elapsed = (
            time.perf_counter() - self.line_start_time
            if self.line_start_time
            else 0.1
        )
        matches = sum(1 for a, b in zip(target, typed) if a == b)

        self.total_time += elapsed
        self.total_chars += len(typed)
        self.correct_keystrokes += matches
        self.total_keystrokes += max(len(target), len(typed))

        wpm = (
            (self.total_chars / 5) / (self.total_time / 60)
            if self.total_time > 0
            else 0
        )
        acc = (
            (self.correct_keystrokes / self.total_keystrokes) * 100
            if self.total_keystrokes > 0
            else 100
        )
        self.lbl_stats.config(text=f"WPM: {wpm:.0f}  |  Accuracy: {acc:.1f}%")
        self.update_pace_indicator(wpm)

        t = self.themes["dark" if self.dark_theme else "light"]

        if typed == target:
            self.stacked_lines.append(typed)
            self.lbl_feedback.config(
                text="Perfect! Layered card stacked above.", fg=t["green"]
            )
            self.current_idx += 1
            self.display_current_line()
        else:
            if not self.recording_mode and self.drill_mode.get():
                self.lbl_feedback.config(
                    text="Not quite—try this line again to keep your accuracy streak.",
                    fg=t["red"],
                )
                self.entry_var.set("")
                self.display_current_line()
            else:
                self.stacked_lines.append(typed)
                self.lbl_feedback.config(
                    text="Card stacked above.",
                    fg=t["orange"],
                )
                self.current_idx += 1
                self.display_current_line()

    def finish_session(self):
        self.entry_var.set("")
        self.entry_input.config(state="disabled")
        self.rebuild_all_cards(force=True)

        self.txt_target.config(state="normal")
        self.txt_target.delete("1.0", tk.END)
        self.txt_target.insert(
            "1.0",
            "Script complete! Open another script or press Ctrl+R to practice again.",
            "correct",
        )
        self.txt_target.config(state="disabled")
        self.lbl_next.config(text="Next: > Finished!")
        self.lbl_feedback.config(
            text="Nice work! Restart this script to practice again, or open another script."
        )

    def confirm_exit(self, event=None):
        if self._has_unsaved_session() and not messagebox.askyesno(
            "Exit practice?",
            "Your current practice progress and stats will be lost. Exit anyway?",
            parent=self.root,
        ):
            return "break"
        self.root.destroy()
        return "break"


if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTrainerApp(root)
    root.mainloop()
