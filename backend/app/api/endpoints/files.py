from pathlib import Path  # 新增：统一文件操作风格
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query  # 新增Query：参数验证
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any  # 优化类型注解

# 导入Pydantic Schema（用于过滤敏感字段，需提前在app/models/schemas.py定义）
from app.models import get_db, schemas
# 导入数据库模型（仅用于数据库操作，不直接返回）
from app.models.db_models import Article, Sentence, Annotation
# 导入优化后的文件服务
from app.services.file_service import save_uploaded_file, extract_sentences_from_docx, read_full_doc_content, extract_sentences_with_position


# 创建路由实例（tags用于自动文档分类）
router = APIRouter(tags=["文件管理"])

# -------------------------- 常量配置（可根据需求调整） --------------------------
MAX_FILE_SIZE = 10 * 1024 * 1024  # 最大文件大小：10MB（字节）
MIN_PAGE = 1  # 最小页码
MIN_PAGE_SIZE = 1  # 最小每页数量
MAX_PAGE_SIZE = 100  # 最大每页数量（避免单次查询数据过多）


@router.post("/upload", summary="文件上传（支持docx/pdf，最大10MB）")
def upload_file(
        file: UploadFile = File(..., description="上传文件（仅支持docx/pdf，最大10MB）"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传文件并完成初始化：
    1. 验证文件类型（docx/pdf）和大小（≤10MB）
    2. 保存文件到服务器（自动生成唯一文件名）
    3. 提取句子并写入数据库
    4. 返回过滤敏感信息后的文档数据
    """
    try:
        # 1. 新增：验证文件大小（避免超大文件耗尽资源）
        file_content = file.file.read()  # 读取文件内容（用于验证大小）
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大（{len(file_content) // 1024}KB），最大支持{MAX_FILE_SIZE // 1024}KB（10MB）"
            )
        # 重置文件指针（读取后指针在末尾，需重置才能让save_uploaded_file正常读取）
        file.file.seek(0)

        # 2. 调用优化后的文件服务：保存文件+生成Article记录
        article_db, _, _ = save_uploaded_file(file)
        db.add(article_db)
        db.commit()
        db.refresh(article_db)  # 刷新获取数据库自动生成的ID（如id、upload_time）

        # 3. 提取句子并批量创建Sentence记录
        annotated_path = Path(article_db.annotated_path)  # 转换为Path对象
        sentences = extract_sentences_from_docx(annotated_path)
        if sentences:
            sentence_objs = [
                Sentence(
                    content=sentence,
                    article_id=article_db.id,
                    has_problem=None,  # 初始无审查结果
                    annotation_id=None  # 初始无标注关联
                ) for sentence in sentences
            ]
            db.add_all(sentence_objs)
            db.commit()

        # 4. 核心优化：用Pydantic Schema过滤敏感字段（不返回服务器文件路径）
        article_response = schemas.ArticleResponseSchema.from_orm(article_db)

        return {
            "success": True,
            "msg": "文件上传成功，等待审查",
            "data": article_response.dict()  # 转换为字典返回，前端易处理
        }

    except HTTPException as e:
        # 已知错误（如文件类型/大小错误），直接抛出
        raise e
    except Exception as e:
        # 未知错误：回滚事务+清理资源
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败：{str(e)}，请检查文件格式或重试"
        )


@router.get("/list", summary="获取文档列表（分页+关键词搜索）")
def get_article_list(
        db: Session = Depends(get_db),
        page: int = Query(MIN_PAGE, description="页码", ge=MIN_PAGE),  # 新增：验证页码≥1
        page_size: int = Query(10, description="每页数量", ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),  # 验证数量范围
        keyword: Optional[str] = Query(None, description="搜索关键词（匹配文件名）")
) -> Dict[str, Any]:
    """
    分页获取所有文档，支持关键词搜索：
    - 关键词：模糊匹配文件名（忽略空格）
    - 排序：按上传时间倒序（最新上传在前）
    - 分页：默认10条/页，最大100条/页
    """
    # 1. 构建查询条件（基础查询+关键词过滤）
    query = db.query(Article)
    if keyword and keyword.strip():
        # 关键词非空：模糊匹配文件名（不区分大小写，需数据库支持，如MySQL的LIKE）
        query = query.filter(Article.name.ilike(f"%{keyword.strip()}%"))

    # 2. 计算分页参数+执行查询
    total = query.count()  # 总文档数
    skip = (page - 1) * page_size  # 跳过的记录数
    articles_db = query.order_by(Article.upload_time.desc()).offset(skip).limit(page_size).all()

    # 3. 过滤敏感字段：用Schema转换所有记录
    articles_response = [
        schemas.ArticleResponseSchema.from_orm(art).dict()
        for art in articles_db
    ]

    return {
        "success": True,
        "msg": "文档列表查询成功",
        "data": {
            "list": articles_response,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size  # 向上取整计算总页数
            }
        }
    }


@router.get("/detail/{article_id}", summary="获取文档详情")
def get_article_detail(
        article_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定文档的详细信息（不含服务器文件路径）：
    - 若文档不存在，返回404错误
    - 仅返回前端需要的字段（如id、文件名、状态、进度等）
    """
    # 1. 查询文档（不存在则抛出404）
    article_db = db.query(Article).filter(Article.id == article_id).first()
    if not article_db:
        raise HTTPException(
            status_code=404,
            detail=f"文档不存在（ID：{article_id}），请检查ID是否正确"
        )

    # 2. 过滤敏感字段：转换为前端可用的响应格式
    article_response = schemas.ArticleResponseSchema.from_orm(article_db).dict()

    return {
        "success": True,
        "msg": "文档详情查询成功",
        "data": article_response
    }


@router.delete("/delete/{article_id}", summary="删除文档（含文件+数据）")
def delete_article(
        article_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    彻底删除文档：
    1. 删除服务器上的原始文件和批注文件
    2. 删除数据库中的Article记录（关联的Sentence自动删除，需模型配置cascade）
    3. 若文档不存在，返回404错误
    """
    # 1. 查询文档（不存在则抛出404）
    article_db = db.query(Article).filter(Article.id == article_id).first()
    if not article_db:
        raise HTTPException(
            status_code=404,
            detail=f"文档不存在（ID：{article_id}），无需删除"
        )

    try:
        # 2. 统一用Path方法操作文件（和file_service.py风格一致）
        original_path = Path(article_db.original_path)
        annotated_path = Path(article_db.annotated_path)

        # 3. 删除服务器文件（忽略不存在的文件，避免报错）
        if original_path.exists():
            original_path.unlink()  # 替代os.remove()
        if annotated_path.exists():
            annotated_path.unlink()

        # 4. 删除数据库记录（需确保Article模型配置了cascade="all, delete-orphan"）
        db.delete(article_db)
        db.commit()

        return {
            "success": True,
            "msg": f"文档删除成功（ID：{article_id}）",
            "data": None
        }

    except Exception as e:
        # 未知错误：回滚事务，避免数据不一致
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"文档删除失败（ID：{article_id}）：{str(e)}，请重试"
        )

@router.get("/full-content/{article_id}", summary="获取完整文档内容（含句子位置，用于前端高亮）")
def get_full_article_content(
        article_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    返回完整文档文本+所有句子的详细信息（支撑前端“全文展示+违规高亮”）：
    - full_content：完整文档文本（保留段落结构，用\n换行）
    - sentences：所有句子列表（含位置、是否违规、标注内容）
    """
    # 1. 验证文档是否存在
    article_db = db.query(Article).filter(Article.id == article_id).first()
    if not article_db:
        raise HTTPException(
            status_code=404,
            detail=f"文档不存在（ID：{article_id}），请检查ID是否正确"
        )

    # 2. 读取完整文档内容（用转换后的docx文件，兼容PDF上传）
    try:
        # 注：PDF已在上传时转为docx，故用annotated_path（转后的docx路径）
        docx_path = Path(article_db.annotated_path)
        full_content = read_full_doc_content(docx_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"读取文档内容失败：{str(e)}，可能文件已被删除或损坏"
        )

    # 3. 从数据库获取该文档的所有句子（含是否违规、标注）
    db_sentences = db.query(
        Sentence.id,
        Sentence.content,
        Sentence.has_problem,
        Sentence.annotation_id,
        Annotation.content.label("annotation_content")  # 给标注内容起别名
    ).outerjoin(
        Annotation,  # 关联标注表（无标注则annotation_content为None）
        Sentence.annotation_id == Annotation.id
    ).filter(
        Sentence.article_id == article_id
    ).all()

    # 4. 构建“句子内容→数据库信息”的映射（快速匹配，避免循环）
    # 格式：{ "句子内容": { "id": 1, "has_problem": True, ... }, ... }
    sentence_db_map = {
        s.content: {
            "id": s.id,
            "has_problem": s.has_problem,
            "annotation_id": s.annotation_id,
            "annotation_content": s.annotation_content or "未标注"  # 兜底
        } for s in db_sentences
    }

    # 5. 提取句子位置，并合并数据库信息（位置+违规状态+标注）
    sentences_with_pos = extract_sentences_with_position(full_content)
    final_sentences = []
    for pos_sent in sentences_with_pos:
        sent_content = pos_sent["content"]
        # 匹配数据库信息（若匹配不到，标记为“未关联”）
        db_info = sentence_db_map.get(sent_content, {
            "id": None,
            "has_problem": None,
            "annotation_id": None,
            "annotation_content": "未关联数据库记录"
        })
        # 合并位置信息和数据库信息
        final_sentences.append({**pos_sent, **db_info})

    # 6. 返回最终数据（前端可直接用）
    return {
        "success": True,
        "msg": "完整文档内容获取成功",
        "data": {
            "article_id": article_id,
            "article_name": article_db.name,  # 文档名称（前端展示）
            "full_content": full_content,     # 完整文本（前端渲染全文）
            "sentences": final_sentences      # 句子信息（前端高亮用）
        }
    }