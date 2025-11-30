"""
文件监控和自动索引更新模块
File scanner and auto indexer module for monitoring data directory and updating RAG index
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from llama_index.core import Document

# 导入现有的模块
from src.config import CONFIG

# 可选导入文件解析器
try:
    from file_import.fileimport import FileParser
    FILE_PARSER_AVAILABLE = True
except ImportError as e:
    FILE_PARSER_AVAILABLE = False
    logging.warning(f"文件解析器不可用: {e}")


class FileScanner:
    """文件扫描器，负责扫描和管理data目录下的文件元数据"""

    def __init__(self, data_dir: str = "data", metadata_file: str = "file_metadata.json"):
        self.data_dir = Path(data_dir)
        self.metadata_file = metadata_file
        self.logger = logging.getLogger(__name__)

        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)

        # 支持的文件扩展名
        self.supported_extensions = {'.pdf', '.ppt', '.pptx', '.docx', '.mp4', '.avi', '.mov', '.mkv', '.jpg', '.jpeg', '.png'}

        # 初始化文件解析器（延迟加载，处理可能的依赖问题）
        self.file_parser = None
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "sk-0e7d09c913e6426dbf7e55450b67daa5")

        # 加载已有文件元数据
        self.file_metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """从文件加载已有元数据"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载文件元数据失败: {e}")

        return {}

    def _save_metadata(self):
        """保存文件元数据到磁盘"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_metadata, f, ensure_ascii=False, indent=2)
            self.logger.info(f"文件元数据已保存到 {self.metadata_file}")
        except Exception as e:
            self.logger.error(f"保存文件元数据失败: {e}")

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值，用于检测文件修改"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # 分块读取大文件
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件基本信息"""
        try:
            stat = file_path.stat()
            return {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_path.suffix.lower(),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_hash': self._get_file_hash(str(file_path)),
                'scanned_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取文件信息失败 {file_path}: {e}")
            return {}

    def scan_all_files(self) -> Dict[str, List[str]]:
        """扫描data目录下的所有支持文件"""
        scan_result = {
            'new_files': [],
            'modified_files': [],
            'existing_files': [],
            'error_files': []
        }

        self.logger.info(f"开始扫描目录: {self.data_dir}")
        print(f"开始扫描目录: {self.data_dir}")
        # 遍历所有子目录
        for file_path in self.data_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    relative_path = str(file_path.relative_to(self.data_dir))
                    current_file_info = self._get_file_info(file_path)

                    if not current_file_info:
                        scan_result['error_files'].append(relative_path)
                        continue

                    # 检查是否为新文件
                    if relative_path not in self.file_metadata:
                        scan_result['new_files'].append(relative_path)
                        self.file_metadata[relative_path] = current_file_info
                        self.file_metadata[relative_path]['status'] = 'discovered'

                    # 检查文件是否被修改
                    elif (self.file_metadata[relative_path].get('file_hash') != current_file_info['file_hash'] or
                          self.file_metadata[relative_path].get('file_size') != current_file_info['file_size']):
                        scan_result['modified_files'].append(relative_path)
                        # 更新文件信息但保留处理状态
                        old_status = self.file_metadata[relative_path].get('status', 'discovered')
                        self.file_metadata[relative_path].update(current_file_info)
                        self.file_metadata[relative_path]['status'] = 'modified'
                        self.file_metadata[relative_path]['previous_status'] = old_status
                    else:
                        scan_result['existing_files'].append(relative_path)

                except Exception as e:
                    relative_path = str(file_path.relative_to(self.data_dir))
                    self.logger.error(f"扫描文件失败 {relative_path}: {e}")
                    scan_result['error_files'].append(relative_path)
        
        print("保存文件元数据...")
        # 保存更新后的元数据
        self._save_metadata()

        # 记录扫描结果
        total_files = len(scan_result['new_files']) + len(scan_result['modified_files']) + len(scan_result['existing_files'])
        self.logger.info(f"扫描完成: 总计 {total_files} 个文件")
        self.logger.info(f"  新增文件: {len(scan_result['new_files'])} 个")
        self.logger.info(f"  修改文件: {len(scan_result['modified_files'])} 个")
        self.logger.info(f"  现有文件: {len(scan_result['existing_files'])} 个")
        self.logger.info(f"  错误文件: {len(scan_result['error_files'])} 个")

        return scan_result

    def get_unprocessed_files(self) -> List[str]:
        """获取未处理的文件列表"""
        unprocessed = []
        for relative_path, metadata in self.file_metadata.items():
            status = metadata.get('status', 'discovered')
            if status in ['discovered', 'modified']:
                unprocessed.append(relative_path)
        return unprocessed

    def mark_file_processed(self, relative_path: str, processing_result: Dict[str, Any] = None):
        """标记文件为已处理"""
        if relative_path in self.file_metadata:
            self.file_metadata[relative_path]['status'] = 'processed'
            self.file_metadata[relative_path]['processed_at'] = datetime.now().isoformat()

            if processing_result:
                self.file_metadata[relative_path]['processing_result'] = {
                    'content_length': processing_result.get('content_length', 0),
                    'parse_status': processing_result.get('parse_status', 'unknown'),
                    'has_course_metadata': bool(processing_result.get('course_metadata'))
                }

            self._save_metadata()
            self.logger.info(f"文件已标记为已处理: {relative_path}")

    def mark_file_error(self, relative_path: str, error_message: str):
        """标记文件处理失败"""
        if relative_path in self.file_metadata:
            self.file_metadata[relative_path]['status'] = 'error'
            self.file_metadata[relative_path]['error_message'] = error_message
            self.file_metadata[relative_path]['error_at'] = datetime.now().isoformat()
            self._save_metadata()
            self.logger.error(f"文件处理失败: {relative_path} - {error_message}")

    def get_file_metadata(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """获取特定文件的元数据"""
        return self.file_metadata.get(relative_path)

    def get_stats(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        stats = {
            'total_files': len(self.file_metadata),
            'by_status': {},
            'by_extension': {},
            'by_directory': {},
            'total_size_mb': 0
        }

        for relative_path, metadata in self.file_metadata.items():
            # 按状态统计
            status = metadata.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # 按扩展名统计
            ext = metadata.get('extension', 'unknown')
            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1

            # 按目录统计
            dir_path = str(Path(relative_path).parent)
            stats['by_directory'][dir_path] = stats['by_directory'].get(dir_path, 0) + 1

            # 总大小
            stats['total_size_mb'] += metadata.get('file_size_mb', 0)

        return stats


class AutoIndexer:
    """自动索引器，负责处理新增文件并更新RAG索引"""

    def __init__(self, data_dir: str = "data"):
        self.scanner = FileScanner(data_dir)
        self.logger = logging.getLogger(__name__)

        # 初始化文件解析器相关属性
        self.file_parser = None
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "sk-0e7d09c913e6426dbf7e55450b67daa5")

        # 延迟导入，避免循环依赖
        self.index_manager = None
        self.query_engine = None

    def set_rag_components(self, index_manager, query_engine):
        """设置RAG组件引用"""
        self.index_manager = index_manager
        self.query_engine = query_engine

    def _get_file_parser(self):
        """延迟初始化文件解析器"""
        if self.file_parser is None:
            try:
                if not FILE_PARSER_AVAILABLE:
                    raise ImportError("文件解析器依赖不可用，请安装必要的包")

                self.file_parser = FileParser(deepseek_api_key=self.deepseek_api_key)
                self.logger.info("文件解析器初始化成功")
            except Exception as e:
                self.logger.error(f"文件解析器初始化失败: {e}")
                self.file_parser = False  # 标记为初始化失败
        return self.file_parser if self.file_parser is not None else None

    def process_file(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """处理单个文件，返回处理结果"""
        try:
            file_path = str(self.scanner.data_dir / relative_path)
            file_metadata = self.scanner.get_file_metadata(relative_path)

            if not file_metadata:
                raise ValueError(f"文件元数据不存在: {relative_path}")

            file_type = file_metadata['extension'][1:] if file_metadata['extension'].startswith('.') else file_metadata['extension']

            self.logger.info(f"开始处理文件: {relative_path} (类型: {file_type})")

            # 获取文件解析器
            parser = self._get_file_parser()
            if not parser:
                raise Exception("文件解析器不可用，请检查依赖安装")

            # 使用文件解析器处理文件
            processing_result = parser.extract_content(
                file_path,
                file_type,
                generate_course_metadata=True
            )

            if processing_result['status'] == 'error':
                raise Exception(processing_result.get('error_message', '文件处理失败'))

            # 创建Document对象
            content_text = processing_result['content_text']
            if not content_text.strip():
                self.logger.warning(f"文件内容为空: {relative_path}")
                return None

            # 确定源类型和目录
            source_dir = self._determine_source_dir(relative_path)
            source_type = self._determine_source_type(source_dir)

            # 创建带有丰富元数据的Document
            document = Document(
                text=content_text,
                metadata={
                    'file_name': file_metadata['file_name'],
                    'file_path': relative_path,
                    'absolute_file_path': file_path,
                    'file_type': file_type,
                    'source_type': source_type,
                    'source_dir': source_dir,
                    'file_size': file_metadata['file_size'],
                    'scanned_at': file_metadata['scanned_at'],
                    'processed_at': datetime.now().isoformat(),
                    # 添加文件解析的元数据
                    'parse_metadata': processing_result.get('metadata', {}),
                }
            )

            # 如果有课程元数据，添加到document metadata中
            if processing_result.get('course_metadata'):
                document.metadata['course_metadata'] = processing_result['course_metadata']

            # 标记文件为已处理
            self.scanner.mark_file_processed(relative_path, processing_result)

            self.logger.info(f"文件处理成功: {relative_path} (内容长度: {len(content_text)})")

            return {
                'document': document,
                'relative_path': relative_path,
                'content_length': len(content_text),
                'source_type': source_type,
                'source_dir': source_dir,
                'course_metadata': processing_result.get('course_metadata', {})
            }

        except Exception as e:
            error_msg = f"处理文件失败: {str(e)}"
            self.logger.error(f"{error_msg} - {relative_path}")
            self.scanner.mark_file_error(relative_path, error_msg)
            return None

    def _determine_source_dir(self, relative_path: str) -> str:
        """根据文件路径确定源目录"""
        path_parts = Path(relative_path).parts
        if path_parts:
            return path_parts[0]  # 第一级目录名
        return 'unknown'

    def _determine_source_type(self, source_dir: str) -> str:
        """根据源目录确定文件类型"""
        dir_mapping = {
            'ppt': 'course_material',
            'textbook': 'textbook',
            'practice': 'practice',
            'evaluation': 'evaluation',
            'feedback': 'feedback'
        }
        return dir_mapping.get(source_dir, 'other')

    def process_new_files(self) -> Dict[str, Any]:
        """处理所有未处理的文件"""
        unprocessed_files = self.scanner.get_unprocessed_files()

        if not unprocessed_files:
            return {
                'processed_count': 0,
                'processed_files': [],
                'failed_count': 0,
                'failed_files': [],
                'message': '没有需要处理的新文件'
            }

        self.logger.info(f"开始处理 {len(unprocessed_files)} 个新文件")
        print(f"开始处理 {len(unprocessed_files)} 个新文件")
        processed_files = []
        failed_files = []
        processed_documents = []

        for relative_path in unprocessed_files:
            try:
                result = self.process_file(relative_path)
                if result:
                    processed_files.append(relative_path)
                    processed_documents.append(result['document'])
                else:
                    failed_files.append(relative_path)
            except Exception as e:
                self.logger.error(f"处理xin文件失败 {relative_path}: {e}")
                failed_files.append(relative_path)

        # 如果有成功处理的文档且RAG组件已初始化，更新索引
        if processed_documents and self.index_manager:
            try:
                self._update_index_with_new_documents(processed_documents)
            except Exception as e:
                self.logger.error(f"更新索引失败: {e}")

        result = {
            'processed_count': len(processed_files),
            'processed_files': processed_files,
            'failed_count': len(failed_files),
            'failed_files': failed_files,
            'message': f'成功处理 {len(processed_files)} 个文件，失败 {len(failed_files)} 个文件'
        }

        self.logger.info(result['message'])
        return result

    def _update_index_with_new_documents(self, new_documents: List[Document]):
        """使用新文档更新RAG索引"""
        if not self.index_manager:
            self.logger.warning("索引管理器未初始化，跳过索引更新")
            return

        self.logger.info(f"正在为 {len(new_documents)} 个新文档更新索引...")

        try:
            # 创建新的索引节点
            from llama_index.core.node_parser import SentenceSplitter

            # 应用与现有索引相同的分块策略
            chunk_size = 1024
            chunk_overlap = 200
            node_parser = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            new_nodes = node_parser.get_nodes_from_documents(new_documents)

            # 重新创建复合索引以包含新文档
            # 注意：这里需要获取所有现有节点，包括新节点
            if hasattr(self.query_engine, 'composite_index') and self.query_engine.composite_index:
                # 获取现有索引中的所有文档
                all_nodes = self._get_existing_nodes() + new_nodes

                # 重新创建复合索引
                new_composite_index = self.index_manager.create_or_load_composite_index(all_nodes)

                if new_composite_index:
                    self.query_engine.composite_index = new_composite_index
                    self.logger.info(f"索引更新成功，新增 {len(new_nodes)} 个节点")
                else:
                    self.logger.error("创建新索引失败")
            else:
                self.logger.warning("查询引擎或复合索引未初始化")

        except Exception as e:
            self.logger.error(f"更新索引时出错: {e}")
            raise

    def _get_existing_nodes(self) -> List[Document]:
        """获取现有索引中的所有节点"""
        try:
            # 这个方法需要根据实际的索引结构来实现
            # 可能需要重新加载所有现有数据
            from src.data_ingestor import DataIngestor
            data_ingestor = DataIngestor(CONFIG)
            return data_ingestor.ingest_all_data()
        except Exception as e:
            self.logger.error(f"获取现有节点失败: {e}")
            return []

    def scan_and_process(self) -> Dict[str, Any]:
        """执行完整的扫描和处理流程"""
        self.logger.info("开始自动扫描和处理流程")
        print("开始自动扫描和处理流程")
        # 1. 扫描文件
        scan_result = self.scanner.scan_all_files()

        # 2. 处理新文件
        process_result = self.process_new_files()

        # 3. 返回综合结果
        return {
            'scan_result': scan_result,
            'process_result': process_result,
            'scanner_stats': self.scanner.get_stats(),
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数，用于在web_app启动时调用
async def run_auto_indexing(data_dir: str = "data") -> Dict[str, Any]:
    """运行自动索引功能"""
    try:
        auto_indexer = AutoIndexer(data_dir)
        result = auto_indexer.scan_and_process()
        return result
    except Exception as e:
        logging.error(f"自动索引失败: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }