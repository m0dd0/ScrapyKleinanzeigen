from random import randint
from pathlib import Path
import json
from scrapy import signals


class RotatingUserAgentsMiddleware:
    """This middleware allows spiders to override the user_agent"""

    def __init__(self, user_agents, shuffle):
        if isinstance(user_agents, (list, tuple)):
            self.user_agents = user_agents
        else:
            p = Path(user_agents)
            try:
                with open(p) as file:
                    user_agent_items = json.load(file)
                    self.user_agents = [
                        i["user_agent_string"] for i in user_agent_items
                    ]
            except:
                with open(p) as file:
                    lines = file.readlines()
                    lines = [line.rstrip() for line in lines]
                    self.user_agents = lines

        self.shuffle = shuffle
        self._last_agent_index = -1

    def _get_user_agent(self):
        if not self.shuffle:
            self._last_agent_index += 1
        else:
            self._last_agent_index = randint(0, len(self.user_agents) - 1)
        return self.user_agents[self._last_agent_index]

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(
            crawler.settings["ROTATING_USER_AGENTS"],
            crawler.settings.get("ROTATING_USER_AGENTS_SHUFFLE", False),
        )
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        return o

    def spider_opened(self, spider):
        pass
        # self.user_agent = getattr(spider, "user_agent", self.user_agent)

    def process_request(self, request, spider):
        ua = self._get_user_agent()
        request.headers.setdefault(b"User-Agent", ua)
