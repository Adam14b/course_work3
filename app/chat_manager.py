import json
import os
from datetime import datetime
from typing import List, Dict, Any

class ChatManager:
    """Manages chat history with save/load functionality."""
    
    def __init__(self, history_dir: str = "data/chat_history"):
        self.history_dir = history_dir
        self.ensure_history_dir()
    
    def ensure_history_dir(self):
        """Ensure the history directory exists."""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
    
    def save_chat_history(self, chat_history: List[Dict[str, Any]], session_name: str = None) -> str:
        """
        Save chat history to a JSON file.
        
        Args:
            chat_history: List of chat messages
            session_name: Optional custom session name
            
        Returns:
            str: Path to saved file
        """
        if not session_name:
            session_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filename = f"{session_name}.json"
        filepath = os.path.join(self.history_dir, filename)
        
        # Add metadata
        save_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "message_count": len(chat_history),
                "session_name": session_name
            },
            "chat_history": chat_history
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_chat_history(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load chat history from a JSON file.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            List[Dict]: Chat history
        """
        filepath = os.path.join(self.history_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Chat history file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both old format (direct list) and new format (with metadata)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "chat_history" in data:
            return data["chat_history"]
        else:
            raise ValueError("Invalid chat history file format")
    
    def list_saved_sessions(self) -> List[Dict[str, Any]]:
        """
        List all saved chat sessions.
        
        Returns:
            List of session info dictionaries
        """
        sessions = []
        
        if not os.path.exists(self.history_dir):
            return sessions
        
        for filename in os.listdir(self.history_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.history_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and "metadata" in data:
                        session_info = data["metadata"].copy()
                        session_info["filename"] = filename
                        sessions.append(session_info)
                    else:
                        # Old format - create basic metadata
                        stat = os.stat(filepath)
                        sessions.append({
                            "filename": filename,
                            "session_name": filename.replace('.json', ''),
                            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "message_count": len(data) if isinstance(data, list) else "Unknown"
                        })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
    
    def delete_session(self, filename: str) -> bool:
        """
        Delete a saved chat session.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            bool: True if deleted successfully
        """
        filepath = os.path.join(self.history_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
            return False
    
    def export_to_text(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Export chat history to a readable text format.
        
        Args:
            chat_history: List of chat messages
            
        Returns:
            str: Formatted text representation
        """
        text_lines = []
        text_lines.append("=== ИСТОРИЯ ДИАЛОГА ФИНАНСОВОГО АССИСТЕНТА ===")
        text_lines.append(f"Экспортировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        text_lines.append(f"Количество сообщений: {len(chat_history)}")
        text_lines.append("=" * 50)
        text_lines.append("")
        
        for i, message in enumerate(chat_history, 1):
            role = "ПОЛЬЗОВАТЕЛЬ" if message["role"] == "user" else "АССИСТЕНТ"
            timestamp = message.get("timestamp", "")
            
            text_lines.append(f"[{i}] {role} ({timestamp})")
            text_lines.append("-" * 30)
            text_lines.append(message["content"])
            
            # Add sources if available
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                text_lines.append("")
                text_lines.append("ИСТОЧНИКИ:")
                for source in message["sources"]:
                    text_lines.append(f"• {source['text']} - {source['link']}")
            
            text_lines.append("")
            text_lines.append("")
        
        return "\n".join(text_lines) 