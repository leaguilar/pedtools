import pluggy  # type: ignore
import os
import argparse
import textwrap
import sys
import yaml

from pedtools.commands.hookspecs import PedtoolsPlugin
from pedtools.commands.action import PedtoolsAction

from pkg_resources import working_set

from typing import Any, Sequence, Dict, Optional, Union, List, Callable, Tuple


def _get_parser() -> argparse.ArgumentParser:
    # LV0/Base Parser
    lv0_parser = argparse.ArgumentParser(
        description=textwrap.dedent('''
        Common tools for pedestrian data analysis
         '''))
    lv0_parser.set_defaults(help=lv0_parser.print_help)
    return lv0_parser


def init_parser(parser: argparse.ArgumentParser, namespace: str, group_description: str = 'Available Commands') -> None:
    if len(list(working_set.iter_entry_points(namespace))):
        subparser = parser.add_subparsers(help=group_description)
    for entry_point in working_set.iter_entry_points(namespace):
        if "hook" not in entry_point.name:
            # load can raise exception due to missing imports or error in
            # object creation
            subcommand = entry_point.load()
            command_parser = subparser.add_parser(
                entry_point.name,
                help=subcommand.help_description(),
                parents=subcommand.register_subparsers())
            action = None
            if not getattr(subcommand.action, '__isnotrunnable__', False):
                action = getattr(subcommand, "action", None)
            if callable(action):
                command_parser.set_defaults(
                    action=subcommand,
                    help=command_parser.print_help,
                    namespace=namespace + "." + entry_point.name)
            else:
                command_parser.set_defaults(
                    help=command_parser.print_help,
                    namespace=namespace + "." + entry_point.name)

            group_description = subcommand.group_description()
            if group_description:
                init_parser(command_parser, namespace + "." +
                            entry_point.name, group_description)
            else:
                init_parser(command_parser, namespace + "." + entry_point.name)


def get_plugin_manager(namespace: str) -> pluggy.PluginManager:
    pm = pluggy.PluginManager("pedtools")
    pm.add_hookspecs(PedtoolsPlugin)
    namespace_list = namespace.split(".")

    current_namespace = ""
    for space in namespace_list:
        current_namespace += space + "."
        pm.load_setuptools_entrypoints(current_namespace + "hook.tree")
    pm.load_setuptools_entrypoints(current_namespace + "hook")
    plugin_list = pm.list_name_plugin()
    if len(plugin_list):
        print("Running using the following plugins:",
              [l[0] for l in plugin_list])
    return pm


def _get_pedtools_environment(args_keys: Sequence[str], namespace: str) -> dict:
    """Extracts environmental variables
        Two Levels of environmental variables apedtoolre possible
        General: PEDTOOLS_VARIABLE_NAME 
        Namespaced: PEDTOOLS_NA_MES_PACE_VARIABLE_NAME
        Namespaced have priority over General environment variables. General environmental variables
        will be used across actions that require that parameter, Namespaced ones only in the specific namespace

    """
    namespace = namespace.replace(".", "_").upper()

    pedtools_env: dict = {}
    for key in args_keys:
        # Read Namespaced environmental variables
        value = os.environ.get(namespace + key.upper())
        if value:
            pedtools_env[key] = value
            continue
        # Read General environmental variables
        value = os.environ.get("PEDTOOLS_" + key.upper())
        if value:
            pedtools_env[key] = value
    return pedtools_env


def _get_nested(dct: Dict[str, Any], keys: List[str]) -> Optional[Union[Dict[str, Any], str]]:
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct


def _get_pedtools_config_file(fname: str, namespace: str) -> dict:
    """Extracts variables from config file
    Two Levels of config file variables are possible
    Namespaced have priority over General variables. General variables
    will be used across actions that require that parameter, Namespaced ones only in the specific namespace

    """
    namespace = namespace.split(".")
    with open(fname) as file:
        pedtools_config_file = yaml.load(file, Loader=yaml.SafeLoader)
        pedtools_config_full_dict = dict((k.replace('-', '_'), v)
                                         for k, v in pedtools_config_file.items())

    pedtools_config_dict = {}
    # Populate Generic Variables
    for k, v in pedtools_config_full_dict.items():
        if k != namespace[0]:
            pedtools_config_dict[k] = v

    # Extract Namespaced Variables
    namespaced_config = _get_nested(pedtools_config_full_dict, namespace)
    if namespaced_config:
        namespaced_config = dict((k.replace('-', '_'), v) for k, v in namespaced_config.items())
        pedtools_config_dict.update(namespaced_config)

    return pedtools_config_dict


def _extract_setup(raw_config: dict, namespace) -> dict:
    config: dict = {key: None for key in raw_config.keys()}

    # Hard coded defaults

    # 0 priority default config file
    default_config = "config.yaml"
    if os.path.isfile(default_config) and (
            default_config.endswith(".yaml") or default_config.endswith(".yml")):
        config.update(_get_pedtools_config_file(default_config, namespace))

    # 1 priority environmental variables
    config.update(_get_pedtools_environment(config.keys(), namespace))

    # 2 priority user specified config file from flags
    if raw_config.get('config', None):
        if os.path.isfile(
                raw_config['config']) and (
                raw_config['config'].endswith(".yml") or raw_config['config'].endswith(".yaml")):
            config.update(_get_pedtools_config_file(raw_config['config'], namespace))

    # 3 priority user specified flags
    for key, value in raw_config.items():
        if value is not None:
            config[key] = value
    return config


def run_action(self, config: dict, action: PedtoolsAction, namespace):
    # Add Hooks
    if namespace:
        pm = get_plugin_manager(namespace)
        action.add_hook(pm.hook)
    action.run_action(config)


def main() -> None:
    lv0_parser: argparse.ArgumentParser = _get_parser()
    init_parser(lv0_parser, 'pedtools')

    args = lv0_parser.parse_args()

    if 'action' not in args and 'help' in args:
        args.help()
        sys.exit(1)

    if 'action' in args:
        try:
            run_action(vars(args), args.action, args.namespace)
        except Exception as e:
            print(e)
            sys.exit(1)
    else:
        print("Error while parsing arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
