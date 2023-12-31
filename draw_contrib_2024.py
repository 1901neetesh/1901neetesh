import os
import subprocess
from datetime import datetime, timedelta

FONT = {
    " ": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "N": [
        "10001",
        "11001",
        "10101",
        "10011",
        "10001",
        "10001",
        "10001",
    ],
    "S": [
        "01111",
        "10000",
        "10000",
        "01111",
        "00001",
        "00001",
        "11110",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "U": [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
}


def run_command(command, env=None):
    subprocess.run(command, shell=True, check=True, env=env)


def build_text_bitmap(text):
    rows = ["" for _ in range(7)]
    for index, char in enumerate(text):
        if char not in FONT:
            raise ValueError(f"Unsupported character: {char}")
        glyph = FONT[char]
        for row_index in range(7):
            rows[row_index] += glyph[row_index]
        if index != len(text) - 1:
            for row_index in range(7):
                rows[row_index] += "0"
    return rows


def build_repeated_bitmap(text, total_columns, spacing=2):
    base = build_text_bitmap(text)
    rows = ["" for _ in range(7)]
    separator = "0" * spacing
    while len(rows[0]) < total_columns:
        for row_index in range(7):
            rows[row_index] += base[row_index]
            rows[row_index] += separator
    for row_index in range(7):
        rows[row_index] = rows[row_index][:total_columns]
    return rows


def first_sunday_on_or_before(value):
    days_to_sunday = (value.weekday() + 1) % 7
    return value - timedelta(days=days_to_sunday)


def main():
    year = int(os.environ.get("YEAR", "2024"))
    text = os.environ.get("TEXT", "NEETESH").upper()
    repeat = os.environ.get("REPEAT", "1") != "0"

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    week_zero = first_sunday_on_or_before(start_date)
    total_columns = ((end_date - week_zero).days // 7) + 1

    if repeat:
        bitmap = build_repeated_bitmap(text, total_columns)
        start_col = 0
    else:
        bitmap = build_text_bitmap(text)
        text_width = len(bitmap[0])
        start_col = max(0, (total_columns - text_width) // 2)

    selected_dates = []
    for row_index in range(7):
        for col_offset, value in enumerate(bitmap[row_index]):
            if value != "1":
                continue
            week_index = start_col + col_offset
            date_value = week_zero + timedelta(days=week_index * 7 + row_index)
            if date_value < start_date or date_value > end_date:
                continue
            selected_dates.append(date_value)

    selected_dates = sorted(set(selected_dates))

    # Preview logic
    print("Preview of the generated graph (transposed):")
    preview_grid = [['.' for _ in range(total_columns)] for _ in range(7)]
    for date_value in selected_dates:
        # Calculate reverse mapping
        delta = (date_value - week_zero).days
        c_week = delta // 7
        c_day = delta % 7
        if 0 <= c_week < total_columns and 0 <= c_day < 7:
            preview_grid[c_day][c_week] = '#'

    for row in preview_grid:
        print("".join(row))

    env = os.environ.copy()
    for date_value in selected_dates:
        commit_date = date_value.replace(hour=12, minute=0, second=0)
        git_date = commit_date.strftime("%Y-%m-%d %H:%M:%S")
        env["GIT_AUTHOR_DATE"] = git_date
        env["GIT_COMMITTER_DATE"] = git_date
        for _ in range(50):
            run_command(f'git commit --allow-empty -q -m "Draw {text} on {git_date}"', env=env)

    print(f"Created {len(selected_dates)} commits for {text} in {year}.")


if __name__ == "__main__":
    main()
