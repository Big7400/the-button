import os
from pathlib import Path

files_to_check = [
    "app/main.py",
    "app/models.py",
    "app/schemas.py",
    "app/database.py",
    "app/core/security.py",
    "app/core/config.py",
    "app/routers/auth.py",
    "app/routers/users.py",
    "app/routers/admin.py",
    "app/routers/trading.py",
    "app/routers/engine.py",
]

output = []
output.append("=" * 80)
output.append("COMPLETE FILE DUMP FOR CLAUDE")
output.append("=" * 80)

for filepath in files_to_check:
    output.append(f"\n{'='*80}")
    output.append(f"FILE: {filepath}")
    output.append(f"{'='*80}")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                output.append(content)
        except Exception as e:
            output.append(f"ERROR reading file: {e}")
    else:
        output.append("FILE DOES NOT EXIST")

# Write to output file
with open("current_codebase_dump.txt", "w") as f:
    f.write("\n".join(output))

print("✅ All files dumped to: current_codebase_dump.txt")
print("Now paste the contents of that file here!")
