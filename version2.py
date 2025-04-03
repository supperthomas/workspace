import os
import json
import argparse

def find_first_node_with_two_children(tree):
    for key, subtree in tree.items():
        if len(subtree) >= 2:
            return key, subtree
        result = find_first_node_with_two_children(subtree)
        if result:
            return result
    return None, None


def filt_tree(tree):
    key, subtree = find_first_node_with_two_children(tree)
    if key:
        return {key: subtree}
    return {}


def add_path_to_tree(tree, path):
    parts = path.split(os.sep)
    current_level = tree
    for part in parts:
        if part not in current_level:
            current_level[part] = {}
        current_level = current_level[part]


def build_tree(paths):
    tree = {}
    current_working_directory = os.getcwd()
    current_folder_name = os.path.basename(current_working_directory)
    #过滤异常和不存在的路径
    relative_dirs = []
    for path in paths:
        normalized_path = os.path.normpath(path)
        try:
            rel_path = os.path.relpath(normalized_path, start=current_working_directory)
            add_path_to_tree(tree, normalized_path)
        except ValueError:
            # print(f"Remove unexcpect dir:{path}")
            pass

    return tree

def print_tree(tree, indent=''):
    for key, subtree in sorted(tree.items()):
        print(indent + key)
        print_tree(subtree, indent + '  ')


def extract_source_dirs(compile_commands):
    source_dirs = set()

    for entry in compile_commands:
        file_path = os.path.abspath(entry['file'])

        if file_path.endswith('.c'):
            dir_path = os.path.dirname(file_path)
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
    #print(f"Source Directories: {source_dirs}")
    return sorted(source_dirs)


def is_path_in_tree(path, tree):
    parts = path.split(os.sep)
    current_level = tree
    found_first_node = False
    root_key = list(tree.keys())[0]
    #print(root_key)
    #print(path)
    index_start = parts.index(root_key)
    length = len(parts)
    try:
        for i in range(index_start, length):
            current_level = current_level[parts[i]]
        return True
    except KeyError:
        return False


def generate_code_workspace_file(source_dirs,command_json_path):
    current_working_directory = os.getcwd()
    current_folder_name = os.path.basename(current_working_directory)
    
    relative_dirs = []
    for dir_path in source_dirs:
        try:
            rel_path = os.path.relpath(dir_path, root_path)
            relative_dirs.append(rel_path)
        except ValueError:
            continue

    root_rel_path = os.path.relpath(root_path, current_working_directory)
    workspace_data = {
        "folders": [
            {
                "path": f"{root_rel_path}"
            }
        ],
        "settings": {
            "clangd.arguments": [
                f"--compile-commands-dir={command_json_path}",
                "--header-insertion=never"
            ],
            "files.exclude": {dir.replace('\\','/'): True for dir in sorted(relative_dirs)}
        }
    }
    workspace_filename = f'{current_folder_name}.code-workspace'
    
    # print(workspace_data)
    with open(workspace_filename, 'w') as f:
        json.dump(workspace_data, f, indent=4)

    os.chdir(root_path)
    current_working_directory = os.getcwd()

    root_rel_path = os.path.relpath(root_path, current_working_directory)
    workspace_data = {
        "folders": [
            {
                "path": f"{root_rel_path}"
            }
        ],
        "settings": {
            "clangd.arguments": [
                f"--compile-commands-dir={command_json_path}",
                "--header-insertion=never"
            ],
            "files.exclude": {dir.replace('\\','/'): True for dir in sorted(relative_dirs)}
        }
    }
    workspace_filename = f'{current_folder_name}.code-workspace'
    # print(workspace_data)
    with open(workspace_filename, 'w') as f:
        json.dump(workspace_data, f, indent=4)

    print(f'Workspace file {workspace_filename} created.')


def main(root_path,command_json_path):
    with open(root_path+'\\'+command_json_path+ 'compile_commands.json', 'r') as f:
        compile_commands = json.load(f)

    source_dirs = extract_source_dirs(compile_commands)
    tree = build_tree(source_dirs)
    #print_tree(tree)
    filtered_tree = filt_tree(tree)
    #print("Filtered Directory Tree:")
    #print_tree(filtered_tree)

    # 打印filtered_tree的root节点的相对路径
    root_key = list(filtered_tree.keys())[0]
    #print(f"Root node relative path: {root_key}")

    # 初始化exclude_fold集合
    exclude_fold = set()

    # os.chdir(root_path)
    # 轮询root文件夹下面的每一个文件夹和子文件夹
    for root, dirs, files in os.walk(root_path):
        # 检查当前root是否在filtered_tree中
        if not is_path_in_tree(root, filtered_tree):
            exclude_fold.add(root)
            dirs[:] = []  # 不往下轮询子文件夹
            continue
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not is_path_in_tree(dir_path, filtered_tree):
                exclude_fold.add(dir_path)

    #print("Excluded Folders:")
    #print(exclude_fold)
    generate_code_workspace_file(exclude_fold,command_json_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='python command_to_workspace.py compile_commands.json ../../../../     ../../../ is rel root path')
    parser.add_argument('command_json', type=str, help='The compile_commands.json to start from')
    parser.add_argument('root_path', type=str, help='The root path to start from')


    args = parser.parse_args()
    # 检查参数是否足够
    if len(vars(args)) < 2:
        parser.print_help()
    else:
        root_path = args.root_path
        command_json = args.command_json
        root_path_abs = os.path.abspath(root_path)
        #print(root_path_abs)
        command_json_path = os.path.relpath(command_json, start=root_path_abs)
        command_json_dir = os.path.join(os.path.dirname(command_json_path), '')
        #print(command_json_dir)
        main(root_path_abs,command_json_dir)

