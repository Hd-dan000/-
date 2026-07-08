import os

# 文件内容分类扩展名映射
CATEGORY_EXTENSIONS = {
    'document': {'.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls', '.ppt', '.pptx', '.csv', '.md'},
    'ui': {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'},
    'code': {'.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.vue', '.jsx',
             '.ts', '.tsx', '.json', '.xml', '.sql', '.php', '.go', '.rb', '.rs', '.cs',
             '.swift', '.kt', '.m', '.mm', '.sh', '.bat', '.ps1', '.yaml', '.yml', '.toml',
             '.ini', '.properties'},
}


def categorize_files(files):
    """
    按扩展名将文件分类。
    files: [{filename, path, size?}, ...]
    返回: {'document': [...], 'ui': [...], 'code': [...], 'unknown': [...]}
    """
    result = {'document': [], 'ui': [], 'code': [], 'unknown': []}
    for f in files:
        ext = os.path.splitext(f.get('filename', ''))[1].lower()
        found = False
        for cat, exts in CATEGORY_EXTENSIONS.items():
            if ext in exts:
                result[cat].append(f)
                found = True
                break
        if not found:
            result['unknown'].append(f)
    return result


def parse_txt_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read()
        except:
            return f"[无法解析文件: {os.path.basename(filepath)}]"
    except Exception:
        return f"[无法读取文件: {os.path.basename(filepath)}]"

def parse_csv_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')[:50]
        return '\n'.join(lines)
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                content = f.read()
            lines = content.split('\n')[:50]
            return '\n'.join(lines)
        except:
            return f"[无法解析CSV文件: {os.path.basename(filepath)}]"
    except Exception:
        return f"[无法读取CSV文件: {os.path.basename(filepath)}]"

def parse_files_to_text(filepaths):
    results = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            continue
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.txt':
            text = parse_txt_file(filepath)
            results.append(f"=== {os.path.basename(filepath)} ===\n{text}")
        elif ext == '.csv':
            text = parse_csv_file(filepath)
            results.append(f"=== {os.path.basename(filepath)} ===\n{text}")
        elif ext in CATEGORY_EXTENSIONS['code'] or ext in {'.md'}:
            text = parse_txt_file(filepath)
            results.append(f"=== {os.path.basename(filepath)} ===\n{text[:8000]}")
        else:
            results.append(f"【{os.path.basename(filepath)}】(非文本格式，无法解析内容)")
    return '\n\n'.join(results)