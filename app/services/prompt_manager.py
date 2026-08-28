"""
提示词管理器 - 加载、存储、版本管理Agent提示词
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.database import db_service

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class PromptManager:
    """提示词管理服务"""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        # 启动时清理script_generator可能存在的旧缓存（旧版prompt_files遗漏导致）
        self._cleanup_stale_script_prompt()

    def _cleanup_stale_script_prompt(self):
        """清理并刷新script_generator提示词
        条件：DB中的提示词与JSON文件内容不一致（文件有更新）时重新加载
        """
        try:
            # 从文件加载最新提示词
            file_prompt = self.load_prompt("script_generator")
            if not file_prompt:
                return

            # 检查DB中的版本
            from app.database import LocalPrompt
            db_prompt = db_service.get_active_prompt("script_generator")
            if db_prompt:
                try:
                    db_content = json.loads(db_prompt.prompt_content)
                    # 比较文件内容和DB内容是否一致（比较system_prompt + user_prompt_template）
                    if (db_content.get("system_prompt") != file_prompt.get("system_prompt") or
                        db_content.get("user_prompt_template") != file_prompt.get("user_prompt_template") or
                        "production_tag" not in db_content.get("system_prompt", "")):
                        # 文件已更新，覆盖DB缓存
                        with db_service.get_session() as session:
                            old = session.query(LocalPrompt).filter_by(
                                id=db_prompt.id, is_active=True
                            ).first()
                            if old:
                                old.is_active = False
                                session.commit()
                except (json.JSONDecodeError, AttributeError):
                    pass
        except Exception:
            import traceback
            traceback.print_exc()

    def load_prompt(self, agent_name: str) -> Optional[dict]:
        """加载Agent的初始提示词（从JSON文件）"""
        if agent_name in self._cache:
            return self._cache[agent_name]

        prompt_files = {
            "content_analyzer": "agent_a_content.json",
            "creative_analyzer": "agent_b_creative.json",
            "scoring_agent": "agent_c_scoring.json",
            "consumption_agent": "agent_d_consumption.json",
            "review_agent": "agent_review.json",
            "prompt_optimizer": "prompt_optimizer.json",
            "script_generator": "agent_script_generator.json",
            "title_generator": "agent_title_generator.json",
            "product_analyzer": "agent_product_analyzer.json",
        }

        filename = prompt_files.get(agent_name)
        if not filename:
            return None

        filepath = PROMPTS_DIR / filename
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            prompt = json.load(f)
            self._cache[agent_name] = prompt
            return prompt

    def get_active_prompt(self, agent_name: str) -> dict:
        """获取当前活跃的提示词（优先取数据库中的最新版本）"""
        # 先从数据库获取
        db_prompt = db_service.get_active_prompt(agent_name)
        if db_prompt:
            try:
                return json.loads(db_prompt.prompt_content)
            except (json.JSONDecodeError, AttributeError):
                pass

        # 无数据库版本，从文件加载
        prompt = self.load_prompt(agent_name)
        if prompt:
            # 同步到数据库
            try:
                db_service.save_prompt(
                    agent_name=agent_name,
                    version=prompt.get("version", "1.0.0"),
                    content=json.dumps(prompt, ensure_ascii=False),
                )
            except Exception:
                pass
            return prompt

        return {
            "agent_name": agent_name,
            "version": "0.0.0",
            "system_prompt": "你是一个AI助手。",
            "user_prompt_template": "请分析: {data}",
        }

    def get_system_prompt(self, agent_name: str) -> str:
        """获取Agent的system_prompt"""
        prompt = self.get_active_prompt(agent_name)
        return prompt.get("system_prompt", "")

    def get_user_prompt(self, agent_name: str, **kwargs) -> str:
        """用模板和数据生成user_prompt"""
        prompt = self.get_active_prompt(agent_name)
        template = prompt.get("user_prompt_template", "{data}")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # 缺失的变量用原始占位符
            return template

    def get_parameters(self, agent_name: str) -> dict:
        """获取Agent的参数配置"""
        prompt = self.get_active_prompt(agent_name)
        return prompt.get("parameters", {"temperature": 0.7, "max_tokens": 2048})

    def save_optimized_prompt(self, agent_name: str, new_prompt: dict):
        """保存优化后的提示词新版本"""
        version = new_prompt.get("new_version", f"{datetime.now().strftime('%Y%m%d%H%M%S')}")
        content = json.dumps(new_prompt.get("optimized_prompt", new_prompt), ensure_ascii=False)
        db_service.save_prompt(agent_name, version, content)
        # 清除缓存
        self._cache.pop(agent_name, None)

    def load_all_prompts(self) -> dict:
        """加载所有提示词的当前版本信息"""
        result = {}
        agent_names = [
            "content_analyzer", "creative_analyzer",
            "scoring_agent", "consumption_agent",
            "review_agent", "prompt_optimizer",
        ]
        for name in agent_names:
            prompt = self.get_active_prompt(name)
            result[name] = {
                "version": prompt.get("version", "0.0.0"),
                "description": prompt.get("description", ""),
            }
        return result


# 全局单例
prompt_manager = PromptManager()

