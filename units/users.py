'''
ПОДПРОГРАММЫ ДЛЯ РАБОТЫ
С ПОЛЬЗОВАТЕЛЯМИ
VOTEBAN BOT
'''

from units import vkapi
from units import chats
import bot_msg
import const

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

def isCanKick(vk, user_id, chat_id, NoCheckIN = False):
    ''' Проверка, можно ли выгнать пользователях

        :param vk: Объект сессии ВК
        :param user_id: id пользователя
        :param chat_id: id беседы ВК
        :param NoCheckIN: Нужно ли проверять на наличие в беседе (False если нужно)

        :return: True если можно кикнуть | False если нельзя
    '''
    if NoCheckIN or chats.isUserInConversation(vk, user_id, chat_id): # Поиск в беседе пользователя. Если найден - продолжаем
        if not(chats.isAdmin(vk, getUser(vk,user_id)[0]['id'], chat_id)): # Если пользователь - не админ, продолжаем
            if not(user_id in const.nokick):
                return True
            else:
                user_message = bot_msg.can_not_kick_user
        else:
            user_message = bot_msg.user_is_admin
    else:
        user_message = bot_msg.user_not_in_chat
    vkapi.writeMessage(vk, chat_id, user_message)
    return False
