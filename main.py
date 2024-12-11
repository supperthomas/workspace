import json
import os

def extract_source_dirs(compile_commands):
    source_dirs = set()

    for entry in compile_commands:
        # 获取文件路径
        file_path = entry['file']

        # 确认是 .c 文件
        if file_path.endswith('.c'):
            # 获取文件所在目录
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

def generate_code_workspace_file(source_dirs, workspace_name='project_workspace'):
    # 获取当前工作目录以计算相对路径
    current_working_directory = os.getcwd()

    # 将所有源目录转换为相对路径
    relative_dirs = []
    for dir_path in source_dirs:
        try:
            rel_path = os.path.relpath(dir_path, start=current_working_directory)
            if rel_path.startswith(('.', '..')):
                relative_dirs.append(rel_path)
        except ValueError:
            # 忽略不同驱动器上的路径
            continue
            
    workspace_data = {
        "folders": [{"path": dir_path} for dir_path in relative_dirs],
        "settings": {"clangd.arguments": [
                "--compile-commands-dir=.",
                "--header-insertion=never"
            ]}
    }
    
    with open(f'{workspace_name}.code-workspace', 'w') as f:
        json.dump(workspace_data, f, indent=4)

def main():
    # 读取 compile_commands.json
    with open('compile_commands.json', 'r') as f:
        compile_commands = json.load(f)
    
    # 提取源文件目录
    source_dirs = extract_source_dirs(compile_commands)
    
    # 生成和保存工作空间文件
    generate_code_workspace_file(source_dirs)

if __name__ == '__main__':
    main()
