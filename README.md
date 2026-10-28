# Photo Workflow App — User Guide

Created by **Jorge Castillo Castro**. The final version of the program was developed with assistance from **GPT-6.1 Sol light**.

**Internal use only.** This program can make mistakes. Review its results and keep backups of your original images.

Please report any problems through the **Issues** tab in this project's GitHub repository so they can be tracked and addressed.


## 1) How to install Hugin

1. Open the [official Hugin download page](https://hugin.sourceforge.io/download/).
2. Download and run the Windows installer.
3. Accept the default installation location unless you prefer a custom folder.
4. Finish the installation.

The app needs these two tools:

- `align_image_stack.exe`
- `enfuse.exe`

Look for them inside Hugin's `bin` folder. A common Windows location is:

```text
C:\Program Files\Hugin\bin
```

Use the actual installation folder on your computer if it differs.

## 2) How to set the PATH to the program

Adding Hugin's tools to PATH lets the app find them by name.

1. Open **Start** and search for **Edit environment variables for your account**.
2. Under **User variables**, select **Path** and click **Edit**.
3. Click **New** and add your Hugin `bin` folder, for example:

   ```text
   C:\Program Files\Hugin\bin
   ```

4. Click **OK** on all windows.
5. Close and reopen the Photo Workflow App so it receives the updated PATH.

You can also select the two executables directly using the **Find…** buttons in the Focus Stacker tab.

## 3) How to open the app with the .exe

1. Download and extract this repository if you have not already done so.
2. Open the `dist` folder.
3. Double-click `combined_photo_workflow_app.exe`.

For easier access, right-click the executable and choose **Send to > Desktop (create shortcut)**. On some Windows versions, select **Show more options** first.

The existing Windows executable is included in this repository. Hugin must be installed separately.

## 4) How to add the images to sort

This is the **Organizer** task. It sorts your original rotary-platform photos into folders for levels and positions.

1. Open `combined_photo_workflow_app.exe`.
2. Go to the **Organizer** tab.
3. Choose the **input folder** containing your original images.
4. Choose or create an **output folder** for the organized files.
5. Set:
   - **Images per rotation**
   - **Rotations per level**
   - **Levels**
6. Choose whether to **copy** or **move** the files.
7. Click **Run Organizer**.

The app reads the input images and places them into a structured set of folders at the output location, ready for stacking.

**Recommended workflow:** use your original photos as input, a separate empty folder as output, and copy mode to keep your originals in place.

## 5) How to add the images to merge-stack

This is the **Focus Stacker** task. It uses `align_image_stack` to align the images and `enfuse` to blend them into a stacked result.

1. Open the app and go to the **Focus Stacker** tab.
2. Choose the **input folder**:
   - **Stack the organized folders:** select the output folder created by Organizer.
   - **Stack another prepared folder:** select a folder containing images you have already arranged for stacking.
3. Choose the **output folder** where the stacked images should be saved.
4. Check the paths to `align_image_stack` and `enfuse`. Use **Find…** to select the executables if needed.
5. Choose a stacking mode:
   - **Folder-based stacking:** searches the input folder and its subfolders for image groups.
   - **Sequential stacking:** groups images in sequence from the input folder only.
6. Set **Images per stack** to match your image groups.
7. Click **Run Batch Stack**.

For each group, the app aligns the images, blends them, and saves a stacked TIFF in the output folder. Check the log for progress and any errors.

The stacker accepts JPG, JPEG, TIF, TIFF, and PNG files. Convert camera RAW files to one of these formats before stacking.

Try a small set of copied images first to confirm your folder structure and settings.
