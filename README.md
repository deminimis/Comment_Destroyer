# Comment Destroyer

**A dependency-free utility to strip comments from source code files, available in both a user-friendly GUI and a command-line tool.**

Built on: [Comment-Parser](https://github.com/jeanralphaviles/comment_parser)

Have you ever needed to prepare a source code file for distribution, analysis, or simply to get a clean line count without comments? Comment Destroyer provides a simple, reliable solution to remove all comment types from a wide range of programming languages, ensuring that what's inside strings or other syntax isn't accidentally broken.

---

## 1. Graphical User Interface (GUI)

For users who prefer a visual interface, the `commentdestroyer.py` application offers a simple and safe workflow.

![GUI Screenshot](https://github.com/deminimis/Comment_Destroyer/blob/main/assets/commentdestroyerscreenshot1.png)

* **Easy File Selection:** Use the native Windows/macOS/Linux file browser to select one or multiple files at once.
* **Multi-Language Support:** Mix and match different file types (e.g., `.py`, `.cpp`, `.js`) in a single batch. The tool automatically detects the language and applies the correct stripping rules.
* **Safe Saving Options:**
    * **Strip & Save As...:** The default, safe option that creates a new file with `.stripped` appended to the name, leaving your original file untouched.
    * **Strip & Overwrite:** A powerful option to permanently modify the original file in place.
* **Interactive Confirmation:** Before any files are modified, a confirmation dialog appears, giving you a final chance to review your choices.
* **Stripping Control:** A checkbox in the confirmation dialog allows you to choose whether to **Preserve blank lines**, which is useful for maintaining line numbers for debugging or analysis.

## 2. Command-Line Interface (CLI)

* **Clear Arguments:** Use simple flags to control the output.
    * `files`: A list of one or more files to process.
    * `-o` or `--overwrite`: Overwrites the original files. Includes a safety confirmation prompt.
    * `-p` or `--preserve-lines`: Keeps blank lines where comments were, preserving line numbers.
* **Built-in Help:** Run with `--help` to see all options and examples.

```bash
# Example: Create new stripped files
python commentdestroyer_cli.py my_code.cpp my_script.py

# Example: Overwrite original files and preserve line numbers
python commentdestroyer_cli.py main.java --overwrite --preserve-lines
```

## Technical Details
This tool was designed for robustness and portability, avoiding the pitfalls of simpler regex-based solutions.

### Core Stripping Engine
The core logic is a dependency-free state machine that parses code character by character. It explicitly tracks its state to differentiate between being inside a multi-line comment, a single-line comment, a string literal ("..."), or a character literal ('...'). This approach correctly handles complex edge cases, such as comment-like syntax appearing within a string, which often cause naive regex strippers to fail.

### Language Extensibility
Language support is not hardcoded. A central LANGUAGE_STYLE_MAP dictionary categorizes file extensions into one of three primary comment "styles":

C-Style ('c'): Supports // for single-line and /* ... */ for block comments.

Python-Style ('python'): Supports # for single-line comments.

HTML-Style ('html'): Supports <!-- ... --> for block comments.


## Supported Languages
The tool currently supports the following comment styles and associated file extensions:

C-Style: .c, .h, .cpp, .hpp, .cc, .java, .js, .mjs, .jsx, .ts, .tsx, .go, .rs, .css

Python-Style: .py, .pyw, .rb, .sh

HTML-Style: .html, .htm, .xml


