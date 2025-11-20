import asyncio

from sqlalchemy import select
import streamlit as st
from app.database import sessionmanager
from app.models import BotVariables

# Streamlit UI
st.set_page_config(page_title="Bot Variables", layout="wide")
st.title("🧠 Bot Variables Viewer")

refresh_rate = st.sidebar.slider("Refresh every N seconds", 5, 60, 10)

placeholder = st.empty()


async def get_variables():
    async with sessionmanager.session() as session:
        result = await session.execute(select(BotVariables))
        return result.scalars().all()


async def run_loop():
    while True:
        bots = await get_variables()
        with placeholder.container():
            for bot in bots:
                st.subheader(f"🤖 Bot {bot.id}")
                st.json(bot.data)
        await asyncio.sleep(refresh_rate)


# Оборачиваем в event loop
asyncio.run(run_loop())