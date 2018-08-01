'''
СООБЩЕНИЯ БОТА
VOTEBAN BOT
'''

prefix = '[VOTEBAN] '

# С ФОРМАТИРОВАНИЕМ:
finish_vote = prefix + 'Голосование за кик {0} завершено. Голосов за: {1}, голосов против: {2}.'
start_vote = prefix + 'Кикаем [{0}|{1}]?\nЧтобы проголосовать за - пишите "!да" / "!+" / "!yes". Против - "!нет" / "!-" / "!no"\nГолосование продлится {2} минут.\n' \
                    'Для голосования необходимо набрать {3} голосов'
vote_accepted = prefix + 'Голос принят. Кол-во голосов за кик: {0}. Кол-во голосов против кика: {1}'

help = prefix + '''Вас привествует бот, позволяющий делать голосование за исключение какого-либо пользователя.

Комманды:
- !voteban ID_ПОЛЬЗОВАТЕЛЯ - создать голосование. ID пользователя находится в его ссылке после vk.com/. Голосование длится {0} минут. Условия исключения: голосовало более {1} участников беседы, голосов "за" набрано больше, чем "против"
- !votehelp - Помощь по использованию бота
- !banlist - Просмотреть заблокированных в этой беседе пользоваетелей
- !unban ID_ПОЛЬЗОВАТЕЛЯ [ТОЛЬКО ДЛЯ АДМИНИСТРАТОРОВ БЕСЕДЫ] - разблокировать пользователя

Авторы бота: [id136385345|Сашка Панкратьев] и [id138738887|Лёшка Лепёшка]

Со временем функционал бота будет пополняться.'''

unban_user = prefix + 'Я разбанил {0}. Можете его возвращать в беседу'

no_votes_cast = prefix + 'Не набрано достаточное количетсво голосов (Набрано: {0}, необходимо: {1}).\nТак что пользователь остается в беседе... Пока что...'

# КонстантныеЖ

can_not_kick_user = prefix + 'Ошибка: Не могу выгнать этого пользователя'
user_is_admin = prefix + 'Ошибка: Пользователь является администратором'
user_not_in_chat = prefix + 'Ошибка: Пользователь не в беседе'
user_not_found = prefix + 'Ошибка: Такого пользователя не существует'

err_vote_for_yourself = prefix + 'Ошибка: Нельзя голосовать самому за себя!'

no_rights_for_kicks = prefix + 'Не могу выгнать пользователя. Скорее всего, меня лишили прав администратора'

no_user_in_banlist = prefix + 'Ошибка: Такого юзера нету в бан-листе...'

banned_user_came_in = prefix +  'Ну вот мы и встретились...'

user_excluded = prefix + 'Пользователь исключен'

user_leave = prefix + 'Этот говнюк ливнул. Зайдет - кикну'
user_remains = prefix + 'Пользователь остается в беседе... Пока что...'

no_admin_rights = prefix + 'Ошибка: У меня нет прав администратора'
voting_is_active = prefix + 'Ошибка: Голосвание уже идет.'

you_are_not_admin = prefix + 'Ошибка: Вы не администратор.'

banned_list = prefix + 'СПИСОК ЗАБАНЕННЫХ ПОЛЬЗОВАТЕЛЕЙ: \n\n'
banlist_empty = prefix + 'Бан-лист пуст.'

user_added_in_banlist = prefix + 'Пользователь добавлен в бан-лист.'
