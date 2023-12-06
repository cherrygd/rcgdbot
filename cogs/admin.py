from typing import Optional, Literal
from discord.utils import MISSING
import discord
import os
import json

from discord import app_commands, ui
from discord.ext import commands

import random
import mysql.connector

def connect():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    return db



class Administration(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print("Administration cog launched")


    @app_commands.command(name="config", description="Настройка файла config")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def config(
        self, 
        interaction: discord.Interaction, 
        votes_to_procced: Optional[int] = -1, 
        report_channel: discord.TextChannel = None, 
        role: discord.Role = None, 
        rates_channel: discord.TextChannel = None
    ):
        try:
            with open("HAHAHA/config.json", "r") as file:
                config = json.load(file)
            
            config["Server_ID"] = str(interaction.guild_id)
            config["VotesToAdvance"] = votes_to_procced if votes_to_procced != -1 else config["VotesToAdvance"]
            config["ReportChannel"] = str(report_channel.id) if report_channel != None else config["ReportChannel"]
            config["MentRole"] = str(role.id) if role != None else config["MentRole"]
            config["RatesChannel"] = str(rates_channel.id) if rates_channel != None else config["RatesChannel"]

            votes = config["VotesToAdvance"]

            with open("HAHAHA/config.json", "w") as file:
                json.dump(config, file, indent=2)

            await interaction.response.send_message(f"Настройка завершена:\n*ID сервера: {interaction.guild_id}*\n*Количество голосов для отправки: {votes}*", ephemeral=True)

        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Что-то пошло не так...", ephemeral=True)


    @app_commands.command(name="manage_user", description="Позволяет установить для пользователя указанную роль")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def manage_user(self, interaction: discord.Interaction, user: discord.Member, role: Literal["Ревьювер", "Хелпер", "Мент", "Бан", "Снять роль"]):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            db = connect()
            cursor = db.cursor()

            cursor.execute(f"SELECT user_role FROM staff WHERE user_discord = '{user.id}'")
            
            curren_role : int = -1
            for x in cursor:
                curren_role = list(x)[0]

            print(curren_role)

            if curren_role == 0:
                await interaction.followup.send(f"Данный пользователь забанен в базе данных. Чтобюы его разбанить, используйте /unban", ephemeral=True)
                db.close()
                return
            
            match role:
                case "Ревьювер":
                    if curren_role == -1:
                        cursor.execute(f"INSERT INTO staff (user_discord, user_role) VALUES ('{user.id}', 1)")
                    else:
                        cursor.execute(f"UPDATE staff SET user_role = 1 WHERE user_discord = '{user.id}'")
                    db.commit()
                    emb = discord.Embed(title="Вы были поставлены на роль Ревьювера!", description=f"Вас назначил **{interaction.user.name}**", colour=discord.Colour.green())
                    emb.add_field(name="Что это значит?", value=f"Теперь у тебя есть возможность оценивать уровени, отправленные командой **/request**. Для этого просто используй прямо тут команду **/review**, и я дам случайный уровень на оценку", inline=False)
                    emb.add_field(name="Можно ли пойти дальше?", value="Конечно! Можно стать **хелпером**, и рассматривать уже те уровни, которые одобрили ревьюверы. Хелперы должны отправлять хорошие уровни модераторам", inline=False)
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await user.send(embed=emb)

                case "Хелпер":
                    if curren_role == -1:
                        cursor.execute(f"INSERT INTO staff (user_discord, user_role) VALUES ('{user.id}', 2)")
                    else:
                        cursor.execute(f"UPDATE staff SET user_role = 2 WHERE user_discord = '{user.id}'")
                    db.commit()
                    emb = discord.Embed(title="Вы были поставлены на роль Хелпера!", description=f"Вас назначил **{interaction.user.name}**", colour=discord.Colour.green())
                    emb.add_field(name="Что это значит?", value=f"Теперь ты можешь брать уровни у меня через команду /rate, чтобы отправить их модератору (вручную!). Эти уровни уже были проверены ревьюверами, так что ты получаешь только достойные рейта и пристойные работы!", inline=False)
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await user.send(embed=emb)


                case "Мент":
                    with open("HAHAHA/config.json", "r") as file:
                        config = json.load(file)
                        role_id = int(config["MentRole"])

                    await user.add_roles(interaction.guild.get_role(role_id))
                    if curren_role == -1:
                        cursor.execute(f"INSERT INTO staff (user_discord, user_role) VALUES ('{user.id}', 3)")
                    else:
                        cursor.execute(f"UPDATE staff SET user_role = 3 WHERE user_discord = '{user.id}'")
                    db.commit()
                    emb = discord.Embed(title="Вы были поставлены на роль Мента!", description=f"Вас назначил **{interaction.user.name}**", colour=discord.Colour.green())
                    emb.add_field(name="Что это значит?", value=f"Теперь ты следишь за тем, чтобы плохие реквесты канули в бездну, а делать ты это будешь путём рассмотрения репортов от Ревьюверов", inline=False)
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await user.send(embed=emb)

                case "Бан":
                    if curren_role == -1:
                        cursor.execute(f"INSERT INTO staff (user_discord, user_role) VALUES ('{user.id}', 0)")
                    else:
                        cursor.execute(f"UPDATE staff SET user_role = 0 WHERE user_discord = '{user.id}'")
                    db.commit()
                    emb = discord.Embed(title="Вы были забанены в системе RCGD бота!", description=f"Вас забанил **{interaction.user.name}**", colour=discord.Colour.red())
                    emb.add_field(name="Почему так произошло?", value=f"Скорее всего, ты злоупотреблял своей ролью, что могло привести к такому исходу. Также, вполне вероятно, тебя снаяли за инактив. В любом случае, причину можно узнать у {interaction.user.name}", inline=False)
                    emb.add_field(name="Могу ли я как-то восстановиться?", value="Увы, но нет. Бан означает, что твои нарушения были крайне серьёзными, поэтому администратору пришлось тебя забанить. Однако, есть вероятность, что это ошибка, и тебя могут разбанить. Уточняй у Администрации", inline=False)
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await user.send(embed=emb)

                case "Снять роль":
                    cursor.execute(f"DELETE FROM staff WHERE user_discord = '{user.id}'")
                    db.commit()
                    emb = discord.Embed(title="Вы были сняты со своей должности!", description=f"Вас снял **{interaction.user.name}**", colour=discord.Colour.red())
                    emb.add_field(name="Почему так произошло?", value=f"Скорее всего, ты злоупотреблял своей ролью, что могло привести к такому исходу. Также, вполне вероятно, тебя снаяли за инактив. В любом случае, причину можно узнать у {interaction.user.name}", inline=False)
                    emb.add_field(name="Могу ли я как-то восстановиться?", value="Да, можешь. Тебя не забанили, а просто сняли с тебя роль, так что, скорее всего, у тебя всё ещё есть шанс восстановиться. Уточни это у администраторов сервера и у Администрации", inline=False)
                    emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
                    await user.send(embed=emb)

            await interaction.followup.send(f"Изменения внесены в отношении {user.name}", ephemeral=True)
            db.close()

        except Exception as e:
            print(e)
            await interaction.followup.send("Что-то пошло не так...", ephemeral=True)
            db.close()


    @app_commands.command(name="unban", description="Позволяет разбанить ранее забаненого участника в системе")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def unban(self, interaction: discord.Interaction, user: discord.Member):
        try:
            db = connect()
            cursor = db.cursor()

            cursor.execute(f"SELECT user_role FROM staff WHERE user_discord = '{user.id}'")
            user_role = -1
            for x in cursor:
                user_role = list(x)[0]

            if user_role != 0:
                await interaction.response.send_message(f"Данный пользователь на забанен! Если Вы уверены, что он забанен, проверьте, того ли пользователя Вы указали: {user.mention}", ephemeral=True)
                db.close()
                return
            
            cursor.execute(f"DELETE FROM staff WHERE user_discord = '{user.id}'")
            db.commit()

            emb = discord.Embed(title="Вы были разбанены в системе RCGD бота!", description=f"Вас разбанил **{interaction.user.name}**", colour=discord.Colour.purple())
            emb.add_field(name="Что это значит?", value=f"Пользователь {interaction.user.name} посчитал, что ты теперь можешь вернуться в систему бота как Ревьювер или Хелпер. Возможно, твоя блокировка произошла по ошибке, и теперь ты можешь вернуться к работе, как только тебя переназначат на новую роль", inline=False)
            emb.set_author(name="RCGD bot", icon_url=self.bot.user.avatar.url)
            await user.send(embed=emb)

            await interaction.response.send_message(f"Пользователь {user.mention} был разбанен! Если Вы планируете, чтобы он вернулся к работе, **назначьте** его на роль командой **/manage_user**", ephemeral=True)


        except Exception as e:
            print(e)
            await interaction.response.send_message("Что-то пошло не так...", ephemeral=True)





async def setup(bot):
    await bot.add_cog(Administration(bot))