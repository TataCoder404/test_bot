import asyncio
import aiomysql

from datetime import datetime, timedelta

from config import host, port, user, password, database

# глобальная переменная, в которой хранится единственный пул соединений
_pool = None
# асинхронная блокировка, чтобы защититься от ситуации, когда несколько корутин одновременно пытаются создать пул (гонка на первом вызове)
_pool_lock = asyncio.Lock()


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                _pool = await aiomysql.create_pool(
                    host=host, port=port, user=user, password=password, db=database,
                    minsize=1, maxsize=10, autocommit=True, charset="utf8mb4",
                )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def create_table_for_user(name):
    '''
    Создание таблицы для юзера
    '''
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f'''CREATE TABLE IF NOT EXISTS {name}(
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            url VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tags VARCHAR(255),
            PRIMARY KEY (id)
            );
            '''
            )


async def add_record_for_user(name, cat_url, tags):
    '''
    Создание записи в таблице юзера
    '''
    sql = f"INSERT INTO {name}(url, tags) VALUES (%s, %s)"
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (cat_url, tags))


async def get_5_last_record_for_user(name):
    '''
    Получить 5 последних записей
    '''
    sql = f"SELECT id, url, tags, created_at FROM {name} ORDER BY created_at DESC LIMIT 5;"
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()
    lines = []
    for i, (rid, url, tags, created_at) in enumerate(rows, start=1):
        tags_display = tags if tags and tags.strip() else "(без тегов)"
        lines.append(f"{i}) {tags_display}\n   {url}\n   {created_at}")

    return "\n\n".join(lines)


async def get_5_last_min_for_user(name):
    '''
    Получить записи за последние 5 минут
    '''
    limit = datetime.now()-timedelta(minutes=5)
    sql = f"SELECT id, url, tags, created_at FROM {name} WHERE created_at >= %s;"
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (limit,))
            rows = await cur.fetchall()
    lines = []
    for i, (rid, url, tags, created_at) in enumerate(rows, start=1):
        tags_display = tags if tags and tags.strip() else "(без тегов)"
        lines.append(f"{i}) {tags_display}\n   {url}\n   {created_at}")

    return "\n\n".join(lines)


async def get_url_by_id(name, record_id):
    '''
    Получить картинку по id записи
    '''
    sql = f"SELECT url FROM {name} WHERE id = %s;"
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (record_id,))
            row = await cur.fetchone()
    return row[0]
