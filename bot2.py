import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import json
import os

# ===== الإعدادات =====
TOKEN = "8852345354:AAFILybdpOLslQus7acOxqkszjPWwzCYgms"
ADMIN_ID = 1025310531

# ===== بيانات التطبيق =====
app_data = {
    'message': '',
    'groups': [],
    'is_running': False
}

# ===== تحميل البيانات =====
def load_data():
    global app_data
    try:
        with open('spammer_config.json', 'r', encoding='utf-8') as f:
            app_data = json.load(f)
    except:
        app_data = {
            'message': '',
            'groups': [],
            'is_running': False
        }

def save_data():
    with open('spammer_config.json', 'w', encoding='utf-8') as f:
        json.dump(app_data, f, ensure_ascii=False, indent=2)

load_data()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== Scheduler =====
scheduler = AsyncIOScheduler()

# ===== Application =====
application = Application.builder().token(TOKEN).build()

# ===== دوال البوت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح لوحة التحكم الرئيسية"""
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا البوت خاص بالأدمن فقط!")
        return
    
    keyboard = [
        [InlineKeyboardButton("✏️ تعديل الكليشة", callback_data="set_message")],
        [InlineKeyboardButton("➕ إضافة كروب", callback_data="add_group")],
        [InlineKeyboardButton("➖ حذف كروب", callback_data="remove_group")],
        [InlineKeyboardButton("📋 عرض القائمة", callback_data="show_list")],
        [InlineKeyboardButton("▶️ ابدأ الإرسال", callback_data="start_sending")],
        [InlineKeyboardButton("⏹️ أوقف الإرسال", callback_data="stop_sending")],
    ]
    
    status = "🔴 متوقف" if not app_data['is_running'] else "🟢 شغال"
    message_preview = (app_data['message'][:50] + "...") if len(app_data['message']) > 50 else app_data['message']
    
    await update.message.reply_text(
        f"🤖 **بوت الكليشة**\n\n"
        f"📊 الحالة: {status}\n"
        f"📝 الكليشة: {message_preview if app_data['message'] else '❌ لم تحدد بعد'}\n"
        f"👥 عدد الكروبات: {len(app_data['groups'])}\n"
        f"⏰ الفاصل: كل دقيقة\n\n"
        f"اختر أحد الخيارات:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعديل الكليشة"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "📝 **أرسل الكليشة اللي تبي تدزها كل دقيقة:**\n\n"
        "(يمكنك استخدام رموز وجوه وأسطر جديدة)\n\n"
        "مثال:\n"
        "🎬 انضم لقناتنا!\n"
        "https://t.me/channel\n"
        "🎯 لا تفوت العروض!"
    )
    
    context.user_data['waiting_for'] = 'message'

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة كروب جديد"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🔢 **أرسل معرف الكروب:**\n\n"
        "الطريقة 1️⃣: اسم الكروب\n"
        "مثال: `@group_name`\n\n"
        "الطريقة 2️⃣: معرف رقمي\n"
        "مثال: `-1001234567890`"
    )
    
    context.user_data['waiting_for'] = 'group'

async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف كروب من القائمة"""
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("❌ لا توجد كروبات في القائمة!")
        return
    
    keyboard = []
    for idx, group in enumerate(app_data['groups']):
        keyboard.append([InlineKeyboardButton(f"🗑️ {group}", callback_data=f"delete_group_{idx}")])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    
    await query.message.reply_text(
        "اختر الكروب اللي تبي تحذفه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الكروبات"""
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("❌ لا توجد كروبات في القائمة!")
        return
    
    text = "📋 **قائمة الكروبات:**\n\n"
    for idx, group in enumerate(app_data['groups'], 1):
        text += f"{idx}. {group}\n"
    
    await query.message.reply_text(text)

async def start_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء الإرسال التلقائي"""
    query = update.callback_query
    await query.answer()
    
    if not app_data['message']:
        await query.message.reply_text("❌ لم تحدد الكليشة بعد!\n\nاستخدم 'تعديل الكليشة' أولاً")
        return
    
    if not app_data['groups']:
        await query.message.reply_text("❌ لم تحدد كروبات بعد!\n\nاستخدم 'إضافة كروب' أولاً")
        return
    
    if app_data['is_running']:
        await query.message.reply_text("⚠️ البوت يعمل بالفعل!")
        return
    
    app_data['is_running'] = True
    save_data()
    
    # إضافة المهمة للـ scheduler
    if not scheduler.running:
        scheduler.start()
    
    # إزالة المهمة القديمة إن وجدت
    if scheduler.get_job('spam_job'):
        scheduler.remove_job('spam_job')
    
    scheduler.add_job(
        send_message_to_groups,
        'interval',
        minutes=1,
        id='spam_job'
    )
    
    await query.message.reply_text(
        "▶️ **البوت شغال!**\n\n"
        f"📝 الكليشة: {app_data['message'][:40]}...\n"
        f"👥 عدد الكروبات: {len(app_data['groups'])}\n"
        f"⏰ الفاصل الزمني: كل دقيقة\n\n"
        f"⏹️ اضغط 'أوقف الإرسال' لإيقاف البوت"
    )
    
    logger.info(f"✅ بدأ الإرسال - {len(app_data['groups'])} كروبات")

async def stop_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف الإرسال التلقائي"""
    query = update.callback_query
    await query.answer()
    
    if not app_data['is_running']:
        await query.message.reply_text("⚠️ البوت متوقف بالفعل!")
        return
    
    app_data['is_running'] = False
    save_data()
    
    if scheduler.get_job('spam_job'):
        scheduler.remove_job('spam_job')
    
    await query.message.reply_text(
        "⏹️ **البوت متوقف!**\n\n"
        "الإرسال توقف بنجاح.\n"
        "اضغط 'ابدأ الإرسال' لتشغيله مرة أخرى."
    )
    
    logger.info("⏹️ توقف الإرسال")

async def send_message_to_groups():
    """إرسال الكليشة لجميع الكروبات"""
    if not app_data['is_running'] or not app_data['message'] or not app_data['groups']:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sent_count = 0
    failed_count = 0
    
    for group in app_data['groups']:
        try:
            await application.bot.send_message(
                chat_id=group,
                text=app_data['message'],
                parse_mode='Markdown'
            )
            sent_count += 1
            logger.info(f"✅ [{timestamp}] تم الإرسال إلى: {group}")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ [{timestamp}] خطأ في إرسال إلى {group}: {str(e)}")
    
    if sent_count > 0:
        logger.info(f"📊 ملخص الإرسال - نجح: {sent_count}, فشل: {failed_count}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ غير مصرح!")
        return
    
    if context.user_data.get('waiting_for') == 'message':
        app_data['message'] = update.message.text
        save_data()
        
        await update.message.reply_text(
            f"✅ **تم حفظ الكليشة!**\n\n"
            f"📝 الرسالة:\n{app_data['message']}"
        )
        context.user_data['waiting_for'] = None
    
    elif context.user_data.get('waiting_for') == 'group':
        group = update.message.text
        
        if group not in app_data['groups']:
            app_data['groups'].append(group)
            save_data()
            await update.message.reply_text(
                f"✅ **تم إضافة الكروب!**\n\n"
                f"🔢 {group}\n\n"
                f"إجمالي الكروبات: {len(app_data['groups'])}"
            )
        else:
            await update.message.reply_text(
                f"⚠️ **هذا الكروب موجود بالفعل!**"
            )
        
        context.user_data['waiting_for'] = None

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ غير مصرح!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == "set_message":
        await set_message(update, context)
    
    elif query.data == "add_group":
        await add_group(update, context)
    
    elif query.data == "remove_group":
        await remove_group(update, context)
    
    elif query.data == "show_list":
        await show_list(update, context)
    
    elif query.data == "start_sending":
        await start_sending(update, context)
    
    elif query.data == "stop_sending":
        await stop_sending(update, context)
    
    elif query.data.startswith("delete_group_"):
        idx = int(query.data.split("_")[-1])
        deleted = app_data['groups'].pop(idx)
        save_data()
        
        await query.message.reply_text(
            f"✅ **تم حذف الكروب!**\n\n"
            f"🗑️ {deleted}\n\n"
            f"الكروبات المتبقية: {len(app_data['groups'])}"
        )
    
    elif query.data == "cancel":
        await query.message.reply_text("❌ تم الإلغاء")

# ===== تسجيل المعالجات =====
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))

from telegram.ext import MessageHandler, filters
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ===== تشغيل البوت =====
def main():
    print("=" * 50)
    print("🤖 بوت الكليشة - شغال الآن!")
    print("=" * 50)
    print(f"🔐 معرف الأدمن: {ADMIN_ID}")
    print(f"📊 البيانات المحفوظة: spammer_config.json")
    print("=" * 50)
    application.run_polling()

if __name__ == "__main__":
    main()
