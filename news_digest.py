import feedparser
import requests
from datetime import datetime
import os

# Конфигурация
RSS_FEEDS = [
    'http://feeds.bbci.co.uk/news/rss.xml',
    'http://feeds.reuters.com/reuters/topNews'
]

def fetch_news(feeds):
    """Парсим RSS-ленты и собираем новости."""
    articles = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            full_text = f"{entry.title}. {entry.get('summary', '')}"
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'source': feed.feed.title,
                'full_text': full_text
            })
    return articles

def summarize_text(text):
    """Суммаризируем текст с помощью Hugging Face API."""
    HF_API_TOKEN = os.environ['HFTOKEN']
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": text}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]['summary_text']
        else:
            return "Не удалось получить суммаризацию."
    except Exception as e:
        return f"Ошибка при суммаризации: {e}"

def send_to_telegram(message):
    """Отправляет дайджест в Telegram-канал."""
    TELEGRAM_BOT_TOKEN = os.environ['TGBOT']
    TELEGRAM_CHAT_ID = os.environ['TGCHAT']
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def main():
    print("Начинаем сбор новостей...")
    articles = fetch_news(RSS_FEEDS)
    print(f"Получено {len(articles)} новостей. Начинаем суммаризацию...")
    
    digest = f"# 🌍 Мир за минуту | {datetime.now().strftime('%d.%m.%Y')}\n\n"
    
    for i, article in enumerate(articles[:8], 1):
        digest += f"**{i}. {article['title']}**\n"
        digest += f"*Источник: {article['source']}*\n"
        
        summary = summarize_text(article['full_text'])
        digest += f"📌 {summary}\n"
        digest += f"🔗 [Читать полностью]({article['link']})\n\n"
    
    print("Отправляем в Telegram...")
    result = send_to_telegram(digest)
    print("Результат отправки:", result)
    
    with open("last_digest.md", "w", encoding="utf-8") as f:
        f.write(digest)

if __name__ == "__main__":
    main()
