'''
ФУНКЦИИ ДЛЯ РАБОТЫ
С БЕСЕДАМИ
VOTEBAN BOT
'''
from functools import lru_cache # Кеширование

from units import vkapi
from units import users
import bot_msg

@lru_cache(maxsize=8)
def getChatMembers(vk, chat_id):
    ''' ВОЗВРАЩАЕТ ОБЪЕКТ БЕСЕДЫ

        :additional: Функция кеширует последние 8 результатов. Кеш очищается при
        обновлении одной из бесед (событие CHAT_EDIT)

        :param vk: Объект сессии вк
        :param chat_id: id беседы ВК

        :return: Объект беседы ВК. Подробнее: https://vk.com/dev/messages.getConversationMembers
    '''

    try:
        return vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id})
    except:
        return {'items': []}



def isUserInConversation(vk, user_id, chat_id):
    ''' Проверяем, находится ли пользователь с id = userid в чате с id = chat_id

        :param vk: Объект сессии вк
        :param user_id: id пользователя
        :param chat_id: id беседы ВК

        :return: Непустой список , если пользователь в беседе | [], если не в беседе
    '''
    user = users.getUser(vk,user_id) # Получаем объект пользователя

    if not user: # Пользователя не существует
        return False

    id = user['id']

    if not id: # ID не существует
        return False

    # Получаем информацию о пользователях беседы
    chatMembers = getChatMembers(vk, chat_id)

    return list(filter(lambda member: member['member_id'] == id, chatMembers['items']))


def getUsersCount(vk, chat_id):
    ''' Получаем число участников беседы

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК

        :return: [int] Число_участников
    '''
    # Получаем информацию о пользователях беседы
    chatMembers = getChatMembers(vk, chat_id)
    return chatMembers['count']

def isAdmin(vk, user_id, chat_id):
    ''' Проверяем, является ли пользователь администратором

        :param vk: Объект сессии ВК
        :param user_id: id пользователя (Не screen_id)

        :return: True, если админ | False, если не админ
    '''

    # Получаем информацию о пользователях беседы
    chatMembers = vk.method('messages.getConversationMembers', {'peer_id': 2000000000+chat_id}) # Кеширование невозможно т.к. нет события на выдачу админки
    for member in chatMembers['items']: # Перебираем пользоваетелей беседы
        if member['member_id'] == user_id:
            return member.get('is_admin', False)
