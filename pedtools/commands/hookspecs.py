import pluggy  # type: ignore
from typing import List, TypeVar, Callable, Any, Dict, cast, Optional

""" Hook Specifications
        Pre hook executed before the main action
        Post hook executed after the main action
"""

# Typed as per: https://stackoverflow.com/questions/54674679/how-can-i-annotate-types-for-a-pluggy-hook-specification

# Improvement suggested by @oremanj on python/typing gitter
F = TypeVar("F", bound=Callable[..., Any])
hookspec = cast(Callable[[F], F], pluggy.HookspecMarker("pedtools"))


class PedtoolsPlugin:
    @staticmethod
    @hookspec
    def pedtools_add_pre_action(config: dict) -> dict:
        """ Hook running before the action
        :param config: dictionary of parsed configuration to be used by the action
        :return: a modified config file
        """
        return config

    @staticmethod
    @hookspec
    def pedtools_add_post_action(config: dict):
        """ Hook running after the action

        :param config: dictionary of parsed configuration used used by the action
        :return: No return value
        """
