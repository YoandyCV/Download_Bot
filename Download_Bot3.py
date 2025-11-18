import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Ej: https://tu-app.onrender.com/webhook

if not TOKEN:
    raise ValueError("La variable de entorno 'TOKEN' no está definida.")

CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

async def descarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor proporciona una URL. Uso: /descarga <URL>")
        return

    url = context.args[0]
    filename = url.split("/")[-1]
    part_files = []  # Mover fuera del try para acceso en finally

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Guardar archivo completo temporalmente
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # Dividir en partes
        part_number = 1
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                part_name = f"{filename}.part{part_number:03d}"
                with open(part_name, 'wb') as part_file:
                    part_file.write(chunk)
                part_files.append(part_name)
                part_number += 1

        # Enviar cada parte
        for part_name in part_files:
            with open(part_name, 'rb') as file:
                await update.message.reply_document(document=file)

        await update.message.reply_text(f"Archivo dividido en {len(part_files)} partes de 20 MB. Puedes unirlas con WinRAR o 7-Zip.")

    except Exception as e:
        await update.message.reply_text(f"Error al descargar o dividir el archivo: {e}")

    finally:
        # Limpiar archivos
        if os.path.exists(filename):
            os.remove(filename)
        for part_name in part_files:
            if os.path.exists(part_name):
                os.remove(part_name)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("descarga", descarga))
    
    # Configurar webhook para Render
    await app.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
    
    print(f"Bot iniciado con webhook en: {WEBHOOK_URL}")
    
    # No usar app.run_polling() - En su lugar iniciar servidor web
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        webhook_url=WEBHOOK_URL,
        webhook_path="/webhook"
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())