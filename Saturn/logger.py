class Logger:
    def __init__(self, callsign: str, printout: bool = True, dumpfile: str | None = None):
        self.callsign = callsign
        self.dumpfile = dumpfile
        self._log = []
        self.printout = printout

        self._template = '[{callsign}/{level}] | {message}'

    def dump(self):
        if self.dumpfile is None:
            print("")
            return

    def _update(self, word: str):
        self._log.append(word)
        if not self.printout: return
        print(word)

    def log(self, message: str):
        self._update(self._template.format(callsign=self.callsign, level='INFO', message=message))

    def error(self, message: str):
        self._update(self._template.format(callsign=self.callsign, level='ERROR', message=message))

    def warning(self, message: str):
        self._update(self._template.format(callsign=self.callsign, level='WARN', message=message))

    def exception(self, message: str):
        pass
