from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    KeyboardButtonRequestChat, 
    ChatPrivileges,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message
)
from pyrogram.enums import ParseMode
import sqlite3
import datetime
import asyncio

# بيانات البوت
API_ID = 20819310
API_HASH = "30b0157f256e5ecd4c099de2f3100698"
BOT_TOKEN = "8101204051:AAEEOsD5j2n1OtFS22JBgQZVDc6JrCZHjVQ"
ADMIN_ID = 7627857345
REQUIRED_CHANNELS = ["pythonyemen1", "pythonyemen12"]

# إنشاء العميل
Hemo = Client("HemoOwn", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# إنشاء قاعدة البيانات
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language TEXT DEFAULT 'ar',
    join_date TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS usage_stats (
    user_id INTEGER,
    command TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_channels (
    user_id INTEGER,
    channel_id INTEGER,
    channel_username TEXT,
    is_owner BOOLEAN,
    is_admin BOOLEAN,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

conn.commit()

# لوحة المفاتيح الرئيسية
def get_main_keyboard(language="ar"):
    if language == "ar":
        return ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("‹ قنواتي مالك ›", request_chat=KeyboardButtonRequestChat(2, chat_is_channel=True, chat_is_created=True)),
                    KeyboardButton("‹ قنواتي ادمن ›", request_chat=KeyboardButtonRequestChat(1, chat_is_channel=True, user_administrator_rights=ChatPrivileges(can_restrict_members=False)))
                ],
                [
                    KeyboardButton("‹ قروباتي مالك ›", request_chat=KeyboardButtonRequestChat(4, chat_is_channel=False, chat_is_created=True)),
                    KeyboardButton("‹ قروباتي ادمن ›", request_chat=KeyboardButtonRequestChat(3, chat_is_channel=False, user_administrator_rights=ChatPrivileges(can_restrict_members=False)))
                ],
                [
                    KeyboardButton("🌐 تغيير اللغة / Change Language"),
                    KeyboardButton("📊 إحصائياتي")
                ]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("‹ My Owned Channels ›", request_chat=KeyboardButtonRequestChat(2, chat_is_channel=True, chat_is_created=True)),
                    KeyboardButton("‹ My Admin Channels ›", request_chat=KeyboardButtonRequestChat(1, chat_is_channel=True, user_administrator_rights=ChatPrivileges(can_restrict_members=False)))
                ],
                [
                    KeyboardButton("‹ My Owned Groups ›", request_chat=KeyboardButtonRequestChat(4, chat_is_channel=False, chat_is_created=True)),
                    KeyboardButton("‹ My Admin Groups ›", request_chat=KeyboardButtonRequestChat(3, chat_is_channel=False, user_administrator_rights=ChatPrivileges(can_restrict_members=False)))
                ],
                [
                    KeyboardButton("🌐 Change Language / تغيير اللغة"),
                    KeyboardButton("📊 My Statistics")
                ]
            ],
            resize_keyboard=True
        )

# لوحة اختيار اللغة
def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
    ])

# التحقق من الاشتراك في القنوات المطلوبة
async def check_subscription(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            try:
                member = await Hemo.get_chat_member(channel, user_id)
                if member.status in ["left", "kicked", "restricted"]:
                    return False
            except Exception:
                return False
        return True
    except Exception:
        return False

# إضافة مستخدم إلى قاعدة البيانات
def add_user(user_id, username, first_name, last_name):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        join_date = datetime.datetime.now()
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, join_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, join_date)
        )
        conn.commit()

# تحديث إحصائيات الاستخدام
def update_usage(user_id, command):
    timestamp = datetime.datetime.now()
    cursor.execute(
        "INSERT INTO usage_stats (user_id, command, timestamp) VALUES (?, ?, ?)",
        (user_id, command, timestamp)
    )
    conn.commit()

# الحصول على لغة المستخدم
def get_user_language(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else "ar"

# تحديث لغة المستخدم
def update_user_language(user_id, language):
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()

# الحصول على إحصائيات المستخدم
def get_user_stats(user_id):
    cursor.execute("SELECT COUNT(*) FROM usage_stats WHERE user_id = ?", (user_id,))
    total_uses = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM usage_stats WHERE user_id = ?", (user_id,))
    time_data = cursor.fetchone()
    first_use = time_data[0] if time_data[0] else "N/A"
    last_use = time_data[1] if time_data[1] else "N/A"
    
    return total_uses, first_use, last_use

# لوحة تحكم للمشرف
def get_admin_keyboard(language="ar"):
    if language == "ar":
        return ReplyKeyboardMarkup(
            [
                ["📊 إحصائيات البوت", "👥 المستخدمون"],
                ["📣 إرسال رسالة للجميع", "🔙 الرجوع للرئيسية"]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            [
                ["📊 Bot Statistics", "👥 Users"],
                ["📣 Broadcast Message", "🔙 Back to Main"]
            ],
            resize_keyboard=True
        )

# معالجة أمر البدء
@Hemo.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    
    add_user(user_id, username, first_name, last_name)
    update_usage(user_id, "start")
    
    language = get_user_language(user_id)
    
    # التحقق من الاشتراك في القنوات
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        if language == "ar":
            text = "**• عذراً عزيزي 🤚\n• يجب عليك الانضمام إلى القنوات التالية أولاً:**\n\n"
            buttons = []
            for channel in REQUIRED_CHANNELS:
                text += f"• @{channel}\n"
                buttons.append([InlineKeyboardButton(f"@{channel}", url=f"https://t.me/{channel}")])
            buttons.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")])
            markup = InlineKeyboardMarkup(buttons)
        else:
            text = "**• Sorry dear 🤚\n• You must join the following channels first:**\n\n"
            buttons = []
            for channel in REQUIRED_CHANNELS:
                text += f"• @{channel}\n"
                buttons.append([InlineKeyboardButton(f"@{channel}", url=f"https://t.me/{channel}")])
            buttons.append([InlineKeyboardButton("✅ Check Subscription", callback_data="check_subscription")])
            markup = InlineKeyboardMarkup(buttons)
        
        await message.reply(text, reply_markup=markup)
        return
    
    if language == "ar":
        text = "**• هلا وسهلا بيك عزيز الانسان\n• اقدر اجيب لك قنوانك او قروباتك وحتى الي مغادر منهم 😁\n• استخدم الازرار تحت ✓**"
    else:
        text = "**• Hello and welcome dear human\n• I can get your channels or groups and even those who left them 😁\n• Use the buttons below ✓**"
    
    await message.reply(text, reply_markup=get_main_keyboard(language))
    
    # إذا كان المستخدم هو المشرف، عرض لوحة التحكم
    if user_id == ADMIN_ID:
        if language == "ar":
            await message.reply("**لوحة تحكم المشرف**", reply_markup=get_admin_keyboard(language))
        else:
            await message.reply("**Admin Control Panel**", reply_markup=get_admin_keyboard(language))

# معالجة استعلامات الزر
@Hemo.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    language = get_user_language(user_id)
    
    if data == "check_subscription":
        is_subscribed = await check_subscription(user_id)
        
        if is_subscribed:
            if language == "ar":
                text = "**• شكراً لك على الاشتراك! ✅\n• يمكنك الآن استخدام البوت**"
            else:
                text = "**• Thank you for subscribing! ✅\n• You can now use the bot**"
            
            await callback_query.message.edit_text(text)
            await callback_query.message.reply(
                text, 
                reply_markup=get_main_keyboard(language)
            )
        else:
            if language == "ar":
                text = "**• لم تنضم بعد إلى جميع القنوات المطلوبة ❌\n• يرجى الانضمام ثم المحاولة مرة أخرى**"
            else:
                text = "**• You haven't joined all required channels yet ❌\n• Please join then try again**"
            
            await callback_query.answer(text, show_alert=True)
    
    elif data.startswith("lang_"):
        new_lang = data.split("_")[1]
        update_user_language(user_id, new_lang)
        
        if new_lang == "ar":
            text = "**• تم تغيير اللغة إلى العربية ✅**"
        else:
            text = "**• Language changed to English ✅**"
        
        await callback_query.message.edit_text(text)
        await callback_query.message.reply(
            text, 
            reply_markup=get_main_keyboard(new_lang)
        )

# معالجة الرسائل النصية
@Hemo.on_message(filters.private & filters.text)
async def text_handler(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    language = get_user_language(user_id)
    
    # التحقق من الاشتراك أولاً
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        if language == "ar":
            await message.reply("**• يجب عليك الانضمام إلى القنوات المطلوبة أولاً**")
        else:
            await message.reply("**• You must join the required channels first**")
        return
    
    update_usage(user_id, text)
    
    # إذا كان المستخدم هو المشرف
    if user_id == ADMIN_ID:
        if text in ["📊 إحصائيات البوت", "📊 Bot Statistics"]:
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usage_stats")
            total_commands = cursor.fetchone()[0]
            
            if language == "ar":
                stats_text = f"""
**📊 إحصائيات البوت:**

**• إجمالي المستخدمين:** {total_users}
**• إجمالي الأوامر:** {total_commands}
"""
            else:
                stats_text = f"""
**📊 Bot Statistics:**

**• Total Users:** {total_users}
**• Total Commands:** {total_commands}
"""
            
            await message.reply(stats_text)
        
        elif text in ["👥 المستخدمون", "👥 Users"]:
            cursor.execute("SELECT user_id, username, first_name, join_date FROM users ORDER BY join_date DESC LIMIT 10")
            users = cursor.fetchall()
            
            if language == "ar":
                users_text = "**👥 آخر 10 مستخدمين:**\n\n"
            else:
                users_text = "**👥 Last 10 Users:**\n\n"
            
            for user in users:
                user_id, username, first_name, join_date = user
                username = f"@{username}" if username else "بدون معرف"
                join_date = join_date.split(".")[0] if isinstance(join_date, str) else str(join_date).split(".")[0]
                
                if language == "ar":
                    users_text += f"• {first_name} ({username}) - {join_date}\n"
                else:
                    users_text += f"• {first_name} ({username}) - {join_date}\n"
            
            await message.reply(users_text)
        
        elif text in ["📣 إرسال رسالة للجميع", "📣 Broadcast Message"]:
            if language == "ar":
                await message.reply("**• أرسل الرسالة التي تريد نشرها لجميع المستخدمين**")
            else:
                await message.reply("**• Send the message you want to broadcast to all users**")
            
            # سنقوم بتخزين حالة المستخدم للخطوة التالية
            # (هذا يحتاج إلى تنفيذ أكثر تطوراً باستخدام FSM)
        
        elif text in ["🔙 الرجوع للرئيسية", "🔙 Back to Main"]:
            await message.reply(
                "**الرئيسية**" if language == "ar" else "**Main Menu**",
                reply_markup=get_main_keyboard(language)
            )
    
    # معالجة الأزرار العادية
    elif text in ["🌐 تغيير اللغة / Change Language", "🌐 Change Language / تغيير اللغة"]:
        if language == "ar":
            await message.reply("**• اختر اللغة المفضلة:**", reply_markup=get_language_keyboard())
        else:
            await message.reply("**• Choose your preferred language:**", reply_markup=get_language_keyboard())
    
    elif text in ["📊 إحصائياتي", "📊 My Statistics"]:
        total_uses, first_use, last_use = get_user_stats(user_id)
        
        if language == "ar":
            stats_text = f"""
**📊 إحصائياتك الشخصية:**

**• عدد استخداماتك للبوت:** {total_uses}
**• أول استخدام:** {first_use}
**• آخر استخدام:** {last_use}
"""
        else:
            stats_text = f"""
**📊 Your Personal Statistics:**

**• Your total uses of the bot:** {total_uses}
**• First use:** {first_use}
**• Last use:** {last_use}
"""
        
        await message.reply(stats_text)

# معالجة مشاركات الدردشة
@Hemo.on_message(filters.private & filters.chat_shared)
async def chat_shared_handler(client, message: Message):
    user_id = message.from_user.id
    language = get_user_language(user_id)
    
    if not message.chat_shared:
        return
    
    chat_id = message.chat_shared.chat_id
    try:
        chat = await client.get_chat(chat_id)
        
        # حفظ معلومات القناة/المجموعة في قاعدة البيانات
        cursor.execute(
            "INSERT OR REPLACE INTO user_channels (user_id, channel_id, channel_username, is_owner, is_admin) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat.id, chat.username, False, True)  # هذه قيم افتراضية، تحتاج إلى تحسين
        )
        conn.commit()
        
        if language == "ar":
            text = f"""
**• تم حفظ القناة/المجموعة بنجاح ✅**

**• الاسم:** {chat.title}
**• المعرف:** @{chat.username if chat.username else 'غير متوفر'}
**• الرقم:** {chat.id}
"""
        else:
            text = f"""
**• Channel/Group saved successfully ✅**

**• Name:** {chat.title}
**• Username:** @{chat.username if chat.username else 'Not available'}
**• ID:** {chat.id}
"""
        
        await message.reply(text)
    
    except Exception as e:
        if language == "ar":
            await message.reply("**• حدث خطأ أثناء جلب معلومات القناة/المجموعة**")
        else:
            await message.reply("**• An error occurred while fetching channel/group information**")

# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    Hemo.run()
