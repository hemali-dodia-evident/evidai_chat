with open("requirements_old.txt", "r") as f:
    lines = f.readlines()

cleaned_lines = sorted(set(lines))  # Remove duplicates and sort

with open("requirements_cleaned.txt", "w") as f:
    f.writelines(cleaned_lines)

print("Cleaned requirements saved to requirements_cleaned.txt")
