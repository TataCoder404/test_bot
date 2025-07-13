from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import aiohttp
from config import BOT_TOKEN

#Словарь анг слов
dictionary = {
    "hello": "привет",
    "world": "мир",
    "cat": "кот",
    "dog": "собака",
    "book": "книга",
    "computer": "компьютер",
    "table": "стол",
    "chair": "стул",
    "house": "дом",
    "car": "машина",
    "tree": "дерево",
    "water": "вода",
    "food": "еда",
    "sun": "солнце",
    "moon": "луна",
    "star": "звезда",
    "school": "школа",
    "friend": "друг",
    "music": "музыка",
    "phone": "телефон"
}

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [["Дай кота"], ["Словарь"], ["Галерея"], ["Справка"]],
    resize_keyboard=True
)

# Инлайн кнопки
keyboard_inline = InlineKeyboardMarkup([
    [InlineKeyboardButton("Белки", callback_data="белки")],
    [InlineKeyboardButton("Бобры", callback_data="бобры")]
])

keyboard_inline_bobr = InlineKeyboardMarkup([
    [InlineKeyboardButton("Обыкновенный бобр", callback_data="обыкновенный")],
    [InlineKeyboardButton("Канадский бобр", callback_data="канадский")]
])

keyboard_inline_belki = InlineKeyboardMarkup([
    [InlineKeyboardButton("Персидская белка", callback_data="персидская")],
    [InlineKeyboardButton("Аризонская белка", callback_data="аризонская")],
    [InlineKeyboardButton("Саблезубая белка", callback_data="саблезубая")]
])

# Функция запроса кота
async def get_cat_image_url():
    url = "https://api.thecatapi.com/v1/images/search?limit=1"
    async with aiohttp.ClientSession() as session: #  создаём асинхронную сессию HTTP-запросов
        async with session.get(url) as response: # отправлем GET-запрос по адресу url
            data = await response.json() # получаем ответ от сервера, декодируем его как JSON
            return data[0]["url"] # извлекаем первый элемент из списка data, берём у него поле "url"


#Функция ответа пользователю
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    if context.user_data.get("awaiting_translation"):
        if text in dictionary:
            key = update.message.text.lower()
            await update.message.reply_text(dictionary[key])
        else:
            await update.message.reply_text("Такого слова нет в словаре. Нажми [Словарь], чтобы попробовать снова.", reply_markup=keyboard)

        context.user_data["awaiting_translation"] = False

    if ("привет" or "здравствуй" or "добрый день") in text:
        await update.message.reply_text("Привет! Выбери команду:", reply_markup=keyboard)

    elif text == "словарь":
        await update.message.reply_text("Напиши слово на английском, которое хочешь перевести. Если оно будет в нашем словаре - ты получишь его перевод")
        context.user_data["awaiting_translation"] = True

    elif text == "дай кота":
        cat_url = await get_cat_image_url()
        await update.message.reply_photo(photo=cat_url)

    elif text == "справка":
        await update.message.reply_text("Нажмите на кнопку [Дай кота], если хотите получить фото котика. \nЕсли хотите перевести слово с английского на русский - нажмите кнопку [Словарь]. \nЕсли хотите посмотреть классифицированные изображения - для вас кнопка [Галерея]. \n\nСоздатель бота: Татьяна Перова")

    elif text == "галерея":
        await update.message.reply_text("Кого хочешь посмотреть?", reply_markup=keyboard_inline)

# Обработчик нажитий инлайн кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "бобры":
        await query.message.reply_text("Каких именно?", reply_markup=keyboard_inline_bobr)

    elif query.data == "белки":
        await query.message.reply_text("Каких именно?", reply_markup=keyboard_inline_belki)

    elif query.data == "обыкновенный":
        await query.message.reply_photo("https://animals.pibig.info/uploads/posts/2024-02/1708671415_animals-pibig-info-p-krichashchii-bober-v-gorakh-vkontakte-1.jpg")

    elif query.data == "канадский":
        await query.message.reply_photo("https://img.freepik.com/premium-vector/beaver-standing-holding-canada-flag-with-golden-flagpole-design-cartoon-style_186298-9679.jpg")
        
    elif query.data == "персидская":
        await query.message.reply_photo("https://animals.pibig.info/uploads/posts/2023-04/1681512059_animals-pibig-info-p-persidskaya-belka-zhivotnie-vkontakte-2.jpg")

    elif query.data == "аризонская":
        await query.message.reply_photo("https://thumbs.dreamstime.com/b/%D0%B1%D0%B5%D0%BB%D0%BA%D0%B0-%D1%81%D0%B8%D0%B4%D0%B8%D1%82-%D0%BD%D0%B0-%D0%BE%D0%B4%D0%B5%D1%8F%D0%BB%D0%B5-%D1%81-%D0%BA%D0%BE%D0%BD%D1%83%D1%81%D0%BE%D0%BC-%D0%BC%D0%BE%D1%80%D0%BE%D0%B6%D0%B5%D0%BD%D0%BE%D0%B3%D0%BE-%D0%B2%D0%BE-%D1%80%D1%82%D1%83-%D1%81%D1%86%D0%B5%D0%BD%D0%B0-%D0%B8%D0%B3%D1%80%D0%B8%D0%B2%D0%B0%D1%8F-%D0%B8-380244128.jpg")

    elif query.data == "саблезубая":
        await query.message.reply_photo("https://portal-kultura.ru/upload/iblock/073/1920x.jpg")


app = ApplicationBuilder().token(BOT_TOKEN).build() # объект Application
app.add_handler(MessageHandler(filters.ALL, echo)) # обработчик входящих сообщений
app.add_handler(CallbackQueryHandler(handle_callback)) # обработчик нажатий на инлайн-кнопки
app.run_polling() # постоянный опрос серверов Telegram (режим polling)
