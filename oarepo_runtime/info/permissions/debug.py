"""Instrumentors for debugging permissions."""

from invenio_records_permissions.generators import ConditionalGenerator, Generator

from .instrumentation import DeepMROInstrumentor, InstrumentorRegistry


class GeneratorDebugMixin:
    def to_debug_dict(self: Generator):
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


class GeneratoConditionalDebugMixin(GeneratorDebugMixin):
    def to_debug_dict(self: ConditionalGenerator):
        ret = super().to_debug_dict()
        r = ret[self.__class__.__name__]
        if self.then_:
            r["then"] = [x.to_debug_dict() for x in self.then_]
        if self.else_:
            r["else"] = [x.to_debug_dict() for x in self.else_]
        return ret


registry = InstrumentorRegistry()
registry.register(DeepMROInstrumentor(Generator))


def add_debugging(gen: Generator):
    return registry.instrument(
        gen,
        {
            Generator: GeneratorDebugMixin,
            ConditionalGenerator: GeneratoConditionalDebugMixin,
        },
    )
