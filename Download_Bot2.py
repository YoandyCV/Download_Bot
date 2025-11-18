import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Leer el token desde una variable de entorno
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("La variable de entorno 'TOKEN' no está definida.")

MAX_SIZE = 50 * 1024 * 1024  # 50 MB
CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

async def descarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor proporciona una URL. Uso: /descarga <URL>")
        return

    url = context.args[0]
    filename = url.split("/")[-1]
    temp_parts = []

    try:
        # Verificar si el servidor permite descargas por rango
        test = requests.head(url)
        if 'accept-ranges' not in test.headers or test.headers['accept-ranges'] != 'bytes':
            await update.message.reply_text("El servidor no permite descargas por partes. Intentando descarga completa...")
            response = requests.get(url)
            response.raise_for_status()
            if len(response.content) > MAX_SIZE:
                await update.message.reply_text("El archivo es demasiado grande para enviarlo por Telegram (límite: 50 MB).")
                return
            with open(filename, 'wb') as f:
                f.write(response.content)
        else:
            total_size = int(test.headers.get('content-length', 0))
            if total_size > MAX_SIZE:
                await update.message.reply_text("El archivo es demasiado grande para enviarlo por Telegram (límite: 50 MB).")
                return

            # Descargar en partes
            for i in range(0, total_size, CHUNK_SIZE):
                start = i
                end = min(i + CHUNK_SIZE - 1, total_size - 1)
                headers = {'Range': f'bytes={start}-{end}'}
                part = requests.get(url, headers=headers)
                part.raise_for_status()
                part_name = f"{filename}.part{i}"
                with open(part_name, 'wb') as f:
                    f.write(part.content)
                temp_parts.append(part_name)

            # Unir partes
            with open(filename, 'wb') as final:
                for part_name in temp_parts:
                    with open(part_name, 'rb') as p:
                        final.write(p.read())

        # Enviar archivo
        await update.message.reply_document(document=open(filename, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"Error al descargar el archivo: {e}")

    finally:
        # Limpiar archivos temporales
        if os.path.exists(filename):
            os.remove(filename)
        for part in temp_parts:
            if os.path.exists(part):
                os.remove(part)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("descarga", descarga))
    print("Bot iniciado...")
    app.run_polling()
