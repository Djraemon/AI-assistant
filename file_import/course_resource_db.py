import pymysql
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime


class CourseResourceDB:
    """
    大数据课程资源数据库操作类
    """

    def __init__(self, host='localhost', user='root', password='123456',
                 database='big_data_courses', charset='utf8mb4'):
        """
        初始化数据库连接
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset
            )
            self.cursor = self.conn.cursor()
            self.logger.info("数据库连接成功")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("数据库连接已关闭")

    def get_next_resource_id(self) -> int:
        """
        获取下一个资源ID（基于现有文件数量）

        Returns:
            下一个资源ID
        """
        if not self.conn:
            if not self.connect():
                return 1  # 默认从1开始

        try:
            # 获取当前最大的ID
            sql = "SELECT MAX(id) FROM course_resources"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()

            if result and result[0] is not None:
                return result[0] + 1
            else:
                return 1  # 如果表为空，从1开始

        except Exception as e:
            self.logger.error(f"获取下一个资源ID失败: {str(e)}")
            return 1  # 出错时从1开始

    def get_file_count(self) -> int:
        """
        获取数据库中的文件数量

        Returns:
            文件数量
        """
        if not self.conn:
            if not self.connect():
                return 0

        try:
            sql = "SELECT COUNT(*) FROM course_resources"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()

            return result[0] if result else 0

        except Exception as e:
            self.logger.error(f"获取文件数量失败: {str(e)}")
            return 0

    def check_file_exists(self, file_path: str) -> bool:
        """
        检查文件是否已存在于数据库中

        Args:
            file_path: 文件路径

        Returns:
            是否存在
        """
        if not self.conn:
            if not self.connect():
                return False

        try:
            sql = "SELECT COUNT(*) FROM course_resources WHERE file_path = %s"
            self.cursor.execute(sql, (file_path,))
            result = self.cursor.fetchone()

            return result[0] > 0 if result else False

        except Exception as e:
            self.logger.error(f"检查文件是否存在失败: {str(e)}")
            return False

    def _prepare_resource_data(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备资源数据，确保必需字段不为空

        Args:
            resource_data: 原始资源数据

        Returns:
            处理后的资源数据
        """
        # 确保必需字段有值
        processed_data = resource_data.copy()

        # 必需字段检查
        if not processed_data.get('file_path'):
            processed_data['file_path'] = 'unknown'

        if not processed_data.get('stored_path'):
            processed_data['stored_path'] = processed_data.get('file_path', 'unknown')

        if not processed_data.get('file_type'):
            # 尝试从文件路径推断文件类型
            file_path = processed_data.get('file_path', '')
            if file_path:
                file_extension = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
                processed_data['file_type'] = file_extension
            else:
                processed_data['file_type'] = 'unknown'

        if not processed_data.get('file_name'):
            file_path = processed_data.get('file_path', '')
            processed_data['file_name'] = file_path.split('/')[-1] if file_path else 'unknown'

        # 确保数值字段有默认值
        numeric_fields = ['file_size', 'file_size_mb', 'pages', 'slides', 'paragraphs',
                          'tables', 'image_width', 'image_height', 'duration', 'content_length']
        for field in numeric_fields:
            if field not in processed_data or processed_data[field] is None:
                processed_data[field] = 0

        # 确保字符串字段不为None
        string_fields = ['file_format', 'creation_time', 'modification_time', 'access_time',
                         'image_mode', 'duration_formatted', 'content_text', 'course_topic',
                         'core_knowledge', 'learning_objectives', 'application_scenarios',
                         'difficulty_level', 'parse_status', 'error_message']
        for field in string_fields:
            if field not in processed_data or processed_data[field] is None:
                processed_data[field] = ''

        # 处理日期时间字段 - 将空字符串转换为None
        datetime_fields = ['creation_time', 'modification_time', 'access_time']
        for field in datetime_fields:
            if field in processed_data and processed_data[field] == '':
                processed_data[field] = None

        return processed_data

    def insert_course_resource(self, resource_data: Dict[str, Any]) -> int:
        """
        插入课程资源数据

        Args:
            resource_data: 资源数据字典

        Returns:
            插入的资源ID，如果失败返回-1
        """
        if not self.conn:
            if not self.connect():
                return -1

        try:
            # 检查文件是否已存在
            file_path = resource_data.get('file_path')
            if file_path and self.check_file_exists(file_path):
                self.logger.warning(f"文件已存在，跳过插入: {file_path}")
                return -2  # 特殊代码表示文件已存在

            # 获取下一个资源ID
            resource_id = self.get_next_resource_id()

            # 准备数据，确保必需字段不为空
            processed_data = self._prepare_resource_data(resource_data)

            sql = """
            INSERT INTO course_resources (
                id, file_name, file_path, stored_path, file_type, file_format, file_size, file_size_mb,
                creation_time, modification_time, access_time, pages, slides, paragraphs,
                tables, image_width, image_height, image_mode, duration, duration_formatted,
                content_text, content_length, course_topic, core_knowledge, learning_objectives,
                application_scenarios, difficulty_level, parse_status, error_message
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            # 准备数据
            values = (
                resource_id,  # 手动指定的ID
                processed_data.get('file_name'),
                processed_data.get('file_path'),
                processed_data.get('stored_path'),
                processed_data.get('file_type'),
                processed_data.get('file_format'),
                processed_data.get('file_size'),
                processed_data.get('file_size_mb'),
                processed_data.get('creation_time'),
                processed_data.get('modification_time'),
                processed_data.get('access_time'),
                processed_data.get('pages'),
                processed_data.get('slides'),
                processed_data.get('paragraphs'),
                processed_data.get('tables'),
                processed_data.get('image_width'),
                processed_data.get('image_height'),
                processed_data.get('image_mode'),
                processed_data.get('duration'),
                processed_data.get('duration_formatted'),
                processed_data.get('content_text'),
                processed_data.get('content_length'),
                processed_data.get('course_topic'),
                processed_data.get('core_knowledge'),
                processed_data.get('learning_objectives'),
                processed_data.get('application_scenarios'),
                processed_data.get('difficulty_level'),
                processed_data.get('parse_status', 'success'),
                processed_data.get('error_message')
            )

            self.cursor.execute(sql, values)
            self.conn.commit()
            self.logger.info(f"成功插入课程资源 ID: {resource_id}, 文件名: {processed_data.get('file_name')}")
            return resource_id

        except Exception as e:
            self.logger.error(f"插入课程资源失败: {str(e)}")
            self.conn.rollback()
            return -1

    def update_course_resource(self, resource_id: int, update_data: Dict[str, Any]) -> bool:
        """
        更新课程资源数据

        Args:
            resource_id: 资源ID
            update_data: 更新数据字典

        Returns:
            更新是否成功
        """
        if not self.conn:
            if not self.connect():
                return False

        try:
            # 动态构建更新语句
            set_clause = []
            values = []

            for key, value in update_data.items():
                set_clause.append(f"{key} = %s")
                values.append(value)

            values.append(resource_id)

            sql = f"UPDATE course_resources SET {', '.join(set_clause)} WHERE id = %s"

            self.cursor.execute(sql, values)
            self.conn.commit()
            self.logger.info(f"成功更新课程资源 ID: {resource_id}")
            return True

        except Exception as e:
            self.logger.error(f"更新课程资源失败: {str(e)}")
            self.conn.rollback()
            return False

    def delete_course_resource(self, resource_id: int) -> bool:
        """
        删除课程资源

        Args:
            resource_id: 资源ID

        Returns:
            删除是否成功
        """
        if not self.conn:
            if not self.connect():
                return False

        try:
            sql = "DELETE FROM course_resources WHERE id = %s"
            self.cursor.execute(sql, (resource_id,))
            self.conn.commit()
            self.logger.info(f"成功删除课程资源 ID: {resource_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除课程资源失败: {str(e)}")
            self.conn.rollback()
            return False

    def get_course_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个课程资源

        Args:
            resource_id: 资源ID

        Returns:
            资源数据字典
        """
        if not self.conn:
            if not self.connect():
                return None

        try:
            sql = "SELECT * FROM course_resources WHERE id = %s"
            self.cursor.execute(sql, (resource_id,))
            result = self.cursor.fetchone()

            if result:
                # 将结果转换为字典
                columns = [col[0] for col in self.cursor.description]
                return dict(zip(columns, result))
            return None

        except Exception as e:
            self.logger.error(f"获取课程资源失败: {str(e)}")
            return None

    def get_all_course_resources(self, file_type: str = None) -> List[Dict[str, Any]]:
        """
        获取所有课程资源

        Args:
            file_type: 文件类型过滤

        Returns:
            资源数据列表
        """
        if not self.conn:
            if not self.connect():
                return []

        try:
            if file_type:
                sql = "SELECT * FROM course_resources WHERE file_type = %s ORDER BY id ASC"
                self.cursor.execute(sql, (file_type,))
            else:
                sql = "SELECT * FROM course_resources ORDER BY id ASC"
                self.cursor.execute(sql)

            results = self.cursor.fetchall()
            resources = []

            if results:
                columns = [col[0] for col in self.cursor.description]
                for result in results:
                    resources.append(dict(zip(columns, result)))

            return resources

        except Exception as e:
            self.logger.error(f"获取课程资源列表失败: {str(e)}")
            return []

    def get_resource_stats(self) -> Dict[str, Any]:
        """
        获取资源统计信息

        Returns:
            统计信息字典
        """
        if not self.conn:
            if not self.connect():
                return {}

        try:
            stats = {}

            # 按文件类型统计
            sql = """
            SELECT file_type, COUNT(*) as count, 
                   AVG(file_size_mb) as avg_size_mb,
                   SUM(content_length) as total_content_length
            FROM course_resources 
            WHERE parse_status = 'success'
            GROUP BY file_type
            """
            self.cursor.execute(sql)
            stats['by_file_type'] = self.cursor.fetchall()

            # 总体统计
            sql = """
            SELECT COUNT(*) as total_files,
                   SUM(file_size) as total_size_bytes,
                   AVG(content_length) as avg_content_length,
                   COUNT(DISTINCT file_type) as file_types_count,
                   MAX(id) as max_id
            FROM course_resources 
            WHERE parse_status = 'success'
            """
            self.cursor.execute(sql)
            stats['overall'] = self.cursor.fetchone()

            return stats

        except Exception as e:
            self.logger.error(f"获取资源统计失败: {str(e)}")
            return {}