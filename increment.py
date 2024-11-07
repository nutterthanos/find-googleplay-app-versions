import re

# Path to download.py
file_path = "download.py"

# Increment value
increment_value = 500000

# Read the file contents
with open(file_path, "r") as file:
    lines = file.readlines()

# Initialize flags to track whether we find the variables
found_start = False
found_end = False

# Modify version_code_start and version_code_end in place
with open(file_path, "w") as file:
    for line in lines:
        # Look for version_code_start inside the main function
        if match := re.match(r"(\s*version_code_start\s*=\s*)(\d+)", line):
            current_value = int(match.group(2))
            new_value = current_value + increment_value
            line = f"{match.group(1)}{new_value}\n"
            found_start = True
            print(f"Updated version_code_start from {current_value} to {new_value}")

        # Look for version_code_end inside the main function
        elif match := re.match(r"(\s*version_code_end\s*=\s*)(\d+)", line):
            current_value = int(match.group(2))
            new_value = current_value + increment_value
            line = f"{match.group(1)}{new_value}\n"
            found_end = True
            print(f"Updated version_code_end from {current_value} to {new_value}")

        # Write each modified (or unmodified) line back to the file
        file.write(line)

# Check if both version codes were found
if not found_start or not found_end:
    print("Error: Could not find version_code_start or version_code_end in download.py.")
    if not found_start:
        print("version_code_start was not found.")
    if not found_end:
        print("version_code_end was not found.")