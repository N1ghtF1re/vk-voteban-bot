<h1 align="center">VOTEBAN BOT</h1>
<p align="center"><img src="https://i.imgur.com/Ip6hszE.png" width="150"></p>

<p align="center">
<a href="https://github.com/N1ghtF1re/voteban-bot/stargazers"><img src="https://img.shields.io/github/stars/N1ghtF1re/voteban-bot.svg" alt="Stars"></a>
<a href="https://github.com/N1ghtF1re/voteban-bot/releases"><img src="https://img.shields.io/badge/downloads-15-brightgreen.svg" alt="Total Downloads"></a>
<a href="https://github.com/N1ghtF1re/voteban-bot/releases"><img src="https://img.shields.io/github/tag/N1ghtF1re/voteban-bot.svg" alt="Latest Stable Version"></a>
<!--<a href="https://github.com/N1ghtF1re/blob/master/LICENSE"><img src="https://img.shields.io/github/license/N1ghtF1re/voteban-bot.svg" alt="License"></a>
-->
</p>
</p>
 
## About the bot
The bot on command starts a vote to exclude a specific user.
Also, the bot keeps a list of excluded users, because of what an excluded user can not add to the conversation again, until the administrator unlocks it

## Technical requirements
Python 3+ should be installed on your computer. If you did not, here's [link](https://www.python.org/downloads/)

The following Python packages must be installed:
* vk_api
* python3_anticaptcha

## How to use
To start working with the bot, you need to configure the config (py) and enter all the necessary data.
If you choose to use an antikapchi, you must register at [getcaptchasolution.com](http://getcaptchasolution.com/qocusckanf) and get the key

After that, you need to run bot.py (the extension must be associated with Python).

Option 2: open the terminal, move through cd to the directory of this repository, and then enter
`` `
python bot.py
`` `

You can also edit the constants in bot.py (the time of voting, the number of votes, etc.)

## Developers
In the development of this bot involved:
+ [**Pankratiew Alexandr**](https://github.com/N1ghtF1re/)
+ [**Shilo Alexey**](https://vk.com/AlexeyLyapeshkin)

# RUS DESCRIPION:
## О боте
Бот по команде запускает голосование за исключение определенного пользователя. 
Так же бот хранит список исключенных пользователей, из-за чего исключенного пользователя не смогут снова добавить в беседу, пока администратор его не разблокирует

## Технические требования
На вашем компьютере должен быть установлен Python 3+. Если вы этого не сделали - вот [ссылка](https://www.python.org/downloads/)

Должны быть установлены следующие пакеты Python
* vk_api
* python3_anticaptcha

## Руководство по использованию
Для начала работы с ботом необходимо настроить конфиг (config.py) и ввести все необходимые данные.
Если выбрано использование антикапчи, необходимо зарегистрироваться на сайте [getcaptchasolution.com](http://getcaptchasolution.com/qocusckanf) и получить ключ

После этого нужно запустить bot.py (Расширение должно быть асоциированно с Python). 

Вариант 2: открыть терминал, переместиться через cd в каталог этого репозитория, после чего в консоли ввести
```
python bot.py
```

Так же можно отредактировать вынесенные константы в bot.py (время голосования, количество голосов и т.д.)

## Разработчики
В разработке этого бота участвовали:
+ [**Панкратьев Александр**](https://github.com/N1ghtF1re/)
+ [**Шило Алексей**](https://vk.com/AlexeyLyapeshkin)
