import pandas as pd
from typing import Optional, List
from discord.utils import MISSING
import re
import discord
import os
import json

from discord import app_commands, ui
from discord.ext import commands

import random
import mysql.connector

from gdmisc import *


def connect():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    return db


class SelectMods(ui.Modal, title="Укажите модераторов (через запятую)"):

    def __init__(
        self,
        *,
        title: str = ...,
        timeout: float | None = None,
        custom_id: str = ...,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    mods_list = ui.TextInput(
        label="Список модераторов", style=discord.TextStyle.paragraph, max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            custom_id = self.custom_id.split("_")
            staff_id = custom_id[0]
            req_id = custom_id[1]
            sender_id = int(custom_id[2])

            db = connect()
            cursor = db.cursor()

            with open("HAHAHA/config.json", "r") as file:
                config = json.load(file)
                guild_id = int(config["Server_ID"])

            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(sender_id)

            print(f"[SelectMods | staff id]: {staff_id}")
            print(f"[SelectMods | req_id]: {req_id}")

            mod_list = str(self.mods_list).split(",")
            print(f"[SelectMods | mod list]: {mod_list}")

            querry = ""
            for mod_name in mod_list:
                querry += f"({staff_id}, {req_id}, '{mod_name.replace(' ', '')}'), "

            print(f"[SelectMods | querry[:-2]]: {querry[:-2]}")

            cursor.execute(
                f"INSERT INTO helpers_sends_logs (helper_id, req_id, mod_name) VALUES {querry[:-2]}"
            )
            db.commit()

            await interaction.response.edit_message(
                content="Твоё решение успешно занесено в БД! Не забывай, что отправить уровень модераторам нужно самостоятельно!",
                view=None,
                embed=None,
                delete_after=5,
            )

            cursor.execute(
                f"INSERT INTO requests_logs (req_id, reviewer_id, reviewer_role) VALUES ({req_id}, {staff_id}, 2)"
            )
            db.commit()
            db.close()

            emb = discord.Embed(
                title="Твой уровень был отправлен модераторам",
                description=f"Хелпер {interaction.user.name} отправил твой уровень модераторам!",
            )
            emb.set_author(
                name=interaction.user.display_name, icon_url=interaction.user.avatar.url
            )
            emb.add_field(
                name="Отправлено следующим модераторам", value=", ".join(mod_list)
            )
            await member.send(embed=emb)
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "Что-то пошло не так...", ephemeral=True
            )
            db.close()


class FormForReq(ui.Modal, title="Отправка уровня хелперам"):

    level_id = ui.TextInput(
        label="ID уровня",
        style=discord.TextStyle.short,
        placeholder="87654321",
        max_length=9,
    )
    level_video_link = ui.TextInput(
        label="Ссылка на видео (только YouTube)",
        style=discord.TextStyle.short,
        placeholder="https://www.youtube.com/watch?v=...",
    )
    level_difficulty = ui.TextInput(
        label="Сложность (в звёздах)", style=discord.TextStyle.short, placeholder="10"
    )
    is_review_needed = ui.TextInput(
        label="Нужно ли ревью?",
        style=discord.TextStyle.short,
        placeholder="Оставьте это поле пустым, если ревью не требуется",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            lvl_id = int(str(self.level_id))
            lvl_link = str(self.level_video_link)
            lvl_difficulty = int(str(self.level_difficulty))
            sender_id = interaction.user.id
            is_needed = 1 if len(self.is_review_needed.value) > 0 else 0

            print(f"[FormForReq | lvl_id] : {lvl_id}")
            print(f"[FormForReq | lvl_link] : {lvl_link}")
            print(f"[FormForReq | sender_id] : {sender_id}")

            try:
                level_data = parser.get_parsed_level_data(lvl_id)
            except IndexError:
                await interaction.response.send_message(
                    f"<:no:1141747496813609011> Ошибка: указанный уровень не быль найден. Проверьте корректность введённого Вами ID, и повторите попытку!\n*Введённый ID: {lvl_id}*",
                    ephemeral=True,
                )
                return

            youtube_regex = r"^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$"
            match = re.fullmatch(youtube_regex, lvl_link.strip())
            print(match)
            print(lvl_link.find(" "))
            if match is None or lvl_link.find(" ") != -1:
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: Укажите ссылку на видео с YouTube",
                    ephemeral=True,
                )
                return

            if lvl_difficulty not in range(1, 11):
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: указанная сложность должна входить в диапазон от 1 (<:auto:1142464075964629002>) до 10 (<:demon:1141747367696154645>)!",
                    ephemeral=True,
                )
                return

            if int(level_data[3]) != 0:
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: уровень уже оценён",
                    ephemeral=True,
                )
                return

            db = connect()
            cursos = db.cursor()

            try:
                q = f"INSERT INTO requests_table (level_id, video_link, sender_id, requested_stars) VALUES ('{lvl_id}', '{lvl_link}', '{sender_id}', {lvl_difficulty})"
                print(f"[FormForReq | INSERT querry]: {q}")
                cursos.execute(q)
            except mysql.connector.Error:
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: данный уровень уже был отправлен на ревью.",
                    ephemeral=True,
                )
                db.close()
                return

            db.commit()

            await interaction.response.send_message(
                "Уровень был отправлен ревьюверам! Что дальшe?\n1. Дождись, пока ревьюверы рассмотрят твою работу\n2. Если работа достойна оценки, ревьюверу её отправляют хелперам\n3. Хелпер может отправить твою работу модератору Geometry Dash!\n\nПо итогу, твой уровень может получить рейт в игре ;)",
                ephemeral=True,
            )
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "Что-то пошло не так...", ephemeral=True
            )
            db.close()


class RequestsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            with open("config.json", "r") as file:
                config = json.load(file)

            if message.channel.id != int(config["RatesChannel"]):
                return
            id_from_message = int(message.embeds[0].footer.text[10:])
            print(f"[NEW RATED] event | id_from_message: {id_from_message}")
            db = connect()
            cursor = db.cursor()

            cursor.execute(
                "SELECT sender_id FROM requests_table WHERE level_id = '%s'",
                (id_from_message,),
            )

            isInDB = False
            member_id = None
            for x in cursor:
                isInDB = True
                member_id = int(list(x)[0])

            if isInDB:
                (
                    await message.reply(
                        f"<:starrate:1141747404283056248> Поздравляем, {message.guild.get_member(member_id).mention}, твой реквест рейтнули!"
                    )
                    if message.guild.get_member(member_id) != None
                    else ...
                )

                print(f"[LEVEL_RATE_NOTIFY]: Уровень {id_from_message} был рейтнут")

                with open("HAHAHA/killed_requests.json", "r") as file:
                    killed_reqs = json.load(file)

                killed_reqs["rated"] += 1

                with open("HAHAHA/killed_requests.json", "w") as file:
                    json.dump(killed_reqs, file, indent=2)

                cursor.execute(
                    "DELETE FROM requests_table WHERE level_id = '%s'",
                    (id_from_message,),
                )
                db.commit()
                await message.guild.get_member(239145251221012488).send(
                    f"Рейтнули, проверь: {message.channel.mention}"
                )

            db.close()
        except Exception as e:
            print(f"Ошибка при отправке сообщения о рейтнутом реквесте: {e}")
            db.close()

    async def punish_req(self, interaction: discord.Interaction):
        try:
            print(list(interaction.data.values())[0][0])
            value = list(interaction.data.values())[0][0].split("_")
            print(value)
            choose = value[0]
            req_id = value[1]
            sender_discord = value[2]

            match choose:
                case "ban":
                    db = connect()
                    cursor = db.cursor()

                    cursor.execute(
                        f"INSERT INTO bans (requester_id, reason_id) VALUES ('{sender_discord}', 1)"
                    )
                    db.commit()

                    await interaction.response.edit_message(
                        content="Репорт успешно закрыт",
                        view=None,
                        embed=None,
                        delete_after=5,
                    )

                    async for message in interaction.message.channel.history(
                        limit=None
                    ):
                        try:
                            if message.embeds[0].author.name == f"Request ID: {req_id}":
                                await message.delete()
                        except IndexError:
                            ...

                    return

                case "ignore":
                    await interaction.response.edit_message(
                        content="Репорт успешно закрыт",
                        view=None,
                        embed=None,
                        delete_after=5,
                    )

                    async for message in interaction.message.channel.history(
                        limit=None
                    ):
                        try:
                            if message.embeds[0].author.name == f"Request ID: {req_id}":
                                await message.delete()
                        except IndexError:
                            ...

                    return
        except Exception as e:
            print(e)

    async def punish_rev(self, interaction: discord.Interaction):
        try:
            value = list(interaction.data.values())[0][0].split("_")
            print(value)
            choose = value[0]
            req_id = value[1]
            staff_discord = value[2]

            match choose:
                case "clear":
                    db = connect()
                    cursor = db.cursor()

                    cursor.execute(
                        f"DELETE FROM staff WHERE user_discord = '{staff_discord}'"
                    )
                    db.commit()

                    await interaction.response.edit_message(
                        content="Репорт успешно закрыт",
                        view=None,
                        embed=None,
                        delete_after=5,
                    )
                    staff = interaction.guild.get_member(int(staff_discord))

                    emb = discord.Embed(
                        title="Вы были сняты со своей должности!",
                        description=f"Вас снял **{interaction.user.name}**",
                        color=discord.Color.red(),
                    )
                    emb.add_field(
                        name="Почему так произошло?",
                        value=f"Тебя снял с роли Мент {interaction.user.name}, так как ты злооупотреблял системой репортов по его мнению. Если это ошибка, обратись к администрации сервера",
                        inline=False,
                    )
                    emb.add_field(
                        name="Могу ли я как-то восстановиться?",
                        value="Да, можешь. Тебя не забанили, а просто сняли с тебя роль, так что, скорее всего, у тебя всё ещё есть шанс восстановиться. Уточни это у администраторов сервера и у Администрации",
                        inline=False,
                    )
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)

                    await staff.send(embed=emb)

                    async for message in interaction.message.channel.history(
                        limit=None
                    ):
                        try:
                            if message.embeds[0].author.name == f"Request ID: {req_id}":
                                await message.delete()
                        except IndexError:
                            ...

                    return

                case "ban":
                    db = connect()
                    cursor = db.cursor()

                    cursor.execute(
                        f"UPDATE staff SET user_role = 0 WHERE user_discord = '{staff_discord}'"
                    )
                    db.commit()

                    await interaction.response.edit_message(
                        content="Репорт успешно закрыт",
                        view=None,
                        embed=None,
                        delete_after=5,
                    )
                    staff = interaction.guild.get_member(int(staff_discord))

                    emb = discord.Embed(
                        title="Вы были забанены в системе RCGD бота!",
                        description=f"Вас забанил **{interaction.user.name}**",
                        color=discord.Color.red(),
                    )
                    emb.add_field(
                        name="Почему так произошло?",
                        value=f"Тебя забанил Мент {interaction.user.name}, так как ты злооупотреблял системой репортов по его мнению. Если это ошибка, обратись к администрации сервера",
                        inline=False,
                    )
                    emb.add_field(
                        name="Могу ли я как-то восстановиться?",
                        value="Увы, но нет. Бан означает, что твои нарушения были крайне серьёзными, поэтому администратору пришлось тебя забанить. Однако, есть вероятность, что это ошибка, и тебя могут разбанить. Уточняй у Администрации",
                        inline=False,
                    )
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await staff.send(embed=emb)

                    async for message in interaction.message.channel.history(
                        limit=None
                    ):
                        try:
                            if message.embeds[0].author.name == f"Request ID: {req_id}":
                                await message.delete()
                        except IndexError:
                            ...

                    return

                case "ignore":
                    await interaction.response.edit_message(
                        content="Репорт успешно закрыт",
                        view=None,
                        embed=None,
                        delete_after=5,
                    )

                    async for message in interaction.message.channel.history(
                        limit=None
                    ):
                        try:
                            if message.embeds[0].author.name == f"Request ID: {req_id}":
                                await message.delete()
                        except IndexError:
                            ...

                    return
        except Exception as e:
            print(e)

    async def punish_reviewer(self, interaction: discord.Interaction):
        custom_id = list(interaction.data.values())[0].split("_")
        staff_discord = int(custom_id[0])
        req_id = custom_id[1]

        view = ui.View()

        view.timeout = None

        emb = discord.Embed(
            title="Укажите наказание",
            description="Выберите, как нужно наказать реквестера, если нужно вообще его наказывать",
            color=discord.Color.red(),
        )
        emb.set_author(
            name=interaction.message.embeds[0].author.name,
            icon_url=interaction.message.embeds[0].author.icon_url,
        )

        punishment_menu = ui.Select(
            placeholder="Выбрать наказание",
            options=[
                discord.SelectOption(
                    label="Снять с роли",
                    description="Убрать данного Ревьювера со своей роли",
                    value=f"clear_{req_id}_{staff_discord}",
                ),
                discord.SelectOption(
                    label="Забанить",
                    description="Заблокировать данного Ревьювера в системе, тем самым он не сможет стать Ревьювером или Хелпером",
                    value=f"ban_{req_id}_{staff_discord}",
                ),
                discord.SelectOption(
                    label="Проигнорировать",
                    description="Не применять никаких санкций в отношении этого Ревьювера",
                    value=f"ignore_{req_id}_{staff_discord}",
                ),
            ],
        )

        punishment_menu.callback = self.punish_rev
        view.add_item(punishment_menu)

        await interaction.response.edit_message(content=None, embed=emb, view=view)

    async def punish_requester(self, interaction: discord.Interaction):
        custom_id = list(interaction.data.values())[0].split("_")
        sender_discord = int(custom_id[0])
        req_id = custom_id[1]

        view = ui.View()

        view.timeout = None

        emb = discord.Embed(
            title="Укажите наказание",
            description="Выберите, как нужно наказать реквестера, если нужно вообще его наказывать",
            color=discord.Color.red(),
        )
        emb.set_author(
            name=interaction.message.embeds[0].author.name,
            icon_url=interaction.message.embeds[0].author.icon_url,
        )

        punishment_menu = ui.Select(
            placeholder="Выбрать наказание",
            options=[
                discord.SelectOption(
                    label="Запретить отправлять реквесты",
                    description="Этот пользователь больше не сможет отпарвлять реквесты через /request",
                    value=f"ban_{req_id}_{sender_discord}",
                ),
                discord.SelectOption(
                    label="Проигнорировать",
                    description="Не применять никаких санкций в отношении этого пользователя",
                    value=f"ignore_{req_id}_{sender_discord}",
                ),
            ],
        )

        punishment_menu.callback = self.punish_req
        view.add_item(punishment_menu)

        await interaction.response.edit_message(content=None, embed=emb, view=view)

    # [(0) ID уровня, (1) ссылка на видос, (2) ID отправителя, (3) голосов "За", (4) голосов "Против", (5) ID реквеста]
    async def get_level_to_review(
        self, count: list, interaction: discord.Interaction, user_db, votes_to_send
    ) -> List[list]:
        try:
            print(
                f"АРГУМЕНТЫ ФУНКЦИИ:\ncount: {count}\nuser_db: {user_db}\nvotes_to_send: {votes_to_send}"
            )
            try:
                rand_id = random.choice(count)
                print(f"rand_id = {rand_id}")
            except IndexError:
                (
                    await interaction.message.delete()
                    if interaction.message != None
                    else ...
                )
                await interaction.channel.send(
                    "Для тебя уровни закончились. Попробуй немного позже",
                    delete_after=5,
                )

            db = connect()
            cursor = db.cursor()

            q = f"""
                SELECT
                    rt.level_id, rt.video_link, rt.sender_id, rt.votes_yes, rt.votes_no, rt.req_id, rt.requested_stars
                FROM
                    requests_table AS rt
                WHERE
                    rt.req_id = {rand_id}
                GROUP BY
                    rt.level_id, rt.video_link, rt.sender_id, rt.votes_yes, rt.votes_no, rt.req_id;            
                """
            print(f"[review | get_level | SELECT querry]: {q}")
            cursor.execute(q)

            level_data = []
            for x in cursor:
                level_data = list(x)

            level = parser.get_parsed_level_data(int(level_data[0]))
            print(f"level_data (ФУНКЦИЯ): {level_data}\nlevel (ФУНКЦИЯ): {level}")

            if level == None:
                try:
                    cursor.execute(
                        "DELETE FROM requests_table WHERE req_id = %s", (rand_id,)
                    )
                    db.commit()
                    count.remove(rand_id)
                    db.close()
                except Exception as e:
                    print(e)

                return await self.get_level_to_review(
                    count, interaction, user_db, votes_to_send
                )

            print(f"[review | get_level | level_data]: {level_data}")
            print(
                f'[review | get_level] Уровень найден: голосов "За" - {level_data[3]} / голосов "Против" - {level_data[4]}'
            )
            db.close()
            return [level, level_data]
        except Exception as e:
            await interaction.response.send_message(
                "Что-то пошло не так...", delete_after=5
            )
            print(e)
            db.close()
            return

    async def get_level_to_send(self, count, interaction, user_db) -> list:
        try:
            try:
                rand_id = random.choice(count)
            except IndexError:
                await interaction.response.send_message(
                    "Уровней для тебя пока что нет. Попробуй в другой раз",
                    delete_after=5,
                )
            print(f"[rate | get_level | rand_id]: {rand_id}")

            db = connect()
            cursor = db.cursor()

            q = f"""
                SELECT
                    rt.req_id,
                    rt.level_id,
                    rt.video_link,
                    rt.sender_id,
                    rt.requested_stars
                FROM
                    requests_table AS rt
                WHERE
                    rt.req_id = {rand_id} AND
                    rt.is_sent_to_h = 1 AND
                    rt.req_id NOT IN (select rl.req_id from requests_logs as rl where rl.reviewer_id = {user_db[0]});
            """
            print(f"[rate | get_level | SELECT querry]: {q}")
            cursor.execute(q)

            level_data = []
            for x in cursor:
                level_data = list(x)
            print(f"[rate | get_level | level_data]: {level_data}")

            # if len(level_data) == 0:
            #     print(f"[rate | get_level]: Уровень не обнаружен, поиск нового")
            #     db.close()
            #     return await self.get_level_to_send(count, interaction, user_db)

            return level_data
        except RecursionError:
            await interaction.response.send_message(
                "Похоже, что не нашлось уровня, который нуждается в твоей оценке",
                delete_after=5,
            )

    async def generate_level_embed(
        self, level, level_data, original_guild_id
    ) -> discord.Embed:
        try:
            emb = discord.Embed(
                title="Уровень нуждается в оценке",
                description=f"__{level[0]}__ by __{level[1]}__",
                color=discord.Color.blurple(),
            )
            print(f"[review | Embed]: Embed created")
            print(f"[review | original_guild_id]: {original_guild_id}")

            cp_count = parser.get_parsed_creator_data(level[1])
            cp_text = ""
            if cp_count == 0:
                cp_text = "У автора уровня **нет** КП"
            elif cp_count > 0 and cp_count < 30:
                cp_text = (
                    f"У автора уровня **есть** КП ({cp_count}<:cp:1141823815081545839>)"
                )
            else:
                cp_text = f"У автора уровня **много** КП ({cp_count}<:cp:1141823815081545839>)"

            dif = enums.DifficultyCalculator.get_difficulty_by_stars(level_data[6])
            emb.add_field(
                name="Инфо",
                value=f"``ID       :`` **{level[2]}**\n``СЛОЖНОСТЬ:`` {dif} **({level_data[6]}<:staar:1141766298997637190>)**\n``ЗАГРУЗКИ :`` <:download:1142445126245953576>**{level[5]}**\n``РЕЙТИНГ  :`` {'<:like:1141747466639777922>' if int(level[6]) >= 0 else '<:dislike:1141747479906373793>'}**{int(level[6])}**\n\n{cp_text}\n[**Видеопрохождение**]({level_data[1]})\n",
                inline=False,
            )
            print(f"[review | Embed]: Info field created")

            original_guild = self.bot.get_guild(int(original_guild_id))
            requester = original_guild.get_member(int(level_data[2]))

            try:
                has_avatar_or_exist = (
                    True if requester != None and requester.avatar != None else False
                )
            except:
                has_avatar_or_exist = False

            emb.set_author(
                name=f"Отправил {requester.name if requester != None else 'Неизвестно'}",
                icon_url=requester.avatar.url if has_avatar_or_exist else None,
            )
            print(f"[review | Embed]: Author placed")

            return emb
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Requests cog launched")

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Команду нельзя использовать больше **1** раза в **10** секунд!",
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = list(interaction.data.values())[0]

        if custom_id == "requestbutton":
            print("Я кнопка!")
            db = connect()
            cursosr = db.cursor()

            cursosr.execute(
                f"SELECT requester_id FROM bans WHERE requester_id = '{interaction.user.id}'"
            )
            for x in cursosr:
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: ты не можешь отправлять реквесты, так как тебя заблокировали Менты.",
                    ephemeral=True,
                )

            db.close()
            mod = FormForReq()
            await interaction.response.send_modal(mod)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if not (
            len(message.embeds) != 0 and message.embeds[0].title == "New rated level!"
        ):
            return

        emb = message.embeds[0]
        level_id = int(emb.footer.text.replace("Level ID: ", ""))
        db = connect()
        cursor = db.cursor()

        cursor.execute(
            f"SELECT req_id, sender_id FROM requests_table WHERE level_id = {level_id}"
        )

        level_data = []
        for x in cursor:
            level_data = list(x)

        if level_data != []:
            try:
                sender = message.guild.get_member(int(level_data[1]))
                level_obj = parser.get_parsed_level_data(level_id)

                new_embed = discord.Embed(
                    title="Твой реквест рейтнули!",
                    description=f"Твой реквест __{level_obj[0]}__ был оценён!",
                    color=discord.Color.green(),
                )
                new_embed.add_field(
                    name="Наши поздравления!",
                    value="Спасибо за твой реквест и искренне поздравляем с рейтом! Желаем успехов и больше удачных уровней",
                )
                new_embed.set_footer(
                    text="Команда РКГД", icon_url=message.guild.icon.url
                )
                new_embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/1140790207646552105/1141105250288287774/star.png"
                )

                await sender.send(embed=new_embed)
            except Exception:
                print(
                    f"Чё-то случилось в on_message. На инфу: {sender}, {new_embed}, {level_obj}"
                )
            finally:
                cursor.execute(
                    f"DELETE FROM requests_table WHERE req_id = {level_data[0]}"
                )
                db.close()
                return

        db.close()

    @app_commands.command(
        name="place_req_message",
        description="Отправляет в этот канал сообщение с кнопкой для реквестов",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def place_req_message(self, interaction: discord.Interaction):
        try:
            view = ui.View()

            view.timeout = None

            emb_about = discord.Embed(
                title="Здесь мы можете отправить свой уровень модераторам!",
                description="Если Вы считаете, что Ваш уровень может получить рейт, то Вы можете его отправить на рассмотрение",
                color=0xFFD02A,
            )

            emb_procces = discord.Embed(
                title="Как это работает?",
                description="Вы отправляете свой уровень, после чего его рассматривют ревьюверы, и если уровень действительно заслуживает оценки, то его будут рассматривать хелперы, и уже они будут отправлять его модераторам",
                color=0xFFB03F,
            )

            emb_rules = discord.Embed(
                title="Что может помешать отправке уровня модераторам?",
                description="Есть определённые правила для отправки реквестов, нарушая которые Вы рискуете получить временную или перманентную блокировку в системе реквестов РКГД.",
                color=0xFF9252,
            )

            emb_rules.add_field(
                name="В реквестах не приветствуются:",
                value="""
- **Рофл-реквесты**: присылайте только серьёзные уровни, цените труд ревьюверов и хелперов.
- **Музыка не с Newgrounds**: уровни с такой музыкой отправляться на рейт не будут. Это не наше требование, а требование большинства модераторов и от части самого РобТопа.
- **Оффтоп запрещён**: отправка левых уровней с ссылками не по теме так же приводят к вашему бану в системе РКГД.
- **NSFW и NSFL уровни запрещены!**""",
            )
            emb_rules.set_footer(
                text="discord.gg/rcgd", icon_url=self.bot.user.avatar.url
            )

            req_but = ui.Button(
                label="Отправить уровень",
                style=discord.ButtonStyle.red,
                custom_id="requestbutton",
                emoji="<:starrate:1141747404283056248>",
            )
            view.add_item(req_but)

            await interaction.channel.send(
                embeds=[emb_about, emb_procces, emb_rules], view=view
            )
            await interaction.response.send_message(
                "Сообщение установлено!", ephemeral=True
            )
        except Exception as e:
            print(e)

    @app_commands.command(name="request", description="Отправляет уровень на оценку")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=10)
    async def request(self, interaction: discord.Interaction):
        try:
            db = connect()
            cursosr = db.cursor()

            cursosr.execute(
                f"SELECT requester_id FROM bans WHERE requester_id = '{interaction.user.id}'"
            )
            for x in cursosr:
                await interaction.response.send_message(
                    "<:no:1141747496813609011> Ошибка: ты не можешь отправлять реквесты, так как тебя заблокировали Менты.",
                    ephemeral=True,
                )
            mod = FormForReq()
            await interaction.response.send_modal(mod)
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "Что-то пошло не так при исполнении команды...", ephemeral=True
            )

    @app_commands.command(
        name="review", description="Команда для ревьюверов: позволяет оценивать уровни"
    )
    async def review(self, interaction: discord.Interaction):
        try:
            db = connect()
            cursor = db.cursor()
            view = ui.View()

            view.timeout = None

            q = f"""
                SELECT 
                    s.id, 
                    s.user_role
                FROM 
                    staff AS s 
                WHERE 
                    s.user_discord = '{interaction.user.id}' AND s.user_role = 1
                """

            print(f"[review | SELECT querry]: {q}")
            cursor.execute(q)

            user_db = []
            for x in cursor:
                user_db = list(x)

            print(f"[review | user_db]: {user_db}")
            print(f"[review | len(user_db)]: {len(user_db)}")

            if len(user_db) == 0:
                await interaction.response.send_message(
                    "Ты не можешь использовать эту команду, так как не являешься ревьювером",
                    delete_after=5,
                )
                db.close()
                return

            if user_db[1] != 1:
                await interaction.response.send_message(
                    "Ты не можешь использовать эту команду, так как не являешься ревьювером",
                    delete_after=5,
                )
                db.close()
                return

            await interaction.response.defer(thinking=True)

            q = f"SELECT req_id FROM requests_table WHERE is_sent_to_h = 0 AND req_id NOT IN(select req_id from requests_logs where reviewer_id = {user_db[0]})"
            print(f"[review | SELECT querry]: {q}")
            cursor.execute(q)

            count = []
            for x in cursor:
                count.append(list(x)[0])

            if count == []:
                await interaction.followup.send("Пока что, уровней на оценку нет")
                db.close()
                return

            with open("HAHAHA/config.json", "r") as file:
                config = json.load(file)
                votes_to_send = config["VotesToAdvance"]
                original_guild_id = int(config["Server_ID"])

            print(f"[review | config]: {config}")
            print(f"[review | votes_to_send]: {votes_to_send}")
            print(f"[review | original_guild_id]: {original_guild_id}")

            level_data = await self.get_level_to_review(
                count, interaction, user_db, votes_to_send
            )  # [(0) ID уровня, (1) ссылка на видос, (2) ID отправителя, (3) голосов "За", (4) голосов "Против", (5) ID реквеста]

            level = level_data[0]
            level_data = level_data[1]
            print(f"[review | level_data]: {level_data}")
            print(f"[review | level]: {level}")

            emb = await self.generate_level_embed(level, level_data, original_guild_id)

            yes_button = ui.Button(
                label="За",
                style=discord.ButtonStyle.green,
                custom_id=f"yes_{original_guild_id}_{level_data[5]}_{votes_to_send}_{user_db[0]}_{level_data[3]+level_data[4]}_{level_data[4]}",
                emoji="<:yes:1141747509899841637>",
            )
            no_button = ui.Button(
                label="Против",
                style=discord.ButtonStyle.red,
                custom_id=f"no_{original_guild_id}_{level_data[5]}_{votes_to_send}_{user_db[0]}_{level_data[3]+level_data[4]}_{level_data[4]}",
                emoji="<:no:1141747496813609011>",
            )
            report_button = ui.Button(
                label="Репорт",
                style=discord.ButtonStyle.red,
                custom_id=f"{level_data[5]}_{user_db[0]}_{level[2]}_{level_data[6]}_{original_guild_id}_{level_data[3]+level_data[4]}_{level_data[4]}",
                emoji="<:report:1141769582378496091>",
            )
            finish_button = ui.Button(
                label="Закончить",
                style=discord.ButtonStyle.gray,
                custom_id=f"finish",
                row=4,
            )

            async def yes_no_callback(interaction: discord.Interaction):
                try:
                    await interaction.message.delete()
                    await interaction.response.defer(thinking=True)

                    view = ui.View()
                    db = connect()
                    cursor = db.cursor()

                    custom_id = list(interaction.data.values())[0].split("_")
                    yes_no = custom_id[0]
                    original_guild_id = int(custom_id[1])
                    req_id = int(custom_id[2])
                    votes_to_send = int(custom_id[3])
                    staff_id = int(custom_id[4])
                    overall_votes = int(custom_id[5])
                    disagree = int(custom_id[6])

                    # if overall_votes == 0:
                    #     print()

                    if yes_no != "afterrep":
                        try:
                            cursor.execute(
                                "INSERT INTO requests_logs (req_id, reviewer_id, reviewer_role) VALUES (%s, %s, 1)",
                                (req_id, staff_id),
                            )
                            cursor.execute(
                                f"UPDATE requests_table SET votes_{yes_no} = votes_{yes_no}+1 WHERE req_id = {req_id}"
                            )
                            cursor.execute(
                                "UPDATE requests_table SET is_sent_to_h = IF(votes_yes+votes_no>=%s, 1, 0) WHERE req_id = %s",
                                (votes_to_send, req_id),
                            )
                            cursor.execute(
                                "DELETE FROM requests_table WHERE votes_no > votes_yes AND is_sent_to_h = 1 AND req_id = %s",
                                (req_id,),
                            )

                            with open("HAHAHA/killed_requests.json", "r") as file:
                                killed_req = json.load(file)

                            print(killed_req)
                            killed_req["rejected"] = (
                                int(killed_req["rejected"]) + 1
                                if overall_votes >= votes_to_send
                                and disagree > overall_votes - disagree
                                else killed_req["rejected"]
                            )

                            with open("HAHAHA/killed_requests.json", "w") as file:
                                json.dump(killed_req, file, indent=2)

                            db.commit()
                        except Exception as e:
                            db.rollback()
                            await interaction.followup.send(
                                f"Что-то пошло не так...\nОшибка: {e}", ephemeral=True
                            )
                            return

                    view.timeout = None

                    q = f"""
                        SELECT 
                            s.id, 
                            s.user_role 
                        FROM 
                            staff AS s 
                        WHERE 
                            s.user_discord = '{interaction.user.id}' AND s.user_role = 1
                        """

                    print(f"[review | SELECT querry]: {q}")
                    cursor.execute(q)

                    user_db = []
                    for x in cursor:
                        user_db = list(x)

                    print(f"[review | user_db]: {user_db}")
                    print(f"[review | len(user_db)]: {len(user_db)}")

                    q = f"SELECT req_id FROM requests_table WHERE is_sent_to_h = 0 AND req_id NOT IN(select req_id from requests_logs where reviewer_id = {user_db[0]})"
                    print(f"[review | SELECT querry]: {q}")
                    cursor.execute(q)

                    count = []
                    for x in cursor:
                        count.append(list(x)[0])
                    print(count)

                    level_data = await self.get_level_to_review(
                        count, interaction, user_db, votes_to_send
                    )
                    level = level_data[0]
                    level_data = level_data[1]

                    print(f"[review | level_data]: {level_data}")
                    print(f"[review | level]: {level}")

                    emb = await self.generate_level_embed(
                        level, level_data, original_guild_id
                    )

                    yes_button = ui.Button(
                        label="За",
                        style=discord.ButtonStyle.green,
                        custom_id=f"yes_{original_guild_id}_{level_data[5]}_{votes_to_send}_{staff_id}_{overall_votes}_{disagree}",
                        emoji="<:yes:1141747509899841637>",
                    )
                    no_button = ui.Button(
                        label="Против",
                        style=discord.ButtonStyle.red,
                        custom_id=f"no_{original_guild_id}_{level_data[5]}_{votes_to_send}_{staff_id}_{overall_votes}_{disagree}",
                        emoji="<:no:1141747496813609011>",
                    )
                    report_button = ui.Button(
                        label="Репорт",
                        style=discord.ButtonStyle.red,
                        custom_id=f"{level_data[5]}_{user_db[0]}_{level[2]}_{level_data[6]}_{original_guild_id}_{overall_votes}_{disagree}",
                        emoji="<:report:1141769582378496091>",
                    )
                    finish_button = ui.Button(
                        label="Закончить",
                        style=discord.ButtonStyle.gray,
                        custom_id=f"finish",
                        row=4,
                    )

                    yes_button.callback = yes_no_callback
                    no_button.callback = yes_no_callback
                    report_button.callback = report_callback
                    finish_button.callback = finish_callback

                    view.add_item(yes_button)
                    view.add_item(no_button)
                    view.add_item(report_button)
                    view.add_item(finish_button)

                    await interaction.followup.send(content=None, embed=emb, view=view)

                except Exception as e:
                    print(e)

            async def finish_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(
                    content="Завершаем...", embed=None, view=None, delete_after=5
                )

            async def report_callback(interaction: discord.Interaction):
                try:
                    db = connect()
                    cursor = db.cursor()
                    view = ui.View()

                    view.timeout = None

                    custom_id = list(interaction.data.values())[0].split("_")
                    req_id = custom_id[0]
                    staff_id = custom_id[1]
                    level_id = int(custom_id[2])
                    requested_stars = int(custom_id[3])
                    original_guild_id = int(custom_id[4])
                    overall_votes = int(custom_id[5])
                    disagree = int(custom_id[6])

                    cursor.execute(
                        f"SELECT video_link, sender_id FROM requests_table WHERE req_id = {req_id}"
                    )
                    sender_id = ""
                    link = ""
                    for x in cursor:
                        link = list(x)[0]
                        sender_id = int(list(x)[1])

                    print(f"[review | report_callback | req_id]: {req_id}")
                    print(f"[review | report_callback | staff_id]: {staff_id}")

                    q = f"INSERT INTO reports (req_id, staff_id, report_type) VALUES ({req_id}, {staff_id}, 1)"
                    print(f"[review | report_callback | INSERT querry]: {q}")
                    cursor.execute(q)
                    db.commit()

                    q = f"INSERT INTO requests_logs (req_id, reviewer_id, reviewer_role) VALUES ({req_id}, {staff_id}, 3)"
                    print(f"[review | report_callback | INSERT querry]: {q}")
                    cursor.execute(q)
                    db.commit()

                    yes_button = ui.Button(
                        label="Да",
                        style=discord.ButtonStyle.green,
                        custom_id=f"afterrep_{original_guild_id}_{req_id}_{votes_to_send}_{staff_id}_{overall_votes}_{disagree}",
                        emoji="<:yes:1141747509899841637>",
                    )
                    finish_button = ui.Button(
                        label="Закончить",
                        style=discord.ButtonStyle.gray,
                        custom_id=f"finish",
                    )

                    yes_button.callback = yes_no_callback
                    finish_button.callback = finish_callback

                    view.add_item(yes_button)
                    view.add_item(finish_button)

                    await interaction.response.edit_message(
                        content="<:yes:1141747509899841637> Твой репорт был отправлен. Скоро менты его рассмотрят.\nПродолжишь смотреть уровни?",
                        embed=None,
                        view=view,
                    )
                    view.clear_items()

                    dif = enums.DifficultyCalculator.get_difficulty_by_stars(
                        requested_stars
                    )
                    level_data = parser.get_parsed_level_data(level_id)
                    emb = discord.Embed(
                        title="Новый репорт!",
                        description=f"Ревьювер __{interaction.user.name}__ создал новый репорт на уровень __{level_data[0]}__",
                        color=discord.Color.red(),
                    )
                    emb.set_author(
                        name=f"Request ID: {req_id}",
                        icon_url=interaction.user.avatar.url,
                    )
                    emb.add_field(
                        name="Об уровне",
                        value=f"``ID       :`` **{level_id}**\n``СЛОЖНОСТЬ:`` {dif} **({requested_stars}<:staar:1141766298997637190>)**\n``ЗАГРУЗКИ :`` <:download:1142445126245953576>**{level_data[5]}**\n``РЕЙТИНГ  :`` {'<:like:1141747466639777922>' if int(level_data[6]) >= 0 else '<:dislike:1141747479906373793>'}**{int(level_data[6])}**\n\n[**Видеопрохождение**]({link})\n",
                    )

                    punish_requester = ui.Button(
                        label="Наказать реквестера",
                        style=discord.ButtonStyle.red,
                        custom_id=f"{sender_id}_{req_id}_req",
                    )
                    punish_reviewer = ui.Button(
                        label="Ложный репорт",
                        style=discord.ButtonStyle.grey,
                        custom_id=f"{interaction.user.id}_{req_id}_rep",
                    )

                    punish_requester.callback = self.punish_requester
                    punish_reviewer.callback = self.punish_reviewer

                    view.add_item(punish_requester)
                    view.add_item(punish_reviewer)

                    with open("HAHAHA/config.json", "r") as file:
                        config = json.load(file)
                        guild_id = int(config["Server_ID"])
                        report_channel = int(config["ReportChannel"])

                    guild = self.bot.get_guild(guild_id)
                    channel = guild.get_channel(report_channel)

                    await channel.send(embed=emb, view=view)

                    db.close()
                except Exception as e:
                    print(e)
                    await interaction.response.send_message(
                        "Что-то пошло не так...", ephemeral=True
                    )
                    db.close()

            yes_button.callback = yes_no_callback
            no_button.callback = yes_no_callback
            report_button.callback = report_callback
            finish_button.callback = finish_callback

            view.add_item(yes_button)
            view.add_item(no_button)
            view.add_item(report_button)
            view.add_item(finish_button)

            await interaction.followup.send(embed=emb, view=view)
            db.close()
        except Exception as e:
            print(e)
            if interaction.response.is_done():
                await interaction.followup.send(
                    "Что-то пошло не так. В случае использования этой команды, вполне вероятно, что закончились уровни на оценку. Попробуй немного позже",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "Что-то пошло не так. В случае использования этой команды, вполне вероятно, что закончились уровни на оценку. Попробуй немного позже",
                    ephemeral=True,
                )
            db.close()

    @app_commands.command(
        name="rate", description="Команда для хелперов: позволяет оценивать уровни"
    )
    async def rate(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            db = connect()
            cursor = db.cursor()
            view = ui.View()

            view.timeout = None

            with open("HAHAHA/config.json", "r") as file:
                config = json.load(file)
                original_guild_id = int(config["Server_ID"])
                votes_to_advance = int(config["VotesToAdvance"])

            q = f"SELECT id, user_role FROM staff WHERE user_discord = '{interaction.user.id}' AND user_role = 2"
            print(f"[rate | SELECT querry]: {q}")

            cursor.execute(q)
            user_db = []
            for x in cursor:
                user_db = list(x)

            print(f"[rate | user_db]: {user_db}")
            print(f"[rate | len(user_db)]: {len(user_db)}")

            if len(user_db) == 0:
                await interaction.followup.send(
                    "Ты не можешь использовать эту команду, так как не являешься хелпером",
                    ephemeral=True,
                )
                db.close()
                return

            q = f"SELECT req_id FROM requests_table WHERE is_sent_to_h = 1 AND req_id NOT IN (select req_id from requests_logs where reviewer_id = {user_db[0]})"
            print(f"[rate | SELECT querry]: {q}")
            cursor.execute(q)
            count = []
            for x in cursor:
                count.append(list(x)[0])

            print(f"[rate | count]: {count}")

            if count == []:
                await interaction.followup.send(
                    "Пока что, уровней на оценку нет", delete_after=5
                )
                db.close()
                return

            # try:
            #     count = [count[0], count[len(count)-1]]
            # except IndexError:
            #     await interaction.followup.send("Похоже, не нашлось уровней, которые нуждаются в отправке модераторам", delete_after=5)
            #     return

            level_data = await self.get_level_to_send(count, interaction, user_db)
            print(f"[rate | level_data]: {level_data}")
            level = parser.get_parsed_level_data(int(level_data[1]))
            print(f"[rate | level]: {level}")
            dif = enums.DifficultyCalculator.get_difficulty_by_stars(int(level_data[4]))
            print(dif)

            emb = discord.Embed(
                title="Уровень нуждается в оценке",
                description=f"__{level[0]}__ by __{level[1]}__",
                color=discord.Color.blurple(),
            )
            emb.add_field(
                name="Инфо",
                value=f"``ID       :`` **{level[2]}**\n``СЛОЖНОСТЬ:`` {dif} **({level_data[4]}<:staar:1141766298997637190>)**\n``ЗАГРУЗКИ :`` <:download:1142445126245953576>**{level[5]}**\n``РЕЙТИНГ  :`` {'<:like:1141747466639777922>' if int(level[6]) >= 0 else '<:dislike:1141747479906373793>'}**{int(level[6])}**\n[**Видеопрохождение**]({level_data[2]})\n",
            )

            original_guild = self.bot.get_guild(original_guild_id)
            print(f"[rate | original guild]: {original_guild}")
            print(f"[rate | level_data[3]]: {level_data[3]}")
            requester = original_guild.get_member(int(level_data[3]))

            print(f"[rate | requester]: {requester}")

            q = f"SELECT mod_name FROM helpers_sends_logs WHERE req_id = {level_data[0]}"
            print(f"[rate | SELECT querry]: {q}")
            cursor.execute(q)

            mods = ""
            for x in cursor:
                print(f"[rate | list(x)]: {list(x)}")
                mods += f"{list(x)[0]} "

            print(f"[rate | mods]: {mods}")

            icon = None
            if requester != None:
                print()
                icon = requester.avatar.url if requester.avatar != None else None

            emb.set_author(
                name=f"Отправил {requester.name if requester != None else 'Неизвестно'}",
                icon_url=icon,
            )
            print(f"[rate | Embed]: Author placed")
            emb.add_field(
                name="Им уже отправили",
                value=(
                    mods
                    if len(mods) > 0
                    else "Данный уровень, пока что, никому не был отправлен"
                ),
            )
            print(f"[rate | Embed]: Mods field added")

            send_button = ui.Button(
                label="Отправить",
                style=discord.ButtonStyle.blurple,
                custom_id=f"{user_db[0]}_{level_data[0]}_{level_data[3]}_send",
            )
            check_sends = ui.Button(
                label="Актуальные сенды",
                style=discord.ButtonStyle.green,
                custom_id=f"{level_data[0]}_check",
            )
            get_data = ui.Button(
                label="Получить данные уровня",
                style=discord.ButtonStyle.gray,
                custom_id=f"{level_data[0]}_data",
            )
            cancel = ui.Button(
                label="Не оценивать",
                style=discord.ButtonStyle.red,
                custom_id=f"{user_db[0]}_{level_data[0]}_{level_data[3]}_cancel",
                row=4,
            )

            async def send_callback(interaction: discord.Interaction):
                try:
                    custom_id = list(interaction.data.values())[0].split("_")
                    mne_o4enb_lenb = list(interaction.data.values())[
                        0
                    ]  # Ебись в рот, нормальный код
                    print(f"[custom_id]: {custom_id}")
                    staff_id = custom_id[0]
                    req_id = custom_id[1]
                    type = custom_id[3]
                    print(f"[type]: {type}")

                    if type == "cancel":
                        cursor.execute(
                            f"INSERT INTO helpers_sends_logs (helper_id, req_id, mod_name) VALUES ({staff_id}, {req_id}, 'skip')"
                        )
                        db.commit()
                        cursor.execute(
                            f"INSERT INTO requests_logs (req_id, reviewer_id, reviewer_role) VALUES ({req_id}, {staff_id}, 2)"
                        )
                        db.commit()
                        await interaction.response.edit_message(
                            content="Уровень пропущен!",
                            view=None,
                            embed=None,
                            delete_after=5,
                        )
                        db.close()
                        return

                    modal = SelectMods(
                        custom_id=mne_o4enb_lenb,
                        title="Укажите модераторов (через запятую)",
                        bot=self.bot,
                    )  # Пошёл нахуй
                    await interaction.response.send_modal(modal)
                except Exception as e:
                    print(e)
                    await interaction.response.send_message(
                        "Что-то пошло не так...", ephemeral=True
                    )

            async def check_callback(interaction: discord.Interaction):
                try:
                    db = connect()
                    cursor = db.cursor()
                    custom_id = list(interaction.data.values())[0].split("_")
                    req_id = custom_id[0]

                    cursor.execute(
                        f"SELECT mod_name FROM helpers_sends_logs WHERE req_id = {req_id}"
                    )
                    mods = ""
                    for x in cursor:
                        mods += f"{list(x)[0]}\n" if list(x)[0] != "skip" else ...

                    if len(mods) == 0:
                        await interaction.response.send_message(
                            "Данный уровень ещё не был отправлен ни одному модератору",
                            ephemeral=True,
                        )
                        db.close()
                        return

                    await interaction.response.send_message(
                        f"Уровень был отправлен следующим модераторам:\n{mods}",
                        ephemeral=True,
                    )

                except Exception as e:
                    print(e)
                    await interaction.response.send_message(
                        "Что-то пошло не так...", ephemeral=True
                    )
                    db.close()

            async def get_data_callback(interaction: discord.Interaction):
                try:
                    db = connect()
                    cursor = db.cursor()

                    custom_id = list(interaction.data.values())[0].split("_")
                    req_id = custom_id[0]

                    send_text = "**Данные этого уровня**\n"

                    cursor.execute(
                        f"SELECT level_id, video_link, requested_stars FROM requests_table WHERE req_id = {req_id}"
                    )
                    level_id = ""
                    level_link = ""
                    level_rs = 0
                    for x in cursor:
                        level_id = int(list(x)[0])
                        level_link = list(x)[1]
                        level_rs = int(list(x)[2])

                    level = parser.get_parsed_level_data(level_id)
                    send_text += f"ID: {level_id}\n"
                    send_text += f"Creator: {level[1]}\n"
                    send_text += f"Requested stars: {level_rs}\n"
                    send_text += f"Video link: {level_link}\n"

                    await interaction.response.send_message(send_text, ephemeral=True)
                except Exception as e:
                    print(e)
                    await interaction.response.send_message(
                        "Что-то пошло не так...", ephemeral=True
                    )
                    db.close()

            send_button.callback = send_callback
            check_sends.callback = check_callback
            get_data.callback = get_data_callback
            cancel.callback = send_callback

            view.add_item(send_button)
            view.add_item(check_sends)
            view.add_item(get_data)
            view.add_item(cancel)

            await interaction.followup.send(embed=emb, view=view)
        except Exception as e:
            print(e)
            await interaction.followup.send("Что-то пошло не так...", ephemeral=True)
            db.close()

    @app_commands.command(
        name="revstats", description="Вызов меню для получения статистики из бота"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def rev_stats(self, interaction: discord.Interaction):

        menu_emb = discord.Embed(
            title="Меню статистики",
            description="Здесь можно посмотреть всю статистику о реквестах, работе стафф состава и т.д.",
            color=discord.Color.purple(),
        )

        view = ui.View()
        view.timeout = None

        async def download_callback(interaction: discord.Interaction):
            try:
                db = connect()
                cursor = db.cursor()
                data = list(interaction.data.values())[0]

                match data:
                    case "rev":
                        cursor.execute(
                            """SELECT
                                staff.user_discord AS admin_discord,
                                COUNT(requests_logs.req_id) AS request_count
                            FROM
                                staff
                            LEFT JOIN
                                requests_logs
                            ON
                                staff.id = requests_logs.reviewer_id
                            WHERE
                                staff.user_role = 1
                            GROUP BY
                                staff.user_discord
                            ORDER BY
                                request_count DESC
                        """
                        )

                        sql_data = cursor.fetchall()

                        i = 0
                        guild = interaction.guild

                        for d_id in sql_data:
                            print(f"{d_id}: {guild.get_member(int(d_id[0]))}")
                            name = (
                                guild.get_member(int(d_id[0])).name
                                if guild.get_member(int(d_id[0])) != None
                                else d_id[0]
                            )
                            sql_data[i] = (name, d_id[1])
                            i += 1

                        df = pd.DataFrame(
                            sql_data, columns=["Ревьювер", "Кол-во оценок"]
                        )
                        writer = pd.ExcelWriter("rev_stats.xlsx")
                        df.to_excel(writer, sheet_name="RevStats", index=False)
                        writer.close()

                        f = open("rev_stats.xlsx", "rb")
                        file = discord.File(f)

                        await interaction.response.edit_message(
                            content="Excel файл",
                            embed=None,
                            view=None,
                            attachments=[file],
                        )
                        f.close()
                        os.remove("rev_stats.xlsx")

                    case "help":
                        cursor.execute(
                            """SELECT
                                staff.user_discord AS admin_discord,
                                COUNT(requests_logs.req_id) AS request_count
                            FROM
                                staff
                            LEFT JOIN
                                requests_logs
                            ON
                                staff.id = requests_logs.reviewer_id
                            WHERE
                                staff.user_role = 2
                            GROUP BY
                                staff.user_discord
                            ORDER BY
                                request_count DESC
                        """
                        )
                        sql_data = cursor.fetchall()

                        i = 0
                        guild = interaction.guild

                        for d_id in sql_data:
                            name = (
                                guild.get_member(int(d_id[0])).name
                                if guild.get_member(int(d_id[0])) != None
                                else d_id[0]
                            )
                            sql_data[i] = (name, d_id[1])
                            i += 1

                        df = pd.DataFrame(sql_data, columns=["Хелпер", "Кол-во оценок"])
                        writer = pd.ExcelWriter("help_stats.xlsx")
                        df.to_excel(writer, sheet_name="HelpStats", index=False)
                        writer.close()

                        f = open("help_stats.xlsx", "rb")
                        file = discord.File(f)

                        await interaction.response.edit_message(
                            content="Excel файл",
                            embed=None,
                            view=None,
                            attachments=[file],
                        )
                        f.close()
                        os.remove("help_stats.xlsx")

                    case "req":
                        cursor.execute(
                            """SELECT 
                                rt.level_id,
                                rt.video_link,
                                rt.sender_id,
                                rt.is_sent_to_h,
                                rt.votes_yes,
                                rt.votes_no,
                                rt.requested_stars
                            FROM
                                requests_table AS rt
                        """
                        )

                        sql_data = cursor.fetchall()
                        df = pd.DataFrame(
                            sql_data,
                            columns=[
                                "ID уровня",
                                "Ссылка",
                                "ID реквестера",
                                "Прошёл отбор?",
                                'Голосов "За"',
                                'Голосов "Против"',
                                "Сложность",
                            ],
                        )
                        writer = pd.ExcelWriter("reqs_stats.xlsx")
                        df.to_excel(writer, sheet_name="ReqsStats", index=False)
                        writer.close()

                        f = open("reqs_stats.xlsx", "rb")
                        file = discord.File(f)

                        await interaction.response.edit_message(
                            content="Excel файл",
                            embed=None,
                            view=None,
                            attachments=[file],
                        )
                        f.close()
                        os.remove("reqs_stats.xlsx")

            except Exception as e:
                print(e)

        async def callback(interaction: discord.Interaction):
            try:
                view = ui.View()
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message(
                        "Для просмотра статистики необходимы права Администратора",
                        ephemeral=True,
                    )
                    return

                db = connect()
                cursor = db.cursor()
                data = list(interaction.data.values())[0]

                match data:
                    case "rev":
                        view.clear_items()
                        emb = discord.Embed(
                            title="Статистика по ревьюверам",
                            description="**ПРИМЕЧАНИЕ**\nЗдесь указана статистика с учётом реквестов, которые ещё не были удалены из БД",
                            color=discord.Color.purple(),
                        )

                        cursor.execute(
                            """SELECT
                                staff.id AS admin_id,
                                staff.user_discord AS admin_discord,
                                staff.user_role AS admin_role,
                                COUNT(requests_logs.req_id) AS request_count
                            FROM
                                staff
                            LEFT JOIN
                                requests_logs
                            ON
                                staff.id = requests_logs.reviewer_id
                            WHERE
                                staff.user_role = 1
                            GROUP BY
                                staff.id, staff.user_discord, staff.user_role
                            ORDER BY
                                request_count DESC
                        """
                        )

                        string = ""
                        for x in cursor:
                            d = list(x)
                            user = interaction.guild.get_member(int(d[1]))
                            req_counter = d[3]

                            string += f"**{user.name if user != None else d[1]}**\n*Отправлено {req_counter}*\n\n"

                        file_button = ui.Button(
                            label="Скачать Excel файл",
                            style=discord.ButtonStyle.gray,
                            custom_id=data,
                        )
                        file_button.callback = download_callback

                        view.add_item(file_button)

                        emb.add_field(name="Список ревьюверов", value=string)

                        await interaction.response.send_message(
                            embed=emb, view=view, ephemeral=True
                        )

                        db.close()

                    case "help":
                        view.clear_items()
                        emb = discord.Embed(
                            title="Статистика по хелперам",
                            description="**ПРИМЕЧАНИЕ**\nЗдесь указана статистика с учётом реквестов, которые ещё не были удалены из БД",
                            color=discord.Color.purple(),
                        )

                        cursor.execute(
                            """SELECT
                                staff.id AS admin_id,
                                staff.user_discord AS admin_discord,
                                staff.user_role AS admin_role,
                                COUNT(requests_logs.req_id) AS request_count
                            FROM
                                staff
                            LEFT JOIN
                                requests_logs
                            ON
                                staff.id = requests_logs.reviewer_id
                            WHERE
                                staff.user_role = 2
                            GROUP BY
                                staff.id, staff.user_discord, staff.user_role
                            ORDER BY
                                request_count DESC
                        """
                        )

                        string = ""
                        for x in cursor:
                            d = list(x)
                            user = interaction.guild.get_member(int(d[1]))
                            req_counter = d[3]

                            string += f"**{user.name if user != None else d[1]}**\n*Отправлено {req_counter}*\n\n"

                        emb.add_field(name="Список хелперов", value=string)

                        file_button = ui.Button(
                            label="Скачать Excel файл",
                            style=discord.ButtonStyle.gray,
                            custom_id=data,
                        )
                        file_button.callback = download_callback

                        view.add_item(file_button)

                        await interaction.response.send_message(
                            embed=emb, view=view, ephemeral=True
                        )

                        db.close()

                    case "req":
                        view.clear_items()
                        emb = discord.Embed(
                            title="Статистика по реквестам",
                            description="**ПРИМЕЧАНИЕ**\nЗдесь указана статистика по реквестам, считая удалённые, начиная с 27.11.23",
                            color=discord.Color.purple(),
                        )

                        cursor.execute(
                            """SELECT
                                COUNT(rt.req_id) AS request_count
                            FROM
                                requests_table as rt
                        """
                        )

                        with open("HAHAHA/killed_requests.json", "r") as file:
                            stats = json.load(file)

                        overall = 0
                        inDB = 0
                        for x in cursor:
                            inDB = int(list(x)[0])
                            overall = int(list(x)[0])
                            overall += (
                                stats["rated"] + stats["deleted"] + stats["rejected"]
                            )

                        emb.add_field(
                            name=f"Всего реквестов: {overall}",
                            value=f"На оценке (существуют): **{inDB}** \nРейтнуто: **{stats['rated']}** \nУдалено (Пустые реквесты): **{stats['deleted']}** \nОтклонено: **{stats['rejected']}**",
                        )

                        file_button = ui.Button(
                            label="Скачать Excel файл",
                            style=discord.ButtonStyle.gray,
                            custom_id=data,
                        )
                        file_button.callback = download_callback

                        view.add_item(file_button)

                        await interaction.response.send_message(
                            embed=emb, view=view, ephemeral=True
                        )

                        db.close()
            except Exception as e:
                print(e)

        view.timeout = None
        b_rev = ui.Button(
            label="Ревьюверы", custom_id="rev", style=discord.ButtonStyle.blurple
        )
        b_rev.callback = callback
        view.add_item(b_rev)

        b_rev = ui.Button(
            label="Хелперы", custom_id="help", style=discord.ButtonStyle.blurple
        )
        b_rev.callback = callback
        view.add_item(b_rev)

        b_rev = ui.Button(
            label="Реквесты", custom_id="req", style=discord.ButtonStyle.blurple
        )
        b_rev.callback = callback
        view.add_item(b_rev)

        await interaction.response.send_message(embed=menu_emb, view=view)


async def setup(bot):
    await bot.add_cog(RequestsCog(bot))
