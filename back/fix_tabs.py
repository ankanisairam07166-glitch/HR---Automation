import sys

# Read the backend.py file
with open('backend.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the specific problematic lines around 2759
# These lines are inside the upload_recording function
for i in range(len(lines)):
    # Check lines around 2759 (give some buffer)
    if 2755 <= i <= 2765:
        # Replace any tabs with 4 spaces
        original = lines[i]
        fixed = lines[i].replace('\t', '    ')
        if original != fixed:
            print(f"Fixed line {i+1}: {repr(original.strip())} -> {repr(fixed.strip())}")
            lines[i] = fixed

# Write the fixed content back
with open('backend.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ Fixed tabs in backend.py around line 2759")
print("Try running 'python backend.py' again")