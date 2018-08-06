# coding: utf8

""" VOTEBAN BOT
:authors: Alexandr Pankratiew, Alexey Shilo
:contact: https://vk.com/sasha_pankratiew, https://vk.com/alexey_shilo
:githubs: https://github.com/N1ghtF1re, https://github.com/AlexeyLyapeshkin
:copyright: (c) 2018
"""

import threading
import json


import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, VkChatEventType

import time

from python3_anticaptcha import ImageToTextTask
from python3_anticaptcha import errors

from config import login,password,my_id,isUsedAntiCaptcha, antiCaptchaKey

# UNITS:
import const
import bot_msg

from units import users
from units import chats
from units import log # Ведение лога бота
from units.vkapi import writeMessage, kickUser

from functools import lru_cache

# INITIANALISATION


black_list = [] # Пользователи в ЧС беседы. Формат: [{'id':id, 'chat_id':chat_id}, {...}]



''' Список голосований на кик.
    Формат: [{'id': [str],'chat_id': [int], 'voted': set(), 'count_yes': [int], 'count_no': [int]}, {...}]

    Особенность: в данном списке может находиться только один элемент для каждой беседы
'''
kick_votes = []


spam_list = []


#  ----------------------------- KICK LIST -----------------------------------------

def addKickMan(vk, user_id, chat_id,county=0,countn=0):
    ''' Генерация словаря для списка претендентов на кик

        :param vk: Объект сессии ВК
        :param user_id: id пользователях
        :param chat_id: id беседы ВК
        :param county: Количество голосов "за"
        :param contn: Количество голосов "против"

        :return: [dict] {'id': [str],'chat_id': [int], 'time': [str], 'voted': set(), 'count_yes': [int], 'count_no': [int]}

    '''
    mem = set()
    dic = {'id': user_id,'chat_id': chat_id, 'voted': mem, 'count_yes': county, 'count_no': countn}
    return dic

def searchKickList(kick_votes, chat_id):
    ''' Поиск в списке претендентов на кик элемента с нужной беседы

        :param kick_votes: Список претендентов на кик
        :param chat_id: id беседы ВК

        :return: [int] Элемент_с_нужной беседы | None, если элемента не существует
    '''
    for element in kick_votes:
        if element['chat_id'] == chat_id:
            return element

def find_delete(kick_votes,chat_id):
    ''' Поиск индекса списка претендетов на кик элемента с нужной беседы

        :param kick_votes: Список претендентов на кик
        :param chat_id: id беседы ВК

        :return: [int] id_элелемента_с_нужной беседы
    '''

    for i, element in enumerate(kick_votes):
        if element['chat_id'] == chat_id:
            return i

def voiceProcessing(event, kick_votes,vk,element, ind):
    ''' Обработка голоса пользователя

        :event: Объект события LongPoll
        :kick_votes: Список претендетов на кик
        :vk: Объект сессии ВК
        :element: Элемент списка претендентов на кик для данного чата
        :ind: Выбранный пользователем вариант голоса. Может принимать
              два значения:
              'count_yes', если пользователь проголосовал за кик.
              'count_no', если против

        :NoReturn:
    '''
    user = users.getUser(vk, element['id']) # Получаем объект пользоваетля
    if not(event.user_id == user['id']): # Если пользователь не голосует сам за себяя
        if not (event.user_id in element['voted']): # Если пользователь еще не голосовал
            element['voted'].add(event.user_id) # Заносим пользователя в множество проголосовавших
            element[ind] += 1 # Увеличиваем количество голосов за/против (В зависимости от выбора пользователя)

            # Формируем и отправляем сообщения о голосе
            user_message = bot_msg.vote_accepted.format(str(element['count_yes']),str(element['count_no']))
            writeMessage(vk, event.chat_id, user_message)
    else:
        writeMessage(vk, event.chat_id, bot_msg.err_vote_for_yourself)



# --------------------------- FILES ----------------------------------
def saveListToFile(my_list,file):
    ''' Сохранение списка в файл

        :param my_list: Список, который надо сохранить
        :param file: Имя файла, в который сохранить (Файл перезапишется)

        :NoReturn:
    '''
    f = open(const.file_name, 'w')
    f.write(json.dumps(my_list))
    f.close()

# -------------------------------- ANTISPAM --------------------------
def antispam(event,spamlist):
    ''' Отслеживание флуда

        :param event: Событие LongPoll: Новое сообщение
        :param spamlist: Список флудеров

        :return True если пользователь не флудит | False если флудит
    '''

    mem = event.text.split()  #
    user_id = event.user_id   #  для удобства
    chat_id = event.chat_id   #
    for element in spamlist:  # перебираем спам-лист
        if (element['id'] == user_id) and (element['chat_id'] == chat_id) and (element['text'] == mem): # если
            # пользователь с его сообщением в спам-листе - игнорим
            return False
            break
    else:
        spamlist.append({'id': event.user_id,'chat_id':event.chat_id, 'text': event.text.split()}) #добавляем новое
        #  сообщение в спам-лист (на всякий, вдруг юзверь долбаеб)
        timer = threading.Timer(const.spam_time, deletespamlist,[event,spamlist]) #ставим таймер на удаление из спсика (многопоточно)
        timer.start()
        return True


# -------------------------- BAN LIST ----------------------------------
def unbanUser(vk,user_id, banlist, chat_id):
    ''' Разблокировка пользователя (Удаление из ЧС беседы)

        :param vk: Объект сессии ВК
        :param user_id: id пользователя, которого надо разбанить
        :param ban_list: Список забаненных пользоваетелей
        :param chat_id: id беседы, в которой надо разблокировать пользователя

        :NoReturn:
    '''
    id = users.getUser(vk,user_id)['id']
    for i, element in enumerate(banlist): # Перебируем список заблокированных
        if element['id'] == id and element['chat'] == chat_id: # Нашли
            del banlist[i] # Удаляем элемент списка
            userName = users.getName(vk, user_id, 'nom')
            user_message = bot_msg.unban_user.format(userName)
            break
    else:
        user_message = bot_msg.no_user_in_banlist
    writeMessage(vk,chat_id,user_message)

def checkForBan(vk, black_list, user_id, chat_id):
    ''' Проверяем, нужно ли выгнать пользователя (находится ли он в черном списке) и если находится, то выгоняем его

        :param vk: Объект сессии ВК
        :param black_list: Бан-лист
        :param user_id: ID пользователя
        :param chat_id: ID беседы ВК

        :NoReturn:
    '''
    id = users.getUser(vk,user_id)['id']

    if isUserInBanList(black_list, id, chat_id):
        # Пользователь из ЧС находится в беседе
        writeMessage(vk, chat_id, bot_msg.banned_user_came_in)
        kickUser(vk, chat_id, id)


def addBanList(vk, black_list, user_id, chat_id, isWrite = False):
    ''' Добавляет пользователя в бан-лист

        :param vk: Объект сессии ВК
        :param black_list: Бан-лист
        :param user_id: ID пользователя
        :param chat_id: ID беседы ВК
        :param isWrite: Отображать ли сообщение о добавлении в бан-лист

        :NoReturn:
    '''

    id = users.getUser(vk,user_id)['id']
    if isUserInBanList(black_list, id, chat_id): # Если пользователь уже в бан-листе
        writeMessage(vk, chat_id, bot_msg.user_already_in_banlist)
    else:
        black_list.append({'id': id, 'chat': chat_id})
        if isWrite:
            writeMessage(vk, chat_id, bot_msg.user_added_in_banlist)

def isUserInBanList(black_list, user_id, chat_id):
    ''' Проверяет наличие пользователя в бан-листе чата
        :param black_list: Бан-лист
        :param user_id: ID пользователя
        :param chat_id: ID беседы ВК

        return [] если нет в списке, [...] если есть
    '''
    return list(filter(lambda ban_dict: (ban_dict['id'] == user_id) and (ban_dict['chat'] == chat_id), black_list) )

def getBanList(vk, black_list, chat_id):
    ''' Вовращает ЧС список беседы с ID = chat_id

        :param vk: Объект сессии ВК
        :param black_list: Бан-лист
        :param chat_id: ID беседы ВК

        :return: [string] BlackList
    '''
    user_message = ''
    if len(black_list) != 0:
       # user_message =
        for element in black_list:
            if element['chat'] == chat_id:
                user_message += '* [id{1}|{0}] [id{1}] \n'.format(str(users.getName(vk,element['id'],'nom')), element['id'])
        if len(user_message) != 0:
            message = bot_msg.banned_list + user_message
        else:
            message = bot_msg.banlist_empty
        return message
    else:
        return bot_msg.banlist_empty

# ------------------------------ HANDLERS -------------------------------------------

def finishVote(vk, chat_id, kick_votes, black_list):
    ''' Обработчик события таймера завершения голосования

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК, в которой завершилось голосование
        :kick_votes: Список претендетов на кик
        :black_list: Список заблокированных пользователей

        :NoReturn:
    '''
    # Получаем элемент списка претендетов на кик для данной беседы
    kick_info = searchKickList(kick_votes, chat_id)

    # Генерируем и отправляем сообщение о завершении голосования
    message = bot_msg.finish_vote.format(users.getName(vk, kick_info['id']),kick_info['count_yes'],kick_info['count_no'])
    writeMessage(vk, chat_id, message)

    logs.write('Vote ended. chat: {0}'.format(chat_id))

    try: # Если возникло исключение => бота кикнули из беседы
        if (len(kick_info['voted']) >= const.vote_count) and (kick_info['count_yes'] > kick_info['count_no']):
            if(chats.isUserInConversation(vk,kick_info['id'], chat_id)): # Если пользователь все еще в беседе
                writeMessage(vk, chat_id, bot_msg.user_excluded)
                # Исключаем пользователя
                kickUser(vk, chat_id, kick_info['id'])
            else: # Пользователь ливнул во время голосования
                writeMessage(vk,chat_id, bot_msg.user_leave)
            addBanList(vk, black_list, kick_info['id'], chat_id)

        elif len(kick_info['voted']) < const.vote_count:
            writeMessage(vk, chat_id, bot_msg.no_votes_cast.format(len(kick_info['voted']), const.vote_count))
        else:
            writeMessage(vk, chat_id, bot_msg.user_remains)
    except vk_api.ApiError:
        logs.write("WARNING! Bot's kicked in chat {0}".format(chat_id))

    kick_votes.pop(find_delete(kick_votes,chat_id)) # Извлекаем из очереди на кик


def onTimerSave(file):
    ''' Обработчик события таймера сохранения списка заблокированных в файл

        :param file: Имя файла

        :NoReturn:
    '''
    global black_list
    saveListToFile(black_list, file)
    logs.write('Create banlist backup..')
    saveTimer = threading.Timer(const.backups_time*60, onTimerSave, [file])
    saveTimer.start()

def checkFriend(vk):
    ''' Проверка на наличие новых друзей и добавление их
        (необходимо для того, что бы бота могли добавить в беседы любые люди)

        :param vk: текущая сессия ВКонтакте

        :NoReturn:
        '''

    logs.write('Checking friends...')
    obj = vk.method('friends.getRequests') # получаем список всех заявок в друзья (непрочитанных!)
    logs.write(obj)
    for id in obj['items']: # перебираем все заявки
         vk.method('friends.add', {'user_id': id, 'follow': 0}) # добавляем в друзья
         logs.write(id, 'added')
    friendTimer = threading.Timer(const.friends_time*60, checkFriend, [vk]) # проверка на наличе новых друзей каждый час
    friendTimer.start()


def captcha_handler(captcha):
    ''' Отлавливание каптчи

    :param captcha: Объект капчи

    :return: Новая_попытка_отправить_сообщение_с_введенно_капчей
    '''

    key = ImageToTextTask.ImageToTextTask(anticaptcha_key=antiCaptchaKey, save_format='const') \
            .captcha_handler(captcha_link=captcha.get_url())
    logs.write('IMPORTANT: Entered captcha. Key: ' + str(key))

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key['solution']['text'])

def deletespamlist(event,spamlist):
    ''' Удаляет пользователя из спам-листа

        :param event: событие LongPoll
        :param spamlist: Список фдудеров

        :NoReturn:
    '''
    for i, element in enumerate(spamlist):  # Перебируем список заблокированных за спам сообщений
        if (element['id'] == event.user_id) and (element['chat_id'] == event.chat_id) and (
                element['text'] == event.text.split()):  # Нашли
            del spamlist[i]  # Удаляем элемент списка
            break


# ADDITIONAL DEFS:
def formatDeltaTime(dt):
    ''' Форматирует разницу во времени из количества секунд в строковое представление

    :param dt: Разница во времени в секундах

    :return: [str] '{0} дней, {1} часов, {2} минут, {3} секунд'
    '''
    d = divmod(dt,86400)  # days
    h = divmod(d[1],3600)  # hours
    m = divmod(h[1],60)  # minutes
    s = m[1]  # seconds
    return bot_msg.time_format.format(d[0],h[0],m[0],s)
# ------------------------ MAIN DEF -------------------------------------------

def main():
    logs.write("I'm starting my work ...")
    start_date = int(time.time()) # Секунд с начала эпохи
    global black_list
    global kick_votes

    try:
        f = open(const.file_name, 'r')
    except FileNotFoundError:
        open(const.file_name, 'w')
        black_list = []
    else:
        black_list = json.loads(f.readline())
        f.close()

    saveTimer = threading.Timer(const.backups_time*60, onTimerSave, [const.file_name])
    saveTimer.start()

    if isUsedAntiCaptcha:
        vk_session = vk_api.VkApi(login, password, captcha_handler=captcha_handler)
    else:
        vk_session = vk_api.VkApi(login, password)

    try:
        vk_session.auth(token_only=True) # Авторизируемся
    except vk_api.AuthError as error_msg:
        logs.write(error_msg)
        return

    checkFriend(vk_session) # Ежечасовая проверка друзей

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen(): # События VkLongPoll
        if (event.type is VkChatEventType.USER_JOINED) or (event.type is VkChatEventType.USER_LEFT) or (event.type is VkChatEventType.USER_KICKED):
            chats.getChatMembers.cache_clear() # Если кто-то пришел/ушел - очищаем кеш функции chats.getChatMembers
            logs.write('Clearing getChatMember cache')

        if event.type is VkChatEventType.USER_JOINED: # Кто-то зашел в беседу
            join_userid = event.info['user_id'] # id пользователя, который зашел в беседу
            logs.write('User id{0} joined at chat {1}'.format(join_userid, event.chat_id))
            checkForBan(vk_session, black_list, join_userid, event.chat_id)


        if (event.type == VkEventType.MESSAGE_NEW) and event.from_chat: # Событие: новое сообщение в чате
            event.text = event.text.lower()
            if antispam(event,spam_list):
                answer = event.text.split() # Отправленное юзверем сообщение

                chat_id = event.chat_id


                if (len(answer) == 2) and (answer[0] == '!voteban'): # если сообщение из двух строк и первое - служебное !voteban
                    if not(chats.isAdmin(vk_session, my_id, chat_id)): # Если бот не является админом
                        writeMessage(vk_session, chat_id, bot_msg.no_admin_rights)
                    else:
                        if searchKickList(kick_votes,chat_id) == None:
                            user_id = answer[1]
                            user = users.getName(vk_session, user_id) # Получаем информацию о пользователе
                            if users.isCanKick(vk_session, user_id, chat_id):
                                try:
                                    test = int(user_id)
                                except ValueError:
                                    'FullID'
                                else:
                                    user_id = 'id' + user_id
                                user_message = bot_msg.start_vote.format(user_id, user, const.vote_time, const.vote_count)
                                kick_votes.append(addKickMan(vk_session,user_id,chat_id)) # Добавляем в список очереди на кик

                                logs.write('New voteban: chat: {0}, member: {1}'.format(chat_id, user_id))

                                timer = threading.Timer(60*const.vote_time, finishVote, [vk_session, chat_id, kick_votes, black_list])
                                timer.start()
                                writeMessage(vk_session, chat_id, user_message)
                        else:
                            user_message = bot_msg.voting_is_active
                            writeMessage(vk_session, chat_id, user_message)

                if (len(answer) == 1) and ((answer[0] == '!votehelp') or (answer[0] == '!voteban')):
                    message = bot_msg.help.format(const.vote_time, const.vote_count)
                    writeMessage(vk_session, chat_id , message)
                if (len(answer) == 1) and (answer[0] in const.kick_commands) and searchKickList(kick_votes, chat_id):
                    voiceProcessing(event,kick_votes,vk_session,searchKickList(kick_votes,event.chat_id),'count_yes')

                if (len(answer) == 1) and (answer[0] in const.anti_kick_commands) and searchKickList(kick_votes, chat_id):
                    voiceProcessing(event,kick_votes,vk_session, searchKickList(kick_votes, event.chat_id),'count_no')

                if (len(answer) == 2) and (answer[0] == '!unban'):
                    if not (chats.isAdmin(vk_session, event.user_id, chat_id)):
                        writeMessage(vk_session, event.chat_id, bot_msg.you_are_not_admin)
                    else:
                        user_id = answer[1]
                        unbanUser(vk_session,user_id,black_list,event.chat_id)
                        logs.write('Unbaned user, chat: {0}, member: {1}'.format(event.chat_id, user_id))

                if (len(answer) == 1) and (answer[0] == '!banlist'):
                    banlist = getBanList(vk_session, black_list, event.chat_id)
                    writeMessage(vk_session, event.chat_id, banlist)


                if (len(answer) == 2) and (answer[0] == '!addinbanlist'):
                    if not (chats.isAdmin(vk_session, event.user_id, chat_id)):
                        writeMessage(vk_session, event.chat_id, bot_msg.you_are_not_admin)
                    else: # Если пользователь - администратор
                        banned_user_id = answer[1] # ID пользователя, которого кидаем в ЧС
                        if users.isCanKick(vk_session, banned_user_id, event.chat_id, True): # Проверка, что пользователь не является админом и тд
                            addBanList(vk_session, black_list, banned_user_id, event.chat_id, True) # Добавляем в черный список
                            logs.write('Added in banlist, chat: {0}, member: {1}'.format(event.chat_id, banned_user_id))
                            if chats.isUserInConversation(vk_session,banned_user_id,event.chat_id): # Если пользователь в беседе - кикаем его
                                checkForBan(vk_session, black_list, banned_user_id, event.chat_id)

                if (len(answer) == 1) and (answer[0] == '!uptime'):
                    now = int(time.time()) # Текущее время
                    delta = now - start_date # Разница во времени
                    writeMessage(vk_session, event.chat_id, bot_msg.my_uptime + formatDeltaTime(delta))



logs = log.Log(const.log_filename) # Создаем объект логов


try:
    if __name__ == '__main__':
        main()
except Exception as error_msg:
    try:
        f = open('error.log', 'a')
    except IOError:
        f = open('error.log', 'w')
    print(str(time.localtime(time.time())), file=f, end=' ')
    print(error_msg, file = f, end='\n')
    logs.write('ERROR!!!!!!' + error_msg)
    f.close()
    saveListToFile(black_list, const.file_name)
    logs.write("I'm finishing my work ...")
    main() # Произошло исключение - пробуем вернуться к работе
else:
    saveListToFile(black_list, const.file_name)
    logs.write("I'm finishing my work ...")

print(black_list)
