import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from datetime import datetime

APP_TITLE = "Photo Workflow App"

ORGANIZER_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp",
    ".cr2", ".cr3", ".nef", ".arw", ".dng"
}
STACKER_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def natural_sort_key_text(value: str):
    parts = re.split(r"(\d+)", value.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def safe_make_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def extract_number(filename: str):
    matches = re.findall(r"(\d+)", filename)
    if not matches:
        return None
    return int(matches[-1])


def get_sorted_images_for_organizer(input_folder: Path):
    image_files = []
    for item in input_folder.iterdir():
        if item.is_file() and item.suffix.lower() in ORGANIZER_EXTENSIONS:
            num = extract_number(item.name)
            if num is not None:
                image_files.append((num, str(item), item.name))
    image_files.sort(key=lambda x: (x[0], natural_sort_key_text(x[2])))
    return image_files


def is_stacker_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in STACKER_EXTENSIONS


def safe_out_name_from_relative(rel: Path) -> str:
    s = rel.as_posix().strip("/")
    s = s.replace("/", "_").replace("\\", "_")
    for ch in [":", "*", "?", '"', "<", ">", "|"]:
        s = s.replace(ch, "_")
    return s or "STACK"


class OrganizerTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.images_per_rotation_var = tk.StringVar(value="24")
        self.rotations_per_level_var = tk.StringVar(value="3")
        self.levels_var = tk.StringVar(value="5")
        self.copy_mode_var = tk.BooleanVar(value=True)
        self.build_ui()

    def build_ui(self):
        title = ttk.Label(self, text="Task 1: Rotary Platform Image Organizer", font=("Arial", 15, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        input_frame = ttk.LabelFrame(self, text="Input Folder", padding=10)
        input_frame.pack(fill="x", pady=4)
        ttk.Entry(input_frame, textvariable=self.input_folder_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(input_frame, text="Browse", command=self.browse_input).pack(side="right")

        output_frame = ttk.LabelFrame(self, text="Output Folder", padding=10)
        output_frame.pack(fill="x", pady=4)
        ttk.Entry(output_frame, textvariable=self.output_folder_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="right")

        settings_frame = ttk.LabelFrame(self, text="Organization Settings", padding=10)
        settings_frame.pack(fill="x", pady=8)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Images per rotation:", width=22).pack(side="left")
        ttk.Entry(row1, textvariable=self.images_per_rotation_var, width=10).pack(side="left", padx=(0, 20))
        ttk.Label(row1, text="Rotations per level:", width=22).pack(side="left")
        ttk.Entry(row1, textvariable=self.rotations_per_level_var, width=10).pack(side="left", padx=(0, 20))
        ttk.Label(row1, text="Levels:", width=10).pack(side="left")
        ttk.Entry(row1, textvariable=self.levels_var, width=10).pack(side="left")

        mode_frame = ttk.LabelFrame(self, text="File Handling", padding=10)
        mode_frame.pack(fill="x", pady=4)
        ttk.Radiobutton(mode_frame, text="Copy files (recommended)", variable=self.copy_mode_var, value=True).pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Move files", variable=self.copy_mode_var, value=False).pack(anchor="w")

        info_frame = ttk.LabelFrame(self, text="How It Works", padding=10)
        info_frame.pack(fill="x", pady=8)
        info_text = (
            "The script assumes images are in capture order.\n\n"
            "For each level:\n"
            "- Rotation 1 contains positions 1 to N\n"
            "- Rotation 2 contains positions 1 to N\n"
            "- Rotation 3 contains positions 1 to N\n\n"
            "It groups matching positions together.\n"
            "Example:\n"
            "- position_01 gets image 1 from rotation 1, image 1 from rotation 2, and image 1 from rotation 3.\n"
            "- position_02 gets image 2 from each rotation, and so on."
        )
        ttk.Label(info_frame, text=info_text, justify="left").pack(anchor="w")

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=8)
        ttk.Button(button_frame, text="Preview Summary", command=self.preview_summary).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Run Organizer", command=self.run_organizer).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side="left")

        log_frame = ttk.LabelFrame(self, text="Organizer Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=8)
        self.log_text = ScrolledText(log_frame, wrap="word", height=18)
        self.log_text.pack(fill="both", expand=True)

    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder_var.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def get_settings(self):
        input_folder = self.input_folder_var.get().strip()
        output_folder = self.output_folder_var.get().strip()
        if not input_folder:
            raise ValueError("Please select an input folder.")
        if not output_folder:
            raise ValueError("Please select an output folder.")
        try:
            images_per_rotation = int(self.images_per_rotation_var.get())
            rotations_per_level = int(self.rotations_per_level_var.get())
            levels = int(self.levels_var.get())
        except ValueError:
            raise ValueError("Images per rotation, rotations per level, and levels must be whole numbers.")
        if images_per_rotation <= 0 or rotations_per_level <= 0 or levels <= 0:
            raise ValueError("All numeric values must be greater than zero.")
        return {
            "input_folder": input_folder,
            "output_folder": output_folder,
            "images_per_rotation": images_per_rotation,
            "rotations_per_level": rotations_per_level,
            "levels": levels,
            "copy_files": self.copy_mode_var.get(),
        }

    def preview_summary(self):
        try:
            settings = self.get_settings()
        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
            return
        input_folder = Path(settings["input_folder"])
        if not input_folder.exists():
            messagebox.showerror("Input Folder Error", "The selected input folder does not exist.")
            return
        images = get_sorted_images_for_organizer(input_folder)
        images_per_level = settings["images_per_rotation"] * settings["rotations_per_level"]
        expected_total = images_per_level * settings["levels"]
        complete_levels = len(images) // images_per_level if images_per_level > 0 else 0
        leftover = len(images) % images_per_level if images_per_level > 0 else 0
        summary = (
            f"Found images: {len(images)}\n"
            f"Images per rotation: {settings['images_per_rotation']}\n"
            f"Rotations per level: {settings['rotations_per_level']}\n"
            f"Levels requested: {settings['levels']}\n"
            f"Images needed per level: {images_per_level}\n"
            f"Expected total images: {expected_total}\n"
            f"Complete levels available: {complete_levels}\n"
            f"Leftover images: {leftover}\n"
            f"Mode: {'Copy' if settings['copy_files'] else 'Move'}"
        )
        messagebox.showinfo("Preview Summary", summary)

    def run_organizer(self):
        self.clear_log()
        try:
            settings = self.get_settings()
        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
            return

        input_folder = Path(settings["input_folder"])
        output_folder = Path(settings["output_folder"])
        if not input_folder.exists():
            messagebox.showerror("Input Folder Error", "The selected input folder does not exist.")
            return
        try:
            safe_make_dir(output_folder)
        except Exception as e:
            messagebox.showerror("Output Folder Error", f"Could not create/access output folder:\n{e}")
            return

        images = get_sorted_images_for_organizer(input_folder)
        if not images:
            messagebox.showerror("No Images Found", "No supported image files with numbers in their filenames were found.")
            return

        images_per_rotation = settings["images_per_rotation"]
        rotations_per_level = settings["rotations_per_level"]
        levels = settings["levels"]
        copy_files = settings["copy_files"]

        images_per_level = images_per_rotation * rotations_per_level
        expected_total = images_per_level * levels

        self.log(f"Found {len(images)} image(s).")
        self.log(f"Images per level: {images_per_level}")
        self.log(f"Expected total for requested levels: {expected_total}")
        self.log("")

        if len(images) < expected_total:
            self.log("WARNING: Fewer images than expected.")
            self.log("The script will organize as many complete levels as possible.")
            self.log("")
        elif len(images) > expected_total:
            self.log("WARNING: More images than expected.")
            self.log("Only the first expected images will be used.")
            self.log("")

        usable_images = images[:expected_total]
        complete_levels = len(usable_images) // images_per_level
        if complete_levels == 0:
            messagebox.showerror("Not Enough Images", "There are not enough images to complete even one full level.")
            return

        self.log(f"Complete level(s) to organize: {complete_levels}")
        self.log("")

        try:
            for level_index in range(complete_levels):
                level_number = level_index + 1
                level_folder = output_folder / f"level_{level_number:02d}"
                safe_make_dir(level_folder)
                self.log(f"Creating {level_folder}")
                level_start = level_index * images_per_level

                for position_index in range(images_per_rotation):
                    position_number = position_index + 1
                    position_folder = level_folder / f"position_{position_number:02d}"
                    safe_make_dir(position_folder)

                    for rotation_index in range(rotations_per_level):
                        focus_number = rotation_index + 1
                        image_global_index = level_start + (rotation_index * images_per_rotation) + position_index
                        if image_global_index >= len(usable_images):
                            continue
                        _, src_path, original_name = usable_images[image_global_index]
                        src_path = Path(src_path)
                        dst_name = f"L{level_number:02d}_P{position_number:02d}_F{focus_number:02d}{src_path.suffix.lower()}"
                        dst_path = position_folder / dst_name
                        if copy_files:
                            shutil.copy2(src_path, dst_path)
                            action = "Copied"
                        else:
                            shutil.move(src_path, dst_path)
                            action = "Moved"
                        self.log(f"{action}: {original_name}  ->  {dst_path}")

            leftover_total = len(images) - len(usable_images)
            self.log("")
            self.log("Done.")
            if leftover_total > 0:
                self.log(f"Extra unused images: {leftover_total}")
            messagebox.showinfo("Finished", "Image organization completed successfully.")
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred:\n{e}")


class StackerTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.cancel_requested = threading.Event()
        self.worker_thread = None
        self.align_path = tk.StringVar(value="align_image_stack")
        self.enfuse_path = tk.StringVar(value="enfuse")
        self.input_dir = tk.StringVar(value="")
        self.output_dir = tk.StringVar(value="")
        self.stack_size = tk.IntVar(value=3)
        self.cleanup_aligned = tk.BooleanVar(value=True)
        self.contrast_weight = tk.DoubleVar(value=1.0)
        self.exposure_weight = tk.DoubleVar(value=0.0)
        self.saturation_weight = tk.DoubleVar(value=0.0)
        self.hard_mask = tk.BooleanVar(value=True)
        self.stack_mode = tk.StringVar(value="folder")
        self.build_ui()

    def build_ui(self):
        title = ttk.Label(self, text="Task 2: Hugin Focus Stacker", font=("Arial", 15, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        paths = ttk.LabelFrame(self, text="Folders and Tools", padding=10)
        paths.pack(fill="x", pady=4)
        ttk.Label(paths, text="Input folder:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.input_dir, width=72).grid(row=0, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(paths, text="Browse…", command=self.pick_input).grid(row=0, column=2, padx=8, pady=6)
        ttk.Label(paths, text="Output folder (stacked TIFF):").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.output_dir, width=72).grid(row=1, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(paths, text="Browse…", command=self.pick_output).grid(row=1, column=2, padx=8, pady=6)
        ttk.Label(paths, text="align_image_stack:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.align_path, width=72).grid(row=2, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(paths, text="Find…", command=self.pick_align).grid(row=2, column=2, padx=8, pady=6)
        ttk.Label(paths, text="enfuse:").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.enfuse_path, width=72).grid(row=3, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(paths, text="Find…", command=self.pick_enfuse).grid(row=3, column=2, padx=8, pady=6)
        paths.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(self, text="Stack Settings", padding=10)
        settings.pack(fill="x", pady=8)
        ttk.Label(settings, text="Stack mode:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        mode_frame = ttk.Frame(settings)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Radiobutton(mode_frame, text="Folder-based stacking", variable=self.stack_mode, value="folder").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="Sequential stacking", variable=self.stack_mode, value="sequential").pack(side="left")
        ttk.Label(settings, text="Folder-based: recursive / subfolders    |    Sequential: root folder only", foreground="gray").grid(row=1, column=1, columnspan=2, sticky="w", padx=8, pady=(0, 6))
        ttk.Label(settings, text="Images per stack:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Spinbox(settings, from_=2, to=500, textvariable=self.stack_size, width=8).grid(row=2, column=1, sticky="w", padx=8, pady=6)
        ttk.Checkbutton(settings, text="Delete aligned temp TIFFs after each stack", variable=self.cleanup_aligned).grid(row=2, column=2, sticky="w", padx=8, pady=6)
        ttk.Label(settings, text="Enfuse weights (typical focus stack: contrast=1, exposure=0, saturation=0)").grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=6)
        row2 = ttk.Frame(settings)
        row2.grid(row=4, column=0, columnspan=3, sticky="we", padx=8, pady=4)
        ttk.Label(row2, text="contrast").grid(row=0, column=0, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.contrast_weight, width=6).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(row2, text="exposure").grid(row=0, column=2, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.exposure_weight, width=6).grid(row=0, column=3, sticky="w", padx=6)
        ttk.Label(row2, text="saturation").grid(row=0, column=4, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.saturation_weight, width=6).grid(row=0, column=5, sticky="w", padx=6)
        ttk.Checkbutton(row2, text="--hard-mask", variable=self.hard_mask).grid(row=0, column=6, sticky="w", padx=10)

        run = ttk.LabelFrame(self, text="Run", padding=10)
        run.pack(fill="x", pady=4)
        self.run_btn = ttk.Button(run, text="Run Batch Stack", command=self.start)
        self.run_btn.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.cancel_btn = ttk.Button(run, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self.progress = ttk.Progressbar(run, orient="horizontal", length=450, mode="determinate")
        self.progress.grid(row=0, column=2, padx=8, pady=8, sticky="we")
        run.columnconfigure(2, weight=1)
        self.status = ttk.Label(run, text="Ready.")
        self.status.grid(row=1, column=0, columnspan=3, sticky="w", padx=8, pady=6)

        logf = ttk.LabelFrame(self, text="Stacker Log", padding=10)
        logf.pack(fill="both", expand=True, pady=8)
        self.log_widget = tk.Text(logf, wrap="word", height=16)
        self.log_widget.pack(fill="both", expand=True)

    def pick_input(self):
        p = filedialog.askdirectory(title="Select input folder")
        if p:
            self.input_dir.set(p)

    def pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.output_dir.set(p)

    def pick_align(self):
        p = filedialog.askopenfilename(title="Select align_image_stack executable", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if p:
            self.align_path.set(p)

    def pick_enfuse(self):
        p = filedialog.askopenfilename(title="Select enfuse executable", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if p:
            self.enfuse_path.set(p)

    def append_log(self, line: str):
        self.log_widget.insert("end", line + "\n")
        self.log_widget.see("end")
        self.update_idletasks()

    def set_status(self, text: str):
        self.status.config(text=text)
        self.update_idletasks()

    def resolve_executable(self, exe_value: str, friendly_name: str):
        exe_value = exe_value.strip()
        if Path(exe_value).exists():
            return str(Path(exe_value))
        found = shutil.which(exe_value)
        if found:
            return found
        messagebox.showerror("Missing executable", f"Could not find {friendly_name}.\n\nCurrent value: {exe_value}\n\nPlease click 'Find…' and select the correct executable file.")
        return None

    def validate(self) -> bool:
        in_dir = Path(self.input_dir.get().strip())
        out_dir = Path(self.output_dir.get().strip())
        if not in_dir.exists():
            messagebox.showerror("Missing input", "Please select a valid input folder.")
            return False
        if not out_dir.exists():
            messagebox.showerror("Missing output", "Please select a valid output folder.")
            return False
        try:
            n = int(self.stack_size.get())
            if n < 2:
                raise ValueError()
        except Exception:
            messagebox.showerror("Bad stack size", "Stack size must be an integer >= 2.")
            return False
        resolved_align = self.resolve_executable(self.align_path.get(), "align_image_stack")
        if not resolved_align:
            return False
        resolved_enfuse = self.resolve_executable(self.enfuse_path.get(), "enfuse")
        if not resolved_enfuse:
            return False
        self.align_path.set(resolved_align)
        self.enfuse_path.set(resolved_enfuse)
        return True

    def start(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return
        if not self.validate():
            return
        self.cancel_requested.clear()
        self.run_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["value"] = 0
        self.log_widget.delete("1.0", "end")
        self.worker_thread = threading.Thread(target=self.run_batch, daemon=True)
        self.worker_thread.start()

    def cancel(self):
        self.cancel_requested.set()
        self.set_status("Cancel requested… will stop after current stack finishes.")
        self.append_log("CANCEL requested by user.")

    def _gather_stacks_by_folder(self, in_dir: Path, stack_n: int):
        stacks = []
        for folder in [in_dir] + [p for p in in_dir.rglob("*") if p.is_dir()]:
            imgs = sorted([p for p in folder.iterdir() if is_stacker_image_file(p)], key=lambda p: natural_sort_key_text(p.name))
            if len(imgs) >= 2:
                use_n = min(len(imgs), stack_n)
                rel = folder.relative_to(in_dir)
                out_base = safe_out_name_from_relative(rel)
                stacks.append({
                    "folder": folder,
                    "images": imgs[:use_n],
                    "out_base": out_base,
                    "label": rel.as_posix() if str(rel) != "." else "(root)",
                })
        stacks.sort(key=lambda x: natural_sort_key_text(str(x["folder"]).lower()))
        return stacks

    def _gather_stacks_sequential(self, in_dir: Path, stack_n: int):
        files = sorted([p for p in in_dir.iterdir() if is_stacker_image_file(p)], key=lambda p: natural_sort_key_text(p.name))
        stacks = []
        total = len(files)
        for i in range(0, total, stack_n):
            chunk = files[i:i + stack_n]
            if len(chunk) >= 2:
                stacks.append({
                    "folder": in_dir,
                    "images": chunk,
                    "out_base": chunk[0].stem,
                    "label": f"Images {i + 1}-{i + len(chunk)}",
                })
        return stacks

    def run_batch(self):
        in_dir = Path(self.input_dir.get().strip())
        out_dir = Path(self.output_dir.get().strip())
        stack_n = int(self.stack_size.get())
        align_exe = self.align_path.get().strip()
        enfuse_exe = self.enfuse_path.get().strip()
        mode = self.stack_mode.get().strip()
        log_file = out_dir / f"FocusStack_Hugin_{timestamp()}.log.txt"

        def log_line(s: str):
            self.append_log(s)
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(s + "\n")
            except Exception:
                pass

        if mode == "folder":
            stacks = self._gather_stacks_by_folder(in_dir, stack_n)
            mode_name = "Folder-based stacking"
        else:
            stacks = self._gather_stacks_sequential(in_dir, stack_n)
            mode_name = "Sequential stacking"

        if not stacks:
            self.after(0, lambda: messagebox.showerror("No stacks found", f"No valid stacks were found.\n\nMode: {mode_name}\nSupported types: {', '.join(sorted(STACKER_EXTENSIONS))}"))
            self.after(0, self.finish_ui)
            return

        total_stacks = len(stacks)
        self.after(0, lambda: self.progress.configure(maximum=total_stacks))
        log_line("=== Hugin Focus Stack Batch ===")
        log_line(f"Mode:          {mode_name}")
        log_line(f"Input:         {in_dir}")
        log_line(f"Output:        {out_dir}")
        log_line(f"Images/stack:  {stack_n}")
        log_line(f"Stacks found:  {total_stacks}")
        log_line(f"align_image_stack: {align_exe}")
        log_line(f"enfuse:            {enfuse_exe}")
        log_line("--------------------------------")

        temp_root = out_dir / "_HUGIN_TEMP_ALIGNED"
        temp_root.mkdir(parents=True, exist_ok=True)
        processed = 0
        failed = 0
        stopped = False

        for idx, stack in enumerate(stacks, start=1):
            if self.cancel_requested.is_set():
                stopped = True
                log_line(f"STOP: Cancel requested before starting stack {idx}.")
                break
            chunk = stack["images"]
            out_base = stack["out_base"]
            label = stack["label"]
            out_file = out_dir / f"{out_base}_STACKED.tif"
            prefix = temp_root / f"tmp_{out_base}_"
            log_line(f"\n[Stack {idx}/{total_stacks}] {label}")
            log_line(f"  Using {len(chunk)} image(s):")
            for p in chunk:
                log_line(f"   - {p.name}")

            self.after(0, lambda ii=idx: self.set_status(f"Stack {ii}/{total_stacks}: aligning…"))
            align_cmd = [align_exe, "-m", "-a", str(prefix)] + [str(p) for p in chunk]
            log_line("  Running align_image_stack:")
            log_line("   " + " ".join(f'"{c}"' if " " in c else c for c in align_cmd))
            try:
                r = subprocess.run(align_cmd, capture_output=True, text=True, check=False)
                if r.stdout:
                    log_line("  [align stdout]")
                    log_line(r.stdout.strip())
                if r.stderr:
                    log_line("  [align stderr]")
                    log_line(r.stderr.strip())
                if r.returncode != 0:
                    raise RuntimeError(f"align_image_stack failed (code {r.returncode})")
            except Exception as e:
                failed += 1
                log_line(f"  ERROR: {e}")
                self.after(0, lambda ii=idx: self.progress.configure(value=ii))
                continue

            aligned = sorted(temp_root.glob(f"{prefix.name}*.tif"), key=lambda p: natural_sort_key_text(p.name))
            if len(aligned) < 2:
                failed += 1
                log_line("  ERROR: alignment produced fewer than 2 aligned TIFFs. Skipping stack.")
                self.after(0, lambda ii=idx: self.progress.configure(value=ii))
                continue

            self.after(0, lambda ii=idx: self.set_status(f"Stack {ii}/{total_stacks}: blending (enfuse)…"))
            enfuse_cmd = [
                enfuse_exe,
                f"--exposure-weight={float(self.exposure_weight.get())}",
                f"--saturation-weight={float(self.saturation_weight.get())}",
                f"--contrast-weight={float(self.contrast_weight.get())}",
            ]
            if self.hard_mask.get():
                enfuse_cmd.append("--hard-mask")
            enfuse_cmd += ["-o", str(out_file)] + [str(p) for p in aligned]
            log_line("  Running enfuse:")
            log_line("   " + " ".join(f'"{c}"' if " " in c else c for c in enfuse_cmd))
            try:
                r = subprocess.run(enfuse_cmd, capture_output=True, text=True, check=False)
                if r.stdout:
                    log_line("  [enfuse stdout]")
                    log_line(r.stdout.strip())
                if r.stderr:
                    log_line("  [enfuse stderr]")
                    log_line(r.stderr.strip())
                if r.returncode != 0:
                    raise RuntimeError(f"enfuse failed (code {r.returncode})")
            except Exception as e:
                failed += 1
                log_line(f"  ERROR: {e}")
                self.after(0, lambda ii=idx: self.progress.configure(value=ii))
                continue

            if self.cleanup_aligned.get():
                for p in aligned:
                    try:
                        p.unlink()
                    except Exception:
                        pass

            processed += 1
            self.after(0, lambda ii=idx: self.progress.configure(value=ii))
            log_line(f"  OK -> {out_file.name}")
            if self.cancel_requested.is_set():
                stopped = True
                log_line("STOP: Cancel requested after completing current stack.")
                break

        log_line("\n--------------------------------")
        log_line("SUMMARY")
        log_line(f"Processed: {processed}")
        log_line(f"Failed:    {failed}")
        log_line(f"Stopped:   {'YES' if stopped else 'NO'}")
        log_line(f"Log file:  {log_file}")
        log_line("=== End ===")
        self.after(0, lambda: self.set_status(f"Done. Processed {processed}, failed {failed}, stopped={'YES' if stopped else 'NO'}."))
        self.after(0, self.finish_ui)

    def finish_ui(self):
        self.run_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")


class CombinedPhotoWorkflowApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x760")
        self.minsize(900, 700)
        self._set_dpi_awareness()
        self.build_ui()

    def _set_dpi_awareness(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    def build_ui(self):
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Combined Photo Workflow App",
            font=("Arial", 18, "bold")
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="Use Tab 1 to organize rotary captures into position folders. Use Tab 2 to focus-stack those folders with Hugin.",
        ).pack(anchor="w", pady=(4, 10))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        self.organizer_tab = OrganizerTab(notebook)
        self.stacker_tab = StackerTab(notebook)
        notebook.add(self.organizer_tab, text="1. Organizer")
        notebook.add(self.stacker_tab, text="2. Focus Stacker")


if __name__ == "__main__":
    app = CombinedPhotoWorkflowApp()
    app.mainloop()
