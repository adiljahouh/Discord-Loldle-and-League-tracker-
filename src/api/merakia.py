import aiohttp


async def pull_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/championrates.json") as response:
            response.raise_for_status()
            content = await response.json()
            data = {}
            for champion_id, positions in content["data"].items():
                champion_id = int(champion_id)
                play_rates = {}
                for position, rates in positions.items():
                    play_rates[position.upper()] = rates["playRate"]
                for position in ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"):
                    if position not in play_rates:
                        play_rates[position] = 0.0
                data[champion_id] = play_rates
            return data
