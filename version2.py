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
    for path in paths:
        normalized_path = os.path.normpath(path)
        add_path_to_tree(tree, normalized_path)
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

    return sorted(source_dirs)

def is_path_in_tree(path, tree):
    parts = path.split(os.sep)
    current_level = tree
    found_first_node = False
    root_key = list(tree.keys())[0]
    for part in parts:
        if not found_first_node:
            print(part)
            print(root_key)
            if part == root_key:
                found_first_node = True
            else:
                continue
        else:
            if part in current_level:
                current_level = current_level[part]
            else:
                return False
    if found_first_node == False:
        return False
    return True
    
def main(root_path):
    with open('compile_commands.json', 'r') as f:
        compile_commands = json.load(f)
    
    source_dirs = extract_source_dirs(compile_commands)
    tree = build_tree(source_dirs)
    filtered_tree = filt_tree(tree)
    print("Filtered Directory Tree:")
    print_tree(filtered_tree)

    # 打印filtered_tree的root节点的相对路径
    root_key = list(filtered_tree.keys())[0]
    print(f"Root node relative path: {root_path}")

    # 初始化exclude_fold集合
    exclude_fold = set()

    os.chdir(root_path)
    # 轮询root文件夹下面的每一个文件夹和子文件夹
    for root, dirs, files in os.walk('.'):
        # 检查当前root是否在filtered_tree中
        if not is_path_in_tree(root, filtered_tree):
            exclude_fold.add(root)
            dirs[:] = []  # 不往下轮询子文件夹
            continue
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not is_path_in_tree(dir_path, filtered_tree):
                exclude_fold.add(dir_path)

    print("Excluded Folders:")
    print(exclude_fold)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some paths.')
    parser.add_argument('root_path', type=str, help='The root path to start from')
    args = parser.parse_args()
    main(args.root_path)
