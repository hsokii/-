import os
import re
import subprocess
import asyncio
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ========== تحميل المتغيرات من ملف .env ==========
load_dotenv()

# ========== توكن البوت من المتغيرات البيئية ==========
HASSAN_7 = os.getenv("HASSAN_7")

if not HASSAN_7:
    raise ValueError("❌ لم يتم العثور على التوكن! تأكد من وجود ملف .env فيه HASSAN_7=توكنك")

# ========== إعدادات التحميل ==========
DOWNLOAD_PATH = "downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ========== قائمة المنصات المدعومة ==========
PLATFORMS = {
    "youtube": {
        "name": "🎬 YouTube",
        "pattern": r'(youtube\.com|youtu\.be)',
        "emoji": "🎬"
    },
    "tiktok": {
        "name": "🎵 TikTok",
        "pattern": r'(tiktok\.com)',
        "emoji": "🎵"
    },
    "instagram": {
        "name": "📸 Instagram",
        "pattern": r'(instagram\.com)',
        "emoji": "📸"
    },
    "facebook": {
        "name": "📘 Facebook",
        "pattern": r'(facebook\.com)',
        "emoji": "📘"
    },
    "twitter": {
        "name": "🐦 Twitter/X",
        "pattern": r'(twitter\.com|x\.com)',
        "emoji": "🐦"
    },
    "reddit": {
        "name": "🤖 Reddit",
        "pattern": r'(reddit\.com)',
        "emoji": "🤖"
    },
    "pinterest": {
        "name": "📌 Pinterest",
        "pattern": r'(pinterest\.com)',
        "emoji": "📌"
    },
    "vimeo": {
        "name": "🎥 Vimeo",
        "pattern": r'(vimeo\.com)',
        "emoji": "🎥"
    },
    "dailymotion": {
        "name": "🎞️ Dailymotion",
        "pattern": r'(dailymotion\.com)',
        "emoji": "🎞️"
    },
    "twitch": {
        "name": "🎮 Twitch",
        "pattern": r'(twitch\.tv)',
        "emoji": "🎮"
    },
    "google_chrome": {
        "name": "🌐 أي رابط (Google Chrome)",
        "pattern": r'.*',
        "emoji": "🌐"
    }
}

# ========== قائمة الأزرار ==========
def get_platform_buttons():
    buttons = []
    row = []
    for i, (key, platform) in enumerate(PLATFORMS.items()):
        row.append(InlineKeyboardButton(
            platform["emoji"] + " " + platform["name"],
            callback_data=f"platform_{key}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

# ========== دالة التحقق من المنصة ==========
def detect_platform(url: str) -> str:
    for key, platform in PLATFORMS.items():
        if key == "google_chrome":
            continue
        if re.search(platform["pattern"], url, re.IGNORECASE):
            return key
    return "google_chrome"

# ========== دالة التحميل ==========
async def download_video(url: str, chat_id: int) -> str:
    try:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
            "--no-playlist",
            "--no-check-certificate",
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(stderr.decode())
        
        files = os.listdir(DOWNLOAD_PATH)
        if files:
            latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(DOWNLOAD_PATH, f)))
            return os.path.join(DOWNLOAD_PATH, latest_file)
        return None
        
    except Exception as e:
        raise Exception(f"خطأ في التحميل: {str(e)}")

# ========== أمر /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🎬 **بوت تحميل الفيديوهات من جميع المواقع**

اختر المنصة من الأزرار أدناه، أو اختر **"أي رابط"** لتحميل فيديو من أي موقع تتصفحه عبر جوجل كروم.

🌐 **ملاحظة:** خيار "أي رابط" يحاول تحميل الفيديو من أي موقع تدعمه أداة yt-dlp (أكثر من 1000 موقع).
"""
    
    keyboard = get_platform_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, reply_markup=reply_markup)

# ========== اختيار المنصة ==========
async def platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    platform_key = query.data.replace("platform_", "")
    platform_info = PLATFORMS.get(platform_key)
    
    if not platform_info:
        await query.edit_message_text("❌ منصة غير معروفة!")
        return
    
    context.user_data['selected_platform'] = platform_key
    
    if platform_key == "google_chrome":
        msg = """
🌐 **تم اختيار: أي رابط (Google Chrome)**

📤 الآن أرسل رابط الفيديو من **أي موقع** تتصفحه عبر جوجل كروم.

✅ سأحاول تحميل الفيديو من أي موقع كان.
⚠️ قد لا تنجح بعض المواقع المحمية أو الخاصة.
"""
    else:
        msg = f"""
✅ تم اختيار: **{platform_info['emoji']} {platform_info['name']}**

📤 الآن أرسل رابط الفيديو من هذه المنصة.
"""
    
    keyboard = [[InlineKeyboardButton("🔙 إلغاء وعودة للقائمة", callback_data="back_to_platforms")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup)

# ========== العودة للقائمة ==========
async def back_to_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.pop('selected_platform', None)
    
    welcome = "🎬 **اختر المنصة التي تريد التحميل منها:**"
    keyboard = get_platform_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome, reply_markup=reply_markup)

# ========== معالجة الروابط ==========
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    selected_platform = context.user_data.get('selected_platform')
    
    if not selected_platform:
        keyboard = get_platform_buttons()
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ الرجاء اختيار المنصة أولاً من القائمة أدناه:",
            reply_markup=reply_markup
        )
        return
    
    detected_platform = detect_platform(url)
    
    if selected_platform == "google_chrome":
        platform_name = "أي رابط (Google Chrome)"
        status_emoji = "🌐"
    else:
        if detected_platform != selected_platform:
            selected_name = PLATFORMS[selected_platform]['name']
            if detected_platform in PLATFORMS:
                detected_name = PLATFORMS[detected_platform]['name']
                await update.message.reply_text(
                    f"⚠️ الرابط يبدو من **{detected_name}**\n"
                    f"لكنك اخترت **{selected_name}**\n\n"
                    f"إما أرسل رابط صحيح أو اختر المنصة الصحيحة."
                )
                return
        platform_name = PLATFORMS[selected_platform]['name']
        status_emoji = PLATFORMS[selected_platform]['emoji']
    
    status_msg = await update.message.reply_text(
        f"{status_emoji} جاري تحميل الفيديو من: {platform_name}\n⏳ قد يستغرق دقيقة أو اثنتين..."
    )
    
    try:
        file_path = await download_video(url, chat_id)
        
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(
                "❌ فشل التحميل.\n"
                "• تأكد من الرابط صحيح\n"
                "• تأكد من أن الفيديو عام وليس خاصاً\n"
                "• حاول مرة أخرى"
            )
            return
        
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size > 50:
            await status_msg.edit_text(f"⚠️ حجم الفيديو كبير جداً ({file_size:.1f}MB). الحد الأقصى 50MB.")
            os.remove(file_path)
            return
        
        await status_msg.edit_text("📤 جاري رفع الفيديو إلى تليجرام...")
        
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                supports_streaming=True,
                write_timeout=60
            )
        
        os.remove(file_path)
        await status_msg.delete()
        
        keyboard = get_platform_buttons()
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✅ تم التحميل بنجاح!\nاختر منصة أخرى للتحميل:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)[:200]}")
        for f in os.listdir(DOWNLOAD_PATH):
            if time.time() - os.path.getctime(os.path.join(DOWNLOAD_PATH, f)) > 3600:
                try:
                    os.remove(os.path.join(DOWNLOAD_PATH, f))
                except:
                    pass

# ========== أمر القائمة ==========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_platform_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎬 **اختر المنصة للتحميل:**",
        reply_markup=reply_markup
    )

# ========== تشغيل البوت ==========
def main():
    application = Application.builder().token(HASSAN_7).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    
    application.add_handler(CallbackQueryHandler(platform_selection, pattern="^platform_"))
    application.add_handler(CallbackQueryHandler(back_to_platforms, pattern="^back_to_platforms$"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🚀 البوت يعمل...")
    print(f"📊 يدعم {len(PLATFORMS)} منصة:")
    for key, platform in PLATFORMS.items():
        print(f"   {platform['emoji']} {platform['name']}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
