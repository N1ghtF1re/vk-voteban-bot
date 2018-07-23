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

# Constants
nokick = {'sasha_pankratiew', 'alexey_shilo', 'id136385345', 'id138738887', '138738887', '136385345'}

file_name = 'v.ban'

vote_count = 5 # Минимальное кол-во голосов
vote_time = 5 # Количество минут, сколько длится голосование
spam_time = 10.0 # Анти-спам задержка
friends_time = 60.0 # Интервал (в минутах) проверки друзей
backups_time = 5 # Интервал проведения бэкапа списка заблокированных


anti_kick_commands = {'!нет','!-','!no','!некик','!некикаемнахой'} # Команды для кика
kick_commands = {'!да', '!yes', '!+', 'кик','!кикаемнахой'} # Команды против кика

# String Constants

finish_message = '[VOTEBAN] Голосование за кик {0} завершено. Голосов за: {1}, голосов против: {2}.'
startvote_message = '[VOTEBAN] Кикаем [{0}|{1}]?\nЧтобы проголосовать за - пишите "!да" / "!+" / "!yes". Против - "!нет" / "!-" / "!no"\nГолосование продлится {2} минут.\n' \
                    'Для голосования необходимо набрать {3} голосов'
vote_message = '[VOTEBAN] Голос принят. Кол-во голосов за кик: {0}. Кол-во голосов против кика: {1}'
help_message = '''[VOTEBAN] Вас привествует бот, позволяющий делать голосование за исключение какого-либо пользователя.

Комманды:
- !voteban ID_ПОЛЬЗОВАТЕЛЯ - создать голосование. ID пользователя находится в его ссылке после vk.com/. Голосование длится {0} минут. Условия исключения: голосовало более {1} участников беседы, голосов "за" набрано больше, чем "против"
- !votehelp - Помощь по использованию бота
- !banlist - Просмотреть заблокированных в этой беседе пользоваетелей
- !unban ID_ПОЛЬЗОВАТЕЛЯ [ТОЛЬКО ДЛЯ АДМИНИСТРАТОРОВ БЕСЕДЫ] - разблокировать пользователя

Авторы бота: [id136385345|Сашка Панкратьев] и [id138738887|Лёшка Лепёшка]

Со временем функционал бота будет пополняться.'''

# INITIANALISATION

needkick = [] # Пользователи в ЧС беседы. Формат: [{'id':id, 'chat_id':chat_id}, {...}]


''' Список претендентов на кик.
    Формат: [{'id': [str],'chat_id': [int], 'time': [str], 'voted': set(), 'count_yes': [int], 'count_no': [int]}, {...}]

    Особенность: в данном списке может находиться только один элемент для каждой беседы
'''
kick_list = []
spam_list = []

# ------------------------------- USERS UTILS: ---------------------------------------
def getUser(vk, user_id, name_case = 'gen'):
    ''' Получаем информацию о пользователе с id = id

        :param vk: Объект сессии ВК
        :param user_id: ID пользователя (id или screen_id)
        :param name_case: Падеж имен пользователей. Подробнее:
                                      https://vk.com/dev/users.get

        :return: Объект пользователя | None если он не найден
    '''

    try:
        return vk.method('users.get', {'user_ids': user_id, 'name_case':name_case})
    except vk_api.exceptions.ApiError:
        return None # Пользователь не найден


def getName(vk, user_id, name_case = 'gen'):
    ''' Получаем строку с фамилей и именем пользователя в нужном падеже

        :param vk: Объект сессии ВК
        :param user_id: id пользователя (id или screen_id)
        :param name_case: Падеж имен пользователей. Подробнее:
                                      https://vk.com/dev/users.get

        :return: [str] Фамилия Имя | None, если его не существует
    '''
    user = getUser(vk,user_id, name_case) # Получаем объект пользователя
    if user == None: return None # Если пользователя не существует
    user = user[0]
    return (user['first_name'] + ' ' + user['last_name'])#.encode('utf-8') # Если проблемы с кодировкой - надо убрать "ecnode("utf-8")"

# ------------------- CONVERSATIONS ---------------------------------
def isUserInConversation(vk, user_id, chat_id):
    ''' Проверяем, находится ли пользователь с id = userid в чате с id = chat_id

        :param vk: Объект сессии вк
        :param user_id: id пользователя
        :param chat_id: id беседы ВК

        :return: True, если пользователь в беседе | False, если не в беседе
    '''
    user = getUser(vk,user_id) # Получаем объект пользователя

    if not user: # Пользователя не существует
        return False

    id = user[0]['id']

    if not id: # ID не существует
        return False

    # Получаем информацию о пользователях беседы
    chatMembers = vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id})

    try:
        for member in chatMembers['items']: # Перебираем пользоваетелей беседы
            if member['member_id'] == id:
                return True # Пользователь найден в беседе
        return False
    except:
        print(member)

def getUsersCount(vk, chat_id):
    ''' Получаем число участников беседы

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК

        :return: [int] Число_участников
    '''
    # Получаем информацию о пользователях беседы
    chatMembers = vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id})
    return chatMembers['count']

def isAdmin(vk, user_id, chat_id):
    ''' Проверяем, является ли пользователь администратором

        :param vk: Объект сессии ВК
        :param user_id: id пользователя (Не screen_id)

        :return: True, если админ | False, если не админ
    '''

    # Получаем информацию о пользователях беседы
    chatMembers = vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id})
    for member in chatMembers['items']: # Перебираем пользоваетелей беседы
        if member['member_id'] == user_id:
            return member.get('is_admin', False)

#  ----------------------------- KICK LIST -----------------------------------------

def AddKickMan(vk, user_id, chat_id,county=0,countn=0):
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
    user = getUser(vk, element['id']) # Получаем объект пользоваетля
    if not(event.user_id == user[0]['id']): # Если пользователь не голосует сам за себяя
        if not (event.user_id in element['voted']): # Если пользователь еще не голосовал
            element['voted'].add(event.user_id) # Заносим пользователя в множество проголосовавших
            element[ind] += 1 # Увеличиваем количество голосов за/против (В зависимости от выбора пользователя)

            # Формируем и отправляем сообщения о голосе
            user_message = vote_message.format(str(element['count_yes']),str(element['count_no']))
            writeMessage(vk, event.chat_id, user_message)
        print(kick_list)
    else:
        user_message = '[VOTEBAN] Ошибка: Нельзя голосовать самому за себя!'
        writeMessage(vk, event.chat_id, user_message)

# ---------------------------- VK API ---------------------------------
def writeMessage(vk, chat_id, message):
    ''' Вывод сообщения в чат

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК
        :param message: Сообщение, которое надо вывести

        :NoReturn:
    '''
    vk.method('messages.send', {'chat_id':chat_id, 'message': message})


# --------------------------- FILES ----------------------------------
def saveListToFile(my_list,file):
    ''' Сохранение списка в файл

        :param my_list: Список, который надо сохранить
        :param file: Имя файла, в который сохранить (Файл перезапишется)

        :NoReturn:
    '''
    f = open(file_name, 'w')
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
        timer = threading.Timer(spam_time, deletespamlist,[event,spamlist]) #ставим таймер на удаление из спсика (многопоточно)
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
    for i, element in enumerate(banlist): # Перебируем список заблокированных
        if element['id'] == user_id and element['chat'] == chat_id: # Нашли
            del banlist[i] # Удаляем элемент списка
            userName = getName(vk, user_id)
            user_message = '[VOTEBAN] Я разбанил {0}. Можете его возвращать в беседу'.format(userName)
            break
    else:
        user_message = '[VOTEBAN] Ошибка: Такого юзера нету в бан-листе...'
    writeMessage(vk,chat_id,user_message)

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
    message = finish_message.format(getName(vk, kick_info['id']),kick_info['count_yes'],kick_info['count_no'])
    writeMessage(vk, chat_id, message)

    try: # Если возникло исключение => бота кикнули из беседы
        if (len(kick_info['voted']) >= vote_count) and (kick_info['count_yes'] > kick_info['count_no']):
            if(isUserInConversation(vk,kick_info['id'], chat_id)): # Если пользователь все еще в беседе
                writeMessage(vk, chat_id, '[VOTEBAN] Пользователь исключен')
                # Исключаем пользователя
                vk.method('messages.removeChatUser', {'chat_id': chat_id, 'user_id':getUser(vk,kick_info['id'])[0]['id']})
            else: # Пользователь ливнул во время голосования
                writeMessage(vk,chat_id, '[VOTEBAN] Этот говнюк ливнул. Зайдет - кикну')

            needkick.append({'id':kick_info['id'], 'chat': chat_id}) # Добавляем пользователя в список заблокированных

        elif len(kick_info['voted']) < vote_count:
            writeMessage(vk, chat_id, '[VOTEBAN] Не набрано достаточное количетсво голосов (Набрано: {0}, необходимо: {1}).\nТак что пользователь остается в беседе... Пока что...'.format(len(kick_info['voted']), vote_count))
        else:
            writeMessage(vk, chat_id, '[VOTEBAN] Пользователь остается в беседе... Пока что...')
    except:
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
    saveTimer = threading.Timer(backups_time*60, onTimerSave, [file])
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
    friendTimer = threading.Timer(friends_time*60, checkFriend, [vk]) # проверка на наличе новых друзей каждый час
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


    saveTimer = threading.Timer(backups_time*60, onTimerSave, [file_name])
    saveTimer.start()

    try:
        f = open(file_name, 'r')
    except FileNotFoundError:
        open(file_name, 'w')
        needkick = []
    else:
        needkick = json.loads(f.readline())
        f.close()
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
    count = 0
    for event in longpoll.listen(): # События VkLongPoll

        if event.type == VkEventType.CHAT_EDIT:
            print(needkick)
            for el in needkick:
                if isUserInConversation(vk_session,el['id'], event.chat_id) and (el['chat'] == event.chat_id):
                # Пользователь ливнул во время голосования и вернулся
                    writeMessage(vk_session, event.chat_id, '[VOTEBAN] Ну вот мы и встретились...')
                    vk_session.method('messages.removeChatUser', {'chat_id': event.chat_id, 'user_id':getUser(vk_session,el['id'])[0]['id']})

        if (event.type == VkEventType.MESSAGE_NEW) and event.from_chat: # Событие: новое сообщение в чате
            '''
            print('Message: ', event.user_id, ' in ', event.chat_id)
            print('>>> ' + event.text)
            '''

            if antispam(event,spam_list):

                answer = event.text.split() # Отправленное юзверем сообщение

                chat_id = event.chat_id


                if (len(answer) == 2) and (answer[0].lower() == '!voteban'): # если сообщение из двух строк и первое - служебное !voteban
                    if not(isAdmin(vk_session, my_id, chat_id)):
                        user_message = '[VOTEBAN] Ошибка: У меня нет прав администратора'
                    else:
                        if searchKickList(kick_list,event.chat_id) == None:
                            user_id = answer[1]
                            user = getName(vk_session, user_id) # Получаем информацию о пользователе
                            if isUserInConversation(vk_session, user_id, chat_id): # Поиск в беседе пользователя. Если найден - продолжаем
                                if not(isAdmin(vk_session, getUser(vk_session,user_id)[0]['id'], chat_id)): # Если пользователь - не админ, продолжаем
                                    if not(user_id in nokick):
                                        try:
                                            test = int(user_id)
                                        except ValueError:
                                            'FullID'
                                        else:
                                            user_id = 'id' + user_id
                                        user_message = startvote_message.format(user_id, user, vote_time, vote_count)
                                        kick_list.append(AddKickMan(vk_session,user_id,chat_id)) # Добавляем в список очереди на кик

                                        timer = threading.Timer(60*vote_time, finishVote, [vk_session, chat_id, kick_list, needkick])
                                        timer.start()
                                    else:
                                        user_message = '[VOTEBAN] Не могу выгнать этого пользователя'
                                else:
                                    user_message = '[VOTEBAN] Ошибка: Пользователь является администратором'
                            else:
                                user_message = '[VOTEBAN] Ошибка: Пользователь не в беседе'

                        else:
                            user_message = '[VOTEBAN] Ошибка: Голосвание уже идет.'
                    writeMessage(vk_session, chat_id, user_message)
                if (len(answer) == 1) and ((answer[0].lower() == '!votehelp') or (answer[0].lower() == '!voteban')):
                    message = help_message.format(vote_time, vote_count)
                    writeMessage(vk_session, chat_id , message)
                if (len(answer) == 1) and (answer[0] in kick_commands) and searchKickList(kick_list, chat_id):
                    voiceProcessing(event,kick_list,vk_session,searchKickList(kick_list,event.chat_id),'count_yes')

                if (len(answer) == 1) and (answer[0] in anti_kick_commands) and searchKickList(kick_list, chat_id):
                    voiceProcessing(event,kick_list,vk_session, searchKickList(kick_list, event.chat_id),'count_no')

                if (len(answer) == 2) and (answer[0].lower() == '!unban'):
                    if not (isAdmin(vk_session, event.user_id, chat_id)):
                        user_message = '[VOTEBAN] Ошибка: Вы не администратор.'
                        writeMessage(vk_session, event.chat_id, user_message)
                    else:
                        user_id = answer[1]
                        unbanUser(vk_session,user_id,needkick,event.chat_id)

                if (len(answer) == 1) and (answer[0].lower() == '!banlist'):
                    user_message = ''
                    if len(needkick) != 0:
                       # user_message =
                        for element in needkick:
                            if element['chat'] == event.chat_id:
                                user_message += '* {0} [{1}] \n'.format(str(getName(vk_session,element['id'],'nom')), element['id'])
                        if len(user_message) != 0:
                            mem = '[VOTEBAN] СПИСОК ЗАБАНЕННЫХ ПОЛЬЗОВАТЕЛЕЙ: \n\n' + user_message
                        else:
                            mem = '[VOTEBAN]  Бан-лист пуст.'
                        writeMessage(vk_session, event.chat_id, mem)
                    else:
                        user_message = '[VOTEBAN]  Бан-лист пуст.'
                        writeMessage(vk_session, event.chat_id, user_message)



try:
    if __name__ == '__main__':
        main()
except Exception as error_msg:
    print(error_msg)
    print(needkick)
    saveListToFile(needkick, file_name)
    print("I'm finishing my work ...")
    main() # Произошло исключение - пробуем вернуться к работе
else:
    saveListToFile(needkick, file_name)
    print("I'm finishing my work ...")

print(needkick)
