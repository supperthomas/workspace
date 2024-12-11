import json
import os
import re
#读取compile_commands.json 进行路径过滤
def extract_source_dirs(compile_commands):
    source_dirs = set()

    for entry in compile_commands:
        file_path = entry['file']

        if file_path.endswith('.c'):
            dir_path = os.path.dirname(os.path.abspath(file_path))
            source_dirs.add(dir_path)
            # command 或者arguments
            command = entry.get('command') or entry.get('arguments')
            
            if isinstance(command, str):
                parts = command.split()
            else:
                parts = command
            # 读取-I或者/I
            for i, part in enumerate(parts):
                if part.startswith('-I'):
                    include_dir = part[2:] if len(part) > 2 else parts[i + 1]
                    source_dirs.add(os.path.abspath(include_dir))
                elif part.startswith('/I'):
                    include_dir = part[2:] if len(part) > 2 else parts[i + 1]
                    source_dirs.add(os.path.abspath(include_dir))

    return sorted(source_dirs)
    
# 过滤路径
def consolidate_directories(dirs):
    consolidated = set()
    
    # 首先根据目录深度（反斜杠数量）排序，浅的在前面
    dirs = sorted(dirs, key=lambda x: x.count('\\'))

    # 正则表达式匹配前两级目录（如果符合）
    pattern = re.compile(r"^(.*?\\[a-zA-Z][^\\]*\\[a-zA-Z][^\\]*)")

    for dir_path in dirs:
        if dir_path == '.':
            consolidated.add('.')
        elif dir_path.startswith('..'):
            #print(dir_path)
            # 检查路径是否在现有集合中包含作为上一级目录的情况
            if any(dir_path.startswith(d + '\\') for d in consolidated):
                continue  # 如果上级目录已经在集合中，就跳过这个路径
            
            match = pattern.match(dir_path)
            if match:
                reduced_dir = match.group(1)
                # 规范化路径以确保输出一致性
                reduced_dir = os.path.normpath(reduced_dir)
                #print(reduced_dir)  # 输出调试信息
                consolidated.add(reduced_dir)

    return sorted(consolidated)
    
#产生workspace文件
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
    consolidated_dirs = consolidate_directories(relative_dirs)
    
    # 检查目录是否存在，只保留存在的目录
    existing_dirs = [dir_path for dir_path in consolidated_dirs if os.path.exists(dir_path)]
    
    # 为每个目录添加名称，使用最后两个目录名
    folders = []
    for dir_path in existing_dirs:
        if dir_path == '.':
            folders.append({"path": dir_path})
            continue
        components = dir_path.strip(os.sep).split(os.sep)
        meaningful_components = [comp for comp in components if comp and comp != '..']
        if len(meaningful_components) >= 2:
            name = '/'.join(meaningful_components[-2:])
        else:
            name = '/'.join(meaningful_components)
        
        folders.append({"path": dir_path, "name": name})

    workspace_data = {
        "folders": folders,
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
