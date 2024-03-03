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
        password=os.getenv("DB_PASSWORD")
    )

    return db



async def show_all_levels(interaction: discord.Interaction):
    db = connect()
    cursor = db.cursor()
    author_id = int(list(interaction.data.values())[0].split("_")[1])

    EH = enums.Emojies

    if interaction.user.id != author_id:
        await interaction.response.send_message(
            f"{EH.NO} **Ошибка**: данной кнопкой может пользоваться только {interaction.guild.get_member(author_id).mention}",
            ephemeral=True
        )
        db.close()
        return

    user = interaction.user

    cursor.execute(
        """
        SELECT
            req_id, level_id, requested_stars
        FROM
            `requests_table`
        WHERE
            sender_id = %s
        """, (user.id,)
    )

    result = cursor.fetchall()

    if len(result) == 0:
        await interaction.response.send_message(
            "Вы не отправили ни одного уровня, либо же все Ваши реквесты были **удалены**. Подробнее, почему это могло произойти, можно узнать по команде **/faq**",
            ephemeral=True
        )
        db.close()
        return
    
    content_to_send = ''

    for req, i in zip(result, range(1, len(result)+1)):
        content_to_send += f"{i}. **ID: {req[1]}**\nDBID: ``{req[0]}``; Сложность: ``{req[2]}``\n\n"

    await interaction.response.send_message(content_to_send, ephemeral=True)
    db.close()




async def show_level_info(interaction: discord.Interaction):
    author_id = int(list(interaction.data.values())[0].split("_")[1])

    EH = enums.Emojies

    if interaction.user.id != author_id:
        await interaction.response.send_message(
            f"{EH.NO} **Ошибка**: данной кнопкой может пользоваться только {interaction.guild.get_member(author_id).mention}",
            ephemeral=True
        )
        return
    
    mod = ModalForLevelInof(title="Укажите DBID", timeout=None, custom_id=None)
    await interaction.response.send_modal(mod)


class ModalForLevelInof(ui.Modal, title="Укажите DBID"):
    def __init__(self, *, title: str = ..., timeout: float | None = None, custom_id: str = ...) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    dbid = ui.TextInput(label="DBID", placeholder="ID уровня из базы данных реквестов", style=discord.TextStyle.short, max_length=6)

    async def on_submit(self, interaction: discord.Interaction):
        dbid = int(self.dbid.value)
        db = connect()
        cursor = db.connect()

        EH = enums.Emojies

        cursor.execute(
            """
            SELECT
                req_id, 
                level_id, 
                is_sent_to_h, 
                votes_yes, 
                votes_no, 
                requested_stars,
                IF(req_id IN (select req_id as rid from reports where reports.req_id = req_id), TRUE, FALSE)
            FROM
                `requests_table`
            WHERE
                req_id = %s AND sender_id = '%s'
            """, (dbid, interaction.user.id)
        )

        result = cursor.fetchall()

        if len(result) == 0:
            await interaction.response.send_message(f"{EH.NO} **Ошибка**: уровень с DBID *{dbid}* не найден среди Ваших уровней", ephemeral=True)
            db.close()
            return
        
        result = result[0]

        ld = parser.get_parsed_level_data(int(result[1]))
        emb = discord.Embed(
            title=f"Статистика уровня {enums.DifficultyCalculator.get_difficulty_by_stars(int(result[5]))} {ld[0]}",
            description="В статистике указан рейтинг Вашего реквеста в системе ревьюверов РКГД",
            color=discord.Color.gold()
        )

        if result[6]:
            emb.add_field(
                name="Нарушение правил системы", 
                value=f"{EH.REP} **На данный реквест был создан репорт одним из ревьюверов!**",
                inline=False
            )

        rating_text = ''
        rc = result[3] + result[4]
        rating_text += EH.YES + ' ' + (EH.GREEN * (round(result[3] / rc * 10))) + (EH.RED * (round(result[4] / rc * 10))) + ' ' + EH.NO

        value_text = f"``Название:`` **{ld[0]}**\n``Автор   :`` **{ld[1]}**\n``Загрузки:``**{ld[5]}**\n``Рейтинг :`` **{ld[6]}**\n"
        value_text += f"Рейтинг в системе РКГД\n{rating_text}"
        emb.add_field(
            name="Основная информация",
            value=value_text
        )

        emb.set_author(name="Статистика вашего реквеста", icon_url=interaction.user.avatar.url)
        emb.set_footer(text=f"DBID: {dbid}")

        await interaction.response.send_message(embed=emb, ephemeral=True)
        db.close()

class StatViewerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Просмотреть статус своих реквестов/оценок/сендов")
    async def stats(self, interaction: discord.Interaction):
        user = interaction.user
        db = connect()
        cursor = db.cursor()

        view = ui.View()
        view.timeout = None

        EH = enums.Emojies

        db_id = None
        user_role = None

        cursor.execute(f"SELECT id, user_role FROM staff WHERE user_discord = '{user.id}'")
        for x in cursor.fetchall():
            db_id = x[0]
            user_role = x[1]

        match user_role:
            case 1, 2:

                desc = f'{EH.CP} ревьювером' if user_role == 1 else f'{EH.STAR} хелпером'
                emb = discord.Embed(
                    title=f"Статистика {user.name}",
                    description=f"Вы являетесь **{desc}** сервера РКГД",
                    colour=discord.Color.gold()
                )

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
                            staff.user_role = %s
                        GROUP BY
                            staff.user_discord
                        ORDER BY
                            request_count DESC
                """, (user_role,))

                result = cursor.fetchall()
                for x, i in zip(result, range(0, len(result))):
                    if int(x[0]) == user.id:

                        if user_role == 2:
                            cursor.execute(
                                """SELECT
                                    mod_name,
                                    COUNT(mod_name)
                                FROM
                                    `helpers_sends_logs`
                                WHERE
                                    helper_id = %s
                                GROUP BY
                                    mod_name
                                ORDER BY
                                    COUNT(mod_name) DESC
                                LIMIT 1
                            """, (db_id,)
                            )

                            fav_mod = cursor.fetchall()[0]

                        value = (
                            f"``Роль      :`` **Ревьювер**\n``Оценок    :`` **{x[1]}**\n``Блокировка:`` {EH.YES} **Отсутствует**"
                        ) if user_role == 1 else (
                            f"``Роль             :`` **Ревьювер**\n``Сендов           :`` **{x[1]}**\n``Любимый модератор:`` {fav_mod}\n``Блокировка       :`` {EH.YES} **Отсутствует**"
                        )
                        emoji = enums.RatingCalculator.get_cup_by_place(i+1)
                        emb.add_field(
                            name=f"Место №{i+1} {emoji}",
                            value=value,
                            inline=False
                        )
                        break

                emb.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
                emb.set_thumbnail(url=user.avatar.url)
                await interaction.response.send_message(embed=emb, delete_after=300)

            case _:
                
                await interaction.response.defer(thinking=True)
                try:
                    emb = discord.Embed(
                        title=f"Статистика {user.name}",
                        description=f"В данной статистике можно посмотреть текущее состояние Ваших реквестов",
                        colour=discord.Color.green()
                    )

                    cursor.execute(
                        """SELECT
                                staff.id AS admin_discord,
                            FROM
                                staff
                            WHERE
                                staff.user_role = 0 AND
                                staff.user_discord = %s
                    """, (user.id,))

                    result = cursor.fetchall()
                    is_banned_stf_text = f"{EH.REP} Заблокирован" if len(result) != 0 else f"{EH.YES} Отсутствует"

                    cursor.execute("""
                        SELECT
                            ban_id
                        FROM
                            `bans`
                        WHERE
                            requester_id = '%s'
                    """, (user.id,))

                    result = cursor.fetchall()
                    is_banned_req_text = (
                        f"{EH.REP} Заблокирован [Ban-ID: {result[0]}]"
                    ) if len(result) != 0 else (
                        f"{EH.YES} Отсутствует"
                    )

                    cursor.execute("""
                        SELECT
                            req_id, 
                            level_id, 
                            is_sent_to_h, 
                            votes_yes, 
                            votes_no, 
                            requested_stars,
                            IF(req_id IN (select req_id as rid from reports where reports.req_id = req_id), TRUE, FALSE)
                        FROM
                            `requests_table`
                        WHERE
                            sender_id = '%s'
                    """, (user.id,))

                    reqs_value = ''
                    result = cursor.fetchall()

                    for req, counter in zip(result, range(0, 3)):
                        diff = DifficultyCalculator.get_difficulty_by_stars(int(req[5]))
                        level_data = parser.get_parsed_level_data(req[1])
                        is_good = req[3] + req[4] >= 5
                        reqs_value += f"{req[0]} {diff} **{level_data[0]}:**\n"
                        reqs_value += f"{EH.LIKE} ``{req[3]}`` \ {EH.DISLIKE} ``{req[4]}`` {f'{EH.YES} Одобрено' if is_good else ''} {f'{EH.REP}' if req[6] else ''}\n\n"

                    left = len(result) - 3

                    emb.add_field(
                        name="Ваши ревесты", 
                        value=reqs_value + (f"*Ещё {left} уровня(ей)...*" if left > 0 else '')
                    ) if len(reqs_value) != 0 else (
                        emb.add_field(
                            name="У Вас нет реквестов",
                            value=f"Отправьте свой реквест через команду **/request**, или воспользуйтесь этой функцией в канале {interaction.guild.get_channel(1125068641461866517).jump_url}",
                            inline=True
                        )
                    )

                    add_text = "*По вопросам блокировок обращайтесь к администрации сервера*"
                    emb.add_field(
                        name="Информация", 
                        value=f"``Количество реквестов:`` **{len(result)}**\n``Бан [Стафф]   :`` **{is_banned_stf_text}**\n``Блокировка [Реквесты]:`` **{is_banned_req_text}**\n\n{add_text}",
                        inline=True
                    )
                    new_value =  f"*• Кнопка {EH.HO} для получения полного списка уровней*"
                    new_value += f"*• Кнопка {EH.DOWNLOAD} для получения информации о конкретном уровне*"
                    emb.add_field(
                        name="",
                        value=new_value,
                        inline=False
                    )
                    
                    emb.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
                    emb.set_thumbnail(url=user.avatar.url)

                    show_all_levels_button     = ui.Button(emoji=EH.HO, style=discord.ButtonStyle.red, custom_id=f"all_{user.id}")
                    show_specific_level_button = ui.Button(emoji=EH.DOWNLOAD, style=discord.ButtonStyle.green, custom_id=f"spec_{user.id}")

                    show_all_levels_button.callback     = show_all_levels
                    show_specific_level_button.callback = show_level_info

                    view.add_item(show_all_levels_button)
                    view.add_item(show_specific_level_button)

                    await interaction.followup.send(embed=emb, view=view)

                except Exception as e:
                    await interaction.followup.send("Что-то пошло не так...")
                    print(e)


async def setup(bot):
    await bot.add_cog(StatViewerCog(bot))