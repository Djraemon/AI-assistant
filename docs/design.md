



index_manager.py中有四种index：

   1. course_materials_index（课程材料索引） - 从标记为"course_material"的节点创建，这些通常来自PPT等课程材料
   2. practice_index（练习索引） - 从标记为"practice"的节点创建，这些来自练习题数据
   3. textbook_index（教科书索引） - 从标记为"textbook"的节点创建，这些来自教科书内容
   4. main_index（主索引） - 从索引节点创建，用于整合所有其他索引

  storage目录下的向量存储分别从以下数据创建：

  1. course_materials_index (课程材料索引)
   - 数据来源：从data/ppt/目录下的文件（如PDF、PPT等）
   - 数据类型：课程幻灯片、讲义、PDF等教学材料
   - 处理方式：在data_ingestor.py中通过ingest_ppt_data()函数处理，添加metadata标记source_type为"course_material"

  2. practice_index (练习索引)  
   - 数据来源：从data/practice/目录下的文件（如练习题、作业等）
   - 数据类型：练习题、测验、习题集等
   - 处理方式：在data_ingestor.py中通过ingest_practice_data()函数处理，添加metadata标记source_type为"practice"

  3. textbook_index (教科书索引)
   - 数据来源：从data/textbook/目录下的文件（如教科书、参考书等）
   - 数据类型：教科书内容、参考文献、课程大纲等
   - 处理方式：在data_ingestor.py中通过ingest_textbook_data()函数处理，添加metadata标记source_type为"textbook"

  4. main_index (主索引)
   - 数据来源：由上述三个索引的索引节点(IndexNode)组成
   - 数据类型：元索引，整合其他三个索引
   - 处理方式：在index_manager.py中通过create_or_load_composite_index()函数创建，使用IndexNode将其他索引作为文档节点进行整合

  处理流程
   1. DataIngestor类从不同目录读取数据，并为每种数据添加适当的元数据
   2. IndexManager类根据元数据中的source_type将节点分组
   3. 分别为每种类型的数据创建独立的向量索引
   4. 创建一个主索引用于整合所有子索引

  这四种索引的设计允许系统可以单独查询特定类型的数据（如仅课程材料或仅练习题），也可以进行跨类型的数据查询。

  每个索引都包含了从原始文档分割成的节点（nodes），并为每个节点生成了向量嵌入以支持语义搜索功能。