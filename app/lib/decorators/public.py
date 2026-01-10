from typing import Callable


def public(route_function: Callable) -> Callable:
    setattr(route_function, "is_public", True)
    return route_function
