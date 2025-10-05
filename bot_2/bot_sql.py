from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
from config import BOT_TOKEN
from db import get_pool, close_pool, create_table_for_user, add_record_for_user, get_5_last_record_for_user, get_url_by_id

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [["Дай кота"], ["История"], ["Поиск по тегу"], ["Поиск id записи"], ["Справка"]],
    resize_keyboard=True,
    is_persistent=True,
)


class UserSession:
    '''
    состояние диалога конкретного пользователя
    '''

    def __init__(self, url: str | None = None, awaiting_tags: bool = False, awaiting_id: bool = False):
        self.url = url
        self.awaiting_tags = awaiting_tags
        self.awaiting_id = awaiting_id


def get_user_session(context: ContextTypes.DEFAULT_TYPE) -> UserSession:
    """Достаём/создаём сессию пользователя из context.user_data."""
    sess = context.user_data.get("user_session")
    if not isinstance(sess, UserSession):
        sess = UserSession()
        context.user_data["user_session"] = sess
    return sess


def get_info_user(update: Update):
    '''
    Получение данных о пользователе
    '''
    user_name = update.message.chat.first_name
    user_id = update.message.chat.id
    return user_name+str(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Команда /start
    '''
    await create_table_for_user(get_info_user(update))
    await update.message.reply_text("Добро пожаловать!", reply_markup=keyboard)


async def get_cat_image_url(context):
    '''
    Запрос кота
    '''
    url = "https://api.thecatapi.com/v1/images/search?limit=1"
    # достаём из context заранее созданную общую HTTP-сессию
    http_session = context.application.bot_data["http"]
    # отправлем GET-запрос по адресу url
    async with http_session.get(url) as response:
        response.raise_for_status()
        # получаем ответ от сервера, декодируем его как JSON
        data = await response.json()
        # извлекаем первый элемент из списка data, берём у него поле "url"
        return data[0]["url"]


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Получение тегов/id
    '''
    user_answer = update.message.text
    return user_answer


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Ответ пользователю
    '''
    text = update.message.text.lower()
    session_state = get_user_session(context)

    if session_state.awaiting_tags and session_state.url:
        session_state.awaiting_tags = False
        user_tag = await get_answer(update, context)
        await add_record_for_user(get_info_user(update), session_state.url, user_tag)
        session_state.url = None
        await update.message.reply_text("Теги сохранены.")
        return

    elif session_state.awaiting_id:
        session_state.awaiting_id = False
        record_id = await get_answer(update, context)
        my_url = await get_url_by_id(get_info_user(update), int(record_id))
        await update.message.reply_photo(photo=my_url)
        return

    if text == "дай кота":
        cat_url = await get_cat_image_url(context)
        await update.message.reply_photo(photo=cat_url)
        await update.message.reply_text("Введите теги для полученной картинки:", reply_markup=keyboard)
        session_state.url = cat_url
        session_state.awaiting_tags = True

    elif text == "история":
        await update.message.reply_text(await get_5_last_record_for_user(get_info_user(update)), reply_markup=keyboard)

    elif text == "поиск id записи":
        await update.message.reply_text("Введите id записи для получения картинки:")
        session_state.awaiting_id = True

    elif text == "справка":
        await update.message.reply_text("Нажмите на кнопку [Дай кота], если хотите получить фото котика. \nПосле того как посмотрите картинку бот будет ждать ввод тегов\n\n"
                                        "Если хотите посмотреть историю своих запросов нажмите [История]\n\n"
                                        "Чтобы воспользоваться поиском нажмите [Поиск по тегу]\n"
                                        "После нажатия [Поиск по тегу] бот будет ждать ввода слова для поиска\n\n"
                                        "Создатель бота: Татьяна Панцырева")
    else:
        await update.message.reply_text("Выберите действие на клавиатуре ↓", reply_markup=keyboard)

# --- хуки приложения ---


async def on_startup(app):
    # создаём пул
    await get_pool()

    # HTTP-сессия — одна на всё приложение
    timeout = aiohttp.ClientTimeout(total=15)        # общие таймауты на запрос
    connector = aiohttp.TCPConnector(limit=100)      # пул TCP-соединений
    app.bot_data["http"] = aiohttp.ClientSession(
        timeout=timeout,
        connector=connector
    )


async def on_shutdown(app):
    # закрываем пул
    await close_pool()

    # закрываем HTTP-сессию
    http: aiohttp.ClientSession | None = app.bot_data.get("http")
    if http and not http.closed:
        await http.close()

# объект Application
app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .post_init(on_startup)
    .post_shutdown(on_shutdown)
    .build()
)

# обработчик входящих сообщений
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
app.run_polling()
