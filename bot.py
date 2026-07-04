import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

async def delete_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        msg = await update.message.reply_text("⏳ جاري حذف كل الرسائل...")

        deleted = 0
        # نجيب آخر 100 رسالة ونمسحها (نكرر إلى 1000)
        for offset in range(0, 1000, 100):
            try:
                # نجيب الرسائل
                updates = await context.bot.get_updates(offset=offset, limit=100)
                for upd in updates:
                    if upd.message:
                        try:
                            await context.bot.delete_message(chat_id, upd.message.message_id)
                            deleted += 1
                        except:
                            pass
            except:
                break

        await msg.edit_text(f"✅ تم حذف {deleted} رسالة!")

    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", delete_everything))
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
