## dataclass for YAML !rand_int functionality
## define !rand_int in config, then when it is encountered in parsing pass we call get() method to get the value.
## handle all keyed random info internally.

import random

## FIXME: we need to figure out where to put this...
class WLDRandomDaemon():
    keyed_randoms = dict()

    @staticmethod
    def reset() -> None:
        WLDRandomDaemon.keyed_randoms.clear()
        
class WLDRandInt():
    def __init__(self, key:str|None = None, min:int = 0, max:int = 1 ) -> None:
        self._key = f"INT:{key}" if isinstance(key, str ) else None
        self._min = min
        self._max = max

    def get(self) -> int:
        if self._key and self._key in WLDRandomDaemon.keyed_randoms:
            return WLDRandomDaemon.keyed_randoms[self._key]
        else:
            rand = random.randrange(self._min, self._max)
            
            ## store random if we are keyed
            if self._key:
                WLDRandomDaemon.keyed_randoms[self._key] = rand
            return rand 