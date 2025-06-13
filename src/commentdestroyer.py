# commentdestroyer.py
import dearpygui.dearpygui as dpg
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

# --- Configuration: All Supported Languages ---
LANGUAGE_STYLE_MAP = {
    # C-style comments: // and /* */
    '.c': 'c', '.h': 'c', '.cpp': 'c', '.hpp': 'c', '.cc': 'c',
    '.java': 'c', '.js': 'c', '.mjs': 'c', '.jsx': 'c', '.ts': 'c',
    '.tsx': 'c', '.go': 'c', '.rs': 'c', '.css': 'c',
    # Python/Ruby/Shell style: #
    '.py': 'python', '.pyw': 'python', '.rb': 'python', '.sh': 'python',
    # HTML/XML style: <!-- -->
    '.html': 'html', '.htm': 'html', '.xml': 'html',
}

# --- Global State ---
selected_files = []

# --- Core Stripping Logic  ---
def get_language_style(file_path: str) -> str | None:
    """Determines the language comment style for a file based on its extension."""
    file_ext = Path(file_path).suffix.lower()
    return LANGUAGE_STYLE_MAP.get(file_ext)

def strip_comments_by_style(code_string: str, style: str, preserve_lines: bool) -> str:
    """
    A robust, dependency-free state machine to strip comments from source code.
    This function iterates through the string character by character, keeping track
    of whether it's inside a string, a comment, etc., to avoid incorrectly
    removing comment-like syntax from within strings.
    """
    # Define comment delimiters based on style
    if style == 'c':
        line_start, block_start, block_end = '//', '/*', '*/'
    elif style == 'python':
        line_start, block_start, block_end = '#', None, None # Python has no formal block comments
    elif style == 'html':
        line_start, block_start, block_end = None, '<!--', '-->'
    else:
        return code_string # Return original if style is unknown

    result = []
    # --- State Flags ---
    in_string = False         # True when inside "..."
    in_char = False           # True when inside '...'
    in_block_comment = False  # True when inside /*...*/ or <!--...-->
    in_line_comment = False   # True when inside //... or #...
    
    i = 0
    while i < len(code_string):
        # --- State: Inside a Block Comment ---
        if in_block_comment:
            if code_string.startswith(block_end, i):
                in_block_comment = False
                i += len(block_end)
            else:
                # If preserving lines, keep the newline characters from the comment block.
                if preserve_lines and code_string[i] == '\n':
                    result.append('\n')
                i += 1
            continue # Move to the next character
        
        # --- State: Inside a Line Comment ---
        if in_line_comment:
            if code_string[i] == '\n':
                in_line_comment = False
                # We always keep the newline after a line comment to preserve the line break.
                # If preserve_lines is False, the preceding text on the line was skipped,
                # effectively deleting the comment content.
                result.append('\n')
                i += 1
            else:
                i += 1
            continue # Move to the next character

        # --- State: Inside a String Literal ---
        if in_string:
            result.append(code_string[i])
            if code_string[i] == '\\': # Handle escaped characters like \"
                if i + 1 < len(code_string):
                    result.append(code_string[i+1])
                    i += 2
                else:
                    i += 1
            elif code_string[i] == '"':
                in_string = False
                i += 1
            else:
                i += 1
            continue # Move to the next character

        # --- State: Inside a Character Literal ---
        if in_char:
            result.append(code_string[i])
            if code_string[i] == '\\': # Handle escaped characters like \'
                if i + 1 < len(code_string):
                    result.append(code_string[i+1])
                    i += 2
                else:
                    i += 1
            elif code_string[i] == "'":
                in_char = False
                i += 1
            else:
                i += 1
            continue # Move to the next character

        # --- Default State: Checking for transitions ---
        # If not in any special state, check if we need to enter one.
        if block_start and code_string.startswith(block_start, i):
            in_block_comment = True
            i += len(block_start)
        elif line_start and code_string.startswith(line_start, i):
            in_line_comment = True
            i += len(line_start)
        elif code_string[i] == '"':
            in_string = True
            result.append(code_string[i])
            i += 1
        elif code_string[i] == "'":
            in_char = True
            result.append(code_string[i])
            i += 1
        else:
            # If no state change, it's a regular character to keep.
            result.append(code_string[i])
            i += 1
            
    return "".join(result)

# --- GUI Functions ---
def setup_dpg():
    dpg.create_context()
    dpg.create_viewport(title='Comment Destroyer', width=700, height=550, small_icon="icon.ico", large_icon="icon.ico")
    dpg.setup_dearpygui()

def create_main_window():
    with dpg.window(tag="Primary Window"):
        dpg.add_text("1. Select files to process using the button below.")
        dpg.add_button(label="Open Native File Browser", callback=open_native_file_dialog)
        dpg.add_separator()
        dpg.add_text("Selected Files:")
        dpg.add_listbox(tag="file_list", width=-1, num_items=5)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(label="Strip & Save As...", tag="strip_button", callback=lambda: show_confirmation_dialog(overwrite=False))
            dpg.add_button(label="Strip & Overwrite", tag="overwrite_button", callback=lambda: show_confirmation_dialog(overwrite=True))
            dpg.add_spacer()
            dpg.add_button(label="Clear Selection", tag="clear_button", callback=clear_selection_callback)
        dpg.add_separator()
        dpg.add_text("Status Log:")
        dpg.add_input_text(tag="status_log", multiline=True, width=-1, height=200, default_value="Welcome! Select files to begin.", readonly=True)

    with dpg.window(label="Confirm Action", modal=True, show=False, id="confirmation_modal", no_close=True, no_title_bar=True, pos=[200, 200]):
        dpg.add_text("Default Text", tag="confirmation_text")
        dpg.add_separator()
        dpg.add_text("Stripping Options:")
        dpg.add_checkbox(label="Preserve blank lines (keeps line numbers)", tag="preserve_lines_checkbox", default_value=False)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(label="Confirm", width=75, tag="confirm_button_action")
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("confirmation_modal", show=False))
    update_button_states()

def log_message(message):
    current_log = dpg.get_value("status_log")
    dpg.set_value("status_log", f"{current_log}\n{message}")

def show_confirmation_dialog(overwrite: bool):
    count = len(selected_files)
    if count == 0: return
    
    dpg.set_value("preserve_lines_checkbox", False)

    if overwrite:
        msg = f"[DANGER] This will PERMANENTLY overwrite {count} original file(s).\n\nThis action CANNOT be undone. Proceed?"
        callback = lambda: process_files_callback(overwrite=True)
    else:
        msg = f"This will create {count} new '.stripped' file(s).\n\nAre you sure you want to proceed?"
        callback = lambda: process_files_callback(overwrite=False)
    
    dpg.set_value("confirmation_text", msg)
    dpg.configure_item("confirm_button_action", callback=callback)
    dpg.configure_item("confirmation_modal", show=True)

def open_native_file_dialog():
    global selected_files
    root = tk.Tk()
    root.withdraw()
    
    file_types = [("All Supported Files", " ".join(LANGUAGE_STYLE_MAP.keys()))]
    file_types.append(("All files", "*.*"))

    filepaths = filedialog.askopenfilenames(title="Select files to strip", filetypes=file_types)
    root.destroy()
    if filepaths:
        for file_path in filepaths:
            if file_path not in selected_files:
                selected_files.append(file_path)
        update_file_list_display()
        update_button_states()

def update_file_list_display():
    basenames = [os.path.basename(p) for p in selected_files]
    dpg.configure_item("file_list", items=basenames)

def clear_selection_callback():
    global selected_files
    selected_files.clear()
    update_file_list_display()
    update_button_states()
    log_message("Selection cleared.")

def update_button_states():
    enable = bool(selected_files)
    dpg.configure_item("strip_button", enabled=enable)
    dpg.configure_item("overwrite_button", enabled=enable)
    dpg.configure_item("clear_button", enabled=enable)

def process_files_callback(overwrite: bool):
    preserve_lines_choice = dpg.get_value("preserve_lines_checkbox")
    
    dpg.configure_item("confirmation_modal", show=False)
    global selected_files
    if not selected_files:
        log_message("ERROR: No files selected to process.")
        return
        
    log_message("\n--- Starting Batch Process ---")
    log_message(f"Option: Preserve blank lines = {preserve_lines_choice}")
    processed_count = 0
    
    for file_path in selected_files:
        style = get_language_style(file_path)
        if not style:
            log_message(f"Skipping: {os.path.basename(file_path)} (Unknown language)")
            continue
        log_message(f"Processing '{os.path.basename(file_path)}'...")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_code = f.read()
            
            original_code = original_code.replace('\u00a0', ' ')

            stripped_code = strip_comments_by_style(original_code, style, preserve_lines_choice)
            
            if overwrite:
                new_filename = file_path
            else:
                path_obj = Path(file_path)
                new_filename = path_obj.with_name(f"{path_obj.stem}.stripped{path_obj.suffix}")
            with open(new_filename, 'w', encoding='utf-8') as f:
                f.write(stripped_code)
            action = "Overwritten" if overwrite else "Saved"
            log_message(f"  -> {action}: {os.path.basename(new_filename)}")
            processed_count += 1
        except Exception as e:
            log_message(f"  -> FAILED: {os.path.basename(file_path)} - {e}")
    log_message(f"--- Batch Complete. Processed {processed_count}/{len(selected_files)} files. ---")
    clear_selection_callback()

def run_app():
    setup_dpg()
    create_main_window()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    run_app()
