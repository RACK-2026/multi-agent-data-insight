"""
Agent 基类 - 所有Agent的公共基类
"""
import json
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.database import db_service, AgentLog
from app.services.llm_service import llm_service
from app.services.prompt_manager import prompt_manager


class BaseAgent(ABC):
    """Agent抽象基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, data: dict) -> dict:
        """执行Agent分析任务（子类实现）"""
        pass

    def get_system_prompt(self) -> str:
        """获取system prompt"""
        return prompt_manager.get_system_prompt(self.name)

    def get_user_prompt(self, **kwargs) -> str:
        """获取user prompt"""
        return prompt_manager.get_user_prompt(self.name, **kwargs)

    async def call_llm(self, data: dict, response_format: dict = None) -> str:
        """调用LLM进行推理"""
        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(**data)
        params = prompt_manager.get_parameters(self.name)

        return await llm_service.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 2048),
            response_format=response_format,
        )

    async def safe_run(self, data: dict, record_id: str = "") -> dict:
        """带异常处理和日志的安全执行"""
        start_time = time.time()
        try:
            result = await self.run(data)
            duration = int((time.time() - start_time) * 1000)

            # 记录成功日志
            self._log(record_id, "success", duration,
                      str(data.get("视频名称", ""))[:50],
                      str(result.get("summary", str(result)[:50]))[:50])
            return result
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            error_msg = traceback.format_exc()
            self._log(record_id, "failed", duration, "", error_msg[:200])
            return {"error": str(e), "agent": self.name, "status": "failed"}

    def _log(self, record_id: str, status: str, duration_ms: int,
             input_summary: str = "", output_summary: str = "", error: str = ""):
        """记录Agent执行日志"""
        try:
            with db_service.get_session() as session:
                log = AgentLog(
                    agent_name=self.name,
                    record_id=record_id,
                    status=status,
                    duration_ms=duration_ms,
                    input_summary=input_summary,
                    output_summary=output_summary,
                    error=error,
                )
                session.add(log)
                session.commit()
        except Exception:
            pass

