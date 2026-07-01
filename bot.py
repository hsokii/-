import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import json
import os

# ===== التوكن =====
TOKEN = "8852082846:AAHoH5gN-X8V5oSULN05G0LKOFIzkUWrJ7A"

# ===== معرف الأدمن =====
ADMIN_ID = 1025310531

# ===== القنوات =====
CHANNELS = ["@cl_plt", "@sllpl7", "@do_tlo", "@lpl_sll", "@k9_lwl"]

# ===== قناة الفيديوهات =====
VIDEO_CHANNEL = "@sllpl0076543210"
TOTAL_VIDEOS = 900
FIRST_VIDEO_ID = 2

# ===== بيانات المستخدمين =====
user_data = {}
user_activity = {}
command_usage = {}
user_positions = {}

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

# ===== دوال البوت =====
async def check_sub(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def log_user_activity(user_id, command):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_activity[str(user_id)] = now
    if command not in command_usage:
        command_usage[command] = 0
    command_usage[command] += 1
    save_data()

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
    user_positions[user_id] = 1

    keyboard = []
    for ch in CHANNELS:
        keyboard.append([InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")])
    keyboard.append([InlineKeyboardButton("✅ تحقق", callback_data="check")])

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔴 لوحة التحكم", callback_data="admin_panel")])

    await update.message.reply_text(
        "أهلا بكم في بوت متحركات 🤤🔥\n\nاشترك بالقنوات ثم اضغط تحقق.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_videos(context, chat_id, num1, num2):
    try:
        if num1 <= TOTAL_VIDEOS:
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=VIDEO_CHANNEL,
                message_id=FIRST_VIDEO_ID + num1 - 1
            )
        if num2 <= TOTAL_VIDEOS:
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=VIDEO_CHANNEL,
                message_id=FIRST_VIDEO_ID + num2 - 1
            )
        return True
    except Exception as e:
        logging.error(f"خطأ في جلب الفيديو: {e}")
        return False

def get_keyboard(current):
    row = []
    if current > 1:
        row.append(InlineKeyboardButton("⬅️ السابق", callback_data="prev"))
    row.append(InlineKeyboardButton("▶️", callback_data="none"))
    if current + 2 <= TOTAL_VIDEOS:
        row.append(InlineKeyboardButton("التالي ➡️", callback_data="next"))
    
    keyboard = [row]
    keyboard.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
    return InlineKeyboardMarkup(keyboard)

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
    stats_text += "📌 **الأوامر الأكثر استخداماً:**\n"
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

async def start_callback(query, context):
    user_id = query.from_user.id
    
    keyboard = []
    for ch in CHANNELS:
        keyboard.append([InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")])
    keyboard.append([InlineKeyboardButton("✅ تحقق", callback_data="check")])
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔴 لوحة التحكم", callback_data="admin_panel")])
    
    await query.message.edit_text(
        "🏠 **القائمة الرئيسية**\n\nاختر أحد الخيارات:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()
    
    log_user_activity(user_id, query.data)
    
    if query.data == "check":
        if not await check_sub(int(user_id), context):
            await query.message.reply_text("❌ أكمل الاشتراك.")
            return
        
        user_positions[int(user_id)] = 1
        await query.message.edit_text(
            "✅ تم التحقق!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 عرض المتحركات", callback_data="next")]
            ])
        )
    
    elif query.data == "next":
        current = user_positions.get(int(user_id), 1)
        if current > TOTAL_VIDEOS:
            await query.message.reply_text("❌ انتهت المتحركات!")
            return
        
        success = await send_videos(context, query.message.chat.id, current, current + 1)
        if not success:
            await query.message.reply_text("❌ خطأ في جلب المتحركات.")
            return
        
        user_positions[int(user_id)] = current + 2
        await query.message.reply_text(
            f"🎬 {current} و {current+1}",
            reply_markup=get_keyboard(current)
        )
    
    elif query.data == "prev":
        current = user_positions.get(int(user_id), 1)
        prev = max(1, current - 2)
        
        success = await send_videos(context, query.message.chat.id, prev, prev + 1)
        if not success:
            await query.message.reply_text("❌ خطأ في جلب المتحركات.")
            return
        
        user_positions[int(user_id)] = prev
        await query.message.reply_text(
            f"🎬 {prev} و {prev+1}",
            reply_markup=get_keyboard(prev)
        )
    
    elif query.data == "home":
        user_positions[int(user_id)] = 1
        await query.message.reply_text(
            "🏠 الرئيسية",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 عرض المتحركات", callback_data="next")]
            ])
        )
    
    elif query.data == "admin_panel":
        if int(user_id) != ADMIN_ID:
            await query.message.reply_text("⛔ هذا الخيار خاص بالمطور فقط.")
            return
        
        admin_keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📥 تصدير البيانات", callback_data="admin_export")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
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
    
    elif query.data == "back_to_main":
        await start_callback(query, context)

# ===== تسجيل الأوامر =====
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))

# ===== تشغيل البوت =====
def main():
    print("🚀 البوت شغال...")
    application.run_polling()

if __name__ == "__main__":
    main()
