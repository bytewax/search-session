from datetime import datetime, timedelta, timezone

from dataclasses import dataclass
from typing import List

from bytewax.connectors.stdio import StdOutput
from bytewax.execution import run_main
from bytewax.window import (
    EventClockConfig,
    SessionWindow,
)


@dataclass
class AppOpen:
    user: int
    time: datetime


@dataclass
class Search:
    user: int
    query: str
    time: datetime


@dataclass
class Results:
    user: int
    items: List[str]
    time: datetime


@dataclass
class ClickResult:
    user: int
    item: str
    time: datetime


from bytewax.inputs import StatefulSource


# The time at which we want all of our windows to align to
align_to = datetime(2022, 1, 1, tzinfo=timezone.utc)


class EventSource(StatefulSource):
    # Simulating events that stream in from users
    client_events = [
        Search(user=1, time=align_to + timedelta(seconds=5), query="dogs"),
        Results(
            1, time=align_to + timedelta(seconds=6), items=["fido", "rover", "buddy"]
        ),
        ClickResult(1, time=align_to + timedelta(seconds=7), item="rover"),
        Search(2, time=align_to + timedelta(seconds=5), query="cats"),
        Results(
            2,
            time=align_to + timedelta(seconds=6),
            items=["fluffy", "burrito", "kathy"],
        ),
        ClickResult(2, time=align_to + timedelta(seconds=7), item="fluffy"),
        ClickResult(2, time=align_to + timedelta(seconds=8), item="kathy"),
    ]

    def __init__(self, resume_state):
        self._idx = resume_state or -1
        self._it = enumerate(self.client_events)
        # Resume to one after the last completed read.
        for i in range(self._idx + 1):
            next(self._it)

    def next(self):
        self._idx, item = next(self._it)
        return item

    def snapshot(self):
        return self._idx


from bytewax.inputs import PartitionedInput


class SearchSessionInput(PartitionedInput):
    def list_parts(self):
        # We only have one producer of events for this example,
        # so we return a single partition as a set.
        return {"single-stream"}

    def build_part(self, for_key, resume_state):
        assert for_key == "single-stream"
        return EventSource(resume_state)


from bytewax.dataflow import Dataflow

flow = Dataflow()
flow.input("input", SearchSessionInput())
# event


def user_event(event):
    return str(event.user), event


flow.map(user_event)
# (user, event)


def add_event(acc, event):
    acc.append(event)
    return acc


clock_config = EventClockConfig(
    lambda e: e.time, wait_for_system_duration=timedelta(seconds=0)
)
window_config = SessionWindow(gap=timedelta(seconds=5))
flow.fold_window("minute_windows", clock_config, window_config, list, add_event)
# ('1', [Search(user=1, query='dogs', time=datetime.datetime...)])


def calc_ctr(user__search_session):
    user, search_session = user__search_session
    searches = [event for event in search_session if isinstance(event, Search)]
    clicks = [event for event in search_session if isinstance(event, ClickResult)]
    return (user, (len(clicks) / len(searches)))


# Calculate search CTR.
flow.map(calc_ctr)
# ('1', 1.0)
# ('2', 2.0)
flow.output("stdout", StdOutput())


if __name__ == "__main__":
    run_main(flow)

# Sample Output
# ('1', 1.0)
# ('2', 2.0)
