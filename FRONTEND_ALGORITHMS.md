# 前端核心算法文档

本文档详细说明首页、文件查询、文件详情页等前端逻辑的核心算法，特别是**高亮**和**定位**的实现机制。

---

## 一、高亮算法核心 🎯

### 1.1 算法位置
- **文件**: `src/views/ReviewPage.vue`
- **函数**: `getHighlightedContent()` (第686-727行)

### 1.2 算法原理

#### **核心思路**：基于字符位置索引的精确定位 + 字符串拼接插入高亮标签

```typescript
// 核心算法流程
const getHighlightedContent = () => {
  // 1. 精确匹配：在句子列表中查找目标句子
  let sentenceInfo = allSentences.value.find(s => s.content === highlightedSentence.value);
  
  // 2. 模糊匹配（容错处理）
  if (!sentenceInfo) {
    const trimmedHighlighted = highlightedSentence.value.trim();
    sentenceInfo = allSentences.value.find(s => s.content.trim() === trimmedHighlighted);
  }
  
  // 3. 包含匹配（兜底方案）
  if (!sentenceInfo) {
    sentenceInfo = allSentences.value.find(s => 
      s.content.includes(trimmedHighlighted) || trimmedHighlighted.includes(s.content.trim())
    );
  }
  
  // 4. 使用位置索引精确插入高亮标签
  if (sentenceInfo) {
    const before = documentContent.value.substring(0, sentenceInfo.start_pos);
    const highlighted = `<mark class="highlight-sentence">${sentenceInfo.content}</mark>`;
    const after = documentContent.value.substring(sentenceInfo.end_pos);
    return before + highlighted + after;
  }
  
  // 5. 正则表达式备选方案（如果找不到位置信息）
  const escapedSentence = highlightedSentence.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const highlightedContent = documentContent.value.replace(
    new RegExp(escapedSentence, 'g'),
    `<mark class="highlight-sentence">${highlightedSentence.value}</mark>`
  );
  
  return highlightedContent;
};
```

### 1.3 关键数据结构

```typescript
// 句子位置信息（从后端获取）
interface SentenceInfo {
  content: string;        // 句子内容
  start_pos: number;      // 在文档中的起始字符位置
  end_pos: number;        // 在文档中的结束字符位置
  id: number | null;
  has_problem: boolean | null;
  annotation_id: number | null;
  annotation_content: string;
}
```

### 1.4 匹配策略（三级容错）

1. **精确匹配**：`content === highlightedSentence.value`
2. **模糊匹配**：去除首尾空格后比较 `trim() === trim()`
3. **包含匹配**：双向包含检查 `includes()` 或 `includes()`

### 1.5 高亮样式

```css
:deep(.highlight-sentence) {
  background-color: #fef3c7;      /* 黄色背景 */
  color: #92410e;                  /* 深棕色文字 */
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 600;
  box-shadow: 0 0 0 2px #f59e0b;  /* 外发光效果 */
  animation: highlight-pulse 0.3s ease-in-out;  /* 脉冲动画 */
}
```

---

## 二、定位算法核心 📍

### 2.1 算法位置
- **文件**: `src/views/ReviewPage.vue`
- **函数**: `scrollToHighlightedSentence()` (第650-684行)

### 2.2 算法原理

#### **核心思路**：DOM查询 + 浏览器原生滚动API

```typescript
const scrollToHighlightedSentence = () => {
  if (!documentContainer.value || !highlightedSentence.value) {
    return;
  }
  
  // 等待 DOM 更新完成（Vue 响应式更新）
  setTimeout(() => {
    // 策略1：直接查找高亮的 mark 元素（最精确）
    const highlightedElement = documentContainer.value?.querySelector('.highlight-sentence');
    if (highlightedElement) {
      highlightedElement.scrollIntoView({
        behavior: 'smooth',      // 平滑滚动
        block: 'center',          // 垂直居中
        inline: 'nearest'         // 水平最近位置
      });
      return;
    }
    
    // 策略2：遍历所有元素，查找包含目标文本的元素（兜底方案）
    const textNodes = documentContainer.value?.querySelectorAll('*');
    if (textNodes) {
      for (const node of textNodes) {
        if (node.textContent?.includes(highlightedSentence.value)) {
          node.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          });
          break;
        }
      }
    }
  }, 100); // 给 DOM 更新一些时间
};
```

### 2.3 定位策略

1. **优先策略**：通过 CSS 类名 `.highlight-sentence` 直接查找
2. **兜底策略**：遍历所有 DOM 节点，通过 `textContent.includes()` 查找

### 2.4 滚动参数说明

```typescript
scrollIntoView({
  behavior: 'smooth',  // 滚动行为：'auto' | 'smooth'
  block: 'center',     // 垂直对齐：'start' | 'center' | 'end' | 'nearest'
  inline: 'nearest'    // 水平对齐：'start' | 'center' | 'end' | 'nearest'
})
```

### 2.5 触发时机

```typescript
// 鼠标悬停违规句子时触发
const highlightSentence = (sentence: string) => {
  highlightedSentence.value = sentence;
  
  // 等待 DOM 更新后自动滚动
  nextTick(() => {
    scrollToHighlightedSentence();
  });
};
```

---

## 三、后端句子位置提取算法 🔧

### 3.1 算法位置
- **文件**: `backend/app/services/file_service.py`
- **函数**: `extract_sentences_with_position()` (第127-169行)

### 3.2 算法原理

#### **核心思路**：正则表达式匹配句末标点 + 记录字符索引

```python
def extract_sentences_with_position(full_content: str) -> list[dict]:
    """
    从完整文本中提取句子，并记录每个句子的「起始索引」和「结束索引」
    返回格式：[{"content": "句子内容", "start_idx": 0, "end_idx": 15}, ...]
    """
    sentences = []
    current_pos = 0
    text_length = len(full_content)
    
    # 正则匹配句末标点（支持。！？；，覆盖常见中文标点）
    sentence_pattern = re.compile(r'[^。！？；，]*[。！？；，]')
    matches = sentence_pattern.finditer(full_content)
    
    for match in matches:
        sentence_text = match.group().strip()
        if not sentence_text:
            current_pos = match.end()
            continue
        
        # 记录句子在完整文本中的起始/结束索引
        start_idx = match.start()
        end_idx = match.end()
        
        sentences.append({
            "content": sentence_text,
            "start_idx": start_idx,
            "end_idx": end_idx
        })
        
        current_pos = end_idx
    
    # 处理最后一个没有标点的句子（如文本末尾的短句）
    if current_pos < text_length:
        remaining_text = full_content[current_pos:].strip()
        if remaining_text:
            sentences.append({
                "content": remaining_text,
                "start_idx": current_pos,
                "end_idx": text_length
            })
    
    return sentences
```

### 3.3 正则表达式说明

```python
r'[^。！？；，]*[。！？；，]'
```

- `[^。！？；，]*`：匹配任意数量的非句末标点字符
- `[。！？；，]`：匹配一个句末标点字符
- **作用**：匹配从上一个句末标点到当前句末标点的完整句子

### 3.4 算法特点

1. **精确索引**：使用 `match.start()` 和 `match.end()` 记录字符位置
2. **容错处理**：处理文本末尾没有标点的句子
3. **支持中文**：专门针对中文标点符号设计

---

## 四、文件查询算法 🔍

### 4.1 前端搜索算法

#### **位置**: `src/components/FileList.vue`

#### **核心算法**：防抖（Debounce）+ 服务端搜索

```typescript
// 搜索防抖定时器
let searchTimeout: NodeJS.Timeout | null = null;

// 实时搜索输入处理（防抖）
const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  // 防抖延迟500ms
  searchTimeout = setTimeout(() => {
    if (searchKeyword.value.trim()) {
      handleSearch();
    } else {
      // 如果搜索框为空，重置到第一页并刷新
      page.value = 1;
      fetchFileList();
    }
  }, 500);
};

// 搜索文件
const handleSearch = () => {
  // 验证搜索关键词
  const keywordValidation = validateSearchKeyword(searchKeyword.value);
  if (!keywordValidation.valid) {
    ElMessage.error(keywordValidation.message || '搜索关键词无效');
    return;
  }
  
  page.value = 1; // 搜索时重置到第1页
  fetchFileList();
};
```

### 4.2 后端搜索算法

#### **位置**: `backend/app/api/endpoints/files.py`

#### **核心算法**：SQL LIKE 模糊匹配

```python
@router.get("/list", summary="获取文档列表（分页+关键词搜索）")
def get_article_list(
    db: Session = Depends(get_db),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配文件名）")
) -> Dict[str, Any]:
    # 1. 构建查询条件（基础查询+关键词过滤）
    query = db.query(Article)
    if keyword and keyword.strip():
        # 关键词非空：模糊匹配文件名（不区分大小写）
        query = query.filter(Article.name.ilike(f"%{keyword.strip()}%"))
    
    # 2. 计算分页参数+执行查询
    total = query.count()  # 总文档数
    skip = (page - 1) * page_size  # 跳过的记录数
    articles_db = query.order_by(Article.upload_time.desc()).offset(skip).limit(page_size).all()
    
    # 3. 返回结果
    return {
        "success": True,
        "data": {
            "list": articles_response,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    }
```

### 4.3 搜索算法特点

1. **防抖优化**：500ms 延迟，减少不必要的 API 请求
2. **服务端搜索**：使用数据库 LIKE 查询，性能更好
3. **分页集成**：搜索时自动重置到第1页
4. **参数验证**：前后端都有参数验证

---

## 五、首页列表展示算法 📋

### 5.1 算法位置
- **文件**: `src/views/Home.vue`

### 5.2 算法原理

#### **核心思路**：计算属性过滤 + 限制显示数量

```typescript
// 待审查文件：不限制数量
const pendingArticles = computed<Article[]>(() => {
  return articles.value.filter(article => article.status === '待审查')
})

// 已审查文件：限制显示前2个
const reviewedArticles = computed<Article[]>(() => {
  return articles.value.filter(article => article.status === '已审查').slice(0, 2)
})
```

### 5.3 自动刷新机制

```typescript
onMounted(() => {
  fetchArticles()
  // 定时刷新：每300秒（5分钟）刷新一次
  listRefreshInterval.value = setInterval(() => {
    fetchArticles()
  }, 300000)
})
```

---

## 六、算法流程图 🎨

### 6.1 高亮流程

```
用户悬停违规句子
    ↓
highlightSentence(sentence)
    ↓
设置 highlightedSentence.value
    ↓
触发 getHighlightedContent() 计算属性
    ↓
三级匹配策略：
    1. 精确匹配
    2. 模糊匹配（trim）
    3. 包含匹配
    ↓
使用 start_pos 和 end_pos 插入 <mark> 标签
    ↓
渲染到 DOM
    ↓
nextTick 后触发 scrollToHighlightedSentence()
    ↓
查找 .highlight-sentence 元素
    ↓
scrollIntoView({ behavior: 'smooth', block: 'center' })
```

### 6.2 搜索流程

```
用户输入搜索关键词
    ↓
handleSearchInput() 触发
    ↓
清除旧定时器，设置新定时器（500ms 防抖）
    ↓
500ms 后执行 handleSearch()
    ↓
验证搜索关键词
    ↓
重置页码为1
    ↓
调用 fetchFileList()
    ↓
发送 API 请求（带 keyword 参数）
    ↓
后端 SQL LIKE 查询
    ↓
返回搜索结果
    ↓
更新 fileList 和 total
```

---

## 七、性能优化点 ⚡

### 7.1 高亮优化

1. **位置索引缓存**：使用 `start_pos` 和 `end_pos` 避免重复字符串匹配
2. **三级容错**：减少匹配失败的次数
3. **DOM 更新延迟**：使用 `setTimeout(100ms)` 等待 Vue 响应式更新

### 7.2 搜索优化

1. **防抖机制**：500ms 延迟，减少 API 请求
2. **服务端搜索**：利用数据库索引，性能优于前端过滤
3. **分页查询**：只返回当前页数据，减少数据传输

### 7.3 滚动优化

1. **优先策略**：直接查找 `.highlight-sentence` 类，避免遍历
2. **平滑滚动**：使用 `behavior: 'smooth'` 提升用户体验
3. **居中显示**：`block: 'center'` 确保高亮内容在视口中央

---

## 八、关键代码片段 📝

### 8.1 高亮核心代码

```typescript
// src/views/ReviewPage.vue:686-727
const getHighlightedContent = () => {
  if (!documentContent.value || !highlightedSentence.value) {
    return documentContent.value || '';
  }
  
  // 三级匹配策略
  let sentenceInfo = allSentences.value.find(s => s.content === highlightedSentence.value);
  if (!sentenceInfo) {
    const trimmedHighlighted = highlightedSentence.value.trim();
    sentenceInfo = allSentences.value.find(s => s.content.trim() === trimmedHighlighted);
  }
  if (!sentenceInfo) {
    const trimmedHighlighted = highlightedSentence.value.trim();
    sentenceInfo = allSentences.value.find(s => 
      s.content.includes(trimmedHighlighted) || trimmedHighlighted.includes(s.content.trim())
    );
  }
  
  // 使用位置索引精确插入
  if (sentenceInfo) {
    const before = documentContent.value.substring(0, sentenceInfo.start_pos);
    const highlighted = `<mark class="highlight-sentence">${sentenceInfo.content}</mark>`;
    const after = documentContent.value.substring(sentenceInfo.end_pos);
    return before + highlighted + after;
  }
  
  // 正则表达式备选方案
  const escapedSentence = highlightedSentence.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return documentContent.value.replace(
    new RegExp(escapedSentence, 'g'),
    `<mark class="highlight-sentence">${highlightedSentence.value}</mark>`
  );
};
```

### 8.2 定位核心代码

```typescript
// src/views/ReviewPage.vue:650-684
const scrollToHighlightedSentence = () => {
  if (!documentContainer.value || !highlightedSentence.value) {
    return;
  }
  
  setTimeout(() => {
    const highlightedElement = documentContainer.value?.querySelector('.highlight-sentence');
    if (highlightedElement) {
      highlightedElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    } else {
      const textNodes = documentContainer.value?.querySelectorAll('*');
      if (textNodes) {
        for (const node of textNodes) {
          if (node.textContent?.includes(highlightedSentence.value)) {
            node.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
              inline: 'nearest'
            });
            break;
          }
        }
      }
    }
  }, 100);
};
```

### 8.3 后端句子提取核心代码

```python
# backend/app/services/file_service.py:127-169
def extract_sentences_with_position(full_content: str) -> list[dict]:
    sentences = []
    current_pos = 0
    text_length = len(full_content)
    
    sentence_pattern = re.compile(r'[^。！？；，]*[。！？；，]')
    matches = sentence_pattern.finditer(full_content)
    
    for match in matches:
        sentence_text = match.group().strip()
        if not sentence_text:
            current_pos = match.end()
            continue
        
        sentences.append({
            "content": sentence_text,
            "start_idx": match.start(),
            "end_idx": match.end()
        })
        
        current_pos = match.end()
    
    if current_pos < text_length:
        remaining_text = full_content[current_pos:].strip()
        if remaining_text:
            sentences.append({
                "content": remaining_text,
                "start_idx": current_pos,
                "end_idx": text_length
            })
    
    return sentences
```

---

## 九、总结 📊

### 9.1 核心算法特点

1. **高亮算法**：
   - ✅ 基于字符位置索引，精确高效
   - ✅ 三级容错匹配，提高成功率
   - ✅ 字符串拼接插入，性能优秀

2. **定位算法**：
   - ✅ 使用浏览器原生 API，性能好
   - ✅ 双重查找策略，提高成功率
   - ✅ 平滑滚动，用户体验佳

3. **搜索算法**：
   - ✅ 防抖机制，减少请求
   - ✅ 服务端搜索，性能优秀
   - ✅ 分页集成，减少数据传输

### 9.2 技术亮点

- 🎯 **精确索引定位**：后端提取句子时记录字符位置，前端直接使用，无需重复计算
- 🎯 **三级容错匹配**：精确匹配 → 模糊匹配 → 包含匹配，确保高亮成功率
- 🎯 **防抖优化**：搜索输入防抖500ms，减少不必要的API请求
- 🎯 **平滑滚动**：使用 `scrollIntoView` API，提供流畅的用户体验

---

## 十、相关文件索引 📁

- **高亮算法**: `src/views/ReviewPage.vue` (第686-727行)
- **定位算法**: `src/views/ReviewPage.vue` (第650-684行)
- **句子提取**: `backend/app/services/file_service.py` (第127-169行)
- **搜索算法**: `src/components/FileList.vue` (第179-195行)
- **后端搜索**: `backend/app/api/endpoints/files.py` (第89-132行)
- **首页列表**: `src/views/Home.vue` (第331-336行)

