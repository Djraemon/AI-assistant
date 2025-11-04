from llama_index.core import PromptTemplate

# Educational Q&A template - focuses on course content and learning
text_qa_template_str = (
    "你是一个专业的AI教学助手，专门回答关于大数据分析课程的问题。\n\n"
    "参考信息如下：\n---------------------\n{context_str}\n---------------------\n\n"
    "请根据以上参考信息，结合你的知识，回答学生的问题：{query_str}\n\n"
    "回答要求：\n"
    "- 基于提供的资料给出准确、详细的回答\n"
    "- 如果参考资料不充分，可以结合通用知识补充说明\n"
    "- 保持回答的学术性和专业性\n"
    "- 如涉及习题解答，请给出解题思路和步骤\n"
    "- 如涉及概念解释，请清晰易懂地阐述"
)

text_qa_template = PromptTemplate(text_qa_template_str)

# Refine template for iterative answer improvement
refine_template_str = (
    "原始问题：{query_str}\n\n"
    "现有答案：{existing_answer}\n\n"
    "现在有机会用以下新信息对答案进行优化：\n------------\n{context_msg}\n------------\n\n"
    "请结合新信息优化现有答案，或如果新信息不相关则保持原答案。"
)

refine_template = PromptTemplate(refine_template_str)

# Template for practice/exercise questions
practice_qa_template_str = (
    "你是一个专业的AI教学助手，帮助学生解决练习题。\n\n"
    "题目信息：\n---------------------\n{context_str}\n---------------------\n\n"
    "学生问题：{query_str}\n\n"
    "请提供：\n"
    "- 详细的解题步骤\n"
    "- 相关概念解释\n"
    "- 解题思路和技巧提示\n"
    "注意保持教学的引导性，帮助学生理解而非简单给出答案。"
)

practice_qa_template = PromptTemplate(practice_qa_template_str)

# Template for concept explanation
concept_explanation_template_str = (
    "你是一个专业的AI教学助手，专门解释大数据分析的概念。\n\n"
    "参考资料：\n---------------------\n{context_str}\n---------------------\n\n"
    "学生想了解：{query_str}\n\n"
    "请提供：\n"
    "- 清晰的概念定义\n"
    "- 实际应用示例（如果资料中包含）\n"
    "- 与其他概念的对比（如果适用）\n"
    "- 学习建议"
)

concept_explanation_template = PromptTemplate(concept_explanation_template_str)

# Template for course summary
summary_template_str = (
    "请根据以下资料，生成一个关于大数据分析的课程内容总结：\n\n"
    "资料：\n{context_str}\n\n"
    "总结要求：\n"
    "- 概述主要内容\n"
    "- 突出关键概念\n"
    "- 提供学习要点\n"
    "- 语言简洁易懂"
)

summary_template = PromptTemplate(summary_template_str)

# Template for concept explanation intent
explanation_template_str = (
    "你是一个专业的AI教学助手，专门解释大数据分析的概念。\\n\\n"
    "参考资料：\\n---------------------\\n{context_str}\\n---------------------\\n\\n"
    "学生想了解：{query_str}\\n\\n"
    "请提供：\\n"
    "- 清晰的概念定义\\n"
    "- 实际应用示例\\n"
    "- 与其他概念的对比（如果适用）\\n"
    "- 学习建议"
)

explanation_template = PromptTemplate(explanation_template_str)

# Template for comprehensive response intent
comprehensive_template_str = (
    "你是一个专业的AI教学助手，专门回答关于大数据分析课程的问题。\\n\\n"
    "参考信息如下：\\n---------------------\\n{context_str}\\n---------------------\\n\\n"
    "学生问题：{query_str}\\n\\n"
    "请提供一个综合性的回答，包括：\\n"
    "- 问题的详细解答\\n"
    "- 相关概念解释\\n"
    "- 实际应用场景\\n"
    "- 进一步学习建议"
)

comprehensive_template = PromptTemplate(comprehensive_template_str)


'''大模型意图识别prompt'''
query_intent_prompt = \
f"""请分析用户的查询意图，并将其分类为以下两种类型之一：

1. **comprehensive** - 用户明确要求知道信息的来源、出处或参考资料
   - 关键词示例：来源、出自、根据什么、参考资料、哪个资料、哪里提到、哪里说的、根据哪个、基于什么、哪个文档、哪本书、哪个文件、原文、出处
   - 用户想知道信息的具体来源

2. **simple** - 用户只是想要获取信息答案，不关心具体来源
   - 一般性问题、概念解释、步骤说明等
   - 用户主要关注答案内容本身

用户查询："{{query_str}}"

将用户的查询语句进行分类。你的回答只能是以下两种结果之一（不可以添加任何其他文字）：
comprehensive 或 simple

分类结果："""