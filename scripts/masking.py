import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import shutil

SUPPORTED_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}


def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def is_image_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in SUPPORTED_EXTS


def natural_sort_key(s: str):
    return s.lower()


def safe_out_name_from_relative(rel: Path) -> str:
    s = rel.as_posix().strip("/")
    s = s.replace("/", "_").replace("\\", "_")
    for ch in [":", "*", "?", '"', "<", ">", "|"]:
        s = s.replace(ch, "_")
    return s or "STACK"


class HuginStackGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hugin Focus Stack (align_image_stack + enfuse)")
        self.geometry("900x580")
        self.resizable(True, True)

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

        # Stacking mode: "folder" or "sequential"
        self.stack_mode = tk.StringVar(value="folder")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- Paths frame ---
        paths = ttk.LabelFrame(self, text="Folders and Tools")
        paths.pack(fill="x", **pad)

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

        # --- Settings frame ---
        settings = ttk.LabelFrame(self, text="Stack Settings")
        settings.pack(fill="x", **pad)

        ttk.Label(settings, text="Stack mode:").grid(row=0, column=0, sticky="w", padx=8, pady=6)

        mode_frame = ttk.Frame(settings)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky="w", padx=8, pady=6)

        ttk.Radiobutton(
            mode_frame,
            text="Folder-based stacking",
            variable=self.stack_mode,
            value="folder"
        ).pack(side="left", padx=(0, 15))

        ttk.Radiobutton(
            mode_frame,
            text="Sequential stacking",
            variable=self.stack_mode,
            value="sequential"
        ).pack(side="left")

        mode_note = ttk.Label(
            settings,
            text="Folder-based: recursive / subfolders    |    Sequential: root folder only",
            foreground="gray"
        )
        mode_note.grid(row=1, column=1, columnspan=2, sticky="w", padx=8, pady=(0, 6))

        ttk.Label(settings, text="Images per stack:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Spinbox(settings, from_=2, to=500, textvariable=self.stack_size, width=8).grid(
            row=2, column=1, sticky="w", padx=8, pady=6
        )

        ttk.Checkbutton(
            settings,
            text="Delete aligned temp TIFFs after each stack",
            variable=self.cleanup_aligned
        ).grid(row=2, column=2, sticky="w", padx=8, pady=6)

        ttk.Label(
            settings,
            text="Enfuse weights (typical focus stack: contrast=1, exposure=0, saturation=0)"
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=6)

        row2 = ttk.Frame(settings)
        row2.grid(row=4, column=0, columnspan=3, sticky="we", padx=8, pady=4)

        ttk.Label(row2, text="contrast").grid(row=0, column=0, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.contrast_weight, width=6).grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(row2, text="exposure").grid(row=0, column=2, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.exposure_weight, width=6).grid(row=0, column=3, sticky="w", padx=6)

        ttk.Label(row2, text="saturation").grid(row=0, column=4, sticky="w", padx=6)
        ttk.Entry(row2, textvariable=self.saturation_weight, width=6).grid(row=0, column=5, sticky="w", padx=6)

        ttk.Checkbutton(row2, text="--hard-mask", variable=self.hard_mask).grid(row=0, column=6, sticky="w", padx=10)

        # --- Run frame ---
        run = ttk.LabelFrame(self, text="Run")
        run.pack(fill="x", **pad)

        self.run_btn = ttk.Button(run, text="Run Batch Stack", command=self.start)
        self.run_btn.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        self.cancel_btn = ttk.Button(run, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        self.progress = ttk.Progressbar(run, orient="horizontal", length=450, mode="determinate")
        self.progress.grid(row=0, column=2, padx=8, pady=8, sticky="we")

        run.columnconfigure(2, weight=1)

        self.status = ttk.Label(run, text="Ready.")
        self.status.grid(row=1, column=0, columnspan=3, sticky="w", padx=8, pady=6)

        # --- Log output ---
        logf = ttk.LabelFrame(self, text="Log")
        logf.pack(fill="both", expand=True, **pad)

        self.log = tk.Text(logf, wrap="word", height=16)
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

    # ---------------- UI helpers ----------------
    def pick_input(self):
        p = filedialog.askdirectory(title="Select input folder")
        if p:
            self.input_dir.set(p)

    def pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.output_dir.set(p)

    def pick_align(self):
        p = filedialog.askopenfilename(
            title="Select align_image_stack executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if p:
            self.align_path.set(p)

    def pick_enfuse(self):
        p = filedialog.askopenfilename(
            title="Select enfuse executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if p:
            self.enfuse_path.set(p)

    def append_log(self, line: str):
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.update_idletasks()

    def set_status(self, text: str):
        self.status.config(text=text)
        self.update_idletasks()

    # ---------------- Validation helpers ----------------
    def resolve_executable(self, exe_value: str, friendly_name: str):
        exe_value = exe_value.strip()

        if Path(exe_value).exists():
            return str(Path(exe_value))

        found = shutil.which(exe_value)
        if found:
            return found

        messagebox.showerror(
            "Missing executable",
            f"Could not find {friendly_name}.\n\n"
            f"Current value: {exe_value}\n\n"
            f"Please click 'Find…' and select the correct executable file."
        )
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

    # ---------------- Run control ----------------
    def start(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        if not self.validate():
            return

        self.cancel_requested.clear()
        self.run_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["value"] = 0
        self.log.delete("1.0", "end")

        self.worker_thread = threading.Thread(target=self.run_batch, daemon=True)
        self.worker_thread.start()

    def cancel(self):
        self.cancel_requested.set()
        self.set_status("Cancel requested… will stop after current stack finishes.")
        self.append_log("CANCEL requested by user.")

    # ---------------- Stack gathering ----------------
    def _gather_stacks_by_folder(self, in_dir: Path, stack_n: int):
        """
        Folder mode:
        - Walk recursively
        - Each folder containing >=2 images becomes one stack
        - Use up to stack_n images from that folder
        """
        stacks = []

        for folder in [in_dir] + [p for p in in_dir.rglob("*") if p.is_dir()]:
            imgs = sorted(
                [p for p in folder.iterdir() if is_image_file(p)],
                key=lambda p: natural_sort_key(p.name)
            )
            if len(imgs) >= 2:
                use_n = min(len(imgs), stack_n)
                rel = folder.relative_to(in_dir)
                out_base = safe_out_name_from_relative(rel)
                stacks.append({
                    "folder": folder,
                    "images": imgs[:use_n],
                    "out_base": out_base,
                    "label": rel.as_posix() if str(rel) != "." else "(root)"
                })

        stacks.sort(key=lambda x: natural_sort_key(str(x["folder"]).lower()))
        return stacks

    def _gather_stacks_sequential(self, in_dir: Path, stack_n: int):
        """
        Sequential mode:
        - Look only in the selected input folder
        - Sort all images
        - Group them every stack_n images
        - Ignore leftover images if fewer than 2 remain
        """
        files = sorted(
            [p for p in in_dir.iterdir() if is_image_file(p)],
            key=lambda p: natural_sort_key(p.name)
        )

        stacks = []
        total = len(files)

        for i in range(0, total, stack_n):
            chunk = files[i:i + stack_n]
            if len(chunk) >= 2:
                out_base = chunk[0].stem
                label = f"Images {i+1}-{i+len(chunk)}"
                stacks.append({
                    "folder": in_dir,
                    "images": chunk,
                    "out_base": out_base,
                    "label": label
                })

        return stacks

    # ---------------- Main batch logic ----------------
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
            self.after(0, lambda: messagebox.showerror(
                "No stacks found",
                f"No valid stacks were found.\n\n"
                f"Mode: {mode_name}\n"
                f"Supported types: {', '.join(sorted(SUPPORTED_EXTS))}"
            ))
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

            # Align
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

            aligned = sorted(
                temp_root.glob(f"{prefix.name}*.tif"),
                key=lambda p: natural_sort_key(p.name)
            )

            if len(aligned) < 2:
                failed += 1
                log_line("  ERROR: alignment produced fewer than 2 aligned TIFFs. Skipping stack.")
                self.after(0, lambda ii=idx: self.progress.configure(value=ii))
                continue

            # Enfuse
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

        self.after(0, lambda: self.set_status(
            f"Done. Processed {processed}, failed {failed}, stopped={'YES' if stopped else 'NO'}."
        ))
        self.after(0, self.finish_ui)

    def finish_ui(self):
        self.run_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")


if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = HuginStackGUI()
    app.mainloop()