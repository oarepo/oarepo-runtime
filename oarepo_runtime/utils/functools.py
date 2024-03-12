def try_sequence(*funcs, ignored_exceptions=(), raised_exception=Exception):
    raised_exceptions = []
    for func in funcs:
        try:
            return func()
        except ignored_exceptions as e:
            raised_exceptions.append(e)
    raise raised_exception(raised_exceptions) from raised_exceptions[-1]


class class_property:
    def __init__(self, getter=None, setter=None):
        if getter is not None and not isinstance(getter, classmethod):
            getter = classmethod(getter)
        if setter is not None and not isinstance(setter, classmethod):
            setter = classmethod(setter)
        self.__get = getter
        self.__set = setter

        if getter:
            info = getter.__get__(object)  # just need the info attrs.
            self.__doc__ = info.__doc__
            self.__name__ = info.__name__
            self.__module__ = info.__module__

    def __get__(self, obj, type=None):  # NOSONAR - this is a descriptor
        if obj and type is None:
            type = obj.__class__  # NOSONAR - this is a descriptor
        return self.__get.__get__(obj, type)()

    def __set__(self, obj, value):
        if obj is None:
            return self
        return self.__set.__get__(obj)(value)

    def setter(self, setter):
        return self.__class__(self.__get, setter)
