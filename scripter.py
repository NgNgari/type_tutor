import time
import tkinter as tk
from tkinter import filedialog, messagebox


class TypingTrainerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Tutorial Script Studio")
        self.root.geometry("1100x760")

        # Keyboard shortcuts
        self.root.bind("<Escape>", self.confirm_exit)
        self.root.bind("<F11>", self.toggle_live_fullscreen)
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

        self.drill_mode = tk.BooleanVar(value=True)
        self.target_wpm = tk.IntVar(value=45)
        self.recording_mode = False
        self.dark_theme = True

        # Dynamic font sizes
        self.base_font_size = 21
        self.rec_font_size = 25

        # Color palettes
        self.themes = {
            "dark": {
                "bg": "#181825",
                "bar": "#11111b",
                "card": "#1e1e2e",
                "active_band": "#26283b",
                "tele_bg": "#13131f",
                "tele_border": "#313244",
                "input_bg": "#11111b",
                "text": "#cdd6f4",
                "stacked_text": "#a6adc8",
                "bullet": "#6c7086",
                "active_bullet": "#89b4fa",
                "active_text": "#ffffff",
                "muted": "#7f849c",
                "accent": "#89b4fa",
                "green": "#a6e3a1",
                "yellow": "#f9e2af",
                "orange": "#fab387",
                "pending": "#fab387",
                "stack_layer_back": "#26283b",
                "stack_layer_front": "#2a2c40",
                "red": "#f38ba8",
                "red_bg": "#452736",
            },
            "light": {
                "bg": "#eff1f5",
                "bar": "#dce0e8",
                "card": "#ffffff",
                "active_band": "#eef2ff",
                "tele_bg": "#e6e9ef",
                "tele_border": "#ccd0da",
                "input_bg": "#f5f7fa",
                "text": "#4c4f69",
                "stacked_text": "#6c6f85",
                "bullet": "#9ca0b0",
                "active_bullet": "#1e66f5",
                "active_text": "#11111b",
                "muted": "#8c8fa1",
                "accent": "#1e66f5",
                "green": "#40a02b",
                "yellow": "#df8e1d",
                "orange": "#fe640b",
                "pending": "#c76d16",
                "stack_layer_back": "#e6e9ef",
                "stack_layer_front": "#dce0e8",
                "red": "#d20f39",
                "red_bg": "#fce4ec",
            },
        }

        self.setup_ui()
        self.apply_theme()

    def current_font_size(self):
        return self.rec_font_size if self.recording_mode else self.base_font_size

    def setup_ui(self):
        # 1. Top Control Bar (Hidden in Live Screen Mode)
        self.top_frame = tk.Frame(self.root, pady=10, padx=16)
        self.top_frame.grid(row=0, column=0, sticky="ew")

        self.btn_load = tk.Button(
            self.top_frame,
            text="Open .txt Script",
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
        self.stats_frame = tk.Frame(self.root, pady=8, padx=24)
        self.stats_frame.grid(row=1, column=0, sticky="ew")

        self.lbl_progress = tk.Label(
            self.stats_frame,
            text="PRACTICE PLACE  |  Line: 0 / 0",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_progress.pack(side="left")

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

        # 3. TOP SCREEN: Big Words Live Typing & Beautiful Stacked Canvas
        self.outer_pad = tk.Frame(self.root, padx=24, pady=8)
        self.outer_pad.grid(row=2, column=0, sticky="nsew")

        self.stage_card = tk.Frame(self.outer_pad, padx=32, pady=24)
        self.stage_card.pack(fill="both", expand=True)

        # Header inside stage card
        stage_header = tk.Frame(self.stage_card)
        stage_header.pack(fill="x", pady=(0, 12))
        self.stage_header = stage_header

        self.lbl_stage_mode = tk.Label(
            stage_header,
            text="PRACTICE PLACE  (Top Screen: Big Words Live View)",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_stage_mode.pack(side="left")

        # Subtle corner pace dot
        self.pace_dot = tk.Canvas(
            stage_header, width=12, height=12, highlightthickness=0, bd=0
        )
        self.pace_dot.pack(side="right")
        self.dot_oval = self.pace_dot.create_oval(2, 2, 10, 10, fill="#6c7086", outline="")

        # Beautifully formatted multi-line document area
        self.txt_stack = tk.Text(
            self.stage_card,
            font=("Segoe UI", self.base_font_size),
            wrap="word",
            bd=0,
            highlightthickness=0,
            state="disabled",
            cursor="arrow",
        )
        self.txt_stack.pack(fill="both", expand=True)

        # 4. BOTTOM GUIDING TELEPROMPTER (Visible in BOTH Practice & Live Modes)
        self.tele_border_frame = tk.Frame(self.root, padx=24, pady=8)
        self.tele_border_frame.grid(row=3, column=0, sticky="ew")

        self.tele_frame = tk.Frame(self.tele_border_frame, padx=22, pady=12)
        self.tele_frame.pack(fill="x")

        tele_header = tk.Frame(self.tele_frame)
        tele_header.pack(fill="x", pady=(0, 4))
        self.tele_header = tele_header

        self.lbl_tele_title = tk.Label(
            tele_header,
            text="TELEPROMPTER GUIDE   |   Tab = Autofill   |   Ctrl+L = Clear   |   F11 = Toggle Live/Practice",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_tele_title.pack(side="left")

        self.lbl_tele_shortcuts = tk.Label(
            tele_header,
            text="Ctrl + / - Zoom   |   Esc Exit",
            font=("Segoe UI", 8, "italic"),
            anchor="e",
        )
        self.lbl_tele_shortcuts.pack(side="right")

        # Guiding target line (shows live green/red progress)
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

        # Next line preview
        self.lbl_next = tk.Label(
            self.tele_frame,
            text="Next: > Load a .txt script to start your teleprompter guide",
            font=("Consolas", 11, "italic"),
            anchor="w",
            pady=2,
        )
        self.lbl_next.pack(fill="x")

        # 5. Typing Input Box
        self.input_container = tk.Frame(self.root, padx=24, pady=8)
        self.input_container.grid(row=4, column=0, sticky="ew")

        self.lbl_input_hint = tk.Label(
            self.input_container,
            text="TYPE BELOW (Appears live in Big Words above  |  Tab = Autofill Next Word  |  Enter = Stack Paragraph):",
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

        # 6. Practice Feedback Banner (Hidden in Live Screen Mode)
        self.lbl_feedback = tk.Label(
            self.root,
            text="Click 'Open .txt Script' to load your tutorial script.",
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

    def apply_theme(self):
        t = self.themes["dark" if self.dark_theme else "light"]
        self.root.configure(bg=t["bg"])
        self.top_frame.configure(bg=t["bar"])
        self.zoom_frame.configure(bg=t["bar"])
        self.wpm_frame.configure(bg=t["bar"])
        self.stats_frame.configure(bg=t["bg"])
        self.outer_pad.configure(bg=t["bg"])
        self.stage_card.configure(bg=t["card"])
        self.stage_header.configure(bg=t["card"])
        self.pace_dot.configure(bg=t["card"])
        self.tele_border_frame.configure(bg=t["bg"])
        self.tele_frame.configure(bg=t["tele_bg"], highlightbackground=t["tele_border"], highlightthickness=1)
        self.tele_header.configure(bg=t["tele_bg"])
        self.input_container.configure(bg=t["bg"])

        self.btn_load.configure(bg=t["accent"], fg="#11111b" if self.dark_theme else "#ffffff")
        self.btn_clear.configure(bg=t["tele_border"], fg=t["text"])
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
        self.spin_wpm.configure(bg=t["input_bg"], fg=t["text"], buttonbackground=t["tele_border"])
        self.chk_drill.configure(
            bg=t["bar"],
            fg=t["text"],
            selectcolor=t["input_bg"],
            activebackground=t["bar"],
            activeforeground=t["text"],
        )
        self.lbl_esc.configure(bg=t["bar"], fg=t["muted"])

        self.lbl_progress.configure(bg=t["bg"], fg=t["yellow"])
        self.lbl_pace.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_stats.configure(bg=t["bg"], fg=t["green"])

        self.lbl_stage_mode.configure(
            bg=t["card"],
            fg=t["red"] if self.recording_mode else t["muted"],
            text="LIVE SCREEN" if self.recording_mode else "PRACTICE PLACE  (Top Screen: Big Words Live View)",
        )

        # Configure beautiful paragraph spacing and active line spotlight tags
        fs = self.current_font_size()
        self.txt_stack.configure(bg=t["card"], fg=t["text"], font=("Segoe UI", fs))
        self.txt_stack.tag_config(
            "stacked_bullet",
            foreground=t["bullet"],
            font=("Segoe UI", fs),
        )
        self.txt_stack.tag_config(
            "stacked",
            foreground=t["stacked_text"],
            font=("Segoe UI", fs),
        )
        self.txt_stack.tag_config(
            "stacked_layer_back",
            background=t["stack_layer_back"],
            spacing1=6,
            spacing3=14,
            lmargin1=10,
            lmargin2=34,
            rmargin=10,
        )
        self.txt_stack.tag_config(
            "stacked_layer_front",
            background=t["stack_layer_front"],
            spacing1=6,
            spacing3=14,
            lmargin1=14,
            lmargin2=38,
            rmargin=10,
        )
        self.txt_stack.tag_config(
            "active_bullet",
            foreground=t["active_bullet"],
            background=t["active_band"],
            font=("Segoe UI", fs, "bold"),
            spacing1=10,
            spacing3=10,
            lmargin1=4,
            lmargin2=28,
        )
        self.txt_stack.tag_config(
            "active_line",
            foreground=t["active_text"],
            background=t["active_band"],
            font=("Segoe UI", fs, "bold"),
            spacing1=10,
            spacing3=10,
            lmargin1=4,
            lmargin2=28,
        )
        self.txt_stack.tag_config(
            "active_wrong",
            foreground=t["red"],
            background=t["red_bg"],
            font=("Segoe UI", fs, "bold"),
            spacing1=10,
            spacing3=10,
            lmargin1=4,
            lmargin2=28,
        )
        self.txt_stack.tag_config(
            "cursor",
            foreground=t["accent"],
            background=t["active_band"],
            font=("Segoe UI", fs, "bold"),
            spacing1=10,
            spacing3=10,
            lmargin1=4,
            lmargin2=28,
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
        self.render_stack_and_active()

    def reset_font_size(self):
        if self.recording_mode:
            self.rec_font_size = 25
            size = self.rec_font_size
        else:
            self.base_font_size = 21
            size = self.base_font_size

        self.lbl_font_size.config(text=f"{size}pt")
        self.apply_theme()
        self.render_stack_and_active()

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()
        self.render_stack_and_active()

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
            self.stage_card.configure(padx=40, pady=28)
            self.tele_border_frame.configure(padx=28, pady=8)
            self.input_container.configure(padx=28, pady=14)
        else:
            self.top_frame.grid(row=0, column=0, sticky="ew")
            self.stats_frame.grid(row=1, column=0, sticky="ew")
            self.outer_pad.configure(padx=24, pady=8)
            self.stage_card.configure(padx=32, pady=24)
            self.tele_border_frame.configure(padx=24, pady=8)
            self.lbl_input_hint.pack(fill="x", pady=(0, 4), before=self.entry_input)
            self.input_container.configure(padx=24, pady=8)
            self.lbl_feedback.grid(row=5, column=0, sticky="ew")

        self.lbl_font_size.config(text=f"{self.current_font_size()}pt")
        self.apply_theme()
        self.render_stack_and_active()
        self.entry_input.config(state="normal")
        self.entry_input.focus_set()
        self.entry_input.update_idletasks()

    def toggle_live_fullscreen(self, event=None):
        """Toggle Live Screen together with fullscreen."""
        if not self.recording_mode:
            self.toggle_recording_mode()
            self.root.attributes("-fullscreen", True)
        else:
            self.root.attributes("-fullscreen", False)
            self.toggle_recording_mode()
        return "break"

    def clear_stack(self, event=None):
        """Clears stacked paragraphs on the top screen (Ctrl+L)."""
        self.stacked_lines = []
        self.render_stack_and_active()
        self.lbl_feedback.config(text="Top screen cleared (Ctrl+L). Ready for next paragraph!")
        self.entry_input.focus_set()

    def render_stack_and_active(self):
        """Renders spaced paragraphs above a highlighted active typing band."""
        typed = self.entry_var.get()
        target = (
            self.lines[self.current_idx]
            if self.lines and self.current_idx < len(self.lines)
            else ""
        )

        self.txt_stack.config(state="normal")
        self.txt_stack.delete("1.0", tk.END)

        # Render completed paragraphs with subtle marker bullets and clean spacing
        for i, line in enumerate(self.stacked_lines):
            layer = "stacked_layer_front" if i % 2 else "stacked_layer_back"
            self.txt_stack.insert(tk.END, "  ", layer)
            self.txt_stack.insert(tk.END, "▸  ", ("stacked_bullet", layer))
            self.txt_stack.insert(tk.END, line + "  \n", ("stacked", layer))

        # Render active typing line inside spotlight band
        if self.lines and self.current_idx < len(self.lines):
            self.txt_stack.insert(tk.END, "▶  ", "active_bullet")
            for i, ch in enumerate(typed):
                if i < len(target) and ch == target[i]:
                    self.txt_stack.insert(tk.END, ch, "active_line")
                else:
                    self.txt_stack.insert(tk.END, ch, "active_wrong")
            self.txt_stack.insert(tk.END, " ▌", "cursor")
        elif not self.stacked_lines:
            self.txt_stack.insert(
                tk.END,
                "Your live typing will appear here in big, clean paragraphs...",
                "stacked",
            )

        self.txt_stack.see(tk.END)
        self.txt_stack.config(state="disabled")

    def autofill_word(self, event=None):
        """Pressing Tab autofills the next word from the target script line."""
        if not self.lines or self.current_idx >= len(self.lines):
            return "break"

        target = self.lines[self.current_idx]
        typed = self.entry_var.get()

        # Trim back to last valid prefix if a typo exists
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
        file_path = filedialog.askopenfilename(
            title="Select your tutorial script (.txt)",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
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

        self.lines = lines
        self.stacked_lines = []
        self.current_idx = 0
        self.total_time = 0.0
        self.total_chars = 0
        self.correct_keystrokes = 0
        self.total_keystrokes = 0

        self.lbl_feedback.config(
            text="Script loaded! Type below or tap Tab to autofill. Press F11 for Live Screen.",
        )
        self.display_current_line()

    def display_current_line(self):
        if self.current_idx >= len(self.lines):
            self.finish_session()
            return

        target = self.lines[self.current_idx]
        self.lbl_progress.config(
            text=f"PRACTICE PLACE  |  Line: {self.current_idx + 1} / {len(self.lines)}"
        )

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
        self.render_stack_and_active()

    def on_type(self, *args):
        if not self.lines or self.current_idx >= len(self.lines):
            return

        typed = self.entry_var.get()
        target = self.lines[self.current_idx]

        if self.line_start_time is None and len(typed) > 0:
            self.line_start_time = time.perf_counter()

        # Update top big-word live display
        self.render_stack_and_active()

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
        goal = self.target_wpm.get()
        low = max(10, goal - 5)
        high = goal + 5

        if current_wpm is None:
            self.lbl_pace.config(text=f"Pace: Ready ({low}-{high} WPM ideal)", fg=t["accent"])
            self.pace_dot.itemconfig(self.dot_oval, fill="#6c7086")
            return

        if low <= current_wpm <= high:
            self.lbl_pace.config(text=f"Pace: ON TARGET ({low}-{high} WPM)", fg=t["green"])
            self.pace_dot.itemconfig(self.dot_oval, fill=t["green"])
        elif current_wpm < low:
            self.lbl_pace.config(text=f"Pace: Too Slow (Aim {low}-{high} WPM)", fg=t["yellow"])
            self.pace_dot.itemconfig(self.dot_oval, fill=t["yellow"])
        else:
            self.lbl_pace.config(text=f"Pace: Too Fast (Aim {low}-{high} WPM)", fg=t["orange"])
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

        wpm = (self.total_chars / 5) / (self.total_time / 60) if self.total_time > 0 else 0
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
                text="Perfect! Line stacked cleanly above.", fg=t["green"]
            )
            self.current_idx += 1
            self.display_current_line()
        else:
            if not self.recording_mode and self.drill_mode.get():
                self.lbl_feedback.config(
                    text="Drill Mode: Mistake detected! Fix or re-type cleanly before stacking.",
                    fg=t["red"],
                )
                self.entry_var.set("")
                self.display_current_line()
            else:
                self.stacked_lines.append(typed)
                self.lbl_feedback.config(
                    text="Line stacked above.",
                    fg=t["orange"],
                )
                self.current_idx += 1
                self.display_current_line()

    def finish_session(self):
        self.entry_var.set("")
        self.entry_input.config(state="disabled")
        self.render_stack_and_active()

        self.txt_target.config(state="normal")
        self.txt_target.delete("1.0", tk.END)
        self.txt_target.insert("1.0", "Script complete! Click 'Open .txt Script' for another file, or press [Esc] to exit.", "correct")
        self.txt_target.config(state="disabled")
        self.lbl_next.config(text="Next: > Finished!")
        self.lbl_feedback.config(
            text="Session finished! Press Ctrl+L to clear screen, or load another .txt script."
        )

    def confirm_exit(self, event=None):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTrainerApp(root)
    root.mainloop()
