"""
脚本导入服务 - 从飞书链接、Excel、CSV、TXT等来源导入编导脚本
"""
import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.database import db_service


class ScriptImportService:
    """脚本导入服务"""

    @staticmethod
    def parse_txt(content: str, filename: str = "") -> list[dict]:
        """解析TXT文件中的脚本
        支持格式：
        - 按空行/分隔线分割的多个脚本
        - 带【标题】标记的脚本
        - 纯文本脚本（直接全文导入）
        """
        scripts = []
        lines = content.strip().split("\n")

        # 尝试按分隔线分割
        blocks = re.split(r'\n\s*[-=]{3,}\s*\n|\n\s*\n\s*\n', content.strip())
        if len(blocks) <= 1:
            # 无分隔，整段作为一条
            blocks = [content.strip()]

        for block in blocks:
            block = block.strip()
            if not block or len(block) < 10:
                continue

            script_type = ""
            title_line = block.split("\n")[0].strip()
            if re.match(r'^[【\[]', title_line):
                script_type = title_line.strip("【】[]")

            scripts.append({
                "source": "txt",
                "source_name": filename or "TXT导入",
                "script_text": block,
                "script_type": script_type,
            })

        return scripts

    @staticmethod
    def parse_csv(file_content: bytes, filename: str = "") -> list[dict]:
        """解析CSV文件中的脚本
        期望列名包含：脚本/文案/内容、类型、产品等
        """
        scripts = []
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = file_content.decode("gbk")
            except UnicodeDecodeError:
                text = file_content.decode("utf-8", errors="replace")

        reader = csv.DictReader(io.StringIO(text))

        # 自动识别列
        script_col = None
        type_col = None
        product_col = None
        director_col = None

        for col in reader.fieldnames or []:
            col_lower = col.lower().strip()
            if any(k in col_lower for k in ["脚本", "文案", "内容", "话术", "script", "copy"]):
                script_col = col
            elif any(k in col_lower for k in ["类型", "分类", "风格", "type"]):
                type_col = col
            elif any(k in col_lower for k in ["产品", "商品", "品名", "product"]):
                product_col = col
            elif any(k in col_lower for k in ["编导", "作者", "导演", "director"]):
                director_col = col

        if not script_col:
            # 如果没识别到脚本列，取最长的文本列
            for row in reader:
                for col, val in row.items():
                    if val and len(val) > 50:
                        script_col = col
                        break
                break
            reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            script_text = row.get(script_col, "") if script_col else ""
            if not script_text or len(script_text.strip()) < 20:
                continue
            scripts.append({
                "source": "csv",
                "source_name": filename or "CSV导入",
                "script_text": script_text.strip(),
                "script_type": row.get(type_col, "").strip() if type_col else "",
                "product_name": row.get(product_col, "").strip() if product_col else "",
                "director": row.get(director_col, "").strip() if director_col else "",
            })

        return scripts

    @staticmethod
    def parse_excel(file_bytes: bytes, filename: str = "") -> list[dict]:
        """解析Excel文件中的脚本"""
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        # 表头识别
        headers = [str(c or "").strip() for c in rows[0]]
        script_col = None
        type_col = None
        product_col = None
        director_col = None

        for i, h in enumerate(headers):
            hl = h.lower()
            if any(k in hl for k in ["脚本", "文案", "内容", "话术", "script", "copy"]):
                script_col = i
            elif any(k in hl for k in ["类型", "分类", "风格", "type"]):
                type_col = i
            elif any(k in hl for k in ["产品", "商品", "品名", "product"]):
                product_col = i
            elif any(k in hl for k in ["编导", "作者", "导演", "director"]):
                director_col = i

        if script_col is None:
            # 无表头则尝试整行合并
            full_text = "\n".join([" ".join([str(c or "") for c in row]) for row in rows])
            return ScriptImportService.parse_txt(full_text, filename)

        scripts = []
        for row in rows[1:]:
            if script_col >= len(row):
                continue
            script_text = str(row[script_col] or "").strip()
            if len(script_text) < 20:
                continue
            scripts.append({
                "source": "excel",
                "source_name": filename or "Excel导入",
                "script_text": script_text,
                "script_type": str(row[type_col] or "").strip() if type_col is not None and type_col < len(row) else "",
                "product_name": str(row[product_col] or "").strip() if product_col is not None and product_col < len(row) else "",
                "director": str(row[director_col] or "").strip() if director_col is not None and director_col < len(row) else "",
            })

        wb.close()
        return scripts

    @staticmethod
    def parse_feishu_url(url: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """解析飞书链接，返回(app_token, table_id, view_id)"""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) < 2:
            return None, None, None

        query = parse_qs(parsed.query)
        table_id = query.get("table", [None])[0]
        view_id = query.get("view", [None])[0]

        if path_parts[0] in ("base", "wiki"):
            return path_parts[1], table_id, view_id
        return None, None, None

    @staticmethod
    async def import_from_feishu(url: str, director_name: str = "") -> list[dict]:
        """从飞书Bitable链接导入脚本"""
        from app.services.feishu_service import feishu_service

        app_token, table_id, view_id = ScriptImportService.parse_feishu_url(url)
        if not app_token:
            return []

        # 创建临时FeishuTable读取数据
        from feishu_table_utils import FeishuTable
        from app.config import settings

        ft = FeishuTable(
            app_id=settings.FEISHU_APP_ID,
            app_secret=settings.FEISHU_APP_SECRET,
            app_token=app_token,
            table_id=table_id,
            view_id=view_id,
            auto_load_fields=True,
        )

        records = ft.query_record(max_records=500)
        if not records:
            return []

        # 自动识别脚本相关字段
        fields = ft.list_fields()
        script_field = None
        type_field = None
        product_field = None

        for f in fields:
            name = f.get("field_name", "")
            if any(k in name for k in ["脚本", "文案", "话术", "script", "内容"]):
                if not script_field or "脚本" in name:
                    script_field = name
            if any(k in name for k in ["类型", "分类", "style"]):
                type_field = name
            if any(k in name for k in ["产品", "商品", "product"]):
                product_field = name

        if not script_field:
            # 取第一个长文本字段
            for f in fields:
                if f.get("type") == 1 and f.get("field_name") not in ("编码", "视频ID"):
                    script_field = f.get("field_name")
                    break

        if not script_field:
            return []

        scripts = []
        for r in records:
            text = r.get(script_field, "")
            if isinstance(text, list):
                text = " ".join([str(t) for t in text])
            text = str(text or "").strip()
            if len(text) < 20:
                continue

            scripts.append({
                "source": "feishu",
                "source_name": url[:100],
                "script_text": text,
                "script_type": str(r.get(type_field, "") or "") if type_field else "",
                "product_name": str(r.get(product_field, "") or "") if product_field else "",
                "director": director_name,
                "raw_data": {k: str(v)[:100] for k, v in list(r.items())[:10]} if r else None,
            })

        return scripts

    @staticmethod
    def import_scripts(scripts: list[dict]) -> dict:
        """将解析后的脚本批量存入数据库"""
        count = db_service.save_imported_scripts_batch(scripts)
        return {"imported": count, "total": len(scripts)}

