# coding: utf8

""" VOTEBAN BOT
:authors: Alexandr Pankratiew, Alexey Shilo
:contact: https://vk.com/sasha_pankratiew, https://vk.com/alexey_shilo
:githubs: https://github.com/N1ghtF1re, https://github.com/AlexeyLyapeshkin
:copyright: (c) 2018
"""

import threading
import json
from datetime import datetime

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from python3_anticaptcha import ImageToTextTask
from python3_anticaptcha import errors

from config import login,password,my_id,isUsedAntiCaptcha, antiCaptchaKey

# UNITS:
import const
import bot_msg

from units import users
from units import chats
from units.vkapi import writeMessage, kickUser


# INITIANALISATION

needkick = [] # Пользователи в ЧС беседы. Формат: [{'id':id, 'chat_id':chat_id}, {...}]


''' Список претендентов на кик.
    Формат: [{'id': [str],'chat_id': [int], 'time': [str], 'voted': set(), 'count_yes': [int], 'count_no': [int]}, {...}]

    Особенность: в данном списке может находиться только один элемент для каждой беседы
'''
kick_list = []
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
    time = str(datetime.now().hour)+':'+str(datetime.now().minute) # Текущее время
    mem = set()
    dic = {'id': user_id,'chat_id': chat_id, 'time': time, 'voted': mem, 'count_yes': county, 'count_no': countn}
    return dic

def searchKickList(kick_list, chat_id):
    ''' Поиск в списке претендентов на кик элемента с нужной беседы

        :param kick_list: Список претендентов на кик
        :param chat_id: id беседы ВК

        :return: [int] Элемент_с_нужной беседы | None, если элемента не существует
    '''
    for element in kick_list:
        if element['chat_id'] == chat_id:
            return element

def find_delete(kick_list,chat_id):
    ''' Поиск индекса списка претендетов на кик элемента с нужной беседы

        :param kick_list: Список претендентов на кик
        :param chat_id: id беседы ВК

        :return: [int] id_элелемента_с_нужной беседы
    '''

    for i, element in enumerate(kick_list):
        if element['chat_id'] == chat_id:
            return i

def voiceProcessing(event, kick_list,vk,element, ind):
    ''' Обработка голоса пользователя

        :event: Объект события LongPoll
        :kick_list: Список претендетов на кик
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
        print(kick_list)
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
            userName = users.getName(vk, user_id)
            user_message = bot_msg.unban_user.format(userName)
            break
    else:
        user_message = bot_msg.no_user_in_banlist
    writeMessage(vk,chat_id,user_message)

def checkForBan(vk, needkick, event):
    ''' Проверяет есть ли в беседе заблокированные пользователи

        :param vk: Объект сессии ВК
        :param needkick: Список заблокированных пользователей
        :param event: Событие LongPoll: Новое сообщение
    '''
    for el in needkick:
        if chats.isUserInConversation(vk,el['id'], event.chat_id) and (el['chat'] == event.chat_id):
        # Пользователь ливнул во время голосования и вернулся
            writeMessage(vk, event.chat_id, bot_msg.banned_user_came_in)
            kickUser(vk, event.chat_id, el['id'])

def addBanList(vk, needkick, user_id, chat_id):
    ''' Добавляет пользователя в бан-лист

        :vk: Объект сессии ВК
        :param needkick: Бан-лист
        :user_id: ID пользователя
        :chat_id: ID беседы ВК
    '''

    id = users.getUser(vk,user_id)['id']
    needkick.append({'id': id, 'chat': chat_id})


# ------------------------------ HANDLERS -------------------------------------------

def finishVote(vk, chat_id, kick_list, needkick):
    ''' Обработчик события таймера завершения голосования

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК, в которой завершилось голосование
        :kick_list: Список претендетов на кик
        :needkick: Список заблокированных пользователей

        :NoReturn:
    '''
    # Получаем элемент списка претендетов на кик для данной беседы
    kick_info = searchKickList(kick_list, chat_id)

    # Генерируем и отправляем сообщение о завершении голосования
    message = bot_msg.finish_vote.format(users.getName(vk, kick_info['id']),kick_info['count_yes'],kick_info['count_no'])
    writeMessage(vk, chat_id, message)

    try: # Если возникло исключение => бота кикнули из беседы
        if (len(kick_info['voted']) >= const.vote_count) and (kick_info['count_yes'] > kick_info['count_no']):
            if(chats.isUserInConversation(vk,kick_info['id'], chat_id)): # Если пользователь все еще в беседе
                writeMessage(vk, chat_id, bot_msg.user_excluded)
                # Исключаем пользователя
                kickUser(vk, chat_id, kick_info['id'])
            else: # Пользователь ливнул во время голосования
                writeMessage(vk,chat_id, bot_msg.user_leave)
            addBanList(vk, needkick, kick_info['id'], chet_id)

        elif len(kick_info['voted']) < const.vote_count:
            writeMessage(vk, chat_id, bot_msg.no_votes_cast.format(len(kick_info['voted']), const.vote_count))
        else:
            writeMessage(vk, chat_id, bot_msg.user_remains)
    except ApiError:
        print('Меня кикнули(')

    kick_list.pop(find_delete(kick_list,chat_id)) # Извлекаем из очереди на кик


def onTimerSave(file):
    ''' Обработчик события таймера сохранения списка заблокированных в файл

        :param file: Имя файла

        :NoReturn:
    '''
    global needkick
    saveListToFile(needkick, file)
    print('Сохранение в файл..')
    saveTimer = threading.Timer(const.backups_time*60, onTimerSave, [file])
    saveTimer.start()

def checkFriend(vk):
    ''' Проверка на наличие новых друзей и добавление их
        (необходимо для того, что бы бота могли добавить в беседы любые люди)

        :param vk: текущая сессия ВКонтакте

        :NoReturn:
        '''

    print('Checking friends...')
    obj = vk.method('friends.getRequests') # получаем список всех заявок в друзья (непрочитанных!)
    print(obj)
    for id in obj['items']: # перебираем все заявки
         vk.method('friends.add', {'user_id': id, 'follow': 0}) # добавляем в друзья
         print(id, 'added')
    friendTimer = threading.Timer(const.friends_time*60, checkFriend, [vk]) # проверка на наличе новых друзей каждый час
    friendTimer.start()


def captcha_handler(captcha):
    ''' Отлавливание каптчи

            :param captcha: Объект капчи

            :return: Новая_попытка_отправить_сообщение_с_введенно_капчей
            '''
    print('Entered captcha')
    key = ImageToTextTask.ImageToTextTask(anticaptcha_key=antiCaptchaKey, save_format='const') \
            .captcha_handler(captcha_link=captcha.get_url())

    print(key)

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



# ------------------------ MAIN DEF -------------------------------------------

def main():
    print("I'm starting my work ...")
    global needkick
    global kick_list
    print('Kick list: ', end='')
    print(kick_list)

    try:
        f = open(const.file_name, 'r')
    except FileNotFoundError:
        open(const.file_name, 'w')
        needkick = []
    else:
        needkick = json.loads(f.readline())
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
        print(error_msg)
        return

    checkFriend(vk_session) # Ежечасовая проверка друзей

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen(): # События VkLongPoll

        if event.type == VkEventType.CHAT_EDIT: # Кто-то вошел/вышел/изменил название беседы
            print(needkick)
            checkForBan(vk_session, needkick, event)


        if (event.type == VkEventType.MESSAGE_NEW) and event.from_chat: # Событие: новое сообщение в чате
            if antispam(event,spam_list):

                answer = event.text.split() # Отправленное юзверем сообщение

                chat_id = event.chat_id


                if (len(answer) == 2) and (answer[0].lower() == '!voteban'): # если сообщение из двух строк и первое - служебное !voteban
                    if not(chats.isAdmin(vk_session, my_id, chat_id)): # Если бот не является админом
                        writeMessage(vk_session, chat_id, bot_msg.no_admin_rights)
                    else:
                        if searchKickList(kick_list,chat_id) == None:
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
                                kick_list.append(addKickMan(vk_session,user_id,chat_id)) # Добавляем в список очереди на кик

                                timer = threading.Timer(60*const.vote_time, finishVote, [vk_session, chat_id, kick_list, needkick])
                                timer.start()
                                writeMessage(vk_session, chat_id, user_message)
                        else:
                            user_message = bot_msg.voting_is_active
                            writeMessage(vk_session, chat_id, user_message)

                if (len(answer) == 1) and ((answer[0].lower() == '!votehelp') or (answer[0].lower() == '!voteban')):
                    message = bot_msg.help.format(const.vote_time, const.vote_count)
                    writeMessage(vk_session, chat_id , message)
                if (len(answer) == 1) and (answer[0] in const.kick_commands) and searchKickList(kick_list, chat_id):
                    voiceProcessing(event,kick_list,vk_session,searchKickList(kick_list,event.chat_id),'count_yes')

                if (len(answer) == 1) and (answer[0] in const.anti_kick_commands) and searchKickList(kick_list, chat_id):
                    voiceProcessing(event,kick_list,vk_session, searchKickList(kick_list, event.chat_id),'count_no')

                if (len(answer) == 2) and (answer[0].lower() == '!unban'):
                    if not (chats.isAdmin(vk_session, event.user_id, chat_id)):
                        writeMessage(vk_session, event.chat_id, bot_msg.you_are_not_admin)
                    else:
                        user_id = answer[1]
                        unbanUser(vk_session,user_id,needkick,event.chat_id)

                if (len(answer) == 1) and (answer[0].lower() == '!banlist'):
                    user_message = ''
                    if len(needkick) != 0:
                       # user_message =
                        for element in needkick:
                            if element['chat'] == event.chat_id:
                                user_message += '* {0} [{1}] \n'.format(str(users.getName(vk_session,element['id'],'nom')), element['id'])
                        if len(user_message) != 0:
                            mem = bot_msg.banned_list + user_message
                        else:
                            mem = bot_msg.banlist_empty
                        writeMessage(vk_session, event.chat_id, mem)
                    else:
                        writeMessage(vk_session, event.chat_id, bot_msg.banlist_empty)

                if (len(answer) == 2) and (answer[0].lower() == '!addbanlist'):
                    if not (chats.isAdmin(vk_session, event.user_id, chat_id)):
                        writeMessage(vk_session, event.chat_id, bot_msg.you_are_not_admin)
                    else:
                        user_id = answer[1]
                        if users.isCanKick(vk_session, user_id, event.chat_id, True):
                            writeMessage(vk_session, chat_id, bot_msg.user_added_in_banlist)
                            addBanList(vk_session, needkick, user_id, event.chat_id)
                            if chats.isUserInConversation(vk_session,user_id,event.chat_id):
                                checkForBan(vk_session, needkick, event)
if __name__ == '__main__':
    main()
'''
try:
    if __name__ == '__main__':
        main()
except Exception as error_msg:
    try:
        f = open('error.log', 'a')
    except IOError:
        f = open('error.log', 'w')
    print(str(datetime.now()), file=f, end=' ')
    print(error_msg, file = f, end='\n')
    f.close()
    print(needkick)
    saveListToFile(needkick, const.file_name)
    print("I'm finishing my work ...")
    main() # Произошло исключение - пробуем вернуться к работе
else:
    saveListToFile(needkick, const.file_name)
    print("I'm finishing my work ...")
'''
print(needkick)
