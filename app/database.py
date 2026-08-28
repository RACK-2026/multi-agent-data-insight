"""
本地数据库 - SQLite缓存层
用于缓存飞书数据、分析结果、脚本生成、编导反馈、提示词版本管理
"""
import json
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, JSON, select, Boolean, inspect, text
from sqlalchemy.orm import declarative_base, Session

from app.config import settings, DATA_DIR

Base = declarative_base()


class DateTimeEncoder(json.JSONEncoder):
    """处理datetime序列化的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# ==================== 飞书数据缓存 ====================

class FeishuFieldCache(Base):
    """飞书Bitable字段定义缓存（含字段提示词信息）"""
    __tablename__ = "feishu_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(64), index=True)
    field_name = Column(String(128))
    field_id = Column(String(64))
    field_type = Column(Integer)
    ui_type = Column(String(32))
    is_primary = Column(Boolean, default=False)
    is_formula = Column(Boolean, default=False)
    is_lookup = Column(Boolean, default=False)
    options = Column(JSON, nullable=True)  # 单选/多选选项
    synced_at = Column(DateTime, default=datetime.now)


class FeishuRecordData(Base):
    """飞书记录完整数据缓存"""
    __tablename__ = "feishu_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(64), index=True)
    record_id = Column(String(64), index=True)
    raw_data = Column(JSON)  # 完整原始数据
    synced_at = Column(DateTime, default=datetime.now)


class VideoRecord(Base):
    """视频记录缓存 - 对应基础千川数据盘"""
    __tablename__ = "video_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(64), unique=True, index=True)
    raw_data = Column(JSON, comment="原始飞书数据JSON")
    同步时间 = Column(DateTime, default=datetime.now)


# ==================== 脚本生成 ====================

class GeneratedScript(Base):
    """生成的脚本文案"""
    __tablename__ = "generated_scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_record_id = Column(String(64), index=True, comment="关联的视频记录ID")
    video_name = Column(String(256))
    product_name = Column(String(128))
    brand = Column(String(128))

    # 脚本内容
    script_text = Column(Text, comment="生成的前10秒脚本文案")
    script_type = Column(String(64), comment="脚本类型")
    focus_point = Column(String(256), comment="核心卖点/焦点")
    hook_type = Column(String(64), comment="开头钩子类型")
    production_tag = Column(String(32), comment="制作标签：AI完全生成/真人+绿幕(低成本)/真人+绿幕(高成本)/真人+绿幕(模拟真实场景)")

    # 脚本生成上下文
    prompt_version = Column(String(32), comment="使用的提示词版本")
    source_data_summary = Column(Text, comment="参考的数据摘要")
    generated_at = Column(DateTime, default=datetime.now)

    # 编导审核状态：pending / approved / rejected
    review_status = Column(String(16), default="pending")
    review_notes = Column(Text, nullable=True, comment="编导备注建议")
    reviewed_at = Column(DateTime, nullable=True)


class ScriptFeedback(Base):
    """编导对脚本的反馈历史"""
    __tablename__ = "script_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, index=True)
    action = Column(String(16))  # approved / rejected
    notes = Column(Text, nullable=True)
    prompt_version = Column(String(32))
    created_at = Column(DateTime, default=datetime.now)


class ImportedScript(Base):
    """导入的编导参考脚本（用于优化提示词的参考素材）"""
    __tablename__ = "imported_scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(32), comment="来源: feishu / excel / csv / txt / manual")
    source_name = Column(String(256), comment="来源名称/文件名/飞书链接")
    script_text = Column(Text, comment="脚本文案内容")
    script_type = Column(String(64), nullable=True, comment="脚本类型")
    product_name = Column(String(128), nullable=True, comment="关联产品")
    director = Column(String(64), nullable=True, comment="编导名称")
    notes = Column(Text, nullable=True, comment="备注说明")
    raw_data = Column(JSON, nullable=True, comment="原始数据（用于追溯）")
    created_at = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)
    prompt_version = Column(String(32))
    created_at = Column(DateTime, default=datetime.now)


# ==================== 标题生成 ====================

class GeneratedTitle(Base):
    """生成的标题"""
    __tablename__ = "generated_titles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(32), comment="平台: douyin/xiaohongshu/kuaishou/shipinhao")
    title_text = Column(Text, comment="标题文案")
    style_tag = Column(String(32), nullable=True, comment="风格标签")
    reason = Column(Text, nullable=True, comment="吸引点击的原因")
    reference_title = Column(Text, nullable=True, comment="参考的网络爆款标题")
    reference_likes = Column(String(32), nullable=True, comment="参考标题的点赞数")
    generated_at = Column(DateTime, default=datetime.now)
    review_status = Column(String(16), default="pending", comment="pending/approved/rejected")
    review_notes = Column(Text, nullable=True, comment="编导备注")


class TitleFeedback(Base):
    """编导对标题的反馈历史"""
    __tablename__ = "title_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_id = Column(Integer, index=True)
    action = Column(String(16))  # approved / rejected
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


# ==================== 创意工坊 ====================

class Suggestion(Base):
    """创意工坊建议"""
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(16), comment="script / title")
    content = Column(Text, comment="建议内容")
    status = Column(String(16), default="pending", comment="pending / reviewed / optimized")
    created_at = Column(DateTime, default=datetime.now)


# ==================== 产品管理 ====================

class Product(Base):
    """产品信息"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), comment="产品名称")
    details = Column(Text, comment="产品详情")
    tags = Column(JSON, nullable=True, comment="产品标签列表")
    source_type = Column(String(32), comment="来源: upload/feishu/manual")
    source_name = Column(String(256), nullable=True, comment="来源文件名/飞书链接")
    created_at = Column(DateTime, default=datetime.now)


# ==================== 提示词管理 ====================

class LocalPrompt(Base):
    """Agent本地提示词版本管理（不写入飞书）"""
    __tablename__ = "local_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(64), index=True, comment="分类: script_generator / content_analyzer / ...")
    version = Column(String(32))
    prompt_content = Column(Text)
    source = Column(String(32), default="initial", comment="来源: initial / optimized / manual")
    notes = Column(Text, nullable=True, comment="版本说明/变更原因")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


# ==================== Agent日志 ====================

class AgentLog(Base):
    """Agent执行日志"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(64), index=True)
    record_id = Column(String(64))
    status = Column(String(16))
    duration_ms = Column(Integer)
    input_summary = Column(String(256))
    output_summary = Column(String(256))
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


# ==================== 数据库服务 ====================

class DatabaseService:
    """本地数据库服务"""

    def __init__(self):
        db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        if db_path.startswith("./"):
            db_path = str(DATA_DIR / Path(db_path).name)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        # 执行数据库迁移：为已存在的表添加新列
        self._run_migrations()

    def _run_migrations(self):
        """运行数据库迁移：为已存在的表添加新列（避免手动删库）"""
        inspector = inspect(self.engine)
        columns = [c["name"] for c in inspector.get_columns("generated_scripts")]
        if "production_tag" not in columns:
            with self.engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE generated_scripts ADD COLUMN production_tag VARCHAR(32) DEFAULT ''")
                )
                conn.commit()
        # 标题表添加引用字段
        try:
            tcols = [c["name"] for c in inspector.get_columns("generated_titles")]
            if "reference_title" not in tcols:
                with self.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE generated_titles ADD COLUMN reference_title TEXT DEFAULT ''"))
                    conn.execute(text("ALTER TABLE generated_titles ADD COLUMN reference_likes VARCHAR(32) DEFAULT ''"))
                    conn.commit()
        except Exception:
            pass

    def get_session(self):
        return Session(self.engine)

    # ---- 飞书缓存 ----

    def save_feishu_fields(self, table_name: str, fields: list[dict]):
        """保存飞书Bitable的字段定义"""
        with self.get_session() as session:
            session.query(FeishuFieldCache).filter_by(table_name=table_name).delete()
            for f in fields:
                prop = f.get("property", {}) or {}
                options = prop.get("options", []) if isinstance(prop, dict) else []
                sf = FeishuFieldCache(
                    table_name=table_name,
                    field_name=f.get("field_name", ""),
                    field_id=f.get("field_id", ""),
                    field_type=f.get("type", 0),
                    ui_type=f.get("ui_type", ""),
                    is_primary=f.get("is_primary", False),
                    is_formula=f.get("type") == 20,
                    is_lookup=f.get("type") in (19, 21),
                    options=[o.get("name", "") for o in options] if options else None,
                )
                session.add(sf)
            session.commit()

    def save_feishu_records(self, table_name: str, records: list[dict]):
        """批量保存飞书记录（自动处理datetime序列化）"""
        with self.get_session() as session:
            for r in records:
                rid = r.get("record_id", "")
                # 先序列化确保所有datetime可转JSON
                r_json = json.loads(json.dumps(r, cls=DateTimeEncoder))
                existing = session.query(FeishuRecordData).filter_by(
                    table_name=table_name, record_id=rid
                ).first()
                if existing:
                    existing.raw_data = r_json
                    existing.synced_at = datetime.now()
                else:
                    session.add(FeishuRecordData(
                        table_name=table_name, record_id=rid, raw_data=r_json
                    ))
            session.commit()

    def get_all_fields(self, table_name: str = "main") -> list[FeishuFieldCache]:
        """获取缓存的字段定义"""
        with self.get_session() as session:
            return list(session.query(FeishuFieldCache).filter_by(table_name=table_name).all())

    def get_all_records(self, table_name: str = "main") -> list[FeishuRecordData]:
        """获取缓存的记录"""
        with self.get_session() as session:
            return list(session.query(FeishuRecordData).filter_by(table_name=table_name).all())

    # ---- 脚本管理 ----

    def save_script(self, script_data: dict) -> int:
        """保存生成的脚本，返回ID"""
        with self.get_session() as session:
            gs = GeneratedScript(**script_data)
            session.add(gs)
            session.commit()
            return gs.id

    def update_script_review(self, script_id: int, status: str, notes: str = ""):
        """更新脚本的编导审核结果"""
        with self.get_session() as session:
            script = session.query(GeneratedScript).filter_by(id=script_id).first()
            if script:
                script.review_status = status
                script.review_notes = notes
                script.reviewed_at = datetime.now()
                session.commit()

    def update_script_tag(self, script_id: int, production_tag: str):
        """更新脚本的制作标签"""
        with self.get_session() as session:
            script = session.query(GeneratedScript).filter_by(id=script_id).first()
            if script:
                script.production_tag = production_tag
                session.commit()

    def get_scripts(self, status: str = None, limit: int = 50) -> list[GeneratedScript]:
        """获取脚本列表"""
        with self.get_session() as session:
            q = session.query(GeneratedScript)
            if status:
                q = q.filter_by(review_status=status)
            return list(q.order_by(GeneratedScript.generated_at.desc()).limit(limit).all())

    def get_script_by_id(self, script_id: int) -> GeneratedScript:
        """获取单个脚本"""
        with self.get_session() as session:
            return session.query(GeneratedScript).filter_by(id=script_id).first()

    def save_feedback(self, script_id: int, action: str, notes: str, prompt_version: str):
        """保存编导反馈"""
        with self.get_session() as session:
            session.add(ScriptFeedback(
                script_id=script_id, action=action,
                notes=notes, prompt_version=prompt_version,
            ))
            session.commit()

    # ---- 本地提示词管理 ----

    def get_local_prompt(self, category: str) -> LocalPrompt:
        """获取当前活跃的本地提示词"""
        with self.get_session() as session:
            return session.query(LocalPrompt).filter_by(
                category=category, is_active=True
            ).order_by(LocalPrompt.id.desc()).first()

    def get_active_prompt(self, agent_name: str) -> LocalPrompt:
        """兼容旧接口：获取指定Agent的当前活跃提示词"""
        return self.get_local_prompt(agent_name)

    def save_prompt(self, agent_name: str, version: str, content: str):
        """兼容旧接口：保存新版本提示词"""
        self.save_local_prompt(category=agent_name, version=version, content=content, source="initial")

    def save_local_prompt(self, category: str, version: str, content: str, notes: str = "", source: str = "optimized"):
        """保存新版本本地提示词"""
        with self.get_session() as session:
            session.query(LocalPrompt).filter_by(
                category=category, is_active=True
            ).update({"is_active": False})
            lp = LocalPrompt(
                category=category, version=version,
                prompt_content=content, notes=notes,
                source=source, is_active=True,
            )
            session.add(lp)
            session.commit()

    def get_prompt_history(self, category: str) -> list[LocalPrompt]:
        """获取提示词历史版本"""
        with self.get_session() as session:
            return list(session.query(LocalPrompt).filter_by(
                category=category
            ).order_by(LocalPrompt.id.desc()).limit(20).all())

    # ---- 导入脚本管理 ----

    def save_imported_script(self, data: dict) -> int:
        """保存一条导入的脚本"""
        with self.get_session() as session:
            imp = ImportedScript(**data)
            session.add(imp)
            session.commit()
            return imp.id

    def save_imported_scripts_batch(self, scripts: list[dict]) -> int:
        """批量保存导入脚本，返回保存数量"""
        count = 0
        with self.get_session() as session:
            for s in scripts:
                # 去重：相同source和script_text视为重复
                existing = session.query(ImportedScript).filter_by(
                    source=s.get("source", ""),
                    script_text=s.get("script_text", ""),
                ).first()
                if not existing:
                    session.add(ImportedScript(**s))
                    count += 1
            session.commit()
        return count

    def get_imported_scripts(self, source: str = None, limit: int = 100) -> list[ImportedScript]:
        """获取导入的参考脚本"""
        with self.get_session() as session:
            q = session.query(ImportedScript)
            if source:
                q = q.filter_by(source=source)
            return list(q.order_by(ImportedScript.created_at.desc()).limit(limit).all())

    # ---- 标题管理 ----

    def save_title(self, data: dict) -> int:
        """保存生成的标题，返回ID"""
        with self.get_session() as session:
            gt = GeneratedTitle(**data)
            session.add(gt)
            session.commit()
            return gt.id

    def get_titles(self, platform: str = None, limit: int = 50) -> list[GeneratedTitle]:
        """获取标题列表"""
        with self.get_session() as session:
            q = session.query(GeneratedTitle)
            if platform:
                q = q.filter_by(platform=platform)
            return list(q.order_by(GeneratedTitle.id.desc()).limit(limit).all())

    def update_title_review(self, title_id: int, status: str, notes: str = ""):
        """更新标题审核状态"""
        with self.get_session() as session:
            t = session.query(GeneratedTitle).filter_by(id=title_id).first()
            if t:
                t.review_status = status
                t.review_notes = notes
                session.commit()

    def save_title_feedback(self, title_id: int, action: str, notes: str):
        """保存标题反馈"""
        with self.get_session() as session:
            session.add(TitleFeedback(title_id=title_id, action=action, notes=notes))
            session.commit()

    # ---- 创意工坊 ----

    def save_suggestion(self, data: dict) -> int:
        """保存建议"""
        with self.get_session() as session:
            s = Suggestion(**data)
            session.add(s)
            session.commit()
            return s.id

    def get_suggestions(self, stype: str = None, status: str = None, limit: int = 50) -> list[Suggestion]:
        """获取建议列表"""
        with self.get_session() as session:
            q = session.query(Suggestion)
            if stype:
                q = q.filter_by(type=stype)
            if status:
                q = q.filter_by(status=status)
            return list(q.order_by(Suggestion.id.desc()).limit(limit).all())

    def mark_suggestion_reviewed(self, suggestion_id: int):
        """标记建议为已评审"""
        with self.get_session() as session:
            s = session.query(Suggestion).filter_by(id=suggestion_id).first()
            if s:
                s.status = "reviewed"
                session.commit()

    # ---- 产品管理 ----

    def save_product(self, data: dict) -> int:
        """保存产品"""
        from sqlalchemy import text as sa_text
        with self.get_session() as session:
            # 去重：同名称不重复
            name = data.get("name", "")
            existing = session.query(Product).filter_by(name=name).first()
            if existing:
                existing.details = data.get("details", existing.details)
                if "tags" in data and data["tags"] is not None:
                    existing.tags = data["tags"]
                session.commit()
                return existing.id
            p = Product(**data)
            session.add(p)
            session.commit()
            return p.id

    def get_products(self, limit: int = 100) -> list[Product]:
        """获取产品列表"""
        with self.get_session() as session:
            return list(session.query(Product).order_by(Product.id.desc()).limit(limit).all())

    def get_product_by_id(self, product_id: int) -> Product:
        """获取单个产品"""
        with self.get_session() as session:
            return session.query(Product).filter_by(id=product_id).first()

    def delete_product(self, product_id: int):
        """删除产品"""
        with self.get_session() as session:
            p = session.query(Product).filter_by(id=product_id).first()
            if p:
                session.delete(p)
                session.commit()


# 全局单例
db_service = DatabaseService()

