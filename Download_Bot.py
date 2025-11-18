# pip install python-telegram-bot requests
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Leer el token desde una variable de entorno
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("La variable de entorno 'TOKEN' no está definida.")

async def descarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor proporciona una URL. Uso: /descarga <URL>")
        return

    url = context.args[0]
    try:
        filename = url.split("/")[-1]
        response = requests.get(url)
        response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(response.content)

        await update.message.reply_document(document=open(filename, 'rb'))
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"Error al descargar el archivo: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("descarga", descarga))
    print("Bot iniciado...")
    app.run_polling()

