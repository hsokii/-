from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8852082846:AAEBMXjHBZHDoozpGiS6QGC5cd1CVOhb3Ps"

CHANNELS = [
    "@cl_plt",
    "@sllpl7",
    "@do_tlo",
    "@lpl_sll",
    "@k9_lwl"
]

VIDEO_CHANNEL = "@sllpl0076543210"
FIRST_VIDEO_ID = 2

async def check_sub(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for ch in CHANNELS:
        keyboard.append(
            [InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")]
        )

    keyboard.append(
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check")]
    )

    text = (
        "📢 أهلاً وسهلاً بكم في بوت المتحركات.\n\n"
        "⚠️ يجب الاشتراك بجميع القنوات حتى يتم تفعيل البوت."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "check":
        ok = await check_sub(user_id, context)

        if not ok:
            await query.message.reply_text(
                "❌ يجب الاشتراك بجميع القنوات أولاً."
            )
            return

        keyboard = [
            [InlineKeyboardButton("🎬 المتحركات", callback_data="video_1")]
        ]

        await query.message.reply_text(
            "✅ تم التحقق من الاشتراك.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("video_"):
        num = int(query.data.split("_")[1])

        msg_id = FIRST_VIDEO_ID + num - 1

        keyboard = []

        row = []

        if num > 1:
            row.append(
                InlineKeyboardButton(
                    "⬅️ السابق",
                    callback_data=f"video_{num-1}"
                )
            )

        row.append(
            InlineKeyboardButton(
                "➡️ التالي",
                callback_data=f"video_{num+1}"
            )
        )

        keyboard.append(row)

        keyboard.append(
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
        )

        await context.bot.copy_message(
            chat_id=query.message.chat.id,
            from_chat_id=VIDEO_CHANNEL,
            message_id=msg_id,
        )

        await query.message.reply_text(
            f"🎬 المتحركة رقم {num}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "home":
        keyboard = [
            [InlineKeyboardButton("🎬 المتحركات", callback_data="video_1")]
        ]

        await query.message.reply_text(
            "🏠 القائمة الرئيسية",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

print("Bot Running...")
app.run_polling()
