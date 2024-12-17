def print_colored(message, color=None):
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

    # Check if the color is valid and fetch its ANSI code
    color_code = color_map.get(color)

    if color_code:
        # Print with ANSI escape codes for color
        print(f"\033[{color_code}m{message}\033[0m")
    else:
        # Fallback: Print the message without color
        print(message)
