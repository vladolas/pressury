import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        'postgresql://bot_user:my_strong_password_123@localhost:5432/pressure_bot'
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS pressure_log (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            systolic SMALLINT NOT NULL,
            diastolic SMALLINT NOT NULL,
            pulse SMALLINT NOT NULL
        )
    ''')
    print("✅ Таблица pressure_log создана")
    await conn.close()

asyncio.run(main())