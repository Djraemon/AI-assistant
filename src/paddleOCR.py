from paddleocr import PaddleOCRVL
import os
pipeline = PaddleOCRVL()
# pipeline = PaddleOCRVL(use_doc_orientation_classify=True) # 通过 use_doc_orientation_classify 指定是否使用文档方向分类模型
# pipeline = PaddleOCRVL(use_doc_unwarping=True) # 通过 use_doc_unwarping 指定是否使用文本图像矫正模块
# pipeline = PaddleOCRVL(use_layout_detection=False) # 通过 use_layout_detection 指定是否使用版面区域检测排序模块
# 将data/ppt路径下的pdf文件遍历一遍
# 设置输入和输出路径
def pdf_to_markdown():
    input_dir = "../data/ppt"
    output_base_dir = "../data/ppt/markdown"  # 您可以修改为所需的输出路径
    # 确保输出目录存在
    os.makedirs(output_base_dir, exist_ok=True)
    # 遍历 data/ppt 路径下的所有 PDF 文件
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
                output = pipeline.predict(
                    input="/home/suny.ding/make_data/PDFrocessor/PaddleOCR-VL/input/Entity_Linking_An_Issue_to_Extract_Corresponding_Entity_With_Knowledge_Base.pdf",
                    use_layout_detection=True,
                    use_chart_recognition=True,
                    format_block_content=True,
                    visualize=True
                    )
                for res in output:
                    res.print()
                    res.save_to_json(save_path=f"/home/suny.ding/make_data/PDFrocessor/PaddleOCR-VL/output/json/{base}")
                    res.save_to_markdown(save_path=f"/home/suny.ding/make_data/PDFrocessor/PaddleOCR-VL/output/markdown/{base}")
                    res.save_to_html(save_path=f"/home/suny.ding/make_data/PDFrocessor/PaddleOCR-VL/output/html/{base}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    print("All PDF files processed.")