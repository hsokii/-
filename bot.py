import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from datetime import datetime, timedelta
import json
import os
TOKEN = os.getenv("BOT_TOKEN")  # ياخذ التوكن من الإعدادات

# ===== معرف الأدمن =====
ADMIN_ID = 8778989076

# ===== القنوات =====
CHANNELS = []

# ===== قناة الفيديوهات =====
VIDEO_CHANNEL = "@xxahmed200q"
TOTAL_VIDEOS = 900
FIRST_VIDEO_ID = 2

# ===== البوتات المرتبطة =====
LINKED_BOTS = []

# ===== بيانات المستخدمين =====
user_data = {}
user_activity = {}
command_usage = {}
user_positions = {}

# ===== States للمحادثات =====
WAITING_CHANNEL = 1
WAITING_VIDEO_CHANNEL = 2
WAITING_BOTS_LIST = 3

# ===== تحميل البيانات =====
def load_data():
    global user_data, user_activity, command_usage, CHANNELS, VIDEO_CHANNEL, LINKED_BOTS
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
    
    try:
        with open('bot_settings.json', 'r') as f:
            settings = json.load(f)
            CHANNELS = settings.get('channels', [])
            VIDEO_CHANNEL = settings.get('video_channel', "@xxahmed200q")
            LINKED_BOTS = settings.get('linked_bots', [])
    except:
        CHANNELS = []
        VIDEO_CHANNEL = "@xxahmed200q"
        LINKED_BOTS = []

def save_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    with open('user_activity.json', 'w') as f:
        json.dump(user_activity, f)
    with open('command_usage.json', 'w') as f:
        json.dump(command_usage, f)
    
    settings = {
        'channels': CHANNELS,
        'video_channel': VIDEO_CHANNEL,
        'linked_bots': LINKED_BOTS
    }
    with open('bot_settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

load_data()

logging.basicConfig(level=logging.INFO)

# ===== Application =====
application = Application.builder().token(TOKEN).build()

# ===== دوال البوت =====
async def check_sub(user_id, context):
    """فحص الاشتراك في جميع القنوات - يجب الاشتراك في الكل"""
    if not CHANNELS:
        return True
    
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

def get_channels_keyboard():
    """لوحة مفاتيح القنوات"""
    keyboard = []
    for ch in CHANNELS:
        keyboard.append([InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")])
    keyboard.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check")])
    return InlineKeyboardMarkup(keyboard)

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

    # ✅ فحص الاشتراك من البداية
    is_subscribed = await check_sub(user_id, context)
    
    if not is_subscribed and CHANNELS:
        # ❌ لم يشترك بكل القنوات
        await update.message.reply_text(
            "⚠️ **تنبيه مهم!**\n\n"
            "يجب الاشتراك بـ **جميع** القنوات التالية أولاً:\n\n"
            "بعد الاشتراك بكل القنوات، اضغط 'تحقق من الاشتراك'",
            reply_markup=get_channels_keyboard()
        )
        return

    # ✅ مشترك بكل القنوات
    user_positions[user_id] = 1
    keyboard = [
        [InlineKeyboardButton("🎬 عرض المتحركات", callback_data="next")],
    ]
    
    if LINKED_BOTS:
        keyboard.append([InlineKeyboardButton("🤖 جميع البوتات", callback_data="show_bots")])
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔴 لوحة التحكم", callback_data="admin_panel")])

    await update.message.reply_text(
        "🎉 **أهلا و سهلا!**\n\n"
        "✅ شكراً لاشتراكك بجميع القنوات!\n\n"
        "اضغط 'عرض المتحركات' لتبدأ! 🎬",
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
    keyboard.append([InlineKeyboardButton("🤖 جميع البوتات", callback_data="show_bots")])
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
    
    keyboard = [
        [InlineKeyboardButton("🎬 عرض المتحركات", callback_data="next")],
    ]
    
    if LINKED_BOTS:
        keyboard.append([InlineKeyboardButton("🤖 جميع البوتات", callback_data="show_bots")])
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔴 لوحة التحكم", callback_data="admin_panel")])
    
    await query.message.edit_text(
        "🏠 **القائمة الرئيسية**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def get_bot_name(context, bot_username):
    """الحصول على اسم البوت من يوزره"""
    try:
        bot_username_clean = bot_username.replace('@', '')
        bot_info = await context.bot.get_chat(f"@{bot_username_clean}")
        return bot_info.title if bot_info.title else bot_username
    except:
        return bot_username

async def show_bots(query, context):
    """عرض قائمة البوتات المرتبطة"""
    if not LINKED_BOTS:
        await query.message.reply_text("❌ لا توجد بوتات مضافة حالياً")
        return
    
    keyboard = []
    
    for bot in LINKED_BOTS:
        bot_username = bot.replace('@', '') if '@' in bot else bot
        # محاولة الحصول على اسم البوت
        bot_name = await get_bot_name(context, bot)
        
        keyboard.append([InlineKeyboardButton(f"🤖 {bot_name}", url=f"https://t.me/{bot_username}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="home")])
    
    await query.message.reply_text(
        "🤖 **البوتات المتاحة:**\n\nاختر أي بوت لاستخدامه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== Admin Panel Functions =====
async def admin_panel(query, context):
    """لوحة التحكم الرئيسية"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        await query.message.reply_text("⛔ هذا الخيار خاص بالمطور فقط.")
        return
    
    admin_keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📥 تصدير البيانات", callback_data="admin_export")],
        [InlineKeyboardButton("⚙️ إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("🎬 تغيير قناة الفيديوهات", callback_data="change_video_channel")],
        [InlineKeyboardButton("🤖 إدارة البوتات", callback_data="manage_bots")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    
    await query.message.edit_text(
        "⚙️ **لوحة التحكم**\n\nاختر أحد الخيارات:",
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )

async def manage_channels(query, context):
    """إدارة القنوات الاجبارية"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    channel_text = "📌 **القنوات المضافة حالياً:**\n\n"
    
    if CHANNELS:
        for i, ch in enumerate(CHANNELS, 1):
            channel_text += f"{i}. {ch}\n"
    else:
        channel_text += "لا توجد قنوات مضافة\n"
    
    channel_keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("🗑️ حذف قناة", callback_data="delete_channel")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin_panel")]
    ]
    
    await query.message.edit_text(
        channel_text,
        reply_markup=InlineKeyboardMarkup(channel_keyboard)
    )

async def add_channel_start(query, context):
    """بداية إضافة قناة"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    await query.message.reply_text(
        "📝 **أرسل اسم القناة**\n\n"
        "مثال: @channel_name"
    )
    
    return WAITING_CHANNEL

async def add_channel_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال اسم القناة الجديدة"""
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    channel_name = update.message.text.strip()
    
    if not channel_name.startswith('@'):
        channel_name = '@' + channel_name
    
    if channel_name in CHANNELS:
        await update.message.reply_text("❌ هذه القناة موجودة بالفعل!")
        return WAITING_CHANNEL
    
    CHANNELS.append(channel_name)
    save_data()
    
    await update.message.reply_text(f"✅ تم إضافة القناة: {channel_name}")
    
    return ConversationHandler.END

async def delete_channel(query, context):
    """حذف قناة"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID or not CHANNELS:
        return
    
    delete_keyboard = []
    for ch in CHANNELS:
        delete_keyboard.append([InlineKeyboardButton(f"🗑️ {ch}", callback_data=f"delete_ch_{ch}")])
    
    delete_keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="manage_channels")])
    
    await query.message.edit_text(
        "اختر القناة المراد حذفها:",
        reply_markup=InlineKeyboardMarkup(delete_keyboard)
    )

async def delete_channel_confirm(query, context):
    """تأكيد حذف القناة"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    channel_to_delete = query.data.replace("delete_ch_", "")
    
    if channel_to_delete in CHANNELS:
        CHANNELS.remove(channel_to_delete)
        save_data()
        await query.message.reply_text(f"✅ تم حذف القناة: {channel_to_delete}")
    
    await manage_channels(query, context)

async def change_video_channel(query, context):
    """تغيير قناة الفيديوهات"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    await query.message.reply_text(
        f"🎬 **قناة الفيديوهات الحالية:** {VIDEO_CHANNEL}\n\n"
        "📝 **أرسل اسم القناة الجديدة**\n\n"
        "مثال: @new_video_channel"
    )
    
    return WAITING_VIDEO_CHANNEL

async def change_video_channel_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال قناة الفيديوهات الجديدة"""
    global VIDEO_CHANNEL
    
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    new_channel = update.message.text.strip()
    
    if not new_channel.startswith('@'):
        new_channel = '@' + new_channel
    
    VIDEO_CHANNEL = new_channel
    save_data()
    
    await update.message.reply_text(f"✅ تم تغيير قناة الفيديوهات إلى: {VIDEO_CHANNEL}")
    
    return ConversationHandler.END

async def manage_bots(query, context):
    """إدارة البوتات المرتبطة"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    bots_text = "🤖 **البوتات المضافة حالياً:**\n\n"
    
    if LINKED_BOTS:
        for i, bot in enumerate(LINKED_BOTS, 1):
            bots_text += f"{i}. {bot}\n"
    else:
        bots_text += "لا توجد بوتات مضافة\n"
    
    bots_keyboard = [
        [InlineKeyboardButton("➕ إضافة بوتات", callback_data="add_bots")],
        [InlineKeyboardButton("🗑️ حذف بوت", callback_data="delete_bot")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin_panel")]
    ]
    
    await query.message.edit_text(
        bots_text,
        reply_markup=InlineKeyboardMarkup(bots_keyboard)
    )

async def add_bots_start(query, context):
    """بداية إضافة بوتات"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    await query.message.reply_text(
        "🤖 **أرسل قائمة البوتات**\n\n"
        "أرسل كل بوت في سطر جديد\n"
        "مثال:\n"
        "@bot1\n"
        "@bot2\n"
        "@bot3"
    )
    
    return WAITING_BOTS_LIST

async def add_bots_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال قائمة البوتات الجديدة"""
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    bots_text = update.message.text.strip()
    bots_list = bots_text.split('\n')
    
    added_bots = []
    for bot in bots_list:
        bot = bot.strip()
        if bot and not bot.startswith('#'):  # تجاهل الأسطر الفارغة والتعليقات
            if not bot.startswith('@'):
                bot = '@' + bot
            
            if bot not in LINKED_BOTS:
                LINKED_BOTS.append(bot)
                added_bots.append(bot)
    
    save_data()
    
    if added_bots:
        message_text = f"✅ تم إضافة {len(added_bots)} بوتات:\n\n"
        for bot in added_bots:
            message_text += f"• {bot}\n"
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("❌ لم يتم إضافة بوتات جديدة")
    
    return ConversationHandler.END

async def delete_bot(query, context):
    """حذف بوت"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID or not LINKED_BOTS:
        return
    
    delete_keyboard = []
    for bot in LINKED_BOTS:
        delete_keyboard.append([InlineKeyboardButton(f"🗑️ {bot}", callback_data=f"delete_bot_{bot}")])
    
    delete_keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="manage_bots")])
    
    await query.message.edit_text(
        "اختر البوت المراد حذفه:",
        reply_markup=InlineKeyboardMarkup(delete_keyboard)
    )

async def delete_bot_confirm(query, context):
    """تأكيد حذف البوت"""
    user_id = int(query.from_user.id)
    
    if user_id != ADMIN_ID:
        return
    
    bot_to_delete = query.data.replace("delete_bot_", "")
    
    if bot_to_delete in LINKED_BOTS:
        LINKED_BOTS.remove(bot_to_delete)
        save_data()
        await query.message.reply_text(f"✅ تم حذف البوت: {bot_to_delete}")
    
    await manage_bots(query, context)

async def back_admin_panel(query, context):
    """العودة إلى لوحة التحكم الرئيسية"""
    await admin_panel(query, context)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)
    await query.answer()
    
    # ✅ فحص الاشتراك قبل أي عملية (إلا للأدمن)
    if user_id != ADMIN_ID:
        is_subscribed = await check_sub(user_id, context)
        
        if not is_subscribed and CHANNELS:
            # ❌ لم يشترك بكل القنوات
            await query.message.reply_text(
                "❌ **تحذير!**\n\n"
                "لقد طلعت من أحد القنوات! 🚫\n\n"
                "يجب الاشتراك بـ **جميع** القنوات التالية:\n\n"
                "بعد الاشتراك بكل القنوات، جرب مرة أخرى!",
                reply_markup=get_channels_keyboard()
            )
            return
    
    log_user_activity(user_id, query.data)
    
    if query.data == "check":
        await query.message.edit_text(
            "✅ **تم التحقق!**\n\n"
            "أنت مشترك بجميع القنوات! 🎉\n\n"
            "اضغط 'عرض المتحركات' للبدء.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 عرض المتحركات", callback_data="next")]
            ])
        )
    
    elif query.data == "next":
        current = user_positions.get(user_id, 1)
        if current > TOTAL_VIDEOS:
            await query.message.reply_text("❌ انتهت المتحركات!")
            return
        
        success = await send_videos(context, query.message.chat.id, current, current + 1)
        if not success:
            await query.message.reply_text("❌ خطأ في جلب المتحركات.")
            return
        
        user_positions[user_id] = current + 2
        await query.message.reply_text(
            f"🎬 **الفيديو {current} و {current+1}**",
            reply_markup=get_keyboard(current)
        )
    
    elif query.data == "prev":
        current = user_positions.get(user_id, 1)
        prev = max(1, current - 2)
        
        success = await send_videos(context, query.message.chat.id, prev, prev + 1)
        if not success:
            await query.message.reply_text("❌ خطأ في جلب المتحركات.")
            return
        
        user_positions[user_id] = prev
        await query.message.reply_text(
            f"🎬 **الفيديو {prev} و {prev+1}**",
            reply_markup=get_keyboard(prev)
        )
    
    elif query.data == "show_bots":
        await show_bots(query, context)
    
    elif query.data == "home":
        user_positions[user_id] = 1
        await start_callback(query, context)
    
    elif query.data == "admin_panel":
        await admin_panel(query, context)
    
    elif query.data == "admin_stats":
        await stats_callback(query.message, context)
    
    elif query.data == "admin_users":
        await users_callback(query.message, context)
    
    elif query.data == "admin_export":
        await export_callback(query.message, context)
    
    elif query.data == "manage_channels":
        await manage_channels(query, context)
    
    elif query.data == "add_channel":
        context.user_data['state'] = 'waiting_channel'
        await query.message.reply_text(
            "📝 **أرسل اسم القناة**\n\n"
            "مثال: @channel_name"
        )
    
    elif query.data == "delete_channel":
        await delete_channel(query, context)
    
    elif query.data.startswith("delete_ch_"):
        await delete_channel_confirm(query, context)
    
    elif query.data == "change_video_channel":
        context.user_data['state'] = 'waiting_video_channel'
        await query.message.reply_text(
            f"🎬 **قناة الفيديوهات الحالية:** {VIDEO_CHANNEL}\n\n"
            "📝 **أرسل اسم القناة الجديدة**\n\n"
            "مثال: @new_video_channel"
        )
    
    elif query.data == "manage_bots":
        await manage_bots(query, context)
    
    elif query.data == "add_bots":
        context.user_data['state'] = 'waiting_bots_list'
        await query.message.reply_text(
            "🤖 **أرسل قائمة البوتات**\n\n"
            "أرسل كل بوت في سطر جديد\n"
            "مثال:\n"
            "@bot1\n"
            "@bot2\n"
            "@bot3"
        )
    
    elif query.data == "delete_bot":
        await delete_bot(query, context)
    
    elif query.data.startswith("delete_bot_"):
        await delete_bot_confirm(query, context)
    
    elif query.data == "back_admin_panel":
        await back_admin_panel(query, context)
    
    elif query.data == "back_to_main":
        await start_callback(query, context)

async def handle_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل للحالات المختلفة"""
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    state = context.user_data.get('state')
    
    if state == 'waiting_channel':
        channel_name = update.message.text.strip()
        
        if not channel_name.startswith('@'):
            channel_name = '@' + channel_name
        
        if channel_name in CHANNELS:
            await update.message.reply_text("❌ هذه القناة موجودة بالفعل!")
            return
        
        CHANNELS.append(channel_name)
        save_data()
        
        await update.message.reply_text(f"✅ تم إضافة القناة: {channel_name}")
        context.user_data['state'] = None
    
    elif state == 'waiting_video_channel':
        global VIDEO_CHANNEL
        new_channel = update.message.text.strip()
        
        if not new_channel.startswith('@'):
            new_channel = '@' + new_channel
        
        VIDEO_CHANNEL = new_channel
        save_data()
        
        await update.message.reply_text(f"✅ تم تغيير قناة الفيديوهات إلى: {VIDEO_CHANNEL}")
        context.user_data['state'] = None
    
    elif state == 'waiting_bots_list':
        bots_text = update.message.text.strip()
        bots_list = bots_text.split('\n')
        
        added_bots = []
        for bot in bots_list:
            bot = bot.strip()
            if bot and not bot.startswith('#'):
                if not bot.startswith('@'):
                    bot = '@' + bot
                
                if bot not in LINKED_BOTS:
                    LINKED_BOTS.append(bot)
                    added_bots.append(bot)
        
        save_data()
        
        if added_bots:
            message_text = f"✅ تم إضافة {len(added_bots)} بوتات:\n\n"
            for bot in added_bots:
                message_text += f"• {bot}\n"
            await update.message.reply_text(message_text)
        else:
            await update.message.reply_text("❌ لم يتم إضافة بوتات جديدة")
        
        context.user_data['state'] = None

# ===== تسجيل الأوامر =====
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_messages))
application.add_handler(CallbackQueryHandler(buttons))

# ===== تشغيل البوت =====
def main():
    print("🚀 البوت شغال...")
    application.run_polling()

if __name__ == "__main__":
    main()
