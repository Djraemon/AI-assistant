from paddleocr import PaddleOCRVL
import os

def pdf_to_markdown():
    """
    将PDF文件转换为Markdown格式的函数
    该函数会遍历指定目录下的所有PDF文件，并将每个PDF文件转换为Markdown格式保存到对应的输出目录中
    """
    # 定义输入目录路径，存储PPT转换后的PDF文件
    input_dir = "input/ppt"
    # 定义输出目录的基础路径，转换后的Markdown文件将保存在此目录下的子文件夹中
    output_base_dir = "output/ppt/markdown"  # 您可以修改为所需的输出路径
    # 确保输出目录存在
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 遍历 input/ppt 路径下的所有 PDF 文件
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            # 获取文件名（不含扩展名）
            base_name = os.path.splitext(filename)[0]
            
            # 构建输入文件路径
            input_path = os.path.join(input_dir, filename)
            
            # 创建以文件名命名的输出文件夹
            output_dir = os.path.join(output_base_dir, base_name)
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"Processing {filename}...")
            try:
                pipeline = PaddleOCRVL()
                # 使用完整的输入文件路径
                output = pipeline.predict(
                    input=input_path,  # 确保使用完整路径
                    use_layout_detection=True,
                    use_chart_recognition=True,
                    format_block_content=True,
                    visualize=True
                )
                for res in output:
                    res.print()
                    res.save_to_markdown(save_path=output_dir)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    print("All PDF files processed.")

if __name__ == '__main__':
    pdf_to_markdown()