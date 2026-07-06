import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import json
import os
import tempfile
import shutil

import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")  # ياخذ التوكن من الإعدادات

# ===== معرف الأدمن =====
ADMIN_ID = 1025310531  # غيّره لمعرفك انت

# ===== إعدادات الفيديو =====
MAX_TELEGRAM_MB = 2000  # حد أقصى لحجم الملف بالميجابايت (2GB - حد تيليجرام الأقصى)
MAX_QUALITY_HEIGHT = 2000  # حد أقصى للجودة (resolution) - 2000p

# ===== المنصات المدعومة =====
PLATFORMS = {
    "tiktok": "🎵 تيك توك (TikTok)",
    "instagram": "📸 انستغرام (Instagram)",
    "twitter": "🐦 تويتر / X",
    "facebook": "📘 فيسبوك (Facebook)",
    "reddit": "👽 ريديت (Reddit)",
    "pinterest": "📌 بينتريست (Pinterest)",
    "snapchat": "👻 سناب شات (Snapchat)",
    "vimeo": "🎬 فيميو (Vimeo)",
    "likee": "💫 لايكي (Likee)",
    "other": "🌐 رابط آخر (أي موقع / Google Chrome)",
}

# ===== بيانات المستخدمين =====
user_data = {}
user_activity = {}
command_usage = {}
user_selected_platform = {}
user_pending_link = {}  # user_id -> الرابط الي ينتظر اختيار جودة له

# ===== تحميل البيانات =====
def load_data():
    global user_data, user_activity, command_usage
    try:
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
    except:
        user_data = {}

    try:
        with open('user_activity.json', 'r') as f:
            user_activity = json.load(f)
    except:
        user_activity = {}

    try:
        with open('command_usage.json', 'r') as f:
            command_usage = json.load(f)
    except:
        command_usage = {}

def save_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    with open('user_activity.json', 'w') as f:
        json.dump(user_activity, f)
    with open('command_usage.json', 'w') as f:
        json.dump(command_usage, f)

load_data()

logging.basicConfig(level=logging.INFO)

# ===== Application =====
application = Application.builder().token(TOKEN).build()

# ===== دوال مساعدة =====
def log_user_activity(user_id, command):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_activity[str(user_id)] = now
    if command not in command_usage:
        command_usage[command] = 0
    command_usage[command] += 1
    save_data()

def get_platforms_keyboard():
    keyboard = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in PLATFORMS.items()
    ]
    return InlineKeyboardMarkup(keyboard)

def get_available_qualities(url: str):
    """
    يفحص الرابط ويرجع قائمة جودات فيديو متاحة (بدون تحميل).
    كل عنصر: {"label": نص للزر, "format": صيغة yt-dlp للتحميل}
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logging.error(f"خطأ في فحص الجودات: {e}")
        return None

    formats = info.get("formats") or []

    # نجمع الارتفاعات (heights) المتوفرة لفيديو فيه صوت وصورة معاً
    heights = set()
    has_audio_only = False
    for f in formats:
        if f.get("vcodec") not in (None, "none") and f.get("height"):
            heights.add(int(f["height"]))
        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none"):
            has_audio_only = True

    # فلترة الجودات بناءً على الحد الأقصى المسموح (2000p)
    filtered_heights = [h for h in heights if h <= MAX_QUALITY_HEIGHT]
    
    options = [{"label": "⭐ أفضل جودة متاحة", "format": f"bestvideo[height<={MAX_QUALITY_HEIGHT}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"}]

    for h in sorted(filtered_heights, reverse=True)[:4]:
        options.append({
            "label": f"🎞️ {h}p",
            "format": f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]",
        })

    if has_audio_only:
        options.append({"label": "🎧 صوت فقط (MP3)", "format": "bestaudio/best", "audio_only": True})

    return options

def download_video(url: str, output_dir: str, format_spec: str = "best[ext=mp4]/best", audio_only: bool = False):
    """يحمل الفيديو/الصوت عبر yt-dlp حسب الصيغة المطلوبة ويرجع مسار الملف أو None لو فشل."""
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_template,
        "format": format_spec,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if audio_only:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = os.path.splitext(filename)[0] + ".mp3"
            if os.path.exists(filename):
                return filename
    except Exception as e:
        logging.error(f"خطأ في تحميل الفيديو: {e}")
    return None

def check_file_size(file_path: str) -> tuple[bool, float]:
    """
    يفحص حجم الملف ويقارنه مع الحد الأقصى.
    يرجع: (صحيح/خطأ, حجم بالميجابايت)
    """
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    is_valid = size_mb <= MAX_TELEGRAM_MB
    return is_valid, size_mb

# ===== دوال البوت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'username': user.username or '',
            'user_id': user_id,
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_bot': user.is_bot,
            'language_code': user.language_code or ''
        }
        save_data()

    log_user_activity(str(user_id), "/start")

    await update.message.reply_text(
        "أهلاً بيك! 🎬\n\n"
        "اختر المنصة الي تريد تحمل منها الفيديو:",
        reply_markup=get_platforms_keyboard()
    )

async def start_callback(query, context):
    await query.message.edit_text(
        "🏠 اختر المنصة:",
        reply_markup=get_platforms_keyboard()
    )

async def stats_callback(message, context):
    total_users = len(user_data)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    active_today = sum(1 for u in user_activity.values() if u.startswith(today))
    active_week = sum(1 for u in user_activity.values() if u >= week_ago)
    active_month = sum(1 for u in user_activity.values() if u >= month_ago)

    stats_text = f"📊 **إحصائيات البوت**\n\n"
    stats_text += f"👥 **إجمالي المستخدمين:** {total_users}\n"
    stats_text += f"🟢 **نشط اليوم:** {active_today}\n"
    stats_text += f"🟡 **نشط الأسبوع:** {active_week}\n"
    stats_text += f"🟠 **نشط الشهر:** {active_month}\n\n"

    sorted_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    stats_text += "📌 **المنصات الأكثر استخداماً:**\n"
    for cmd, count in sorted_commands:
        stats_text += f"`{cmd}`: {count} مرة\n"

    await message.reply_text(stats_text)

async def users_callback(message, context):
    users_list = list(user_data.values())
    users_list.reverse()
    users_list = users_list[:10]

    text = "👥 **آخر 10 مستخدمين:**\n\n"
    for i, user in enumerate(users_list, 1):
        name = user.get('first_name', 'غير معروف')
        username = user.get('username', '')
        added = user.get('added_date', '')
        user_id_display = user.get('user_id', '')

        text += f"{i}. **{name}**\n"
        if username:
            text += f"   🆔 @{username}\n"
        text += f"   📅 {added}\n"
        text += f"   🆔 {user_id_display}\n\n"

    await message.reply_text(text)

async def export_callback(message, context):
    data = {
        'users': user_data,
        'activity': user_activity,
        'commands': command_usage,
        'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_users': len(user_data)
    }

    with open('export_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    await context.bot.send_document(
        chat_id=message.chat.id,
        document=open('export_data.json', 'rb'),
        filename=f'users_export_{datetime.now().strftime("%Y%m%d")}.json',
        caption="📊 **تصدير بيانات المستخدمين**"
    )

    os.remove('export_data.json')

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)
    await query.answer()

    log_user_activity(user_id, query.data)

    if query.data in PLATFORMS:
        user_selected_platform[user_id] = query.data
        label = PLATFORMS[query.data]
        await query.message.reply_text(
            f"تمام، اخترت: {label}\n\n"
            "الحين ابعثلي رابط الفيديو وراح أسحبه لك."
        )

    elif query.data.startswith("q_"):
        await quality_chosen(query, context, user_id)

    elif query.data == "home":
        await start_callback(query, context)

    elif query.data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ هذا الخيار خاص بالمطور فقط.")
            return

        admin_keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📥 تصدير البيانات", callback_data="admin_export")],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="home")]
        ]

        await query.message.edit_text(
            "⚙️ **لوحة التحكم**\n\nاختر أحد الخيارات:",
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )

    elif query.data == "admin_stats":
        await stats_callback(query.message, context)

    elif query.data == "admin_users":
        await users_callback(query.message, context)

    elif query.data == "admin_export":
        await export_callback(query.message, context)

    elif query.data == "admin_settings":
        settings_text = (
            "⚙️ **إعدادات البوت الحالية**\n\n"
            f"📦 **حد أقصى لحجم الملف:** {MAX_TELEGRAM_MB} MB\n"
            f"🎬 **حد أقصى للجودة:** {MAX_QUALITY_HEIGHT}p\n\n"
            "_لتغيير الإعدادات، عدّل المتغيرات في أول الكود_"
        )
        await query.message.reply_text(settings_text)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if not text.startswith("http"):
        await update.message.reply_text("ابعث رابط صحيح يبدأ بـ http أو https 🙏")
        return

    if user_id not in user_selected_platform:
        await update.message.reply_text(
            "اختر منصة أول من القائمة:",
            reply_markup=get_platforms_keyboard()
        )
        return

    checking_msg = await update.message.reply_text("🔎 جاري فحص الجودات المتاحة...")

    options = get_available_qualities(text)
    if not options:
        await checking_msg.edit_text(
            "ما قدرت أوصل للفيديو 😕\n"
            "تأكد إن الرابط صحيح، أو إن المحتوى مو خاص/محمي."
        )
        return

    user_pending_link[user_id] = {"url": text, "options": options}

    keyboard = [
        [InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")]
        for i, opt in enumerate(options)
    ]
    await checking_msg.edit_text(
        f"اختر الجودة الي تريدها:\n\n⚠️ _الحد الأقصى المسموح: {MAX_TELEGRAM_MB} MB_",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality_chosen(query, context, user_id):
    pending = user_pending_link.get(user_id)
    if not pending:
        await query.message.reply_text("انتهت صلاحية هذا الطلب، ابعث الرابط من جديد 🙏")
        return

    try:
        idx = int(query.data.split("_", 1)[1])
        option = pending["options"][idx]
    except (ValueError, IndexError):
        await query.message.reply_text("خيار غير صحيح، جرب من جديد.")
        return

    url = pending["url"]
    audio_only = option.get("audio_only", False)

    status_msg = await query.message.reply_text("⏳ جاري التحميل...")
    tmp_dir = tempfile.mkdtemp(prefix="vid_")

    try:
        file_path = download_video(url, tmp_dir, format_spec=option["format"], audio_only=audio_only)

        if file_path is None:
            await status_msg.edit_text(
                "ما قدرت أحمل بهذي الجودة 😕\n"
                "جرب جودة ثانية أو تأكد من الرابط."
            )
            return

        # فحص حجم الملف
        is_valid, size_mb = check_file_size(file_path)
        if not is_valid:
            await status_msg.edit_text(
                f"❌ حجم الملف {size_mb:.1f} MB\n\n"
                f"الحد الأقصى المسموح: {MAX_TELEGRAM_MB} MB\n\n"
                "جرب جودة أقل أو فيديو أقصر ⬇️"
            )
            return

        await status_msg.edit_text("✅ تم التحميل، جاري الإرسال...")
        if audio_only:
            with open(file_path, "rb") as audio_file:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=audio_file)
        else:
            with open(file_path, "rb") as video_file:
                await context.bot.send_video(chat_id=query.message.chat_id, video=video_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"خطأ أثناء المعالجة: {e}")
        await status_msg.edit_text(f"صار خطأ: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        user_pending_link.pop(user_id, None)

# ===== تسجيل الأوامر =====
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

# ===== تشغيل البوت =====
def main():
    print("🚀 البوت شغال...")
    application.run_polling()

if __name__ == "__main__":
    main()
