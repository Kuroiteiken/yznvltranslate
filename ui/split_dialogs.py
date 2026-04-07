import ast
import os
import re

TARGET_DIR = "ui"

with open("dialogs.py", "r", encoding="utf-8") as f:
    source = f.read()

# Top level imports + helper functions are before the first class (line 51)
tree = ast.parse(source)
first_class_idx = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.ClassDef))
first_class_node = tree.body[first_class_idx]
first_class_line = first_class_node.lineno

lines = source.splitlines()
header_lines = lines[:first_class_line - 1]
header_text = "\n".join(header_lines) + "\n\n"

# Helper to covert CamelCase to snake_case
def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

created_files = []

for node in classes:
    class_name = node.name
    snake_name = camel_to_snake(class_name)
    file_name = f"{snake_name}.py"
    file_path = os.path.join(TARGET_DIR, file_name)
    
    start_line = node.lineno - 1
    end_line = node.end_lineno
    # Include decorator if any
    if node.decorator_list:
        start_line = node.decorator_list[0].lineno - 1
        
    class_text = "\n".join(lines[start_line:end_line]) + "\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header_text)
        f.write(class_text)
        
    created_files.append((class_name, snake_name))
    print(f"Created {file_path}")

# Rewrite dialogs.py to re-export
new_dialogs = header_text + "\n# --- Re-exports (SRP Update) ---\n"
for c_name, snake in created_files:
    new_dialogs += f"from ui.{snake} import {c_name}\n"

with open("dialogs.py", "w", encoding="utf-8") as f:
    f.write(new_dialogs)

print("dialogs.py updated with re-exports.")
