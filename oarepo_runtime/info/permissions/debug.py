"""Instrumentors for debugging permissions."""

import contextvars
import json

from invenio_records_permissions.generators import ConditionalGenerator, Generator


def generator_to_debug_dict(self: Generator):
    ret = {
        "name": self.__class__.__name__,
    }
    ret = {}
    for fld in self.__dict__:
        if fld.startswith("__"):
            continue
        if fld in ("then_", "else_"):
            continue
        value = self.__dict__[fld]
        if not isinstance(value, (str, int, float, bool)):
            value = str(value)
        ret[fld] = value

    return {self.__class__.__name__: ret}


def conditional_generator_to_debug_dict(self: ConditionalGenerator):
    ret = generator_to_debug_dict(self)
    r = ret[self.__class__.__name__]
    if self.then_:
        r["then"] = [x.to_debug_dict() for x in self.then_]
    if self.else_:
        r["else"] = [x.to_debug_dict() for x in self.else_]
    return ret


def get_all_generators():
    generator_classes = set()
    queue = [Generator]
    while queue:
        gen = queue.pop()
        generator_classes.add(gen)
        for cls in gen.__subclasses__():
            if cls in generator_classes:
                continue
            queue.append(cls)
    return generator_classes


debugging_level = contextvars.ContextVar("debugging_level", default=0)


def debug_output(clz, method_name):
    method = getattr(clz, method_name)

    def wrapper(self, *args, **kwargs):
        dd = json.dumps(self.to_debug_dict())
        print(f"{'  ' * debugging_level.get()}{dd}.{method_name} ->")
        reset = debugging_level.set(debugging_level.get() + 1)
        ret = method(self, *args, **kwargs)
        debugging_level.reset(reset)
        if "debug_identity" in kwargs:
            matched_needs = set(ret) & set(kwargs["debug_identity"].provides)
            print(f"{'  ' * debugging_level.get()}  -> match: {matched_needs}")
        else:
            print(f"{'  ' * debugging_level.get()}  -> {ret}")
        return ret

    return wrapper


def add_debugging():
    for generator in get_all_generators():
        if issubclass(generator, ConditionalGenerator):
            generator.to_debug_dict = conditional_generator_to_debug_dict
        else:
            generator.to_debug_dict = generator_to_debug_dict
        if not hasattr(generator.needs, "__is_debug_instrumented__"):
            generator.needs.__is_debug_instrumented__ = True
            generator.needs = debug_output(generator, "needs")
        if not hasattr(generator.excludes, "__is_debug_instrumented__"):
            generator.excludes.__is_debug_instrumented__ = True
            generator.excludes = debug_output(generator, "excludes")
