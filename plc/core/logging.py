from .settings import conf
import sys, time, os
import traceback as tb

settings = conf["logging"]

if conf.get("daemon") or settings.get("client"):
    DESCRIPTORS = [open(os.devnull, "w"),
                   open(os.path.join(settings.get("folder", "."), "output.log"), "a"),
                   open(os.path.join(settings.get("folder", "."), "errors.log"), "a")]
else:
    DESCRIPTORS = [open(os.devnull, "w"), sys.stdout, sys.stderr]

def _log(level, *args):
    print(time.strftime("[%m/%d/%y %H:%M:%S]"), *args, file=DESCRIPTORS[settings[level]])

def log(*args):
    _log("logging", *args)

def debug(*args):
    _log("debug", "Debug:", *args)

def warn(*args):
    _log("warnings", "Warning:", *args)

def error(*args):
    _log("errors", *args)

def last_exception():
    error(tb.format_exc())
