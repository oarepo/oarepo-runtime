"""Instrumentors for debugging permissions."""

import contextvars
import inspect
import json
import sys

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


def debug_needs_output(clz, method_name):
    method = getattr(clz, method_name)

    def wrapper(self, *args, **kwargs):
        dd = json.dumps(self.to_debug_dict())
        print(f"{'  ' * debugging_level.get()}{dd}.{method_name} ->", file=sys.stderr)
        reset = debugging_level.set(debugging_level.get() + 1)
        ret = method(self, *args, **kwargs)
        debugging_level.reset(reset)
        if "debug_identity" in kwargs:
            matched_needs = set(ret) & set(kwargs["debug_identity"].provides)
            print(
                f"{'  ' * debugging_level.get()}  -> match: {matched_needs}",
                file=sys.stderr,
            )
        else:
            print(f"{'  ' * debugging_level.get()}  -> {ret}", file=sys.stderr)
        return ret

    return wrapper


def debug_search_output(clz, method_name, print_search):
    method = getattr(clz, method_name)

    def wrapper(self, *args, **kwargs):
        dd = json.dumps(self.to_debug_dict())
        if print_search:
            print(f"{'  ' * debugging_level.get()}{dd}.{method_name}:", file=sys.stderr)
        reset = debugging_level.set(debugging_level.get() + 2)
        ret = method(self, *args, **kwargs)
        debugging_level.reset(reset)
        if isinstance(ret, list):
            r = merge_communities([x.to_dict() for x in ret])
        elif ret:
            r = merge_communities(ret.to_dict())
        else:
            r = None
        if print_search:
            print(
                f"{'  ' * debugging_level.get()}{dd}.{method_name} -> {r}",
                file=sys.stderr,
            )
        return ret

    wrapper.__module__ = clz.__module__
    wrapper.__qualname__ = f"{clz.__qualname__}.{method_name}"
    wrapper.__name__ = method_name
    return wrapper


def merge_communities(x):
    if isinstance(x, list):
        return [merge_communities(y) for y in x]
    if isinstance(x, dict):
        ret = {k: merge_communities(v) for k, v in x.items()}
        if "parent.communities.default" in ret:
            ret["parent.communities.default"] = "#communities#"
        if "parent.communities.ids" in ret:
            ret["parent.communities.ids"] = "#communities#"
        return ret
    return x


def get_opensearch_caller():
    # Get the current call stack
    stack = inspect.stack()
    # Extract function names from the stack frames
    function_names = []
    state = "skipping_to_opensearch"
    for frame in stack:
        module_name = frame.frame.f_globals["__name__"]
        if state == "skipping_to_opensearch":
            if module_name.startswith("opensearch_dsl.") or module_name.startswith(
                "oarepo_runtime.info"
            ):
                state = "found_opensearch"
        if state == "found_opensearch":
            if not module_name.startswith(
                "opensearch_dsl."
            ) and not module_name.startswith("oarepo_runtime.info"):
                state = "outside_opensearch"
        if state == "outside_opensearch":
            if frame.function == "<lambda>":
                continue
            if "self" in frame.frame.f_locals:
                self_instance = frame.frame.f_locals["self"]
                class_name = self_instance.__class__.__name__
                function_names.append(
                    f"{class_name}.{frame.function} @ {frame.filename}:{frame.lineno}"
                )
            else:
                function_names.append(
                    f"{frame.function} @ {frame.filename}:{frame.lineno}"
                )
        del frame

    return function_names


def add_debugging(print_needs=True, print_excludes=True, print_search=True):
    for generator in get_all_generators():
        if issubclass(generator, ConditionalGenerator):
            generator.to_debug_dict = conditional_generator_to_debug_dict
        else:
            generator.to_debug_dict = generator_to_debug_dict
        if print_needs and not hasattr(generator.needs, "__is_debug_instrumented__"):
            generator.needs = debug_needs_output(generator, "needs")
            generator.needs.__is_debug_instrumented__ = True
        if print_excludes and not hasattr(
            generator.excludes, "__is_debug_instrumented__"
        ):
            generator.excludes = debug_needs_output(generator, "excludes")
            generator.excludes.__is_debug_instrumented__ = True

        if hasattr(generator, "query_filters"):
            if not hasattr(generator.query_filters, "__is_debug_instrumented__"):
                generator.query_filters = debug_search_output(
                    generator, "query_filters", print_search
                )
                generator.query_filters.__is_debug_instrumented__ = True
        if hasattr(generator, "query_filter"):
            if not hasattr(generator.query_filter, "__is_debug_instrumented__"):
                generator.query_filter = debug_search_output(
                    generator, "query_filter", print_search
                )
                generator.query_filter.__is_debug_instrumented__ = True
    # try to add _name to queries
    from opensearch_dsl.query import Query

    previous_init = Query.__init__

    def new_init(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self._params["_name"] = get_opensearch_caller()[0]

    Query.__init__ = new_init
