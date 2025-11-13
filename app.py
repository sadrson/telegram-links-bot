import os
import logging
from flask import Flask, request
import requests
import json

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# База данных ссылок
LINKS_DATABASE = {
    'supplies': {
        'name': '📦 Расходные материалы',
        'url': 'https://docs.google.com/spreadsheets/d/1XH-SB5At8kCqez8aRS3iRoPpW0EhcHlswunjieg2j88/edit?gid=1324562956#gid=1324562956',
        'description': 'Форма для заказа расходных материалов'
    },
    'database': {
        'name': '📊 База контрагентов и товаров', 
        'url': 'https://docs.google.com/spreadsheets/d/1a4kobUwHwEgXX2NztjpyqsG0pfI-bwABMApWHtalBSE/edit?gid=1090155469#gid=1090155469',
        'description': 'База данных контрагентов и товарных позиций'
    },
    'goods': {
        'name': '🛒 Операционные заявки (Goods & Services)',
        'url': 'https://docs.google.com/spreadsheets/d/1KdwehGZScK2xq938UT9JZxceviCxCzJ7xaaICISj6lE/edit?resourcekey=&gid=259871996#gid=259871996',
        'description': 'Форма для операционных заявок на товары и услуги'
    },
    'supports': {
        'name': '🔧 База сервисных служб',
        'url': 'https://docs.google.com/spreadsheets/d/11F9ZCf-3t6651Ir_X1JZ13U6-TwuJjUaIB4nKPHGsVs/edit#gid=1945488126',
        'description': 'База контактов сервисных служб и поставщиков'
    }
}

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def send_telegram_message(text, chat_id=None, reply_markup=None):
    """Отправляет сообщение в Telegram"""
    if chat_id is None:
        chat_id = CHAT_ID
        
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data)
        if response.ok:
            logger.info("✅ Сообщение отправлено в Telegram")
            return True
        else:
            logger.error(f"❌ Ошибка Telegram: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

def create_main_keyboard():
    """Создает основную клавиатуру с кнопками (только 4 основные ссылки)"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📦 Расходники", "callback_data": "supplies"},
                {"text": "📊 База данных", "callback_data": "database"}
            ],
            [
                {"text": "🛒 Заявки", "callback_data": "goods"},
                {"text": "🔧 Сервисы", "callback_data": "supports"}
            ]
        ]
    }
    return keyboard

def create_back_button():
    """Создает кнопку 'Назад'"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "⬅️ Назад к меню", "callback_data": "back_to_menu"}]
        ]
    }
    return keyboard

def send_link(link_key, chat_id=None):
    """Отправляет конкретную ссылку с кнопкой 'Назад'"""
    if link_key in LINKS_DATABASE:
        link_data = LINKS_DATABASE[link_key]
        message = f"**{link_data['name']}**\n\n{link_data['description']}\n\n🔗 {link_data['url']}"
        return send_telegram_message(message, chat_id, create_back_button())
    else:
        logger.error(f"❌ Неизвестный ключ ссылки: {link_key}")
        return False

def send_all_links(chat_id=None):
    """Отправляет все ссылки списком с кнопкой 'Назад'"""
    message = "📋 **Доступные формы и базы данных:**\n\n"
    
    for key, data in LINKS_DATABASE.items():
        message += f"• **{data['name']}**\n"
        message += f"  {data['description']}\n"
        message += f"  🔗 {data['url']}\n\n"
    
    return send_telegram_message(message, chat_id, create_back_button())

def send_help(chat_id=None):
    """Отправляет справку по командам с кнопкой 'Назад'"""
    message = """🤖 **Бот для доступа к формам и базам данных**

📋 **Доступные команды:**

• `/supplies` - 📦 Расходные материалы
• `/database` - 📊 База контрагентов и товаров  
• `/goods` - 🛒 Операционные заявки
• `/supports` - 🔧 База сервисных служб
• `/all` - 📋 Все ссылки сразу
• `/help` - ℹ️ Эта справка

⚡ **Использование:** Отправьте команду в чат и бот пришлёт нужную ссылку!

👇 **Или используйте кнопки ниже для быстрого доступа:**
"""
    return send_telegram_message(message, chat_id, create_main_keyboard())

def send_welcome(chat_id=None):
    """Приветственное сообщение с кнопками"""
    message = """👋 **Добро пожаловать!**

🤖 Я помогу вам быстро получить доступ к формам и базам данных.

👇 **Выберите нужный раздел:**"""
    
    return send_telegram_message(message,
