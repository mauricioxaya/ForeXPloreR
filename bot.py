import time
import requests
import schedule
import telebot
import pyttsx3
from bs4 import BeautifulSoup

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = "TU_TELEGRAM_BOT_TOKEN"
CHAT_ID = "TU_CHAT_ID"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Configuración de Twitter API
TWITTER_BEARER_TOKEN = "TU_TWITTER_BEARER_TOKEN"
TWITTER_ACCOUNTS = ["ZssBecker", "whale_alert", "realDonaldTrump", "elonmusk", "milesdeutscher"]

# Función para hacer scraping de noticias de ForexFactory
def obtener_noticias_forex():
    url = "https://www.forexfactory.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    noticias = []
    for item in soup.find_all("tr", class_="calendar__row"):
        impacto = item.find("td", class_="calendar__impact")
        moneda = item.find("td", class_="calendar__currency")
        evento = item.find("td", class_="calendar__event")
        hora = item.find("td", class_="calendar__time")
        
        if impacto and moneda and evento and hora:
            nivel = impacto.get("title", "").lower()
            divisa = moneda.get_text(strip=True)
            evento_texto = evento.get_text(strip=True)
            hora_texto = hora.get_text(strip=True)

            if divisa == "USD":
                noticias.append({"impacto": nivel, "evento": evento_texto, "hora": hora_texto})

    alto_impacto = [n for n in noticias if "high impact" in n["impacto"]]
    bajo_medio = [n for n in noticias if "low impact" in n["impacto"] or "medium impact" in n["impacto"]]

    return alto_impacto, len(bajo_medio)

# Función para obtener tweets recientes de las cuentas seleccionadas
def obtener_tweets():
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    resultados = []

    for cuenta in TWITTER_ACCOUNTS:
        params = {"query": f"from:{cuenta}", "max_results": 5}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                for tweet in data["data"]:
                    resultados.append(f"{cuenta}: {tweet['text']}")

    return resultados

# Función para enviar el resumen diario a Telegram
def enviar_resumen():
    alto_impacto, num_bajo_medio = obtener_noticias_forex()
    tweets = obtener_tweets()
    
    mensaje = "📢 **Resumen Diario** 📢\n\n"
    mensaje += f"📊 Noticias Forex de alto impacto:\n"
    for noticia in alto_impacto:
        mensaje += f"- {noticia['hora']}: {noticia['evento']}\n"
    
    mensaje += f"\n📉 Total de noticias de bajo y medio impacto: {num_bajo_medio}\n"
    mensaje += f"\n🐦 Tweets recientes:\n"
    for tweet in tweets:
        mensaje += f"- {tweet}\n"

    bot.send_message(CHAT_ID, mensaje)

# Función para monitorear eventos en tiempo real
def monitorear_nuevas_noticias():
    alto_impacto, _ = obtener_noticias_forex()
    if alto_impacto:
        mensaje = "🚨 **Nueva Noticia de Alto Impacto** 🚨\n"
        for noticia in alto_impacto:
            mensaje += f"- {noticia['hora']}: {noticia['evento']}\n"
        bot.send_message(CHAT_ID, mensaje)

# Programar la ejecución diaria
schedule.every().day.at("06:30").do(enviar_resumen)
schedule.every(10).minutes.do(monitorear_nuevas_noticias)

# Mantener el bot en ejecución
while True:
    schedule.run_pending()
    time.sleep(60)
