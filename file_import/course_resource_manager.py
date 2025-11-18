import os
import logging
import shutil
from typing import Dict, Any
from fileimport import FileParser
from course_resource_db import CourseResourceDB


class CourseResourceManager:
    """
    大数据课程资源管理器
    整合文件解析、数据库存储和文件管理功能
    """

    def __init__(self, deepseek_api_key: str = None, db_config: Dict[str, Any] = None,
                 resources_base_dir: str = "resources"):
        """
        初始化资源管理器
        """
        self.logger = logging.getLogger(__name__)

        # 初始化文件解析器
        self.file_parser = FileParser(deepseek_api_key=deepseek_api_key)

        # 初始化数据库连接
        default_db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'big_data_courses'
        }
        if db_config:
            default_db_config.update(db_config)

        self.db = CourseResourceDB(**default_db_config)

        # 设置资源存储目录
        self.resources_base_dir = resources_base_dir
        self._ensure_resources_directory()

        # 获取当前文件数量统计
        self.file_count = self.db.get_file_count()
        self.logger.info(f"数据库当前文件数量: {self.file_count}")
        self.logger.info(f"资源文件存储目录: {os.path.abspath(self.resources_base_dir)}")

    def _ensure_resources_directory(self):
        """
        确保资源存储目录存在
        """
        try:
            if not os.path.exists(self.resources_base_dir):
                os.makedirs(self.resources_base_dir)
                self.logger.info(f"创建资源存储目录: {self.resources_base_dir}")

        except Exception as e:
            self.logger.error(f"创建资源目录失败: {str(e)}")
            raise

    def _get_file_extension(self, file_path: str) -> str:
        """
        获取文件后缀名（不带点）

        Args:
            file_path: 文件路径

        Returns:
            文件后缀名
        """
        try:
            # 获取文件扩展名并转换为小写，去掉点号
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension.startswith('.'):
                return file_extension[1:]  # 去掉点号
            return file_extension
        except:
            return 'unknown'

    def _store_resource_file(self, file_path: str) -> str:
        """
        存储资源文件到本地目录，按照 resources/文件后缀名/文件名 的结构

        Args:
            file_path: 原始文件路径

        Returns:
            存储后的文件路径
        """
        try:
            # 获取文件名和文件后缀
            file_name = os.path.basename(file_path)
            file_extension = self._get_file_extension(file_path)

            # 创建文件后缀目录
            extension_dir = os.path.join(self.resources_base_dir, file_extension)
            if not os.path.exists(extension_dir):
                os.makedirs(extension_dir)
                self.logger.info(f"创建文件后缀目录: {extension_dir}")

            # 目标文件路径
            target_path = os.path.join(extension_dir, file_name)

            # 如果目标文件已存在，添加序号
            counter = 1
            original_target = target_path
            while os.path.exists(target_path):
                name, ext = os.path.splitext(file_name)
                target_path = os.path.join(extension_dir, f"{name}_{counter}{ext}")
                counter += 1

            # 复制文件
            shutil.copy2(file_path, target_path)
            self.logger.info(f"资源文件已存储: {file_path} -> {target_path}")

            return target_path

        except Exception as e:
            self.logger.error(f"存储资源文件失败: {str(e)}")
            raise

    def _prepare_db_data(self, file_path: str, stored_path: str, metadata_result: Dict[str, Any],
                         updated_data: Dict[str, Any], generate_course_metadata: bool) -> Dict[str, Any]:
        """
        准备数据库插入数据

        Args:
            file_path: 原始文件路径
            stored_path: 存储后的文件路径
            metadata_result: 元数据结果
            updated_data: 更新后的数据
            generate_course_metadata: 是否生成课程元数据

        Returns:
            数据库数据字典
        """
        # 基础数据
        db_data = {
            'file_path': file_path,
            'stored_path': stored_path,  # 存储后的文件路径
            'file_name': os.path.basename(file_path),
        }

        # 添加基本元数据
        if metadata_result.get('status') == 'success' and 'metadata' in metadata_result:
            metadata = metadata_result['metadata']
            db_data.update({
                'file_type': metadata.get('file_type', ''),
                'file_format': metadata.get('file_format', ''),
                'file_size': metadata.get('file_size', 0),
                'file_size_mb': metadata.get('file_size_mb', 0),
                'creation_time': metadata.get('creation_time', ''),
                'modification_time': metadata.get('modification_time', ''),
                'access_time': metadata.get('access_time', ''),
            })

        # 添加特定文件类型元数据
        specific_metadata = updated_data.get('metadata', {})
        db_data.update({
            'pages': specific_metadata.get('pages', 0),
            'slides': specific_metadata.get('slides', 0),
            'paragraphs': specific_metadata.get('paragraphs', 0),
            'tables': specific_metadata.get('tables', 0),
            'image_width': specific_metadata.get('image_width', 0),
            'image_height': specific_metadata.get('image_height', 0),
            'image_mode': specific_metadata.get('image_mode', ''),
            'duration': specific_metadata.get('duration', 0),
            'duration_formatted': specific_metadata.get('duration_formatted', ''),
        })

        # 添加内容数据
        db_data.update({
            'content_text': updated_data.get('content_text', ''),
            'content_length': len(updated_data.get('content_text', '')),
        })

        # 添加课程元数据 - 确保所有课程元数据字段都被包含
        if generate_course_metadata:
            course_meta = updated_data.get('course_metadata', {})
            db_data.update({
                'course_topic': course_meta.get('course_topic', ''),
                'core_knowledge': course_meta.get('core_knowledge', ''),
                'learning_objectives': course_meta.get('learning_objectives', ''),
                'application_scenarios': course_meta.get('application_scenarios', ''),
                'difficulty_level': course_meta.get('difficulty_level', ''),
            })
        else:
            # 即使不生成课程元数据，也要确保这些字段存在
            db_data.update({
                'course_topic': '',
                'core_knowledge': '',
                'learning_objectives': '',
                'application_scenarios': '',
                'difficulty_level': '',
            })

        db_data['parse_status'] = 'success'

        return db_data

    def process_course_file(self, file_path: str, generate_course_metadata: bool = True,
                            store_file: bool = True) -> Dict[str, Any]:
        """
        处理课程文件：解析内容、存储文件并存入数据库

        Args:
            file_path: 文件路径
            generate_course_metadata: 是否生成课程元数据（默认为True）
            store_file: 是否存储文件到资源目录

        Returns:
            处理结果字典
        """
        result = {
            'file_path': file_path,
            'stored_path': None,
            'success': False,
            'message': '',
            'resource_id': None,
            'course_metadata_generated': generate_course_metadata
        }

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 1. 获取文件元数据
            metadata_result = self.file_parser.get_file_metadata_only(file_path)
            if metadata_result['status'] != 'success':
                raise ValueError(f"获取文件元数据失败: {metadata_result.get('error_message', '未知错误')}")

            # 2. 存储文件到资源目录
            stored_path = file_path  # 默认使用原始路径
            if store_file:
                stored_path = self._store_resource_file(file_path)
                result['stored_path'] = stored_path

            # 3. 提取文件内容
            sample_data = {
                'file_path': file_path,
                'file_type': metadata_result['metadata']['file_type'],
                'content_text': ''
            }

            updated_data = self.file_parser.update_content_field(
                sample_data,
                generate_course_metadata=generate_course_metadata
            )

            if updated_data['parse_status'] != 'success':
                raise ValueError(f"文件内容解析失败: {updated_data.get('error', '未知错误')}")

            # 4. 准备数据库插入数据
            db_data = self._prepare_db_data(file_path, stored_path, metadata_result, updated_data,
                                            generate_course_metadata)

            # 5. 插入数据库
            resource_id = self.db.insert_course_resource(db_data)

            if resource_id > 0:
                result['success'] = True
                result['message'] = '文件处理并存储成功'
                result['resource_id'] = resource_id
                # 添加课程元数据到结果中
                if generate_course_metadata:
                    result['course_metadata'] = updated_data.get('course_metadata', {})
                self.file_count += 1  # 更新文件计数
            elif resource_id == -2:
                result['message'] = '文件已存在，跳过处理'
            else:
                raise ValueError("数据库插入失败")

        except Exception as e:
            result['success'] = False
            result['message'] = str(e)
            self.logger.error(f"处理课程文件失败: {str(e)}")

            # 记录错误到数据库
            try:
                error_data = {
                    'file_path': file_path,
                    'stored_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_type': self._get_file_extension(file_path),
                    'parse_status': 'error',
                    'error_message': str(e),
                    # 确保所有课程元数据字段都有默认值
                    'course_topic': '',
                    'core_knowledge': '',
                    'learning_objectives': '',
                    'application_scenarios': '',
                    'difficulty_level': ''
                }
                self.db.insert_course_resource(error_data)
            except Exception as db_error:
                self.logger.error(f"记录错误信息到数据库失败: {str(db_error)}")

        return result

    def _get_file_type_from_path(self, file_path: str) -> str:
        """
        从文件路径获取文件类型
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            return file_extension[1:] if file_extension.startswith('.') else file_extension
        except:
            return 'unknown'

    def get_file_count(self) -> int:
        """
        获取当前文件数量

        Returns:
            文件数量
        """
        return self.file_count

    def get_next_resource_id(self) -> int:
        """
        获取下一个资源ID

        Returns:
            下一个资源ID
        """
        return self.db.get_next_resource_id()

    def get_resource_directory_structure(self) -> Dict[str, Any]:
        """
        获取资源目录结构信息

        Returns:
            目录结构信息
        """
        structure = {
            'base_directory': os.path.abspath(self.resources_base_dir),
            'subdirectories': {},
            'total_files': 0
        }

        try:
            for item in os.listdir(self.resources_base_dir):
                item_path = os.path.join(self.resources_base_dir, item)
                if os.path.isdir(item_path):
                    files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))]
                    structure['subdirectories'][item] = {
                        'path': item_path,
                        'file_count': len(files),
                        'files': files
                    }
                    structure['total_files'] += len(files)

        except Exception as e:
            self.logger.error(f"获取资源目录结构失败: {str(e)}")

        return structure

    def process_directory(self, directory_path: str, generate_course_metadata: bool = True,
                          store_files: bool = True) -> Dict[str, Any]:
        """
        处理目录中的所有支持的文件

        Args:
            directory_path: 目录路径
            generate_course_metadata: 是否生成课程元数据（默认为True）
            store_files: 是否存储文件到资源目录

        Returns:
            处理结果统计
        """
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': [],
            'start_file_count': self.file_count,
            'end_file_count': self.file_count
        }

        try:
            supported_extensions = ['.pdf', '.ppt', '.pptx', '.docx', '.mp4', '.avi', '.mov', '.mkv', '.jpg', '.jpeg',
                                    '.png']

            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)

                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(filename)[1].lower()

                    if file_ext in supported_extensions:
                        results['total_files'] += 1

                        file_result = self.process_course_file(
                            file_path,
                            generate_course_metadata=generate_course_metadata,
                            store_file=store_files
                        )
                        results['details'].append(file_result)

                        if file_result['success']:
                            results['successful'] += 1
                        elif file_result.get('message', '').startswith('文件已存在'):
                            results['skipped'] += 1
                        else:
                            results['failed'] += 1

                        self.logger.info(f"处理文件: {filename} - {file_result['message']}")

            results['end_file_count'] = self.file_count

        except Exception as e:
            self.logger.error(f"处理目录失败: {str(e)}")

        return results

    def get_resource_statistics(self) -> Dict[str, Any]:
        """
        获取资源统计信息

        Returns:
            统计信息
        """
        return self.db.get_resource_stats()

    def close(self):
        """关闭资源"""
        if self.db:
            self.db.disconnect()


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 初始化资源管理器
    manager = CourseResourceManager(
        deepseek_api_key="sk-0e7d09c913e6426dbf7e55450b67daa5",  # 替换为你的API密钥
        db_config={
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'big_data_courses'
        },
        resources_base_dir="resources"  # 资源文件存储目录
    )

    try:
        # 显示当前状态
        print(f"当前数据库文件数量: {manager.get_file_count()}")
        print(f"下一个资源ID: {manager.get_next_resource_id()}")

        # 显示资源目录结构
        dir_structure = manager.get_resource_directory_structure()
        print(f"资源目录结构: {dir_structure}")

        print("\n" + "=" * 50 + "\n")

        # 示例1: 处理单个文件（默认会生成课程元数据）
        print("处理单个文件示例:")
        result = manager.process_course_file('3-1-cn.docx')  # 替换为实际文件路径
        print(f"处理结果: {result}")

        # 显示课程元数据
        if result.get('course_metadata'):
            print("生成的课程元数据:")
            for key, value in result['course_metadata'].items():
                print(f"  {key}: {value}")

        print("\n" + "=" * 50 + "\n")

        # 示例2: 获取统计信息
        print("资源统计信息:")
        stats = manager.get_resource_statistics()
        print(f"统计信息: {stats}")

    finally:
        manager.close()