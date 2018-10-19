'''
ПОДПРОГРАММЫ ДЛЯ УДОБНОЙ
РАБОТЫ С VK API
VOTEBAN BOT
'''

import bot_msg
from units import users

def writeMessage(vk, chat_id, message):
    ''' Вывод сообщения в чат

        :param vk: Объект сессии ВК
        :param chat_id: id беседы ВК
        :param message: Сообщение, которое надо вывести

        :NoReturn:
    '''
    if len(message) >= 3000:
        for i in range(3000, len(message)):
            print(i)
            print(len(message))
            if message[i] == '\n' or i == 4000:
                restMessage=message[slice(i, len(message))]
                message = message[slice(0,i)]
                vk.method('messages.send', {'chat_id':chat_id, 'message': message})
                writeMessage(vk, chat_id, restMessage)
                break
    else:
        vk.method('messages.send', {'chat_id':chat_id, 'message': message})

def kickUser(vk, chat_id, user_id):
    ''' Выгоняет пользователя из беседы

        :param vk: Объект сессии ВК
        :param user_id: id пользователях
        :param chat_id: id беседы ВК

        :NoReturn:
    '''
    try:
        vk.method('messages.removeChatUser', {'chat_id': chat_id, 'user_id':users.getUser(vk,user_id)['id']})
    except:
        writeMessage(vk, chat_id, bot_msg.no_rights_for_kicks)
