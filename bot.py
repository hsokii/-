import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

async def delete_all_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هذا الأمر يحذف جميع رسائل البوت في المحادثة (حتى القديمة).
    """
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        # نرسل رسالة بأن الحذف بدأ
        msg = await update.message.reply_text("⏳ جاري حذف جميع رسائلي القديمة...")

        # نجيب آخر 1000 رسالة من المحادثة (أقصى حد)
        async for message in context.bot.get_chat_history(chat_id, limit=1000):
            # نتحقق إن الرسالة من البوت نفسه
            if message.from_user and message.from_user.id == context.bot.id:
                try:
                    await context.bot.delete_message(chat_id, message.message_id)
                    logging.info(f"تم حذف رسالة ID: {message.message_id}")
                except Exception as e:
                    logging.warning(f"ما قدرت أحذف: {e}")
            
            # نريح السيرفر شوي عشان لا نتعطل
            await asyncio.sleep(0.05)

        # نعدل الرسالة الأولى للتأكيد
        await msg.edit_text("✅ تم حذف جميع رسائلي من هذه المحادثة!")

    except Exception as e:
        logging.error(f"خطأ: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", delete_all_my_messages))
    
    print("✅ البوت شغال... ارسل /start في أي محادثة لحذف جميع رسائلي القديمة")
    app.run_polling()

if __name__ == "__main__":
    main()
