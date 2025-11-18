CREATE TABLE IF NOT EXISTS course_resources (
    -- 主键和标识字段
    id INT NOT NULL PRIMARY KEY,

    -- 文件基本信息
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL COMMENT '原始文件路径',
    stored_path VARCHAR(500) NOT NULL DEFAULT '' COMMENT '存储后的文件路径',
    file_type VARCHAR(50) NOT NULL,
    file_format VARCHAR(20) DEFAULT '',

    -- 文件大小信息
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    file_size_mb DECIMAL(10,2) DEFAULT 0 COMMENT '文件大小(MB)',

    -- 时间信息
    creation_time DATETIME NULL,
    modification_time DATETIME NULL,
    access_time DATETIME NULL,

    -- 特定文件类型元数据
    pages INT DEFAULT 0 COMMENT 'PDF页数',
    slides INT DEFAULT 0 COMMENT 'PPT幻灯片数',
    paragraphs INT DEFAULT 0 COMMENT 'DOCX段落数',
    tables INT DEFAULT 0 COMMENT 'DOCX表格数',
    image_width INT DEFAULT 0 COMMENT '图片宽度',
    image_height INT DEFAULT 0 COMMENT '图片高度',
    image_mode VARCHAR(20) DEFAULT '' COMMENT '图片色彩模式',
    duration FLOAT DEFAULT 0 COMMENT '视频时长(秒)',
    duration_formatted VARCHAR(20) DEFAULT '' COMMENT '格式化视频时长',

    -- 内容数据
    content_text LONGTEXT COMMENT '提取的文本内容',
    content_length INT DEFAULT 0 COMMENT '内容长度',

    -- 课程分析元数据
    course_topic TEXT COMMENT '课程主题概括',
    core_knowledge TEXT COMMENT '核心知识点',
    learning_objectives TEXT COMMENT '学习目标',
    application_scenarios TEXT COMMENT '实际应用场景',
    difficulty_level VARCHAR(100) DEFAULT '' COMMENT '难度级别评估',

    -- 处理状态
    parse_status VARCHAR(20) DEFAULT 'pending' COMMENT '解析状态: pending, success, error',
    error_message TEXT COMMENT '错误信息',
    processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '处理时间',

    -- 索引
    INDEX idx_file_type (file_type),
    INDEX idx_file_size (file_size),
    INDEX idx_parse_status (parse_status),
    INDEX idx_processed_time (processed_time),
    INDEX idx_file_name (file_name),
    INDEX idx_difficulty (difficulty_level)
) COMMENT='大数据课程资源表';

-- 创建文件类型统计视图
CREATE OR REPLACE VIEW course_resource_stats AS
SELECT
    file_type,
    COUNT(*) as file_count,
    AVG(file_size_mb) as avg_file_size_mb,
    SUM(content_length) as total_content_length,
    MIN(processed_time) as first_processed,
    MAX(processed_time) as last_processed
FROM course_resources
WHERE parse_status = 'success'
GROUP BY file_type;

-- 创建难度级别统计视图
CREATE OR REPLACE VIEW difficulty_stats AS
SELECT
    difficulty_level,
    COUNT(*) as resource_count,
    AVG(content_length) as avg_content_length
FROM course_resources
WHERE parse_status = 'success' AND difficulty_level IS NOT NULL AND difficulty_level != ''
GROUP BY difficulty_level;

-- 创建存储过程：获取下一个资源ID
DELIMITER //
CREATE PROCEDURE GetNextResourceId(OUT next_id INT)
BEGIN
    SELECT COALESCE(MAX(id), 0) + 1 INTO next_id FROM course_resources;
END //
DELIMITER ;

-- 创建存储过程：更新资源统计信息
DELIMITER //
CREATE PROCEDURE UpdateResourceStats()
BEGIN
    -- 这里可以添加统计信息更新逻辑
    SELECT '资源统计信息已更新' AS result;
END //
DELIMITER ;