import discord
from discord.ext import commands
from datetime import timedelta
from collections import defaultdict
import time


# =========================
# ТОКЕН
# =========================
import os

TOKEN = os.getenv("TOKEN")


# =========================
# НАСТРОЙКИ
# =========================

LOG_CHANNEL = "logs"
WELCOME_ROLE = "member"


# =========================
# INTENTS
# =========================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# АНТИСПАМ
# =========================

spam_messages = defaultdict(list)
spam_strikes = defaultdict(int)


MAX_MESSAGES = 5
TIME_WINDOW = 5


timeout_times = [
    60,      # 1 минута
    300,     # 5 минут
    600      # 10 минут
]


# =========================
# ЛОГИ
# =========================

async def send_log(guild, text):

    channel = discord.utils.get(
        guild.text_channels,
        name=LOG_CHANNEL
    )

    if channel:

        await channel.send(text)



# =========================
# ЗАПУСК
# =========================

@bot.event
async def on_ready():

    print(
        f"✅ Бот онлайн: {bot.user}"
    )



# =========================
# АВТО-РОЛЬ
# =========================

@bot.event
async def on_member_join(member):

    role = discord.utils.get(
        member.guild.roles,
        name=WELCOME_ROLE
    )


    if role:

        await member.add_roles(role)


        await send_log(
            member.guild,
            f"👋 {member.mention} вошёл на сервер\n"
            f"Выдана роль: {role.name}"
        )

    else:

        await send_log(
            member.guild,
            f"⚠️ Роль {WELCOME_ROLE} не найдена"
        )



# =========================
# АНТИСПАМ
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return


    user_id = message.author.id

    now = time.time()


    spam_messages[user_id].append(now)


    spam_messages[user_id] = [
        x for x in spam_messages[user_id]
        if now - x <= TIME_WINDOW
    ]


    if len(spam_messages[user_id]) >= MAX_MESSAGES:


        strike = spam_strikes[user_id]


        mute_time = timeout_times[strike]


        try:

            await message.author.timeout(
                timedelta(seconds=mute_time),
                reason="Спам"
            )


            await message.channel.send(
                f"🔇 {message.author.mention} получил тайм-аут "
                f"за спам на {mute_time//60} минут"
            )


            await send_log(
                message.guild,
                f"🔇 Спам\n"
                f"Пользователь: {message.author}\n"
                f"Тайм-аут: {mute_time//60} минут"
            )


            spam_strikes[user_id] += 1


            if spam_strikes[user_id] >= 3:

                spam_strikes[user_id] = 0


            spam_messages[user_id].clear()



        except Exception as e:

            print(e)



    await bot.process_commands(message)



# =========================
# КОМАНДЫ
# =========================


@bot.command()
async def ping(ctx):

    await ctx.send(
        f"🏓 Pong! {round(bot.latency*1000)}ms"
    )



@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount:int):

    await ctx.channel.purge(
        limit=amount + 1
    )


    await ctx.send(
        f"🧹 Удалено {amount} сообщений",
        delete_after=3
    )


    await send_log(
        ctx.guild,
        f"🧹 {ctx.author} удалил {amount} сообщений"
    )



@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member:discord.Member, seconds:int):

    await member.timeout(
        timedelta(seconds=seconds),
        reason="Мут"
    )


    await ctx.send(
        f"🔇 {member.mention} получил мут на {seconds} секунд"
    )


    await send_log(
        ctx.guild,
        f"🔇 {member} получил мут\n"
        f"Модератор: {ctx.author}\n"
        f"Время: {seconds} секунд"
    )



@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member:discord.Member, *, reason="Нет причины"):

    await member.kick(
        reason=reason
    )


    await ctx.send(
        f"👢 {member} был кикнут"
    )


    await send_log(
        ctx.guild,
        f"👢 {member} кикнут\n"
        f"Причина: {reason}"
    )



@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member:discord.Member, *, reason="Нет причины"):

    await member.ban(
        reason=reason
    )


    await ctx.send(
        f"🔨 {member} получил бан"
    )


    await send_log(
        ctx.guild,
        f"🔨 {member} забанен\n"
        f"Причина: {reason}"
    )



# =========================
# ЗАПУСК БОТА
# =========================

bot.run(TOKEN)