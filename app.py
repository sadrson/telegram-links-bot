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

def send_link(link_key, chat_id=None):
    """Отправляет конкретную ссылку"""
    if link_key in LINKS_DATABASE:
        link_data = LINKS_DATABASE[link_key]
        message = f"**{link_data['name']}**\n\n{link_data['description']}\n\n🔗 {link_data['url']}"
        return send_telegram_message(message, chat_id)
    else:
        logger.error(f"❌ Неизвестный ключ ссылки: {link_key}")
        return False

def send_all_links(chat_id=None):
    """Отправляет все ссылки списком"""
    message = "📋 **Доступные формы и базы данных:**\n\n"
    
    for key, data in LINKS_DATABASE.items():
        message += f"• **{data['name']}**\n"
        message += f"  {data['description']}\n"
        message += f"  🔗 {data['url']}\n\n"
    
    return send_telegram_message(message, chat_id)

def send_help(chat_id=None):
    """Отправляет справку по командам"""
    message = """🤖 **Бот для доступа к формам и базам данных**

📋 **Доступные команды:**

• `/supplies` - 📦 Расходные материалы
• `/database` - 📊 База контрагентов и товаров  
• `/goods` - 🛒 Операционные заявки
• `/supports` - 🔧 База сервисных служб
• `/all` - 📋 Все ссылки сразу
• `/help` - ℹ️ Эта справка

⚡ **Использование:** Отправьте команду в чат и бот пришлёт нужную ссылку!
"""
    return send_telegram_message(message, chat_id)

def send_welcome(chat_id=None):
    """Приветственное сообщение"""
    message = """👋 **Добро пожаловать!**

🤖 Я помогу вам быстро получить доступ к формам и базам данных.

Отправьте команду /help для просмотра всех доступных команд."""
    
    return send_telegram_message(message, chat_id)

# ===== WEB ROUTES =====
@app.route("/")
def home():
    """Главная страница"""
    links_list = "\n".join([f"• {data['name']} (`/{key}`)" for key, data in LINKS_DATABASE.items()])
    
    return {
        "status": "active",
        "service": "Telegram Links Bot",
        "description": "Бот для отправки ссылок на формы и базы данных",
        "available_links": links_list,
        "endpoints": {
            "GET /": "Эта страница",
            "POST /send/<link_key>": "Отправить конкретную ссылку",
            "POST /send_all": "Отправить все ссылки",
            "POST /help": "Отправить справку",
            "POST /menu": "Отправить приветствие"
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
    """Отправляет приветствие"""
    success = send_welcome()
    if success:
        return {"message": "Приветствие отправлено"}, 200
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
            
            if text == "/start":
                send_welcome(chat_id)
            elif text == "/help":
                send_help(chat_id)
            elif text == "/all":
                send_all_links(chat_id)
            elif text in [f"/{key}" for key in LINKS_DATABASE.keys()]:
                link_key = text[1:]  # Убираем слеш
                send_link(link_key, chat_id)
            elif text == "/menu":
                send_welcome(chat_id)
            # Убрано сообщение "Неизвестная команда" - бот просто игнорирует другие сообщения
                
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

@app.route("/test_all", methods=["POST"])
def test_all():
    """Тест отправки всех ссылок"""
    success = send_all_links()
    return {"message": "Тест всех ссылок отправлен"}, 200 if success else 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("🚀 Бот ссылок запущен!")
    app.run(host="0.0.0.0", port=port)
