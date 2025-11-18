import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("La variable de entorno 'TOKEN' no está definida.")

CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

async def descarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor proporciona una URL. Uso: /descarga <URL>")
        return

    url = context.args[0]
    filename = url.split("/")[-1]
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Guardar archivo completo temporalmente
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # Dividir en partes
        part_number = 1
        part_files = []
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
            await update.message.reply_document(document=open(part_name, 'rb'))

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

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("descarga", descarga))
    print("Bot iniciado...")
    app.run_polling()
