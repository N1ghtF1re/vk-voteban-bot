import datetime

class Log(object):
    '''
        Класс ведение логов

        :param filename: название файла логов
    '''

    def __init__(self, filename):
        try:
            self.logfile = open(filename, 'a')
        except IOError:
            self.logfile =  open(filename, 'w')

    def write(self, message):
        currtime = str(datetime.datetime.now())

        message = '> [{0}] {1}'.format(currtime, message)

        print(message, end='\n', file=self.logfile)

    def __del__(self):
        self.logfile.close()