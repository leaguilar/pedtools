import argparse
import abc
from typing import List, Any, Optional, Dict
from pedtools.commands.hookspecs import PedtoolsPlugin


# From https://stackoverflow.com/questions/44542605/python-how-to-get-all-default-values-from-argparse
def get_argparse_defaults(parser):
    defaults = {}
    for action in parser._actions:
        if not action.required and action.dest != "help":
            defaults[action.dest] = action.default
    return defaults


def get_argparse_required(parser):
    required = []
    for action in parser._actions:
        if action.required:
            required.append(action.dest)
    return required


def non_runnable(funcobj: Any) -> Any:
    """A decorator indicating non runnable action
        This attribute remains unless overridden by the implemented action
    """
    funcobj.__isnotrunnable__ = True
    return funcobj


class PedtoolsAction(metaclass=abc.ABCMeta):
    """ Base class to define actions

        If the child object doesn't implement the action method, print help is assumed
        Defines base fags and methods that can be overridden by the children
    """

    def __init__(self) -> None:
        self._hook: Optional[PedtoolsPlugin] = None

    @non_runnable
    def action(self, config: dict):  # needs to be implemented in the child objects, else
        pass

    @abc.abstractmethod
    def help_description(self) -> Optional[str]:
        raise NotImplementedError

    def action_flags(self) -> List[argparse.ArgumentParser]:
        return []

    def group_description(self) -> Optional[str]:
        return None

    def register_subparsers(self) -> List[argparse.ArgumentParser]:
        # define common shared arguments
        base_subparser = argparse.ArgumentParser(add_help=False)
        base_subparser.add_argument(
            '--cite', action=store_true, help='Print citable reference for this module')
        additional_parsers = self.action_flags()
        additional_parsers.append(base_subparser)
        return additional_parsers

    def get_config_parameters(self):
        all_parsers = self.register_subparsers()
        defaults = {}
        required = []
        for parser in all_parsers:
            defaults.update(get_argparse_defaults(parser))
            required = required + get_argparse_required(parser)
        return (required, defaults)

    def add_hook(self, hook: PedtoolsPlugin) -> None:
        self._hook = hook

    def run_action(self, config: dict):

        config = self.pre_action(config)
        self.action(config)
        self.post_action(config)

    def pre_action(self, config: dict) -> dict:
        if self._hook:
            configs = self._hook.pedtoolsclient_add_pre_action(
                config=config)
            final_config = {}
            for c in configs:
                final_config.update(c)
                return final_config
        return config

    def post_action(self, config: dict):
        if self._hook:
            self._hook.pedtoolsclient_add_post_action(
                config=config)
