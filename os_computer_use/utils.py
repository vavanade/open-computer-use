import os

# Mapping standard color names to ANSI color codes
color_map = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "gray": "37;2",
}

# Mapping standard color names to web colors
css_color_map = {
    "black": ("#000000", "#e3f2fd"),
    "red": ("#8B0000", "#ffebee"),
    "green": ("#006400", "#e8f5e9"),
    "yellow": ("#8B8B00", "#fff3e0"),
    "blue": ("#00008B", "#e8eaf6"),
    "magenta": ("#8B008B", "#f5f5f5"),
    "cyan": ("#008B8B", "#f5f5f5"),
    "white": ("#CCCCCC", "#f5f5f5"),
    "gray": ("#666666", "#f5f5f5"),
}

# Load the HTML template when module is imported
LOG_FILE_TEMPLATE = None
try:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "log.html")
    with open(template_path, "r") as f:
        LOG_FILE_TEMPLATE = f.read()
except Exception as e:
    print(f"Warning: Could not load log template: {e}")


# Print to the terminal in color
def print_colored(message, color=None):

    # Check if the color is valid and fetch its ANSI code
    color_code = color_map.get(color)

    if color_code:
        # Print with ANSI escape codes for color
        print(f"\033[{color_code}m{message}\033[0m")
    else:
        # Fallback: Print the message without color
        print(message)


# Write the log file in color
def write_log_file(logs, filepath):
    """Write the complete log file using the stored log entries"""
    content = ""
    for entry in logs:
        color_info = css_color_map.get(entry["color"], (entry["color"], "#f5f5f5"))
        content += f"<p style='color:{color_info[0]};background:{color_info[1]}'>{entry['text']}</p>\n"

    with open(filepath, "w") as f:
        f.write(LOG_FILE_TEMPLATE.replace("{{content}}", content))
