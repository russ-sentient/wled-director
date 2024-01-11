## Daemon class to handle keyed randoms.  We should figure out a way to pass a reference to this when we create helpers.

class WLDRandomDaemon():
    keyed_randoms = dict()

    @staticmethod
    def reset() -> None:
        WLDRandomDaemon.keyed_randoms.clear()