from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# 关键：添加项目根目录到Python路径，确保Alembic能找到app模块
sys.path.append(str(Path(__file__).parent.parent))

from app.models.db_models import Base  # 导入模型基类
from app.models.db_models import (
    Article, Sentence, Annotation,  # 原有模型
    ChatSession, ChatMessage, ChatAttachment, ChatSettings  # 聊天相关模型
)

# Alembic配置对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 关联模型的元数据（用于自动生成迁移脚本）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（使用URL而非引擎）"""
    # 从 alembic.ini 读取数据库连接地址
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（创建引擎并关联连接）"""
    # 使用 alembic.ini 的数据库地址创建引擎
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据模式选择执行离线或在线迁移
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
