##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Configuration collection
************************

:module: global_config

:synopsis: expose the framework configuration to the user's scope

.. currentmodule:: global_config

"""
import functools
import json
import threading
from types import SimpleNamespace
from typing import Any, Callable


class Singleton(type):
    """Thread safe Singleton pattern implementation."""

    #: store the unique created class instance
    _instance = None
    #: used to safely return the class instance
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs) -> Any:
        """Ensure that one and only one instance of the class is created.

        :param args: positonal arguments
        :param kwargs: named arguments

        :return: created class instance
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class ProtectedNamespace(SimpleNamespace):
    """Represent a basic write protected object instance."""

    def __init__(self, **kwargs) -> None:
        """Initialize SimpleNamespace attributes.

        :param kwargs: named arguments
        """
        super().__init__(**kwargs)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Protect instance attributes from writing.

        :param attr: attribute's name
        :param value: value to apply

        :raises AttributeError: when value assignation is intended
        """
        raise AttributeError(f"Attribute {attr} is not writable")


class GlobalConfig(metaclass=Singleton):
    """Container object used by the user to have access to all
    configuration information coming from the different levels of the
    framework(yaml, cli...).
    """

    def __init__(self) -> None:
        """Initialize cli and yaml attributes by taking the content of
        Grabber collector object.
        """
        self.cli = None
        self.yaml = None


class Grabber:
    """Responsible to collect configuration information at different
    levels of the framework."""

    @staticmethod
    def create_config_object(config: dict) -> ProtectedNamespace:
        """Create a configuration object by converting the given
        dictionary into a object representation.

        :param config: configuration's content

        :return: configuration's content as an object representation
        """
        str_conf = json.dumps(config)
        return json.loads(str_conf, object_hook=lambda x: ProtectedNamespace(**x))

    @staticmethod
    def grab_yaml_config(func: Callable) -> Callable:
        """Collect all parsed yaml information.

        :param func: decorated class

        :return: decorator inner function
        """

        @functools.wraps(func)
        def grab_inner(*args, **kwargs) -> dict:
            """Grab the return values from yaml configuration parser
            method and store it in the GlobalConfig instance.

            :param args: positonal arguments
            :param kwargs: named arguments

            :return: parsed yaml configuration information
            """
            dict_config = func(*args, **kwargs)
            object_config = Grabber.create_config_object(dict_config)
            GlobalConfig().yaml = object_config
            return dict_config

        return grab_inner

    @staticmethod
    def grab_cli_config(func) -> Callable:
        """Collect all cli configuration information.

        :param func: decorated class

        :return: decorator inner function
        """

        @functools.wraps(func)
        def grab_inner(*args, **kwargs) -> None:
            """Grab the given values from cli entry point level and
            store it in the GlobalConfig instance.

            :param args: positonal arguments
            :param kwargs: named arguments
            """
            object_config = Grabber.create_config_object(kwargs)
            GlobalConfig().cli = object_config
            return func(*args, **kwargs)

        return grab_inner
