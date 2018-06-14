#coding:utf-8

class Context:
    def __init__(self, reader, reporter):
        self.__reader = reader
        self.__reporter = reporter

    @property
    def reader(self):
        return self.__reader

    @property
    def config(self):
        pass

    @property
    def reporter(self):
        return self.__reporter
