# commentdestroyer_cli.py
import argparse
import os
from pathlib import Path

# --- Configuration: All Supported Languages ---
# This dictionary now maps file extensions to a 'style' for our internal stripper.
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

# --- Core Stripping Logic  ---
def get_language_style(file_path: str) -> str | None:
    """Determines the language comment style for a file based on its extension."""
    file_ext = Path(file_path).suffix.lower()
    return LANGUAGE_STYLE_MAP.get(file_ext)

def strip_comments_by_style(code_string: str, style: str, preserve_lines: bool) -> str:
    """A robust, dependency-free state machine to strip comments from source code."""
    if style == 'c':
        line_start, block_start, block_end = '//', '/*', '*/'
    elif style == 'python':
        line_start, block_start, block_end = '#', None, None
    elif style == 'html':
        line_start, block_start, block_end = None, '<!--', '-->'
    else:
        return code_string

    result = []
    in_string, in_char, in_block_comment, in_line_comment = False, False, False, False
    i = 0
    while i < len(code_string):
        if in_block_comment:
            if code_string.startswith(block_end, i):
                in_block_comment = False
                i += len(block_end)
            else:
                if preserve_lines and code_string[i] == '\n':
                    result.append('\n')
                i += 1
            continue
        
        if in_line_comment:
            if code_string[i] == '\n':
                in_line_comment = False
                result.append('\n')
                i += 1
            else:
                i += 1
            continue

        if in_string:
            result.append(code_string[i])
            if code_string[i] == '\\':
                if i + 1 < len(code_string): result.append(code_string[i+1]); i += 1
            elif code_string[i] == '"': in_string = False
            i += 1
            continue

        if in_char:
            result.append(code_string[i])
            if code_string[i] == '\\':
                if i + 1 < len(code_string): result.append(code_string[i+1]); i += 1
            elif code_string[i] == "'": in_char = False
            i += 1
            continue

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
            result.append(code_string[i])
            i += 1
    return "".join(result)

# --- CLI Main Function ---
def process_file(file_path_str: str, overwrite: bool, preserve_lines: bool):
    """Processes a single file based on the provided command-line options."""
    path_obj = Path(file_path_str)
    
    if not path_obj.is_file():
        print(f"Error: File not found at '{file_path_str}'")
        return

    style = get_language_style(str(path_obj))
    if not style:
        print(f"Skipping: {path_obj.name} (Unknown language for extension '{path_obj.suffix}')")
        return

    print(f"Processing '{path_obj.name}'...")
    try:
        with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
            original_code = f.read()
        
        # Sanitize non-breaking spaces
        original_code = original_code.replace('\u00a0', ' ')
        
        stripped_code = strip_comments_by_style(original_code, style, preserve_lines)

        if overwrite:
            new_filename = path_obj
        else:
            new_filename = path_obj.with_name(f"{path_obj.stem}.stripped{path_obj.suffix}")
        
        with open(new_filename, 'w', encoding='utf-8') as f:
            f.write(stripped_code)
        
        action = "Overwritten" if overwrite else "Saved to"
        print(f"  -> Success! {action}: {new_filename.name}")

    except Exception as e:
        print(f"  -> FAILED: An unexpected error occurred: {e}")

def main():
    """Parses command-line arguments and initiates file processing."""
    parser = argparse.ArgumentParser(
        description="A powerful command-line tool to strip comments from various source code files.",
        epilog="Example: python commentdestroyer_cli.py file1.cpp file2.py --overwrite"
    )
    
    parser.add_argument(
        'files', 
        nargs='+', # Requires at least one file path
        help="One or more paths to the source code files to be processed."
    )
    
    parser.add_argument(
        '-o', '--overwrite',
        action='store_true',
        help="Overwrite the original files instead of creating new '.stripped' files."
    )
    
    parser.add_argument(
        '-p', '--preserve-lines',
        action='store_true',
        help="Preserve blank lines where comments were, which keeps original line numbers."
    )

    args = parser.parse_args()

    print("--- Comment Destroyer (CLI) ---")
    if args.overwrite:
        print("Mode: OVERWRITE (Original files will be modified)")
        # Add a confirmation step for safety when overwriting
        confirm = input("Are you sure you want to proceed? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    else:
        print("Mode: SAVE AS (New '.stripped' files will be created)")

    for file_path in args.files:
        process_file(file_path, args.overwrite, args.preserve_lines)
    
    print("--- Batch Complete ---")

if __name__ == "__main__":
    main()

