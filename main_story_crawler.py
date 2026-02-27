import requests
import json
import time
import os

# ================= 配置区域 =================
# 您的完整数据列表
data_list = [
    {"name": "远航星", "entryId": "1466875785278619648"},
    {"name": "致第二次日出", "entryId": "1459283087973330944"},
    {"name": "冰原下的星炬", "entryId": "1452394891366207488"},
    {"name": "未知的既感", "entryId": "1452385119459971072"},
    {"name": "星光流转于眼眸之间", "entryId": "1439949994134757376"},
    {"name": "曙光停摆于荒地之上", "entryId": "1439221762898063360"},
    {"name": "独在异乡为异客", "entryId": "1433436825011941376"},
    {"name": "暗潮将映的黎明", "entryId": "1423344971962478592"},
    {"name": "已逝的必将归来", "entryId": "1423058186011807744"},
    {"name": "今夜，注定属于月亮", "entryId": "1417172340329828352"},
    {"name": "灼我以烈阳", "entryId": "1408753175363067904"},
    {"name": "铁锈，剑与烈阳", "entryId": "1408826543900962816"},
    {"name": "捕梦于神秘园中", "entryId": "1396949918158663680"},
    {"name": "燃烧的心", "entryId": "1383208376710463488"},
    {"name": "荣耀暗面", "entryId": "1383842797711962112"},
    {"name": "圣者，忤逆者，告死者", "entryId": "1356335036092030976"},
    {"name": "老人鱼海", "entryId": "1345143080352051200"},
    {"name": "昔我悲伤，今却歌唱", "entryId": "1322907582504562688"},
    {"name": "夜与昼，均请摘下面纱", "entryId": "1322899908986294272"},
    {"name": "那神圣微风时常吹入", "entryId": "1322891157203251200"},
    {"name": "如一叶小舟穿行于茫茫海洋", "entryId": "1322876820824510464"},
    {"name": "行至海岸尽头", "entryId": "1321591709639163904"},
    {"name": "往岁乘霄醒惊蛰", "entryId": "1321252342351679488"},
    {"name": "行路遇新知", "entryId": "1321239890227818496"},
    {"name": "千里卷戎旌 · 下", "entryId": "1321240291303739392"},
    {"name": "千里卷戎旌 · 上", "entryId": "1321236014615425024"},
    {"name": "欲知天将雨", "entryId": "1321227794152878080"},
    {"name": "庭际刀刃鸣", "entryId": "1319417602112999424"},
    {"name": "奔策候残星", "entryId": "1319052342580748288"},
    {"name": "撞金止行阵", "entryId": "1318681287772200960"},
    {"name": "嘤鸣初相召", "entryId": "1317978599912316928"},
    {"name": "万象新声 · 下", "entryId": "1316542410030260224"},
    {"name": "万象新声 · 上", "entryId": "1304475756600438784"}
]

API_URL = "https://api.kurobbs.com/wiki/core/catalogue/item/getEntryDetail"

# ⚠️ 重要：如果报错，请替换为您浏览器最新的 devcode
DEV_CODE = "FMREw8DaqobqEkMYVcevJ1z5NIAfzKVL"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "devcode": DEV_CODE,
    "host": "api.kurobbs.com",
    "origin": "https://wiki.kurobbs.com",
    "referer": "https://wiki.kurobbs.com/",
    "source": "h5",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "wiki_type": "9"
}

# 输出根目录
OUTPUT_ROOT = "mingchao_stories_output"


def get_story_raw(entry_id):
    """获取原始 JSON 数据"""
    payload_str = f"id={entry_id}&wiki_type=9"

    try:
        response = requests.post(
            API_URL,
            data=payload_str,
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def sanitize_filename(name):
    """清理文件名中非法字符"""
    invalid_chars = '<>:"/\\|？*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def main():
    print(f"📂 开始归档 {len(data_list)} 个剧情条目...\n")
    print(f"⚠️ 注意：如果全部失败，请更新代码中的 DEV_CODE\n")

    # 创建总输出目录
    if not os.path.exists(OUTPUT_ROOT):
        os.makedirs(OUTPUT_ROOT)
        print(f"已创建根目录: {OUTPUT_ROOT}/\n")

    success_count = 0

    for i, item in enumerate(data_list):
        name = item['name']
        entry_id = item['entryId']

        # 清理名字作为文件夹名
        safe_name = sanitize_filename(name)
        folder_path = os.path.join(OUTPUT_ROOT, safe_name)

        print(f"[{i + 1}/{len(data_list)}] 处理: {name} ...", end=" ")

        # 1. 获取数据
        data_json = get_story_raw(entry_id)

        if "error" in data_json:
            print(f"❌ 请求失败: {data_json['error']}")
            continue

        if data_json.get("code") != 200 and data_json.get("success") is not True:
            print(f"❌ API返回错误: {data_json.get('msg', 'Unknown')}")
            continue

        # 2. 创建章节文件夹
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # 3. 保存完整原始 JSON
        raw_file_path = os.path.join(folder_path, "raw_data.json")
        with open(raw_file_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文正常显示，indent=2 格式化方便阅读
            json.dump(data_json, f, ensure_ascii=False, indent=2)

        # 4. (可选) 单独提取 content 字段保存，方便快速查看
        # 很多时候 content 里是 HTML 字符串，我们把它存为 .html 或 .txt
        content_data = data_json.get("data", {}).get("content", {})
        if content_data:
            content_file_path = os.path.join(folder_path, "content_structure.json")
            with open(content_file_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)

            # 如果 content 里有 title，也存一个简易文本标记
            title = content_data.get("title", "Untitled")
            info_file_path = os.path.join(folder_path, "info.txt")
            with open(info_file_path, 'w', encoding='utf-8') as f:
                f.write(f"标题: {title}\n")
                f.write(f"Entry ID: {entry_id}\n")
                f.write(f"更新时间: {data_json.get('data', {}).get('lastUpdateTime', 'N/A')}\n")
                f.write(f"浏览数: {data_json.get('data', {}).get('browseCount', 'N/A')}\n")

        print(f"✅ 已保存至: {folder_path}/")
        success_count += 1

        # 延时
        time.sleep(0.3)

    print(f"\n🎉 --- 归档完成 ---")
    print(f"成功: {success_count}/{len(data_list)}")
    print(f"📂 所有文件位于: {os.path.abspath(OUTPUT_ROOT)}/")
    print("\n每个文件夹包含:")
    print("  - raw_data.json      : 完整的 API 返回数据 (含 modules, story, flow 等所有细节)")
    print("  - content_structure.json : 仅 content 部分的结构化数据")
    print("  - info.txt           : 基础信息摘要")


if __name__ == "__main__":
    main()