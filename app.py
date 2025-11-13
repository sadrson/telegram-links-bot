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

def send_telegram_message(text, chat_id=None):
    """Отправляет сообщение в Telegram"""
    if chat_id is None:
        chat_id = CHAT_ID
        
    logger.info(f"📤 Попытка отправить сообщение в чат {chat_id}")
    
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
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        logger.info(f"🔗 Отправка запроса к Telegram API...")
        response = requests.post(url, data=data, timeout=30)
        
        logger.info(f"📨 Ответ Telegram: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Сообщение успешно отправлено в Telegram")
            return True
        else:
            error_data = response.json()
            logger.error(f"❌ Ошибка Telegram API: {response.status_code} - {error_data}")
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
        message = f"**{link_data['name']}**\n\n{link_data['description']}\n\n🔗 {link_data['url']}"
        logger.info(f"📝 Текст сообщения: {message}")
        return send_telegram_message(message, chat_id)
    else:
        logger.error(f"❌ Неизвестный ключ ссылки: {link_key}")
        return False

# ===== WEB ROUTES =====
@app.route("/")
def home():
    """Главная страница"""
    return {
        "status": "active",
        "service": "Telegram Links Bot",
        "endpoints": {
            "GET /": "Эта страница",
            "POST /send/<link_key>": "Отправить ссылку",
            "GET /debug": "Диагностика",
            "GET /ping": "Health check"
        }
    }

@app.route("/send/<link_key>", methods=["POST"])
def send_specific_link(link_key):
    """Отправляет конкретную ссылку"""
    logger.info(f"🌐 Запрос на отправку ссылки: {link_key}")
    
    if link_key in LINKS_DATABASE:
        success = send_link(link_key)
        if success:
            return {"message": f"Ссылка '{link_key}' отправлена"}, 200
        else:
            return {"error": "Ошибка отправки в Telegram"}, 500
    else:
        return {"error": "Неизвестный ключ ссылки", "available_keys": list(LINKS_DATABASE.keys())}, 400

@app.route("/debug", methods=["GET"])
def debug():
    """Диагностика проблемы"""
    debug_info = {
        "BOT_TOKEN_set": bool(BOT_TOKEN),
        "CHAT_ID_set": bool(CHAT_ID),
        "CHAT_ID_value": CHAT_ID,
        "available_links": list(LINKS_DATABASE.keys())
    }
    
    # Тест отправки простого сообщения
    if BOT_TOKEN and CHAT_ID:
        try:
            test_message = "🔧 Тестовое сообщение для диагностики"
            success = send_telegram_message(test_message)
            debug_info["test_message_sent"] = success
        except Exception as e:
            debug_info["test_message_error"] = str(e)
    
    return debug_info

@app.route("/ping")
def ping():
    """Health check"""
    return "pong", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("🚀 Бот ссылок запущен!")
    app.run(host="0.0.0.0", port=port)
