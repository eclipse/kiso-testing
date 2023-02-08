##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Auxiliary Interface Definition
******************************

:module: dynamic_loader

:synopsis: Import magic that enables aliased auxiliary loading in TestCases


"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import logging
import pathlib
import sys
import types
from typing import TYPE_CHECKING, Type, Union

# TODO: remove it after all auxes are adapted to DTAuxiliaryInterface
#################################################################################
import pykiso

#################################################################################
from pykiso.exceptions import ConnectorRequiredError

if TYPE_CHECKING:
    from ..auxiliary import AuxiliaryCommon
    from ..connector import Connector

PACKAGE = __package__.split(".")[0]

__all__ = ["DynamicImportLinker"]

log = logging.getLogger(__name__)


class DynamicFinder(importlib.abc.MetaPathFinder):
    """A MetaPathFinder that delegates everything to the loader."""

    def __init__(self, loader: AuxLinkLoader):
        """Initialize attributes.

        :param loader: any Loader object from importlib.abc.Loader
        """
        self._loader = loader

    def find_spec(self, fullname, path, target=None):
        """Attempt to locate the requested module.

        :param fullname: is the fully-qualified name of the module,
        :param path: is set to __path__ for sub-modules/packages,
            or None otherwise.
        :param target: can be a module object, but is unused in this example.
        """
        if self._loader.provides(fullname):
            return self._gen_spec(fullname)

    def _gen_spec(self, fullname):
        spec = importlib.machinery.ModuleSpec(fullname, self._loader)
        return spec


class AuxLinkLoader(importlib.abc.Loader):
    """A Loader for auxiliaries.

    Something is imported from `pykiso.auxiliaries` gets redirected to
    a lookup table of configured auxiliares (done via config file).
    """

    _COMMON_PREFIX = PACKAGE + ".auxiliaries"

    def __init__(self, aux_cache: AuxiliaryCache):
        """Initialize attributes.

        :param aux_cache: AuxiliaryChache instance
        """
        self._auxiliaries = []
        self._aux_cache = aux_cache
        # create a dummy module to return when Python attempts to import
        # myapp and myapp.virtual, the :-1 removes the last "." for
        # aesthetic reasons :)
        self._dummy_module = types.ModuleType(self._COMMON_PREFIX.rstrip("."))
        # set __path__ so Python believes our dummy module is a package
        # this is important, since otherwise Python will believe our
        # dummy module can have no submodules
        self._dummy_module.__path__ = []

    def provide(self, name: str):
        """Register a service as provided via the given module.

        A service is any Python object in this context - an imported module,
        a class, etc.

        :param name: aliased auxiliary instance
        """
        self._auxiliaries.append(name)

    def provides(self, fullname: str) -> bool:
        """Check if this loader provides the requested module.

        :param fullname: fully qualified name (e.g. pykiso.auxiliaries.alias)
        """
        if self._truncate_name(fullname) in self._auxiliaries:
            return True
        else:
            # this checks if we should return the dummy module,
            # since this evaluates to True when importing myapp and
            # myapp.virtual
            return self._COMMON_PREFIX.startswith(fullname)

    def create_module(
        self, spec: importlib.machinery.ModuleSpec
    ) -> Union[types.ModuleType, AuxiliaryCommon]:
        """Create the given module from the supplied module spec.

        Under the hood, this module returns a service or a dummy module,
        depending on whether Python is still importing one of the names listed
        in _COMMON_PREFIX.
        """
        name = self._truncate_name(spec.name)
        if name not in self._auxiliaries:
            # return our dummy module since at this point we're loading
            # *something* along the lines of "pykiso.components" that's not
            # a module
            return self._dummy_module
        return self._aux_cache.get_instance(name)

    def exec_module(self, module):
        """Execute the given module in its own namespace.

        This method is required to be present by importlib.abc.Loader,
        but since we know our module object is already fully-formed,
        this method merely no-ops.
        """
        pass

    def _truncate_name(self, fullname: str) -> str:
        """Strip off _COMMON_PREFIX from the given module name.

        Convenience method when checking if a service is provided.
        """
        return fullname[len(self._COMMON_PREFIX) + 1 :]


class ModuleCache:
    """Caches modules, configs and instances.

    This class serves as a cache for configurations and instances for modules to be loaded.

    An entry consists of

    * an alias for the instance
    * a location (path to python file or python module)
    * a class
    * configuration parameters
    * active instance (lazily created)
    """

    def __init__(self):
        """Initialize attributes."""
        self.locations = dict()
        self.configs = dict()
        self.modules = dict()
        self.instances = dict()

    def provide(self, name: str, module: str, **config_params):
        """Provide an aliased instance.

        :param name: the instance alias
        :param module: either 'python/file/path.py:Class' or 'module:Class'
            of the class we want to provide
        """
        self.locations[name] = module
        self.configs[name] = config_params

    def _import(self, name: str) -> Type[Union[AuxiliaryCommon, Connector]]:
        """Import the class registered under the alias <name>."""
        try:
            import_path = self.locations[name]
            location, _class = import_path.rsplit(":", 1)
        except KeyError:
            raise ValueError(f"Could not find {name!r} in provided configuration")
        except ValueError:
            raise ValueError(
                f"Specified type for {name!r} must be 'path:Class' or 'module:Class', got {import_path!r}"
            )
        if ".py" in location:
            path_loc = pathlib.Path(location)
            if path_loc.exists() and path_loc.is_file():
                spec = importlib.util.spec_from_file_location(path_loc.stem, path_loc)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                log.internal_debug(f"loading {_class} as {name} from {path_loc}")
            else:
                raise ImportError(
                    f"no python module found at {path_loc!r}", name=_class
                )
        else:
            module = importlib.import_module(location)
        cls = getattr(module, _class)
        log.internal_debug(f"loaded {_class} as {name} from {location}")
        return cls

    def get_instance(self, name: str) -> Union[AuxiliaryCommon, Connector]:
        """Get an instance of alias <name> (create and configure one of not existed)."""
        if name in self.instances:
            log.internal_debug(f"instance for {name} found ({self.instances[name]})")
            return self.instances[name]
        if name not in self.modules:
            log.internal_debug(f"module for {name} not found, loading...")
            self.modules[name] = self._import(name)
        log.internal_debug(
            f"instantiating {name}: {self.modules[name]}({self.configs[name]})"
        )
        inst = self.modules[name](name=name, **self.configs[name])
        self.instances[name] = inst
        log.internal_debug(f"instantiated {name}")
        return inst


class AuxiliaryCache(ModuleCache):
    """A ModuleCache that specifically provides Auxiliaries.

    This has the additional functionality that if an auxiliary has any defined connectors,
    these will be provided automatically.
    """

    def __init__(self, con_cache: ModuleCache):
        """Initialize attributes.

        :param con_cache: connector ModuleCache object
        """
        super().__init__()
        self.con_cache = con_cache
        self.connectors = dict()

    def provide(self, name: str, module: str, connectors=None, **config_params):
        """Provide an aliased instance.

        :param name: the instance alias
        :param module: either 'python-file-path:Class' or 'module:Class' of the class we want
        :param connectors: list of connector aliases
            to provide
        """
        self.connectors[name] = connectors
        super().provide(name, module, **config_params)

    def get_instance(self, name: str) -> AuxiliaryCommon:
        """Get an instance of alias <name> (create and configure one of not existed)."""
        for cn, con in self.connectors.get(name, dict()).items():
            # add connector-instances as configs
            self.configs[name][cn] = self.con_cache.get_instance(con)
        inst = super().get_instance(name)

        if getattr(inst, "connector_required", True) and not getattr(
            inst, "channel", False
        ):
            self.instances.pop(name)
            raise ConnectorRequiredError(name)
        # if auto start is needed start the auxiliary otherwise store
        # the created instance
        auto_start = getattr(inst, "auto_start", True)
        # due to the simple aux interface test if start method is part
        # of the current auxiliary
        start_method = getattr(inst, "start", None)

        # TODO: remove it after all auxes are adapted to DTAuxiliaryInterface
        #################################################################################
        is_dt = isinstance(inst, pykiso.interfaces.dt_auxiliary.DTAuxiliaryInterface)
        if not inst.is_instance and auto_start and is_dt:
            inst.create_instance()
            log.internal_debug(f"called create_instance on {name}")
        #################################################################################
        elif not inst.is_instance and auto_start:
            # if auxiliary is type of thread
            if start_method is not None:
                inst.start()
            inst.create_instance()
            log.internal_debug(f"called create_instance on {name}")
        self.instances[name] = inst
        return inst

    def _stop_auxiliaries(self):
        """Elegant workaround to shut down all the auxiliaries."""
        for alias, aux in self.instances.items():
            log.internal_debug(f"issuing stop for auxiliary '{aux}'")
            aux.stop()
            aux_mod = f"{AuxLinkLoader._COMMON_PREFIX}.{alias}"
            # ensure that the module was created
            if sys.modules.get(aux_mod) is not None:
                # remove all modules create by our custom loader
                sys.modules.pop(aux_mod)

        # remove the common prefix "pykiso.auxiliaries" to enforce the
        # path finder -> loader -> module
        if AuxLinkLoader._COMMON_PREFIX in sys.modules:
            sys.modules.pop(AuxLinkLoader._COMMON_PREFIX)


class DynamicImportLinker:
    """Public Interface of Import Magic.

    initialises the Loaders, Finders and Caches, implements interfaces to
    install the magic and register the auxiliaries and connectors."""

    def __init__(self):
        """Initialize attributes."""
        self._con_cache = ModuleCache()
        self._aux_cache = AuxiliaryCache(self._con_cache)
        self._aux_loader = AuxLinkLoader(self._aux_cache)
        self._finders = [DynamicFinder(self._aux_loader)]

    def install(self):
        """Install the import hooks with the system."""
        log.internal_debug(f"installed the {self.__class__.__name__}")
        sys.meta_path.insert(0, *self._finders)

    def provide_connector(self, name: str, module: str, **config_params):
        """Provide a connector.

        :param name: the connector alias
        :param module: either 'python-file-path:Class' or 'module:Class'
            of the class we want to provide.
        """
        log.internal_debug(f"provided connector {name} (at {module})")
        self._con_cache.provide(name, module, **config_params)

    def provide_auxiliary(self, name: str, module: str, aux_cons=None, **config_params):
        """Provide a auxiliary.

        :param name: the auxiliary alias
        :param module: either 'python-file-path:Class' or 'module:Class'
            of the class we want to provide.
        :param aux_cons: list of connectors this auxiliary has
        """
        log.internal_debug(f"provided auxiliary {name} (at {module})")
        self._aux_cache.provide(name, module, connectors=aux_cons, **config_params)
        self._aux_loader.provide(name)

    def uninstall(self):
        """Deregister the import hooks, close all running threads, delete all instances."""
        log.internal_debug("closing and uninstalling all dynamic modules and loaders")
        self._stop_auxiliaries()
        del self._con_cache
        del self._aux_cache
        del self._aux_loader
        for finder in self._finders:
            sys.meta_path.remove(finder)

    def _stop_auxiliaries(self):
        """Elegant workaround to shut down all the auxiliaries."""
        self._aux_cache._stop_auxiliaries()
