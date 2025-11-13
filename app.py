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
        'name': '📦 Данные расходных материалов',
        'url': 'https://docs.google.com/spreadsheets/d/1XH-SB5At8kCqez8aRS3iRoPpW0EhcHlswunjieg2j88/edit?gid=1324562956#gid=1324562956',
        'description': 'Данные расходных материалов'
    },
    'database': {
        'name': '📊 База контрагентов и товаров', 
        'url': 'https://docs.google.com/spreadsheets/d/1a4kobUwHwEgXX2NztjpyqsG0pfI-bwABMApWHtalBSE/edit?gid=1090155469#gid=1090155469',
        'description': 'База контрагентов и товаров'
    },
    'goods': {
        'name': '🛒 Данные операционных заявок',
        'url': 'https://docs.google.com/spreadsheets/d/1KdwehGZScK2xq938UT9JZxceviCxCzJ7xaaICISj6lE/edit?resourcekey=&gid=259871996#gid=259871996',
        'description': 'Данные операционных заявок'
    },
    'supports': {
        'name': '🔧 База сервисных служб',
        'url': 'https://docs.google.com/spreadsheets/d/11F9ZCf-3t6651Ir_X1JZ13U6-TwuJjUaIB4nKPHGsVs/edit?usp=sharing',
        'description': 'База сервисных служб'
    }
}

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def send_telegram_message(text, chat_id=None, parse_mode="Markdown"):
    """Отправляет сообщение в Telegram"""
    if chat_id is None:
        chat_id = CHAT_ID
        
    logger.info(f"🔧 Отправка сообщения в чат {chat_id}")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен")
        return False
        
    if not chat_id:
        logger.error("❌ CHAT_ID не установлен")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Сообщение успешно отправлено в Telegram")
            return True
        else:
            error_info = response.json()
            logger.error(f"❌ Ошибка Telegram API: {response.status_code} - {error_info}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return False

def send_link(link_key, chat_id=None):
    """Отправляет конкретную ссылку"""
    logger.info(f"🔗 Отправка ссылки: {link_key}")
    
    if link_key in LINKS_DATABASE:
        link_data = LINKS_DATABASE[link_key]
        
        # Для supports используем простое сообщение без Markdown
        if link_key == 'supports':
            message = f"🔧 База сервисных служб\n\nБаза сервисных служб\n\n{link_data['url']}"
            return send_telegram_message(message, chat_id, parse_mode=None)
        else:
            message = f"**{link_data['name']}**\n\n{link_data['description']}\n\n🔗 {link_data['url']}"
            return send_telegram_message(message, chat_id)
    else:
        logger.error(f"❌ Неизвестный ключ ссылки: {link_key}")
        return False

def send_all_links(chat_id=None):
    """Отправляет все ссылки списком"""
    message = "📋 Доступные базы данных:\n\n"
    
    for key, data in LINKS_DATABASE.items():
        message += f"• {data['name']}\n"
        message += f"  {data['description']}\n"
        message += f"  {data['url']}\n\n"
    
    return send_telegram_message(message, chat_id, parse_mode=None)

def send_help(chat_id=None):
    """Отправляет справку по командам"""
    message = """🤖 Бот для доступа к базам данных

📋 Доступные команды:

• /database - База контрагентов и товаров
• /goods - Данные операционных заявок
• /supplies - Данные расходных материалов
• /supports - База сервисных служб
• /all - 📋 Все ссылки сразу
• /help - ℹ️ Эта справка
• /menu - 📱 Меню команд

⚡ Использование: Отправьте команду в чат и бот пришлёт нужную ссылку!"""
    
    return send_telegram_message(message, chat_id, parse_mode=None)

def send_welcome(chat_id=None):
    """Приветственное сообщение"""
    message = """👋 Добро пожаловать!

🤖 Я помогу вам быстро получить доступ к базам данных.

Отправьте команду /help для просмотра всех доступных команд."""
    
    return send_telegram_message(message, chat_id, parse_mode=None)

def send_menu_commands(chat_id=None):
    """Показывает все команды в виде меню"""
    message = """📱 Меню команд:

📊 Базы данных
• /database - База контрагентов и товаров
• /goods - Данные операционных заявок
• /supplies - Данные расходных материалов
• /supports - База сервисных служб

📋 Общее
• /all - Все ссылки сразу
• /help - Подробная справка
• /menu - Это меню

⚡ Выберите команду и отправьте в чат"""
    
    return send_telegram_message(message, chat_id, parse_mode=None)

# ===== WEB ROUTES =====
@app.route("/")
def home():
    """Главная страница"""
    links_list = "\n".join([f"• {data['name']} (`/{key}`)" for key, data in LINKS_DATABASE.items()])
    
    return {
        "status": "active",
        "service": "Telegram Links Bot",
        "description": "Бот для отправки ссылок на базы данных",
        "available_links": links_list,
        "endpoints": {
            "GET /": "Эта страница",
            "POST /send/<link_key>": "Отправить конкретную ссылку",
            "POST /send_all": "Отправить все ссылки",
            "POST /help": "Отправить справку",
            "POST /menu": "Отправить меню команд"
        }
    }

@app.route("/send/<link_key>", methods=["POST"])
def send_specific_link(link_key):
    """Отправляет конкретную ссылку"""
    if link_key in LINKS_DATABASE:
        success = send_link(link_key)
        if success:
            return {"message": f"Ссылка '{link_key}' отправлена"}, 200
        else:
            return {"error": "Ошибка отправки в Telegram"}, 500
    else:
        return {"error": "Неизвестный ключ ссылки", "available_keys": list(LINKS_DATABASE.keys())}, 400

@app.route("/send_all", methods=["POST"])
def send_all_links_endpoint():
    """Отправляет все ссылки"""
    success = send_all_links()
    if success:
        return {"message": "Все ссылки отправлены"}, 200
    else:
        return {"error": "Ошибка отправки в Telegram"}, 500

@app.route("/help", methods=["POST"])
def send_help_endpoint():
    """Отправляет справку"""
    success = send_help()
    if success:
        return {"message": "Справка отправлена"}, 200
    else:
        return {"error": "Ошибка отправки в Telegram"}, 500

@app.route("/menu", methods=["POST"])
def send_menu():
    """Отправляет меню команд"""
    success = send_menu_commands()
    if success:
        return {"message": "Меню команд отправлено"}, 200
    else:
        return {"error": "Ошибка отправки в Telegram"}, 500

@app.route("/ping")
def ping():
    """Health check"""
    return "pong", 200

# ===== WEBHOOK для обработки команд =====
@app.route("/webhook", methods=["POST"])
def webhook():
    """Обработка входящих сообщений"""
    try:
        data = request.get_json()
        
        # Обработка текстовых сообщений
        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"].strip()
            chat_id = data["message"]["chat"]["id"]
            
            # Обработка команд
            if text == "/start":
                send_welcome(chat_id)
            elif text == "/help":
                send_help(chat_id)
            elif text == "/all":
                send_all_links(chat_id)
            elif text == "/menu":
                send_menu_commands(chat_id)
            elif text == "/supports":
                send_link('supports', chat_id)
            elif text == "/supplies":
                send_link('supplies', chat_id)
            elif text == "/database":
                send_link('database', chat_id)
            elif text == "/goods":
                send_link('goods', chat_id)
            # Неизвестные команды игнорируем
                
            return {"ok": True}, 200
            
        return {"ok": True}, 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return {"error": "Internal server error"}, 500

# ===== ТЕСТОВЫЕ ЭНДПОИНТЫ =====
@app.route("/test_supplies", methods=["POST"])
def test_supplies():
    """Тест отправки ссылки на расходные материалы"""
    success = send_link('supplies')
    return {"message": "Тест supplies отправлен"}, 200 if success else 500

@app.route("/test_supports", methods=["POST"])
def test_supports():
    """Тест отправки ссылки на сервисные службы"""
    success = send_link('supports')
    return {"message": "Тест supports отправлен"}, 200 if success else 500

@app.route("/test_menu", methods=["POST"])
def test_menu():
    """Тест отправки меню команд"""
    success = send_menu_commands()
    return {"message": "Тест меню отправлен"}, 200 if success else 500

@app.route("/test_all", methods=["POST"])
def test_all():
    """Тест отправки всех ссылок"""
    success = send_all_links()
    return {"message": "Тест всех ссылок отправлен"}, 200 if success else 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("🚀 Бот ссылок запущен!")
    app.run(host="0.0.0.0", port=port)
