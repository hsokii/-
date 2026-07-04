import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

async def delete_all_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        
        # نرسل رسالة بأن الحذف بدأ
        msg = await update.message.reply_text("⏳ جاري حذف جميع رسائلي القديمة...")
        
        # نجيب كل الرسائل من المحادثة (بطريقة مختلفة)
        offset = 0
        deleted_count = 0
        
        while True:
            # نجيب 100 رسالة كل مرة
            messages = await context.bot.get_chat_history(chat_id, limit=100, offset=offset)
            
            if not messages:
                break
                
            for message in messages:
                # نتحقق إن الرسالة من البوت نفسه
                if message.from_user and message.from_user.id == context.bot.id:
                    try:
                        await context.bot.delete_message(chat_id, message.message_id)
                        deleted_count += 1
                    except Exception as e:
                        logging.warning(f"ما قدرت أحذف: {e}")
            
            # نزود الـ offset عشان نجيب الرسائل الأقدم
            offset += 100
            
            # نوقف إذا وصلنا لـ 1000 رسالة (حد تليجرام)
            if offset >= 1000:
                break
        
        await msg.edit_text(f"✅ تم حذف {deleted_count} رسالة من رسائلي!")
        
    except Exception as e:
        logging.error(f"خطأ: {e}")
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", delete_all_my_messages))
    
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
