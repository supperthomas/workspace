import json
import os
import re

def extract_source_dirs(compile_commands):
    source_dirs = set()

    for entry in compile_commands:
        file_path = entry['file']

        if file_path.endswith('.c'):
            dir_path = os.path.dirname(os.path.abspath(file_path))
            source_dirs.add(dir_path)

            command = entry.get('command') or entry.get('arguments')
            
            if isinstance(command, str):
                parts = command.split()
            else:
                parts = command
                
            for i, part in enumerate(parts):
                if part.startswith('-I'):
                    include_dir = part[2:] if len(part) > 2 else parts[i + 1]
                    source_dirs.add(os.path.abspath(include_dir))
                elif part.startswith('/I'):
                    include_dir = part[2:] if len(part) > 2 else parts[i + 1]
                    source_dirs.add(os.path.abspath(include_dir))

    return sorted(source_dirs)

def consolidate_directories(dirs):
    consolidated = set()
    dirs = sorted(dirs)

    pattern = re.compile(r"^(.*?\\[a-zA-Z][^\\]*)")

    for dir_path in dirs:
        if dir_path == '.':
            consolidated.add('.')
        elif dir_path.startswith('..'):
            match = pattern.match(dir_path)
            if match:
                reduced_dir = match.group(1)
                #print(reduced_dir)
                consolidated.add(reduced_dir)

    return sorted(consolidated)

def generate_code_workspace_file(source_dirs):

    current_working_directory = os.getcwd()
    current_folder_name = os.path.basename(current_working_directory)
    
    relative_dirs = []
    for dir_path in source_dirs:
        try:
            rel_path = os.path.relpath(dir_path, start=current_working_directory)
            relative_dirs.append(rel_path)
        except ValueError:
            continue
    
    relative_dirs.sort(key=lambda x: (x != '.', x))
    source_dirs = consolidate_directories(relative_dirs)
    
    workspace_data = {
        "folders": [{"path": dir_path} for dir_path in source_dirs],
        "settings": {"clangd.arguments": [
                "--compile-commands-dir=.",
                "--header-insertion=never"
            ]}
    }

    workspace_filename = f'{current_folder_name}.code-workspace'
    with open(workspace_filename, 'w') as f:
        json.dump(workspace_data, f, indent=4)

    print(f'Workspace file {workspace_filename} created.')

def main():
    with open('compile_commands.json', 'r') as f:
        compile_commands = json.load(f)
    
    source_dirs = extract_source_dirs(compile_commands)
    generate_code_workspace_file(source_dirs)

if __name__ == '__main__':
    main()
