import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        'postgresql://bot_user:my_strong_password_123@localhost:5432/pressure_bot'
    )
    rows = await conn.fetch('SELECT * FROM pressure_log ORDER BY id DESC LIMIT 5')
    for row in rows:
        print(row)
    await conn.close()

asyncio.run(main())