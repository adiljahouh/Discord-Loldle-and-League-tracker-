import requests
import json


async def duck_api():
    try:
        response = requests.get("https://random-d.uk/api/v2/random")
        content = json.loads(response.content.decode("utf-8"))
        response.raise_for_status()
        if content['url']:
            return content['url']
        else:
            return "Internal API error"
    except requests.exceptions.HTTPError as e:
        return "HTTP error, no ducks for you"


async def dog_api():
    try:
        response = requests.get("https://dog.ceo/api/breeds/image/random")
        content = json.loads(response.content.decode("utf-8"))
        response.raise_for_status()
        if content['status'] == 'success':
            return content['message']
        else:
            return "Internal API error"
    except requests.exceptions.HTTPError as e:
        return "HTTP error, no dogs for you"


async def cat_api():
    try:
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        content = json.loads(response.content.decode("utf-8"))
        response.raise_for_status()
        if content[0]['url']:
            return content[0]['url']
        else:
            return "Internal API error"
    except requests.exceptions.HTTPError as e:
        return "HTTP error, no cats for you"

