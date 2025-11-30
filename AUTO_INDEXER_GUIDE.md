# 自动文件索引功能指南

## 功能概述

本功能为AI助教RAG系统添加了自动文件扫描和索引更新能力，能够：

1. **自动扫描** data/ 目录下的所有支持文件
2. **检测新增或修改**的文件
3. **自动处理**新文件内容提取
4. **更新RAG索引**以包含新处理的内容
5. **元数据持久化**跟踪文件处理状态

## 自动触发

功能会在以下情况自动运行：
- **Web应用启动时**: 每次运行 `python web_app.py` 时会自动扫描和处理新文件
- **无需手动干预**: 完全自动化，用户无需手动触发

## 支持的文件类型

- **文档**: `.pdf`, `.docx`
- **演示文稿**: `.ppt`, `.pptx`
- **图像**: `.jpg`, `.jpeg`, `.png`
- **视频**: `.mp4`, `.avi`, `.mov`, `.mkv`

## 目录结构

系统会根据文件所在目录自动识别内容类型：

```
data/
├── ppt/           # 课程材料 (course_material)
├── textbook/      # 教科书内容 (textbook)
├── practice/      # 练习题库 (practice)
├── evaluation/    # 评估材料 (evaluation)
└── feedback/      # 反馈资料 (feedback)
```

## 元数据管理

### 元数据文件
- 文件名: `file_metadata.json`
- 位置: 项目根目录
- 功能: 持久化存储文件扫描和处理状态

### 文件状态
- `discovered`: 新发现但未处理的文件
- `modified`: 已修改需要重新处理的文件
- `processed`: 已成功处理的文件
- `error`: 处理失败的文件

## 使用方式

### 1. 启动时自动扫描
```bash
# 启动Web应用，自动运行文件扫描
python web_app.py
```

启动时会看到类似输出：
```
📂 File scan completed:
  New files: 3
  Modified files: 0
  Existing files: 77
  ✅ Processed 3 new files successfully
     Files: textbook/chapter1.pdf, ppt/lesson1.pptx, practice/test1.docx
```

### 2. 添加新文件
1. 将新文件放入 `data/` 目录的相应子目录中
2. 重启Web应用，系统会自动检测和处理新文件

### 3. 修改现有文件
1. 修改已有文件
2. 重启Web应用，系统会自动检测文件变化并重新处理

## 技术实现

### 核心组件

1. **FileScanner** (`src/file_scanner.py`)
   - 负责文件扫描和元数据管理
   - 计算文件哈希值检测变化
   - 持久化文件元数据

2. **AutoIndexer** (`src/file_scanner.py`)
   - 协调文件处理流程
   - 调用文件解析器处理内容
   - 更新RAG索引

3. **FileParser** (`file_import/fileimport.py`)
   - 多格式文件内容提取
   - 生成课程元数据
   - 支持OCR和语音识别

### 集成点

功能已集成到 `web_app.py` 的启动流程中：
```python
# 在 lifespan 函数中
auto_indexer = AutoIndexer()
auto_indexer.set_rag_components(index_manager, query_engine)

# 运行自动扫描和处理
auto_index_result = auto_indexer.scan_and_process()
```

## 配置说明

### 环境变量
- `DEEPSEEK_API_KEY`: 用于生成课程元数据的API密钥
- `SILICONFLOW_API_KEY`: 用于嵌入模型的API密钥

### 数据目录配置
默认扫描 `data/` 目录，可在代码中修改：
```python
scanner = FileScanner(data_dir="your_data_directory")
```

## 故障排除

### 常见问题

1. **依赖缺失**
   ```
   WARNING:root:文件解析器不可用: No module named 'whisper'
   ```
   **解决方案**: 安装缺失的依赖包
   ```bash
   pip install openai-whisper paddleocr
   ```

2. **文件处理失败**
   ```
   ❌ Failed to process 1 files
   ```
   **解决方案**: 检查文件格式是否支持，文件是否损坏

3. **索引更新失败**
   ```
   ⚠️ Auto indexing failed: ...
   ```
   **解决方案**: 检查RAG系统初始化是否正常

### 调试模式

可以通过以下方式调试：

```python
from src.file_scanner import FileScanner, AutoIndexer

# 创建扫描器
scanner = FileScanner()

# 手动扫描
scan_result = scanner.scan_all_files()
print(f"发现 {len(scan_result['new_files'])} 个新文件")

# 查看统计信息
stats = scanner.get_stats()
print(f"文件状态分布: {stats['by_status']}")
```

## 性能考虑

- **首次扫描**: 可能需要较长时间处理所有文件
- **增量扫描**: 后续只处理新文件，速度较快
- **文件哈希**: 使用MD5检测文件变化，避免重复处理
- **错误处理**: 失败的文件不会影响整体流程

## 扩展功能

未来可以考虑添加：
1. **文件监控**: 实时监控文件变化，无需重启
2. **并行处理**: 多线程处理多个文件
3. **更多文件格式**: 支持更多文档类型
4. **增量索引**: 更高效的索引更新策略

## 示例工作流

### 首次使用
1. 准备数据文件放入 `data/` 目录
2. 运行 `python web_app.py`
3. 系统自动扫描和处理所有文件
4. RAG索引创建完成
5. 可以开始查询

### 日常使用
1. 添加新课程材料到 `data/` 目录
2. 重启Web应用
3. 新材料自动处理并加入索引
4. 立即可在查询中使用新内容

## 相关文件

- `src/file_scanner.py`: 核心扫描和索引功能
- `web_app.py`: 集成点，启动时自动扫描
- `file_import/fileimport.py`: 文件解析功能
- `file_metadata.json`: 文件元数据存储