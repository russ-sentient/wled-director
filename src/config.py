## TODO: create a YAML class, and helper classes for yaml constructors to handle LISTS, RANDOMS.
## - Try to find a way to pass the parent key to the constructor to use with this ( list can handle category, random can have automatic keys, etc )
from collections.abc import Mapping
from typing import Any
import yaml
from yamlinclude import YamlIncludeConstructor
from yaml.dumper import _Inf
from yaml.emitter import _WriteStream
from yaml.reader import _ReadStream

from .random_daemon import WLDRandomDaemon
import random


class WLDCList():
    def __init__(self, name:str, parent:str ) -> None:
        pass

class WLDRandInt():
    def __init__(self, key:str, min:int, max:int ) -> None:
        self._key = f"INT:{key}"
        self._min = min
        self._max = max

    def get(self) -> int:
        if self._key in WLDRandomDaemon.keyed_randoms:
            return WLDRandomDaemon.keyed_randoms[self._key]
        else:
            rand = random.randrange(self._min, self._max)
            WLDRandomDaemon.keyed_randoms[self._key] = rand
            return rand
        



class WLDYaml():
    ## define our loader and dumpers.  We can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlLoader( yaml.SafeLoader ):
        def __init__(self, stream: _ReadStream ) -> None:
            super().__init__(stream)

            self.add_constructor( "!clist", WLDYaml._clist_constructor )
    
    class WLDYamlDumper( yaml.SafeDumper ):
        def __init__(self, stream: _WriteStream[Any], default_style: str | None = None, default_flow_style: bool | None = False, canonical: bool | None = None, indent: int | None = None, width: int | _Inf | None = None, allow_unicode: bool | None = None, line_break: str | None = None, encoding: str | None = None, explicit_start: bool | None = None, explicit_end: bool | None = None, version: tuple[int, int] | None = None, tags: Mapping[str, str] | None = None, sort_keys: bool = True) -> None:
            super().__init__(stream, default_style, default_flow_style, canonical, indent, width, allow_unicode, line_break, encoding, explicit_start, explicit_end, version, tags, sort_keys)
    
    @staticmethod
    def _clist_constructor( loader: yaml.SafeLoader, node: yaml.nodes.MappingNode ) -> WLDCList:
        return WLDCList( **loader.construct_mapping(node) )


    YamlIncludeConstructor.add_to_loader_class( WLDYamlLoader, base_dir="./config" )