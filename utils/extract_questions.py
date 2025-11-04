'''
# 题目提取脚本
此脚本从一个文件夹中的Vue.js文件提取题目和答案，并将其保存到结构化的JSON文件中。

## 脚本功能

- 在指定文件夹中查找所有Vue文件，解析每个Vue文件以找到题目数组
- 提取题目文本、类型（单选或判断）以及所有选项和正确性标识
- 为每个Vue文件生成对应的JSON输出文件
- 打印所有题目的摘要并标记正确答案

脚本将处理当前目录下所有的Vue文件，并为每个文件生成对应的 `extracted_questions_[filename].json` 文件，同时输出所有题目的摘要。
'''
import re
import json
import os

def split_questions(questions_content):
    """
    通过正确处理嵌套大括号来分割题目内容
    """
    question_blocks = []
    brace_count = 0
    current_block = ""
    
    for char in questions_content:
        if char == '{':
            brace_count += 1
            current_block += char
        elif char == '}':
            brace_count -= 1
            current_block += char
            # 当我们在顶层关闭一个题目对象（brace_count 变为 0）并后跟逗号时，这是一个题目的结束
            if brace_count == 0 and current_block.strip().endswith('}'):
                question_blocks.append(current_block.strip().rstrip(','))
                current_block = ""
        else:
            current_block += char
    
    # 如果还有剩余内容，添加最后一个块
    if current_block.strip():
        question_blocks.append(current_block.strip().rstrip(','))
    
    return question_blocks

def extract_questions_from_vue(file_path):
    """
    从包含测验数据的Vue文件中提取题目和答案
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用更灵活的正则表达式查找Vue文件中的问题数组
    # 这将从赋值匹配到闭合括号
    questions_pattern = r'const questions = ref<Question\[]>\(\s*\[(.*?)\]\s*\);'
    match = re.search(questions_pattern, content, re.DOTALL)
    
    if not match:
        # 尝试没有分号的替代模式
        questions_pattern = r'const questions = ref<Question\[]>\(\s*\[(.*?)\]\s*\)'
        match = re.search(questions_pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError("Questions array not found in the file")
    
    questions_content = match.group(1)
    
    # 通过正确处理嵌套大括号来分割内容
    question_blocks = split_questions(questions_content)
    
    questions = []
    for block in question_blocks:
        question = parse_question(block)
        if question:
            questions.append(question)
    
    return questions

def parse_question(block):
    """
    解析单个题目块以提取类型、文本和选项
    """
    # 提取类型
    type_match = re.search(r"'(single|judge)'", block)
    question_type = type_match.group(1) if type_match else None
    
    # 使用更灵活的方法提取文本
    # 查找 text: '...' 或 text: "..." 模式
    text_pattern = r'text:\s*[\'"](.*?)[\'"]'
    text_match = re.search(text_pattern, block, re.DOTALL)
    question_text = text_match.group(1) if text_match else None
    
    # 提取选项
    options_pattern = r'options:\s*\[(.*?)\]'
    options_match = re.search(options_pattern, block, re.DOTALL)
    options = []
    
    if options_match:
        options_content = options_match.group(1)
        
        # 在选项数组中查找所有选项
        # 一个选项的格式为: { text: '...', correct: true|false }
        option_pattern = r'\{\s*text:\s*[\'"](.*?)[\'"]\s*,\s*correct:\s*(true|false)\s*\}'
        option_matches = re.findall(option_pattern, options_content, re.DOTALL)
        
        for option_match in option_matches:
            option_text = option_match[0]
            is_correct = option_match[1] == 'true'
            options.append({
                'text': option_text,
                'correct': is_correct
            })
    
    if question_text and options:
        return {
            'type': question_type,
            'text': question_text,
            'options': options
        }
    
    return None

def save_questions_to_file(questions, output_file):
    """
    将题目保存到JSON文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

def print_questions_summary(questions):
    """
    打印提取题目的摘要
    """
    print(f"已提取 {len(questions)} 道题目")
    print("\n" + "="*50 + "\n")
    
    for i, question in enumerate(questions, 1):
        print(f"题目 {i} ({question['type']}): {question['text']}")
        print("选项:")
        for j, option in enumerate(question['options'], ord('A')):
            letter = chr(j)
            status = "✓" if option['correct'] else "✗"
            print(f"  {letter}. {option['text']} {status}")
        print("-" * 30)

def main():
    # 定义文件夹路径，处理该文件夹中的所有Vue文件
    vue_folder_path = "/Users/suny.ding/Desktop/schoolRAG/data/practice/exercise_vue"
    output_folder_path = "/Users/suny.ding/Desktop/schoolRAG/data/practice/exercise_json"
    
    # 查找文件夹中所有的Vue文件
    vue_files = [f for f in os.listdir(vue_folder_path) if f.endswith('.vue')]
    
    if not vue_files:
        print(f"错误: 在 {vue_folder_path} 中未找到Vue文件")
        return
    
    print(f"找到 {len(vue_files)} 个Vue文件: {vue_files}")
    
    # 处理每个Vue文件
    for vue_file in vue_files:
        vue_file_path = os.path.join(vue_folder_path, vue_file)
        base_name = os.path.splitext(vue_file)[0]  # 获取文件名（不含扩展名）
        output_file_path = os.path.join(output_folder_path, f"extracted_questions_{base_name}.json")
        
        print(f"\n正在处理文件: {vue_file_path}")
        
        try:
            # 提取题目
            questions = extract_questions_from_vue(vue_file_path)
            
            # 保存到JSON文件
            save_questions_to_file(questions, output_file_path)
            print(f"题目已提取并保存到 {output_file_path} (共 {len(questions)} 道题)")
            
            # 打印摘要
            print_questions_summary(questions)
            
        except Exception as e:
            print(f"处理文件 {vue_file} 时出错: {str(e)}")

if __name__ == "__main__":
    main()