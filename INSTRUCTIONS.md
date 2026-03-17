# 📘 Houdini Project Manager - Workflow Guide

Welcome to your new workflow! This tool is designed to balance **Structure** (keeping things organized) with **Freedom** (working how you want).

---

## 1. Creating a Project 🆕

When you click **+ New Project**, you are answering two simple questions:

### A. Where does it live? (Location)
You pick a folder like `P:/Jobs/2026` or `D:/Freelance/ClientX`.
*   **The Tool** creates a container folder inside there.
*   **Result**: `P:/Jobs/2026/MyNewProject`

### B. What is inside? (Preset)
You pick a template (e.g., "Base - Seq & Shot").
*   This defines the **folders inside** your project (`seq`, `assets`, `delivery`).
*   **Tip**: "Category" (like Personal/Client) is just a label (tag). It does **not** create extra folders.

---

## 2. Managing Presets 🎛️

Presets are the heart of your pipeline. Go to **Settings (Gear Icon)** to edit them.

### "Freedom + Structure" Philosophy
*   **Root is Protected**: The tool always gives you a clean project folder.
*   **Inside is Yours**: You decide what goes in it.

### How to Edit
1.  **Open Editor**: Click "Edit" on a preset.
2.  **Project Root (Top Level)**: This represents your main project folder.
3.  **Add Folders**: Everything you add here goes *inside* the project.
    *   *Example*: Add `seq`, `assets`, `render`.
    *   *Don't*: Do not add a folder named `{project_name}` here. You are already inside it!

---

## 3. The Dashboard Workflow 🚀

Once a project is open, you are in the **Dashboard**.

### 📂 Navigation
*   **Folder Tree**: On the left.
*   **Yellow Icons**: Folders that look like "Work Areas" (contain `geo`, `render`, etc.).
*   **Orange Icons + Badge**: Folders that actually contain `.hip` files.

### ✨ Creating Files
**Don't know where to save?**
1.  Click a **Yellow Folder** (e.g., `shot010`).
2.  You will see a large blue button: **"Create First Version"**.
3.  Click it to instantly generate `shot010_v001.hip` and start working!

### 🛠️ Right-Click Powers
*   **Rename**: Safely rename folders (even if files are open).
*   **Delete File**: Quickly clean up junk `test_v999.hip` files.
*   **Environment**: The variable `$JOB` is automatically set to your project root.
