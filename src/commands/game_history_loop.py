    # @tasks.loop(hours=24)
    # async def send_message(self):
    #     print("Setting up exposing session...")
    #     channel_id: int = self.channel_id
    #     channel = self.bot.get_channel(channel_id)
    #     try:
    #         discord_ids: list[bytes] = self.main_db.get_all_users()
    #     except ConnectionError as e:
    #         print(e)
    #         await channel.send("No connection to DB")

    #     if len(discord_ids) > 0:
    #         discord_ids = [id.decode('utf-8') for id in discord_ids]
    #     else:
    #         await channel.send("No users registered")
    #         return
    #     embed = discord.Embed(title="⏰ ITS EXPOSING TIME ⏰\n\n",
    #                             description="BOTTOM G's WILL BE REPRIMANDED",
    #                             color=0xFF0000)
    #     inters = 0
    #     for index, discord_id in enumerate(discord_ids):
    #         riot_id = self.main_db.get_user_field(discord_id, "puuid")
    #         try:
    #             flame_text = await self.riot_api.get_bad_kda_by_puuid(riot_id.decode('utf-8'), 5, sleep_time=30)
    #         except aiohttp.ClientResponseError as e:
    #             print(e.message)
    #             await channel.send(f"Exposing command errored with: {e}")
    #             return

    #         if flame_text:
    #             inters += 1
    #             embed.add_field(name=f"SUSPECT #{inters}", value=f"<@{discord_id}>\n {flame_text}\n")
    #         else:
    #             print("no inters found for our exposing session")
    #             return

    #     if channel is not None:
    #         """
    #         query redis db for all users, check recents kdas and retrieve the cumulative worst.
            
    #         """
    #         try:
    #             await channel.send(embed=embed)
    #             print("Message sent successfully.")
    #         except discord.Forbidden:
    #             print("I don't have permission to send messages to that channel.")
    #         except discord.HTTPException:
    #             print("Failed to send the message.")

    # @tasks.loop(hours=24)
    # # # FIXME: Remove the concurrency here, its redundant
    # async def leaderboard(self):
    #     """
    #         Keeps track of top 5 in each role of the leaderboard
    #     """
    #     channel_id: int = self.channel_id
    #     channel = self.bot.get_channel(channel_id)
    #     print("Retrieving Leaderboard...")
    #     try:
    #         discord_ids: list[bytes] = self.main_db.get_all_users()
    #     except ConnectionError as e:
    #         await channel.send("Could not connect to database.")
    #         return
    #     leaderboard_text = ''
    #     if len(discord_ids) > 0:
    #         discord_ids = [id.decode('utf-8') for id in discord_ids]
    #     else:
    #         await channel.send("No users are registered.")
    #     tasks = []
    #     delay = 1
    #     for discord_id in discord_ids:
    #         puuid = self.main_db.get_user_field(discord_id, "puuid")
    #         tasks.append(self.riot_api.get_highest_damage_taken_by_puuid(puuid=puuid.decode('utf-8'), count=5,
    #                                                                         sleep_time=delay, discord_id=discord_id))
    #         delay += 20
    #     try:
    #         result = await asyncio.gather(*tasks)
    #     except aiohttp.ClientResponseError as e:
    #         print(e)
    #         # await channel.send(f"")
    #     top_5 = sorted(result, key=lambda x: x['taken'], reverse=True)[:5]
    #     for index, top_g in enumerate(top_5):
    #         leaderboard_text += f'\n{index + 1}. <@{top_g["disc_id"]}> | {top_g["taken"]} on **{top_g["champion"]}**'
    #     description = f"Type .register to be able to participate"
    #     embed = discord.Embed(title="💪🏽TOPPEST G's💪🏽\n\n", description=f"{description}", color=0xFF0000)
    #     embed.add_field(name="Top Damage Taken Past 5 Games", value=leaderboard_text)
    #     await channel.send(embed=embed)