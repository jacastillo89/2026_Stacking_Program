import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp",
    ".cr2", ".cr3", ".nef", ".arw", ".dng"
}


def extract_number(filename):
    """
    Extract the last number found in a filename.
    Example:
        'photo stacking test 014.jpg' -> 14
    """
    matches = re.findall(r'(\d+)', filename)
    if not matches:
        return None
    return int(matches[-1])


def get_sorted_images(input_folder):
    """
    Return supported image files sorted by the numeric value found in the filename.
    """
    image_files = []

    for item in os.listdir(input_folder):
        full_path = os.path.join(input_folder, item)

        if os.path.isfile(full_path):
            ext = Path(item).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                num = extract_number(item)
                if num is not None:
                    image_files.append((num, full_path, item))

    image_files.sort(key=lambda x: x[0])
    return image_files


def safe_make_dir(path):
    os.makedirs(path, exist_ok=True)


class ImageOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rotary Photo Organizer")
        self.root.geometry("820x700")

        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()

        self.images_per_rotation_var = tk.StringVar(value="24")
        self.rotations_per_level_var = tk.StringVar(value="3")
        self.levels_var = tk.StringVar(value="5")

        self.copy_mode_var = tk.BooleanVar(value=True)

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Rotary Platform Image Organizer",
            font=("Arial", 16, "bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        # Input folder
        input_frame = ttk.LabelFrame(main, text="Input Folder", padding=10)
        input_frame.pack(fill="x", pady=5)

        ttk.Entry(input_frame, textvariable=self.input_folder_var, width=90).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(input_frame, text="Browse", command=self.browse_input).pack(side="right")

        # Output folder
        output_frame = ttk.LabelFrame(main, text="Output Folder", padding=10)
        output_frame.pack(fill="x", pady=5)

        ttk.Entry(output_frame, textvariable=self.output_folder_var, width=90).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="right")

        # Settings
        settings_frame = ttk.LabelFrame(main, text="Organization Settings", padding=10)
        settings_frame.pack(fill="x", pady=10)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=4)

        ttk.Label(row1, text="Images per rotation:", width=22).pack(side="left")
        ttk.Entry(row1, textvariable=self.images_per_rotation_var, width=10).pack(side="left", padx=(0, 20))

        ttk.Label(row1, text="Rotations per level:", width=22).pack(side="left")
        ttk.Entry(row1, textvariable=self.rotations_per_level_var, width=10).pack(side="left", padx=(0, 20))

        ttk.Label(row1, text="Levels:", width=10).pack(side="left")
        ttk.Entry(row1, textvariable=self.levels_var, width=10).pack(side="left")

        # Copy / Move
        mode_frame = ttk.LabelFrame(main, text="File Handling", padding=10)
        mode_frame.pack(fill="x", pady=5)

        ttk.Radiobutton(
            mode_frame,
            text="Copy files (recommended)",
            variable=self.copy_mode_var,
            value=True
        ).pack(anchor="w")

        ttk.Radiobutton(
            mode_frame,
            text="Move files",
            variable=self.copy_mode_var,
            value=False
        ).pack(anchor="w")

        # Explanation
        info_frame = ttk.LabelFrame(main, text="How It Works", padding=10)
        info_frame.pack(fill="x", pady=10)

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

        # Buttons
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Preview Summary", command=self.preview_summary).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Run Organizer", command=self.run_organizer).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side="left")

        # Log
        log_frame = ttk.LabelFrame(main, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=10)

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
        self.root.update_idletasks()

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
            "copy_files": self.copy_mode_var.get()
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

        images = get_sorted_images(str(input_folder))
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

        images = get_sorted_images(str(input_folder))

        if not images:
            messagebox.showerror(
                "No Images Found",
                "No supported image files with numbers in their filenames were found."
            )
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
            messagebox.showerror(
                "Not Enough Images",
                "There are not enough images to complete even one full level."
            )
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

                        dst_name = (
                            f"L{level_number:02d}_"
                            f"P{position_number:02d}_"
                            f"F{focus_number:02d}"
                            f"{src_path.suffix.lower()}"
                        )
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOrganizerGUI(root)
    root.mainloop()