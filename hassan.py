import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== إعدادات التسجيل ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== توكن البوت ==========
HASSAN_7 = os.environ.get("HASSAN_7")

if not HASSAN_7:
    logger.error("❌ HASSAN_7 غير موجود في المتغيرات البيئية!")
    exit(1)

logger.info("✅ تم تحميل التوكن بنجاح")

# ========== منصات التحميل ==========
PLATFORMS = {
    "youtube": {"name": "🎬 YouTube", "emoji": "🎬"},
    "tiktok": {"name": "🎵 TikTok", "emoji": "🎵"},
    "instagram": {"name": "📸 Instagram", "emoji": "📸"},
    "facebook": {"name": "📘 Facebook", "emoji": "📘"},
    "twitter": {"name": "🐦 Twitter/X", "emoji": "🐦"},
    "reddit": {"name": "🤖 Reddit", "emoji": "🤖"},
    "pinterest": {"name": "📌 Pinterest", "emoji": "📌"},
    "vimeo": {"name": "🎥 Vimeo", "emoji": "🎥"},
    "dailymotion": {"name": "🎞️ Dailymotion", "emoji": "🎞️"},
    "twitch": {"name": "🎮 Twitch", "emoji": "🎮"},
    "google_chrome": {"name": "🌐 أي رابط", "emoji": "🌐"}
}

# ========== إنشاء الأزرار ==========
def get_platform_buttons():
    buttons = []
    row = []
    for key, platform in PLATFORMS.items():
        row.append(InlineKeyboardButton(
            platform["name"],
            callback_data=f"platform_{key}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

# ========== أمر /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        welcome = "🎬 أهلاً بك في بوت تحميل الفيديوهات!\n\nاختر المنصة من الأزرار أدناه:"
        keyboard = get_platform_buttons()
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"✅ تم إرسال القائمة للمستخدم {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ خطأ في start: {e}")

# ========== اختيار المنصة ==========
async def platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        platform_key = query.data.replace("platform_", "")
        platform_name = PLATFORMS.get(platform_key, {}).get("name", "غير معروف")
        
        context.user_data['selected_platform'] = platform_key
        
        msg = f"✅ تم اختيار: {platform_name}\n\n📤 أرسل رابط الفيديو الآن."
        
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        
        logger.info(f"✅ المستخدم اختار: {platform_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في platform_selection: {e}")

# ========== العودة للقائمة ==========
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data.pop('selected_platform', None)
        
        welcome = "🎬 اختر المنصة التي تريد التحميل منها:"
        keyboard = get_platform_buttons()
        await query.edit_message_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطأ في back: {e}")

# ========== معالجة الروابط ==========
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = update.message.text.strip()
        selected = context.user_data.get('selected_platform')
        
        if not selected:
            keyboard = get_platform_buttons()
            await update.message.reply_text(
                "❌ الرجاء اختيار المنصة أولاً!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        platform_name = PLATFORMS.get(selected, {}).get("name", "غير معروف")
        
        await update.message.reply_text(
            f"⏳ جاري معالجة الرابط من {platform_name}...\n\n"
            f"📌 **ملاحظة:** هذا إصدار تجريبي. التحميل الفعلي سيتم تفعيله قريباً."
        )
        
        logger.info(f"✅ المستخدم أرسل رابط: {url[:50]}... من {platform_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_url: {e}")
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى.")

# ========== أمر مساعدة ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 **كيفية الاستخدام:**

1️⃣ اضغط /start
2️⃣ اختر المنصة من الأزرار
3️⃣ أرسل رابط الفيديو
4️⃣ انتظر التحميل

✅ **المنصات المدعومة:**
• YouTube • TikTok • Instagram
• Facebook • Twitter/X • Reddit
• Pinterest • Vimeo • Dailymotion
• Twitch • أي رابط آخر

⚠️ **الحد الأقصى:** 50MB
"""
    await update.message.reply_text(help_text)

# ========== التشغيل الرئيسي ==========
def main():
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # إنشاء التطبيق
        app = Application.builder().token(HASSAN_7).build()
        
        # إضافة المعالجات
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CallbackQueryHandler(platform_selection, pattern="^platform_"))
        app.add_handler(CallbackQueryHandler(back, pattern="^back$"))
        app.add_handler(CommandHandler("menu", start))
        
        # معالج الروابط
        from telegram.ext import filters
        app.add_handler(CommandHandler("url", handle_url))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
        
        # تشغيل البوت
        logger.info("✅ البوت جاهز للاستخدام!")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح: {e}")
        exit(1)

if __name__ == "__main__":
    main()
