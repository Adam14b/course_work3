import streamlit as st
from rag_system import RAGSystem
from gpt_client import get_chat_completion_with_history
from telegram_client import update_messages
from chat_manager import ChatManager
import traceback
from datetime import datetime, timezone
import json

# Initialize systems
rag_system = RAGSystem(data_file='data/telegram_messages.json', index_file='data/faiss_index.idx')
chat_manager = ChatManager()

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'show_sources' not in st.session_state:
    st.session_state.show_sources = {}

if 'current_session_name' not in st.session_state:
    st.session_state.current_session_name = None

st.set_page_config(
    page_title="Financial Assistant",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Financial Assistant")
st.markdown("💬 Задавайте вопросы о финансовых рынках и получайте ответы на основе актуальных новостей")

def get_session_name_from_first_message():
    """Generate session name from first user message."""
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            # Take first 30 characters and clean up
            first_msg = message["content"][:30]
            # Remove problematic characters for filename
            cleaned = "".join(c for c in first_msg if c.isalnum() or c in (' ', '-', '_')).strip()
            # Replace spaces with underscores and limit length
            session_name = cleaned.replace(' ', '_')[:25]
            return session_name if session_name else f"session_{datetime.now().strftime('%Y%m%d_%H%M')}"
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M')}"

def update_database():
    """Update the database with new messages."""
    try:
        new_messages = update_messages()
        rag_system.update_documents(new_messages)
        st.success("База данных успешно обновлена!")
    except Exception as e:
        st.error(f"Произошла ошибка при обновлении базы данных: {str(e)}")
        st.error(traceback.format_exc())

def generate_todays_summary():
    """Generate a summary of today's news."""
    try:
        today = datetime.now(timezone.utc).date()
        today_str = today.isoformat()
        todays_docs = [doc for doc in rag_system.documents if doc['date'].startswith(today_str)]

        if todays_docs:
            context = "\n".join([f"{doc['text']} [Link to Info]({doc['link']})" for doc in todays_docs])
            prompt = f"Summarize the following news in 3-4 sentences with reference links in text:\n\n{context}\n\nSummary:"
            summary = get_chat_completion_with_history(prompt, [])
            
            # Add to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": "Сводка новостей за сегодня",
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": summary,
                "sources": todays_docs,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Update session name if this is the first message
            if not st.session_state.current_session_name:
                st.session_state.current_session_name = get_session_name_from_first_message()
            
            st.rerun()
        else:
            st.warning("Нет новостей за сегодня. Обновите базу данных")
    except Exception as e:
        st.error(f"Произошла ошибка при генерации сводки: {str(e)}")
        st.error(traceback.format_exc())

def answer_question(question):
    """Answer a user question about financial markets."""
    try:
        relevant_docs = rag_system.get_relevant_documents(question)
        context = "\n".join([f"{doc['text']} [Link to Info]({doc['link']})" for doc in relevant_docs])
        
        # Get chat history for context
        chat_context = st.session_state.chat_history[-10:]  # Last 10 messages for context
        
        answer = get_chat_completion_with_history(f"Context: {context}\n\nQuestion: {question}", chat_context)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": relevant_docs,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Update session name if this is the first message
        if not st.session_state.current_session_name:
            st.session_state.current_session_name = get_session_name_from_first_message()
        
    except Exception as e:
        st.error(f"Произошла ошибка при обработке вопроса: {str(e)}")
        st.error(traceback.format_exc())

# Sidebar with controls
with st.sidebar:
    st.header("🛠️ Управление")
    
    # Database controls
    st.subheader("База данных")
    if st.button("🔄 Обновить базу данных", use_container_width=True):
        with st.spinner("Обновление базы данных..."):
            update_database()
    
    if st.button("📰 Сводка за сегодня", use_container_width=True):
        with st.spinner("Генерация сводки..."):
            generate_todays_summary()
    
    st.divider()
    
    # Chat history controls
    st.subheader("💬 История диалога")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.show_sources = {}
            st.session_state.current_session_name = None
            st.rerun()
    
    with col2:
        if st.button("💾 Сохранить", use_container_width=True, disabled=len(st.session_state.chat_history) == 0):
            try:
                session_name = st.session_state.current_session_name or get_session_name_from_first_message()
                filepath = chat_manager.save_chat_history(st.session_state.chat_history, session_name)
                st.success(f"История сохранена")
                st.session_state.current_session_name = session_name
            except Exception as e:
                st.error(f"Ошибка сохранения: {str(e)}")
    
    # Load saved sessions
    saved_sessions = chat_manager.list_saved_sessions()
    if saved_sessions:
        st.subheader("📂 Сохранённые сессии")
        
        for session in saved_sessions[:5]:  # Show last 5 sessions
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                session_display = f"{session['session_name']} ({session['message_count']} сообщений)"
                if len(session_display) > 25:
                    session_display = session_display[:22] + "..."
                st.text(session_display)
            
            with col2:
                if st.button("📂", key=f"load_{session['filename']}", help="Загрузить"):
                    try:
                        loaded_history = chat_manager.load_chat_history(session['filename'])
                        st.session_state.chat_history = loaded_history
                        st.session_state.show_sources = {}
                        st.session_state.current_session_name = session['session_name']
                        st.success(f"Загружена сессия: {session['session_name']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка загрузки: {str(e)}")
            
            with col3:
                if st.button("🗑️", key=f"delete_{session['filename']}", help="Удалить"):
                    if chat_manager.delete_session(session['filename']):
                        st.success("Сессия удалена")
                        st.rerun()
                    else:
                        st.error("Ошибка удаления")
    
    st.divider()
    
    # Export options
    if st.session_state.chat_history:
        st.subheader("📤 Экспорт")
        
        # JSON export
        chat_json = json.dumps(st.session_state.chat_history, ensure_ascii=False, indent=2)
        st.download_button(
            "💾 Экспорт JSON",
            chat_json,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Text export
        chat_text = chat_manager.export_to_text(st.session_state.chat_history)
        st.download_button(
            "📄 Экспорт TXT",
            chat_text,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Session info
    if st.session_state.current_session_name:
        st.divider()
        st.info(f"Текущая сессия: {st.session_state.current_session_name}")
    
    if st.session_state.chat_history:
        st.info(f"Сообщений в диалоге: {len(st.session_state.chat_history)}")

# Main chat interface
st.subheader("💬 Диалог")

# Display chat history
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.info("👋 Привет! Я ваш финансовый ассистент. Задайте мне вопрос о финансовых рынках или попросите сводку новостей за сегодня.")
    
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(f"**{message['timestamp']}** - {message['content']}")
        else:
            with st.chat_message("assistant"):
                st.write(f"**{message['timestamp']}**")
                st.write(message['content'])
                
                # Show sources if available
                if 'sources' in message and message['sources']:
                    sources_key = f"sources_{i}"
                    if sources_key not in st.session_state.show_sources:
                        st.session_state.show_sources[sources_key] = False
                    
                    if st.button(f"📚 Показать источники ({len(message['sources'])})", key=f"btn_{i}"):
                        st.session_state.show_sources[sources_key] = not st.session_state.show_sources[sources_key]
                    
                    if st.session_state.show_sources[sources_key]:
                        st.markdown("**Источники:**")
                        for doc in message['sources']:
                            st.markdown(f"• {doc['text']} [Ссылка]({doc['link']})")

# Input for new message
st.divider()
question = st.chat_input("Задайте вопрос о финансовых рынках...")

if question:
    with st.spinner("Обработка вопроса..."):
        answer_question(question)
        st.rerun()
