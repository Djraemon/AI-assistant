"""Streamlit web application for the AI Teaching Assistant."""

import sys
import os
import streamlit as st
from streamlit_chat import message

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from data_ingestor import DataIngestor
from index_manager import IndexManager
from query_engine import TeachingQueryEngine
from evaluation import EvaluationManager


def initialize_rag_system():
    """Initialize the RAG system components."""
    with st.spinner("初始化AI教学助手系统..."):
        # Initialize models
        from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
        from llama_index.llms.siliconflow import SiliconFlow
        from llama_index.core import Settings
        
        Settings.embed_model = SiliconFlowEmbedding(
            api_key=CONFIG.model_config.api_key,
            model_name=CONFIG.model_config.embedding_model
        )
        
        Settings.llm = SiliconFlow(
            api_key=CONFIG.model_config.api_key,
            model=CONFIG.model_config.llm_model
        )
        
        # Initialize data ingestor
        data_ingestor = DataIngestor(CONFIG)
        
        # Ingest all available data
        all_nodes = data_ingestor.ingest_all_data()
        
        if not all_nodes:
            st.error("没有找到可处理的数据，请在data目录中添加文档")
            return None, None
        
        # Initialize index manager
        index_manager = IndexManager(CONFIG)
        
        # Create or load composite index
        composite_index = index_manager.create_or_load_composite_index(all_nodes)
        
        if composite_index is None:
            st.error("创建索引失败")
            return None, None
        
        # Initialize query engine
        query_engine = TeachingQueryEngine(None, CONFIG, composite_index)
        eval_manager = EvaluationManager(CONFIG)
        
        return query_engine, eval_manager


def main():
    st.set_page_config(
        page_title="AI教学助手",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 AI教学助手")
    st.markdown("基于RAG技术的大数据分析课程智能助手")
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'query_engine' not in st.session_state:
        st.session_state.query_engine = None
    if 'eval_manager' not in st.session_state:
        st.session_state.eval_manager = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'evaluations' not in st.session_state:
        st.session_state.evaluations = {}
    
    # Initialize the RAG system if not already done
    if not st.session_state.initialized:
        query_engine, eval_manager = initialize_rag_system()
        if query_engine and eval_manager:
            st.session_state.query_engine = query_engine
            st.session_state.eval_manager = eval_manager
            st.session_state.initialized = True
            st.success("AI教学助手系统初始化成功！")
        else:
            st.error("系统初始化失败，请检查配置和数据文件")
            return
    
    # Display initialization status
    if st.session_state.initialized:
        st.success("✅ 系统已就绪，可以开始提问")
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Chat interface
            st.subheader("💬 对话")
            
            # Display chat messages
            for i, msg in enumerate(st.session_state.messages):
                key = f"msg_{i}"
                if msg["role"] == "user":
                    message(msg["content"], is_user=True, key=key)
                else:
                    # Show response with evaluation scores
                    response_text = msg["content"]
                    eval_info = st.session_state.evaluations.get(i, {})
                    
                    # Display the response
                    message(response_text, is_user=False, key=key)
                    
                    # Display evaluation scores if available
                    if eval_info:
                        with st.expander("📊 评估详情", expanded=False):
                            st.write(f"**相关性**: {eval_info.get('relevance_score', 0):.2f}")
                            st.write(f"**完整性**: {eval_info.get('completeness_score', 0):.2f}")
                            st.write(f"**准确率**: {eval_info.get('accuracy_score', 0):.2f}")
                            st.write(f"**整体评分**: {eval_info.get('overall_score', 0):.2f}")
        
        with col2:
            st.subheader("📊 系统信息")
            
            # Get and display system stats
            if st.button("🔄 更新统计信息"):
                try:
                    performance = st.session_state.eval_manager.get_system_performance()
                    
                    st.metric("总评估数", performance['evaluation_metrics']['total_evaluations'])
                    st.metric("平均相关性", f"{performance['evaluation_metrics']['average_relevance']:.2f}")
                    st.metric("平均完整性", f"{performance['evaluation_metrics']['average_completeness']:.2f}")
                    st.metric("平均准确率", f"{performance['evaluation_metrics']['average_accuracy']:.2f}")
                    st.metric("平均整体评分", f"{performance['evaluation_metrics']['average_overall']:.2f}")
                    st.metric("用户平均评分", f"{performance['feedback_summary']['average_rating']:.2f}")
                except Exception as e:
                    st.error(f"获取统计信息失败: {e}")
            
            with st.expander("📋 数据统计"):
                try:
                    from data_ingestor import get_data_stats
                    data_ingestor = DataIngestor(CONFIG)
                    all_nodes = data_ingestor.ingest_all_data()
                    data_stats = get_data_stats(all_nodes)
                    
                    st.write(f"**总节点数**: {data_stats['total_docs']}")
                    st.write(f"**总字符数**: {data_stats['total_chars']:,}")
                    st.write("**按来源类型**: ")
                    for source_type, count in data_stats['by_source_type'].items():
                        st.write(f"- {source_type}: {count}")
                except Exception as e:
                    st.error(f"获取数据统计失败: {e}")
        
        # User input
        st.markdown("---")
        user_input = st.text_input("请输入您的问题:", key="input")
        
        if user_input and st.button("发送问题"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("AI助手正在思考中..."):
                try:
                    # Get response from query engine
                    response = st.session_state.query_engine.query(user_input)
                    response_text = str(response)
                    
                    # Evaluate the response
                    evaluation = st.session_state.eval_manager.evaluate_and_log(user_input, response_text)
                    
                    # Add AI response
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    # Store evaluation with the response
                    eval_idx = len(st.session_state.messages) - 1
                    st.session_state.evaluations[eval_idx] = evaluation
                    
                    # Rerun to update the UI
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"处理问题时出错: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"抱歉，处理您的问题时出现错误: {e}"})
                    st.rerun()
        
        # Feedback section for the last response
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.markdown("---")
            st.subheader("⭐ 评价回答")
            
            # Get the last query and response
            last_query = st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else ""
            last_response = st.session_state.messages[-1]["content"]
            
            col_rate, col_comment = st.columns([1, 2])
            
            with col_rate:
                rating = st.selectbox("请为本次回答评分:", [1, 2, 3, 4, 5], key="rating")
            
            with col_comment:
                comment = st.text_input("请输入您的反馈意见（可选）:", key="comment")
            
            if st.button("提交反馈"):
                try:
                    st.session_state.eval_manager.evaluate_and_log(
                        last_query,
                        last_response,
                        user_rating=rating,
                        user_comment=comment if comment else None
                    )
                    st.success("感谢您的反馈！")
                except Exception as e:
                    st.error(f"提交反馈失败: {e}")
        
        # Clear chat button
        if st.button("🗑️ 清空对话"):
            st.session_state.messages = []
            st.session_state.evaluations = {}
            st.rerun()
    
    else:
        st.info("正在初始化系统，请稍候...")


if __name__ == "__main__":
    main()