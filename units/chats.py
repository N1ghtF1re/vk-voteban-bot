'''
ПОДПРОГРАММЫ ДЛЯ РАБОТЫ
С БЕСЕДАМИ
VOTEBAN BOT
'''

from units import vkapi
from units import users
import bot_msg


def isUserInConversation(vk, user_id, chat_id):
    ''' Проверяем, находится ли пользователь с id = userid в чате с id = chat_id

        :param vk: Объект сессии вк
        :param user_id: id пользователя
        :param chat_id: id беседы ВК

        :return: True, если пользователь в беседе | False, если не в беседе
    '''
    user = users.getUser(vk,user_id) # Получаем объект пользователя

    if not user: # Пользователя не существует
        return False

    id = user[0]['id']

    if not id: # ID не существует
        return False

    # Получаем информацию о пользователях беседы
    try:
        chatMembers = vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id})
    except:
        return False

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
