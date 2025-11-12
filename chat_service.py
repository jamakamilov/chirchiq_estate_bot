from datetime import datetime
from database import Session, Chat, ChatMessage, User
from aiogram import Bot
from locales import get_text

class ChatService:
    def _init_(self, bot: Bot):
        self.bot = bot
    
    @staticmethod
    def get_or_create_chat(user1_id, user2_id, property_id):
        """Получает или создает чат между пользователями"""
        session = Session()
        try:
            chat = session.query(Chat).filter(
                ((Chat.user1_id == user1_id) & (Chat.user2_id == user2_id)) |
                ((Chat.user1_id == user2_id) & (Chat.user2_id == user1_id)),
                Chat.property_id == property_id
            ).first()
            
            if chat:
                return chat
            
            chat = Chat(
                user1_id=user1_id,
                user2_id=user2_id,
                property_id=property_id,
                created_at=datetime.now()
            )
            session.add(chat)
            session.commit()
            return chat
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    async def send_message(self, chat_id, sender_id, message_text):
        """Отправляет сообщение в чат"""
        session = Session()
        try:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return False, "Чат не найден"
            
            message = ChatMessage(
                chat_id=chat_id,
                sender_id=sender_id,
                message=message_text,
                sent_at=datetime.now()
            )
            session.add(message)
            
            # Обновляем время последнего сообщения
            chat.last_message_at = datetime.now()
            session.commit()
            
            # Определяем получателя
            receiver_id = chat.user1_id if chat.user1_id != sender_id else chat.user2_id
            
            # Отправляем уведомление получателю
            await self.notify_receiver(receiver_id, sender_id, message_text, chat_id)
            
            return True, "Сообщение отправлено"
            
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()
    
    async def notify_receiver(self, receiver_id, sender_id, message_text, chat_id):
        """Уведомляет получателя о новом сообщении"""
        session = Session()
        try:
            sender = session.query(User).filter(User.telegram_id == sender_id).first()
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            property_obj = session.query(Property).filter(Property.id == chat.property_id).first()
            
            if not sender or not property_obj:
                return
            
            notification = (
                f"💬 <b>Новое сообщение от {sender.full_name}</b>\n\n"
                f"🏠 Объект: {property_obj.property_type} в {property_obj.district}\n"
                f"💬 Сообщение: {message_text}\n\n"
                f"<i>Ответьте на это сообщение, чтобы продолжить диалог</i>"
            )
            
            await self.bot.send_message(receiver_id, notification, parse_mode="HTML")
            
        except Exception as e:
            print(f"Failed to notify receiver: {e}")
        finally:
            session.close()
    
    @staticmethod
    def get_chat_history(chat_id, limit=50):
        """Получает историю чата"""
        session = Session()
        try:
            messages = session.query(ChatMessage).filter(
                ChatMessage.chat_id == chat_id
            ).order_by(ChatMessage.sent_at.desc()).limit(limit).all()
            
            return list(reversed(messages))
        finally:
            session.close()
    
    @staticmethod
    def get_user_chats(user_id):
        """Получает все чаты пользователя"""
        session = Session()
        try:
            chats = session.query(Chat).filter(
                (Chat.user1_id == user_id) | (Chat.user2_id == user_id),
                Chat.is_active == True
            ).order_by(Chat.last_message_at.desc()).all()
            
            return chats
        finally:
            session.close()
