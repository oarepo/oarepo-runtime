from .polymorphic import PolymorphicSchema


def consistent_resolution(*classes):
    """
    A helper function to solve resolution order of classes.
    If the classes are in a correct mro order, it will return
    them in the same order. Otherwise it will try to reorder
    them and remove those that are already contained in mro
    of others.
    """

    # remove classes that are already in mro of others
    filtered_classes = []
    for cls in classes:
        for other_cls in classes:
            if cls != other_cls and issubclass(other_cls, cls):
                break
        else:
            if cls not in filtered_classes:
                filtered_classes.append(cls)

    name = [cls.__name__ for cls in filtered_classes]
    name = "".join(name) + "ConsistentResolution"
    try:
        return type(name, tuple(filtered_classes), {})
    except TypeError:
        pass

    filtered_classes.sort(key=lambda cls: -len(cls.mro()))
    try:
        return type(name, tuple(filtered_classes), {})
    except TypeError:
        pass

    bases = ", ".join(cls.__name__ for cls in filtered_classes)
    orig_bases = ", ".join(cls.__name__ for cls in classes)
    raise TypeError(
        f"Cannot create a consistent method resolution order (MRO) "
        f"for bases {orig_bases}, tried {bases}"
    )


__all__ = ("PolymorphicSchema", "consistent_resolution")
