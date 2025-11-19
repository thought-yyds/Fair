import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.models import get_db
from backend.app.models.db_models import Article
from sqlalchemy.orm import Session

# 获取数据库会话
db = next(get_db())

# 查询ID为4的文章
article = db.query(Article).filter(Article.id == 4).first()

if article:
    print(f"文章ID: {article.id}")
    print(f"文章名称: {article.name}")
    print(f"原始路径: {article.original_path}")
    print(f"批注路径: {article.annotated_path}")
    print(f"状态: {article.status}")
    print(f"审查进度: {article.review_progress}")
    print(f"风险等级: {article.risk_level}")
    print(f"审查时间: {article.review_time}")
else:
    print("未找到ID为4的文章")

db.close()
