import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

async def delete_all_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # رسالة بداية
        msg = await update.message.reply_text("⏳ جاري حذف جميع رسائلي القديمة...")
        
        deleted_count = 0
        message_id = update.message.message_id - 1
        
        # نمسح 100 رسالة كل مرة (ننزل للخلف)
        for i in range(100):  # نحاول 100 مرة
            try:
                await context.bot.delete_message(chat_id, message_id)
                deleted_count += 1
            except Exception as e:
                # إذا الخطأ معناه إن الرسالة مو موجودة أو قديمة
                if "message to delete not found" in str(e).lower():
                    break
                elif "message can't be deleted" in str(e).lower():
                    break
                else:
                    logging.warning(f"خطأ بسيط: {e}")
            
            message_id -= 1  # نروح للرسالة اللي قبلها
            
            # نوقف إذا وصلنا لـ 1000 رسالة
            if deleted_count >= 1000:
                break
        
        await msg.edit_text(f"✅ تم حذف {deleted_count} رسالة من رسائلي!")
        
    except Exception as e:
        logging.error(f"خطأ كبير: {e}")
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", delete_all_my_messages))
    
    print("✅ البوت شغال... ارسل /start في أي محادثة لحذف جميع رسائلي القديمة")
    app.run_polling()

if __name__ == "__main__":
    main()
