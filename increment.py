import re

# File path to download.py
file_path = "download.py"

# Increment values
increment_value = 500000

# Read the file contents
with open(file_path, "r") as file:
    lines = file.readlines()

# Modify version_code_start and version_code_end in place
with open(file_path, "w") as file:
    for line in lines:
        # Look for version_code_start and version_code_end assignments
        if match := re.match(r"(version_code_start\s*=\s*)(\d+)", line):
            current_value = int(match.group(2))
            new_value = current_value + increment_value
            line = f"{match.group(1)}{new_value}\n"
        elif match := re.match(r"(version_code_end\s*=\s*)(\d+)", line):
            current_value = int(match.group(2))
            new_value = current_value + increment_value
            line = f"{match.group(1)}{new_value}\n"

        # Write each modified (or unmodified) line back to the file
        file.write(line)

print("Incremented version_code_start and version_code_end by 500,000 in download.py.")