# README
## Project
Project is under maintenance until API key is updated.

My buddy Matthijs really wanted a README so he could understand the code eventhough its written like an epilogue of Stephen King's latest books.

This Discord bot is used to incorporate the RIOT API to fetch user data and periodically send it to Discord. Furthermore, using a redis cache users can be stored in-memory and be fetched quickly. 

I have hacky workarounds for the horrible rate limits (apparently without a production key you are rate limited at like 100 requests per 2 minutes after being verified even..).

## Docker
Containers can be ran by installing docker and docker compose.
Default path is set to /opt/discbot/ this path contains the .env file with the follow:
- DISCORDTOKEN: str
- CHANNELID: int
- JAILROLE: int
- RIOTTOKEN:str
- REDISURL: str
- PLAYERROLE: int
- GROLE: int
- PINGROLE: int
- SUPERUSER: int

Having this .env file somewhere else means you are forced to change this path in the ```docker-compose.yml```.
Running ```docker-compose up --build``` or ```docker compose up --build``` will start both containers.



## Language Model
One of the desired features is to train a language model, probably a seq2seq model to immitate the behaviour of people within the discord. This is replacing the chatgpt.py file because I just realized the free version is free for a very limited amount of time.