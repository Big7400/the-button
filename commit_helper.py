import os

print("=== Staging all changes ===")
os.system("git add .")

commit_msg = input("Enter commit message: ").strip()
if not commit_msg:
    print("No commit message provided. Exiting.")
    exit(1)

print("=== Committing changes ===")
os.system(f'git commit -m "{commit_msg}"')

push_choice = input("Push to remote? (y/n): ").strip().lower()
if push_choice == "y":
    os.system("git push")
    print("Changes pushed to remote.")
else:
    print("Commit complete. Not pushed.")
