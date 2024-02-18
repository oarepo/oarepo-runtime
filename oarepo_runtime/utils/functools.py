def try_sequence(*funcs, ignored_exceptions=(), raised_exception=Exception):
    raised_exceptions = []
    for func in funcs:
        try:
            return func()
        except ignored_exceptions as e:
            raised_exceptions.append(e)
    raise raised_exception(raised_exceptions) from raised_exceptions[-1]
