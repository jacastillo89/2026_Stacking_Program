import os
import re
import shutil

SOURCE_ROOT = r"E:\Boulder\Exports\stils"
DEST_ROOT   = r"E:\Boulder\Exports\selected"

os.makedirs(DEST_ROOT, exist_ok=True)

# Adjust/expand as needed (or set to None to copy any extension)
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".exr")

TARGETS = {11, 31, 51, 71, 91, 111, 131, 151, 171, 191, 211}

# f0121-... (case-insensitive) capture the 4 digits
pattern = re.compile(r"^f(\d{4})-", re.IGNORECASE)

copied = []
skipped_existing = 0

for root, _, files in os.walk(SOURCE_ROOT):
    for name in files:
        if IMAGE_EXTS and not name.lower().endswith(IMAGE_EXTS):
            continue

        m = pattern.match(name)
        if not m:
            continue

        frame_number = int(m.group(1))
        if frame_number not in TARGETS:
            continue

        src_path = os.path.join(root, name)

        # Preserve folder structure under SOURCE_ROOT
        rel_dir = os.path.relpath(root, SOURCE_ROOT)   # e.g., ShotA\Cam05
        dst_dir = os.path.join(DEST_ROOT, rel_dir)     # e.g., ...\selected\ShotA\Cam05
        os.makedirs(dst_dir, exist_ok=True)

        dst_path = os.path.join(dst_dir, name)

        # If the exact destination file already exists, skip (no overwrite)
        if os.path.exists(dst_path):
            skipped_existing += 1
            continue

        shutil.copy2(src_path, dst_path)
        copied.append(dst_path)

print(f"\nCopied {len(copied)} files into:")
print(DEST_ROOT)
print(f"Skipped (already existed): {skipped_existing}")
