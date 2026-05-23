import json
from pathlib import Path

# Configurable exclusion list
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "Backup_history", ".ipynb_checkpoints"}

def extract_description(file_path: Path) -> str:
    """
    Extract first comment or docstring (multi-line supported).
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            # Single-line comment
            if stripped.startswith("#"):
                return stripped.lstrip("# ").strip()

            # Multi-line docstring
            if stripped.startswith(('"""', "'''")):
                quote_type = '"""' if stripped.startswith('"""') else "'''"
                doc = stripped.strip(quote_type).strip()
                
                # If the docstring is closed on the same line
                if stripped.count(quote_type) == 2:
                    return doc
                
                # Else, collect next lines until closing quotes found
                for next_line in lines[i + 1:]:
                    next_stripped = next_line.strip()
                    if quote_type in next_stripped:
                        doc += " " + next_stripped.replace(quote_type, "").strip()
                        return doc.strip()
                    doc += " " + next_stripped
                return doc.strip()
            
            # If we hit code before a comment/docstring, stop looking
            break

        return ""
    except Exception as e:
        return f"Error reading file: {e}"

def scan_project(root_dir: Path) -> dict:
    structure = {}
    print(f"\n🔍 Scanning: {root_dir.resolve()}\n")

    for path in root_dir.rglob("*"):
        # Skip unwanted directories by checking if any EXCLUDE_DIRS is in the path parts
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        if path.is_file():
            # Get path relative to the root
            rel_folder = str(path.parent.relative_to(root_dir))
            if rel_folder == ".":
                rel_folder = "root"

            structure.setdefault(rel_folder, [])

            file_info = {
                "file_name": path.name,
                "description": ""
            }

            if path.suffix == ".py":
                file_info["description"] = extract_description(path)

            structure[rel_folder].append(file_info)

    return structure

def print_structure(structure: dict):
    total_files = 0
    for folder in sorted(structure.keys()):
        print(f"\n📁 {folder}/")
        files = structure[folder]
        
        for f in sorted(files, key=lambda x: x["file_name"]):
            total_files += 1
            print(f"  ├── {f['file_name']}")
            if f["description"]:
                print(f"      → {f['description']}")

    print(f"\n📊 Total files scanned: {total_files}")

def save_json(structure: dict, root_dir: Path):
    output = root_dir / "project_structure.json"
    with output.open("w", encoding="utf-8") as f:
        json.dump(structure, f, indent=4)
    print(f"\n✅ JSON saved: {output.name}")

if __name__ == "__main__":
    # DYNAMIC PATH: This targets the directory where THIS script is located
    project_path = Path(__file__).parent.absolute()

    if not project_path.exists():
        print(f"⚠️ Path does not exist: {project_path}")
    else:
        structure = scan_project(project_path)

        if not structure:
            print("\n⚠️ No files found. Check your EXCLUDE_DIRS or file permissions.")
        else:
            print_structure(structure)
            save_json(structure, project_path)