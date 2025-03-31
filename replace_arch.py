import json
import re
import os

def replace_march_in_json(file_path):
    try:
        # 备份原始文件
        backup_path = file_path + ".bak"
        # 如果备份文件存在，先删除它
        if os.path.exists(backup_path):
            os.remove(backup_path)
            print(f"已删除旧备份文件: {backup_path}")
            
        os.rename(file_path, backup_path)
        print(f"已备份原始文件到: {backup_path}")

        # 读取备份文件
        with open(backup_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 替换内容
        def replace_march(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        # 使用正则表达式替换 " -march=**"（注意前面的空格）
                        obj[key] = re.sub(r' -march=[^ ]*', '', value)
                    elif isinstance(value, (dict, list)):
                        replace_march(value)
            elif isinstance(obj, list):
                for item in obj:
                    replace_march(item)
            return obj

        # 递归替换 JSON 中的所有内容
        data = replace_march(data)

        # 写回修改后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"已成功替换文件: {file_path}")

    except Exception as e:
        print(f"处理文件时出错: {e}")
        # 如果出错，恢复原始文件
        if os.path.exists(backup_path):
            os.rename(backup_path, file_path)
            print(f"已恢复原始文件: {file_path}")

if __name__ == "__main__":
    # 替换为你的文件路径
    file_path = "build/compile_commands.json"
    replace_march_in_json(file_path)
