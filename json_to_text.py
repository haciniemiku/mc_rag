import json
import re
import os
from pathlib import Path

# ================= 配置区域 =================
# 输入根目录
INPUT_ROOT = 'mingchao_stories_output'
# 输出根目录 (新生成的 md 文件夹)
OUTPUT_ROOT = 'md_output'


# ===========================================

def clean_html(text):
    """清理 HTML 标签和实体"""
    if not text:
        return ""
    text = text.replace('&hellip;', '...')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('<br>', '\n')
    text = text.replace('<br/>', '\n')
    clean = re.sub(r'<[^>]+>', '', text)
    lines = [line.strip() for line in clean.split('\n') if line.strip()]
    return ' '.join(lines)


def get_modules_titles(data):
    """从 modules 中提取 {标题: idx} 的有序字典"""
    if not data or 'modules' not in data:
        return {}

    titles_map = {}
    for module in data['modules']:
        title = module.get('title', 'Untitled Module')
        components = module.get('components', [])

        if isinstance(components, list) and len(components) > 0:
            idx = components[0].get('idx', '')
            if idx:
                titles_map[title] = idx
    return titles_map


def generate_markdown_script_mode(sorted_stories):
    """生成剧本模式的 Markdown 字符串"""
    if not sorted_stories:
        return ""

    md_lines = []

    for item in sorted_stories:
        chapter_title = item['title']
        story_data = item['content']

        md_lines.append(f"## {chapter_title}\n")

        raw_list = story_data.get('flow', {}).get('raw', [])

        for node in raw_list:
            option_text = node.get('title', '')
            dialogue_html = node.get('content', '')

            has_output = False

            # 1. 输出选项
            if option_text:
                clean_opt = clean_html(option_text)
                if clean_opt:
                    md_lines.append(f"> **👉 {clean_opt}**")
                    has_output = True

            # 2. 输出对话
            if dialogue_html:
                clean_dlg = clean_html(dialogue_html)
                if clean_dlg:
                    if has_output:
                        md_lines.append("")  # 选项和对话之间空一行
                    md_lines.append(clean_dlg)
                    has_output = True

            if has_output:
                md_lines.append("")  # 节点后空行

        md_lines.append("---\n")

    return "\n".join(md_lines)


def process_single_file(json_path, output_md_path):
    """处理单个 JSON 文件并保存为 MD"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取失败 {json_path}: {e}")
        return False

    # 1. 获取顺序
    order_dict = get_modules_titles(data)
    if not order_dict:
        print(f"⚠️ 未找到模块信息: {json_path}")
        return False

    # 2. 提取有序数据
    story_dict = data.get('story', {})
    sorted_stories = []

    for title, idx in order_dict.items():
        if idx in story_dict:
            sorted_stories.append({
                "title": title,
                "idx": idx,
                "content": story_dict[idx]
            })
        else:
            # 如果找不到，可以选择跳过或记录警告
            pass

    if not sorted_stories:
        print(f"⚠️ 无有效剧情数据: {json_path}")
        return False

    # 3. 生成 Markdown
    md_content = generate_markdown_script_mode(sorted_stories)

    # 4. 写入文件
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_md_path), exist_ok=True)

        with open(output_md_path, 'w', encoding='utf-8') as f:
            # 可选：在文件开头加一个大标题（使用文件夹名）
            folder_name = os.path.basename(os.path.dirname(json_path))
            f.write(f"# {folder_name}\n\n")
            f.write(md_content)

        print(f"✅ 成功: {output_md_path}")
        return True
    except Exception as e:
        print(f"❌ 写入失败 {output_md_path}: {e}")
        return False


def main():
    input_root = Path(INPUT_ROOT)
    output_root = Path(OUTPUT_ROOT)

    if not input_root.exists():
        print(f"❌ 错误：输入目录 '{INPUT_ROOT}' 不存在！")
        return

    # 创建输出根目录
    output_root.mkdir(exist_ok=True)

    print(f"🚀 开始批量处理 '{INPUT_ROOT}' 下的所有故事...\n")

    success_count = 0
    total_count = 0

    # 遍历输入目录下的一级子文件夹
    for child_dir in input_root.iterdir():
        if child_dir.is_dir():
            json_file = child_dir / 'content_structure.json'

            if json_file.exists():
                total_count += 1

                # 构建输出路径：保持相同的文件夹结构
                # 例如：input/A/content.json -> output/A/content.md
                relative_path = child_dir.relative_to(input_root)
                output_dir = output_root / relative_path
                output_file = output_dir / f"{child_dir.name}.md"  # 文件名用文件夹名，或者 content.md

                # 执行处理
                if process_single_file(str(json_file), str(output_file)):
                    success_count += 1
            else:
                print(f"⚠️ 跳过 (无 content_structure.json): {child_dir.name}")

    print("\n" + "=" * 50)
    print(f"🎉 处理完成！")
    print(f"📂 输入目录：{INPUT_ROOT}")
    print(f"📂 输出目录：{OUTPUT_ROOT}")
    print(f"📊 成功处理：{success_count} / {total_count} 个故事")
    print("=" * 50)


if __name__ == "__main__":
    main()