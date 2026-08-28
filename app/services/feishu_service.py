"""Optional external-table adapter for the public demo."""
from typing import Any, Optional


class FeishuService:
    """No-op boundary; the original private integration is not distributed."""

    enabled = False

    def get_table(self, name: str) -> Optional[Any]:
        return None

    def get_fields(self, table_name: str) -> list[dict]:
        return []

    def query_records(self, table_name: str, **kwargs: Any) -> list[dict]:
        return []

    def get_records(self, table_name: str, record_ids: list[str]) -> list[dict]:
        return []

    def get_record_count(self, table_name: str) -> int:
        return 0

    def get_field_types(self, table_name: str) -> dict:
        return {}


feishu_service = FeishuService()

