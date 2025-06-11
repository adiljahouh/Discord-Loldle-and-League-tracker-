# README
## Project

This Discord bot is used to incorporate the RIOT API to fetch user data and periodically send it to Discord. Furthermore, using a redis cache users can be stored in-memory and be fetched quickly. 

I have hacky workarounds for the horrible rate limits (apparently without a production key you are rate limited at like 100 requests per 2 minutes after being verified even..).

Implements discord moderation tools such as striking and jailing people (fun little tool), loldles (inspired by loldle.net) by combining the use of multiple API's (wiki and riot) and
webscraping of the wiki to reach a fully fledged loldle with automatically updated champions!

Full league integration, being able to register, summarize, rank and track individuals (by a live betting system!) using a point system with free daily points, rolling of points and betting. 

## LOLDLE in Discord!
Loldle inspired by loldle.net! Now fully in discord with 3 gamemodes and a point reward!
#### Preview Loldle with abilities (blurred, distorted etc.)

https://github.com/user-attachments/assets/686c7927-e21d-4595-b15c-cbe3214f8b53


## Live League Tracking & Betting
Live game tracking for multiple users and a betting system to bet on your friends games!

#### Preview Game Found For USER:
![image](https://github.com/user-attachments/assets/91aa1ccc-ca07-40ee-b02a-fb8c47e714ef)

#### Preview Game End Found + Point return if bets were placed:
![image](https://github.com/user-attachments/assets/487d53b5-6eec-4911-8413-e02434c343fc)

#### Betting on a win or loss:
![image](https://github.com/user-attachments/assets/5f639c12-9221-4c2f-91b7-90325096a39d)


## Jailing system
Jailing system for striking individuals, 3 strikes and you're OUT!

![image](https://github.com/user-attachments/assets/44f41e8d-19fa-47a2-b8dc-6bf8b4d3931f)

#### POV JAILED PERSON (can only type in #confessional and can be released by mods):

![image](https://github.com/user-attachments/assets/ef8843cc-6cf8-4eaa-9971-425dad2e1cb5)

#### POV 3rd strike, which removes all roles and assigns the "Jail role":

![image](https://github.com/user-attachments/assets/e0364fd4-16fe-4fa4-8717-2bab768fb1ae)

#### POV Release, which returns all roles

![image](https://github.com/user-attachments/assets/5ca6c2ad-9de8-4ecc-a412-67136bce031c)

## League integration
#### League integration for ranks, summaries, clash etc.
![image](https://github.com/user-attachments/assets/13620f4a-034d-4c60-9e0e-a89ea643d080)

## Animals API
#### Basic usage:
![image](https://github.com/user-attachments/assets/05b91597-0a13-4fec-be04-54d52f2a046c)

#### Random events:
![image](https://github.com/user-attachments/assets/3a9b204d-4ba5-4d39-a658-f924da354c12)

## Points

#### Some random examples of the point system
![image](https://github.com/user-attachments/assets/07999d46-693d-41d0-9071-eba6bbac95da)

## Docker
Containers can be ran by installing docker and docker compose.
Default path is set to /opt/discbot/ this path contains the .env file with the follow:
- DISCORDTOKEN: str
- TOPGZONECHANNELID: int
- JAILROLE: int
- RIOTTOKEN:str
- REDISURL: str
- PLAYERROLE: int
- GROLE: int
- PINGROLE: int
- SUPERUSER: int

Having this .env file somewhere else means you are forced to change this path in the ```docker-compose.yml```.
Running ```docker-compose up --build``` or ```docker compose up --build``` will start both containers.
