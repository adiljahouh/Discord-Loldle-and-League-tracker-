# README
## Project
Project is under maintenance until API key is updated.

This Discord bot is used to incorporate the RIOT API to fetch user data and periodically send it to Discord. Furthermore, using a redis cache users can be stored in-memory and be fetched quickly. 

I have hacky workarounds for the horrible rate limits (apparently without a production key you are rate limited at like 100 requests per 2 minutes after being verified even..).

Implements discord moderation tools such as striking and jailing people (fun little tool), loldles (inspired by loldle.net) by combining the use of multiple API's (wiki and riot) and
webscraping of the wiki to reach a fully fledged loldle with automatically updated champions!

Animal commands are also part of the bot with the chance of receiving a personalized animal.

Full league integration, being able to register, summarize, rank and track individuals (by a live betting system!) using a point system with free daily points, rolling of points and betting. 

The live-betting system ran into a memory leak during one of the pushes. If it occurs revert to one of the previous commits.

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
