
from .settings import conf
from .integration import *
from .persistence import *
from .data import *

from ..network.protocols import ServerProtocol
from ..network.messages import *

import asyncio, os

class Controller:
    def __init__(self,settings=conf):
        self.settings = settings
        i = settings["universe"]
        self.universe = Universe(
            i["output"], i["dimmers"], i["interval"],
            INTEGRATION_MODES[i["mode"]], i["input"],
            self, i.get("allow_ignore_dmx",False))
        
        self.saver = PersistentData(settings["saving"]["autosave"])
        if not self.saver.loaded:
            self.saver.groups = Registry(Group)
            self.saver.cues = Registry(Cue)
        self.groups = self.saver.groups
        self.cues = self.saver.cues

        self.loop = asyncio.get_event_loop()
        self.coroutine = self.loop.create_server(lambda: ServerProtocol(self),
                                       settings["server"].get("address", ""),
                                       settings["server"].get("port", 7832))
        self.clients = []

    def register_client(self, p):
        self.clients.append(p)
        p.send_message(DimmerMessage(dict(zip(range(len(self.universe.dimmers)),
                                              self.universe.dimmers))))
        p.send_message(RegistryMessage("groups", self.groups))
        p.send_message(RegistryMessage("cues", self.cues))

    def unregister_client(self, p):
        self.clients.remove(p)

    def on_dmx(self, universe, changed, data, ignore_input):
        if len(changed):
            for i in self.clients:
                i.send_message(DimmerMessage(changed, "input"))

    def launch(self):
        if (not conf.get("daemon",False)) or os.fork() == 0:
            ola_thread.start()
            try:
                self.server = self.loop.run_until_complete(self.coroutine)
                self.loop.run_forever()
            finally:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
                self.loop.close()
    
    def do_update(self, t, obj):
        if t == "dimmers":
            dimmers = obj
        else:
            dimmers = obj.get_dimmers()
        self.universe.set_dimmers(dimmers)
        for i in self.clients:
            i.send_message(DimmerMessage(dimmers))
        self.saver.save()
