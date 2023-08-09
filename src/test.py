import random
import os
import requests
from PIL import Image
from io import BytesIO
def hello_decorator(func):
    def wrapper(*args, **kwargs):
        print("Hello")
        result = func(*args, **kwargs)
        return result
    return wrapper


@hello_decorator
def httprequest(ree, bee, kree):
    return [ree, bee, kree]


test = httprequest("koo", "moo", "doo")
print(test)
## from config import *
# async def main():
#     settings = Settings()
#     riot_api = riotAPI(settings.RIOTTOKEN)
#     puuids = ['ftCv851wC2M95ROX3CQPVtxLdc2V8Od4EBfsjfvSgguvuOqvuBRcdWpuPjLYEy0bT5WKkyl43qFl1w', \
#               'SEV_5s1jFp9mfXed2gjosvfaRLq15JP86IWIolwUKnc5WwHvrIUveapZWf7BjO-dSqvJ_brA9FQlRA', \
#                 'NbE-Y8A7afr6fhaZK6XwqoFkQkKPDOBh_M4X6QgR5qXQqjwt3UgbIWRWTlBjaoooXmQOMOd9-91F1Q', \
#                     'A2sy0Y_gCeayApKm0pFAB54uwbwlEKuPZ13awDMEMJgKKME7zpu4SSQw59Yxhi0AnTSzhIrJbMwkYQ']
#     tasks = []
#     sleep_time = 0.5
#     for puuid in puuids:
#     # puuid = await riot_api.get_puuid("meshh")
#     # matches= await riot_api.get_match_ids("puuid", puuid)
#     # matches_details_user = await riot_api.get_multiple_match_details_by_matchIDs_and_filter_for_puuid(puuid, matchIDs=matches)
#     # print(matches_details_user)
#         print(sleep_time)
#         tasks.append(riot_api.get_highest_damage_taken_by_puuid(puuid, count=10, sleep_time=sleep_time, discord_id= 123124134))
#         sleep_time += 2
#     try:
#         result = await asyncio.gather(*tasks)
#         print(result)
#     except aiohttp.ClientResponseError as e:
#         print(e.message, e.status)
#         print("beep")
#     top_5 = sorted(result, key=lambda x: x['taken'], reverse=True)[:2]
#     print(top_5)
# asyncio.run(main())
