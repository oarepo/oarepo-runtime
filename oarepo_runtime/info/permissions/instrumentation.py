"""Permission introspection, instrumentation and performing operations on them."""

import copy
import inspect
from typing import Any, Protocol, override


class Instrumentor(Protocol):
    """Instrumentor protocol."""

    def can_instrument(self, inst: Any) -> bool:
        """Return True if the instrumentor can instrument the given instance."""
        ...

    def instrument[T](
        self,
        inst: T,
        mixins: dict[type, type],
        instrumentors: "InstrumentorRegistry",
        context: dict,
    ) -> T:
        """Instrument the generator.

        Wrap the generator class with the mixin class, instantiate it and
        return the instance filled the same arguments
        """
        ...


class MROInstrumentor(Instrumentor):
    """Instrumentor that manipulates MRO."""

    def can_instrument(self, inst: Any) -> bool:
        """Return True if the instrumentor can instrument the given instance."""
        return True

    @override
    def instrument[T](
        self,
        inst: T,
        mixins: dict[type, type],
        instrumentors: "InstrumentorRegistry",
        context: dict,
    ) -> T:
        cloned = copy.copy(inst)
        for m in type(cloned).mro():
            if m in mixins:
                mixin = mixins[m]
                break
        else:
            raise Exception(
                f"Mixin for {type(cloned).mro()} not found, known mixins {mixins.keys()}"
            )
        cloned.__class__ = type(
            type(cloned).__name__,
            (mixin, type(cloned)),
            {"__module__": type(cloned).__module__},
        )  # type: ignore
        return cloned


class DeepMROInstrumentor(MROInstrumentor):
    def __init__(self, instrumented_base_class: type):
        self._instrumented_base_class = instrumented_base_class

    @override
    def instrument[T](
        self,
        inst: T,
        mixins: dict[type, type],
        instrumentors: "InstrumentorRegistry",
        context: dict,
    ) -> T:
        # prevent infinite recursion

        if id(inst) in context:
            return context[id(inst)]

        if isinstance(inst, self._instrumented_base_class):
            ret = super().instrument(inst, mixins, instrumentors, context)
        else:
            ret = copy.copy(inst)
        context[id(inst)] = ret

        try:

            def is_ignored(k, v):
                return (
                    k.startswith("__")
                    or inspect.isfunction(v)
                    or isinstance(v, staticmethod)
                )

            def pick_subvalues(d):
                subvalues = {}
                for k, v in list(d.items()):
                    if is_ignored(k, v):
                        continue
                    subvalues[k] = v
                return subvalues

            sub_values = {}
            for m in reversed(type(ret).mro()):
                sub_values.update(pick_subvalues(m.__dict__))
            sub_values.update(pick_subvalues(ret.__dict__))
            ret.__dict__ = sub_values
        except AttributeError:
            return ret

        for k, v in list(sub_values.items()):
            if is_ignored(k, v):
                continue
            new_v: Any
            if isinstance(v, tuple):
                new_v = tuple(instrumentors.instrument(i, mixins, context) for i in v)
            elif isinstance(v, list):
                new_v = [instrumentors.instrument(i, mixins, context) for i in v]
            elif isinstance(v, dict):
                new_v = {
                    key: instrumentors.instrument(value, mixins, context)
                    for key, value in v.items()
                }
            elif isinstance(v, set):
                new_v = {
                    item: instrumentors.instrument(item, mixins, context) for item in v
                }
            else:
                new_v = instrumentors.instrument(v, mixins, context)
            sub_values[k] = new_v

        return ret


class InstrumentorRegistry:
    def __init__(self):
        self._instrumentors = []

    def register(self, instrumentor: Instrumentor):
        self._instrumentors.append(instrumentor)

    @property
    def instrumentors(self) -> list[Instrumentor]:
        return self._instrumentors

    def instrument(
        self, inst: Any, mixins: dict[type[Any], type[Any]], context: dict | None = None
    ) -> Any:
        if context is None:
            context = {}
        for instrumentor in reversed(self.instrumentors):
            if instrumentor.can_instrument(inst):
                return instrumentor.instrument(inst, mixins, self, context)
        raise Exception("No instrumentor found")


if __name__ == "__main__":
    registry = InstrumentorRegistry()
    registry.register(MROInstrumentor())

    class A:
        def a(self):
            print("a")

    class Mixin:
        def a(self):
            print("a inside mixin before super")
            super().a()
            print("a inside mixin after super")

        def b(self):
            print("b inside mixin")

    a = A()
    a_instrumented = registry.instrument(a, {object: Mixin})
    a_instrumented.b()
    a_instrumented.a()

    deep_registry = InstrumentorRegistry()
    deep_registry.register(DeepMROInstrumentor(A))

    class B:
        def __init__(self):
            pass

    b = B()
    b.a = A()
    b.list_a = [A(), A()]
    b.tuple_a = (A(), A())
    b.dict_a = {"a": A(), "b": A(), "c": 1}

    b_instrumented = deep_registry.instrument(b, {object: Mixin})
    assert isinstance(b_instrumented.a, Mixin)
    assert isinstance(b_instrumented.list_a[0], Mixin)
    assert isinstance(b_instrumented.list_a[1], Mixin)
    assert isinstance(b_instrumented.tuple_a[0], Mixin)
    assert isinstance(b_instrumented.tuple_a[1], Mixin)
    assert isinstance(b_instrumented.dict_a["a"], Mixin)
    assert isinstance(b_instrumented.dict_a["b"], Mixin)
    assert b_instrumented.dict_a["c"] == 1
