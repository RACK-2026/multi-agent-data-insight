"""
飞书数据迁移脚本 - 将飞书Bitable的所有字段定义和记录数据完整拷贝到Agent本地数据库
（只读飞书，不写入，不修改飞书任何内容）
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import db_service, LocalPrompt
from app.services.feishu_service import feishu_service
from app.services.prompt_manager import prompt_manager


def sync_all_fields():
    """同步所有字段定义"""
    print("[1/4] 同步字段定义...")
    tables = [
        ("main", "基础千川数据盘", settings.TABLE_MAIN),
        ("review", "千川复盘表", settings.TABLE_REVIEW),
        ("account", "千川账户", settings.TABLE_ACCOUNT),
        ("team", "视频组人员信息", settings.TABLE_TEAM),
    ]

    for name, label, table_id in tables:
        if not table_id:
            continue
        try:
            ft = feishu_service.get_table(name)
            if not ft:
                print(f"  [跳过] {label} - 未连接")
                continue
            fields = ft.list_fields()
            db_service.save_feishu_fields(name, fields)
            print(f"  [OK] {label}: {len(fields)}个字段")

            ai_fields = [f for f in fields if any(k in (f.get("field_name","")) for k in ["AI","分析","总结","评分","拆解","标签","脚本","输出"])]
            if ai_fields:
                print(f"       其中AI/分析相关字段: {len(ai_fields)}个")
                for af in ai_fields[:5]:
                    print(f"       - {af['field_name']} (type={af.get('type','?')})")
                if len(ai_fields) > 5:
                    print(f"       ... 还有{len(ai_fields)-5}个")
        except Exception as e:
            print(f"  [FAIL] {label}: {e}")


def sync_all_records():
    """同步所有记录数据"""
    print("\n[2/4] 同步记录数据...")
    tables = [("main", "基础千川数据盘"), ("review", "千川复盘表")]

    for name, label in tables:
        try:
            ft = feishu_service.get_table(name)
            if not ft:
                print(f"  [跳过] {label}")
                continue
            records = ft.query_record(max_records=500)
            db_service.save_feishu_records(name, records)
            print(f"  [OK] {label}: {len(records)}条记录")

            has_ai = 0
            for r in records:
                if any(v for k, v in r.items() if ("输出结果" in k or "输出" in k) and v):
                    has_ai += 1
            print(f"       含AI分析结果的记录: {has_ai}/{len(records)}")
        except Exception as e:
            print(f"  [FAIL] {label}: {e}")


def init_local_prompts():
    """初始化本地提示词"""
    print("\n[3/4] 初始化本地提示词...")

    agent_names = [
        "script_generator", "content_analyzer", "creative_analyzer",
        "scoring_agent", "consumption_agent",
    ]

    for name in agent_names:
        try:
            prompt = prompt_manager.load_prompt(name)
            if prompt:
                content = json.dumps(prompt, ensure_ascii=False)
                db_service.save_local_prompt(
                    category=name,
                    version=prompt.get("version", "1.0.0"),
                    content=content,
                    notes="从飞书和初始文件导入",
                    source="initial",
                )
                print(f"  [OK] {name}: v{prompt.get('version','1.0.0')}")
            else:
                # 即使没有初始文件，也创建一个默认版本
                default = {
                    "agent_name": name,
                    "version": "1.0.0",
                    "system_prompt": f"你是一个千川视频脚本分析专家，负责{name}任务。",
                    "user_prompt_template": "请分析以下数据: {data}",
                }
                content = json.dumps(default, ensure_ascii=False)
                db_service.save_local_prompt(
                    category=name, version="1.0.0",
                    content=content, notes="默认初始版本",
                    source="initial",
                )
                print(f"  [OK] {name}: 默认v1.0.0（无初始文件）")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")


def run_migration():
    """执行完整迁移"""
    print("=" * 60)
    print("飞书数据 -> Agent本地 完整迁移")
    print("（只读飞书，不写入、不修改飞书任何内容）")
    print("=" * 60)

    sync_all_fields()
    sync_all_records()
    init_local_prompts()

    # 统计
    fields = db_service.get_all_fields("main")
    records = db_service.get_all_records("main")
    print(f"\n[4/4] 迁移完成!")
    print(f"  - 基础千川数据盘: {len(fields)}个字段, {len(records)}条记录")
    print(f"  - 数据位置: {settings.DATABASE_URL}")
    print(f"  - 飞书状态: 仅读取，未修改")

    return {"fields": len(fields), "records": len(records)}


if __name__ == "__main__":
    run_migration()

