from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List

from bytewax.connectors.stdio import StdOutSink
from bytewax.operators.window import SessionWindow, \
                                    EventClockConfig
from bytewax.operators import window as wop
import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.testing import TestingSource

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


def user_event(event):
    
    return str(event.user), event

def add_event(acc, event):
    acc.append(event)
    return acc

def calc_ctr(user__search_session):
    user, (window_metadata, search_session) = user__search_session
    
    searches = [event for event in search_session if isinstance(event, Search)]
    clicks = [event for event in search_session if isinstance(event, ClickResult)]
    
    # See counts of searches and clicks
    print(f"User {user}: {len(searches)} searches, {len(clicks)} clicks")

    if len(searches) == 0:
        return (user, 0)
    return (user, len(clicks) / len(searches))


# The time at which we want all of our windows to align to
align_to = datetime(2024, 1, 1, tzinfo=timezone.utc)

# Simulated events to emit into our Dataflow
# In these events we have two users, each of which 
# performs a search, gets results, and clicks on a result
# User 1 searches for dogs, clicks on rover
# User 2 searches for cats, clicks on fluffy and kathy
client_events = [
    Search(user=1, time=align_to + timedelta(seconds=5), query="dogs"),
    Results(user=1, time=align_to + timedelta(seconds=6), items=["fido", "rover", "buddy"]),
    ClickResult(user=1, time=align_to + timedelta(seconds=7), item="rover"),
    Search(user=2, time=align_to + timedelta(seconds=5), query="cats"),
    Results(
        user=2,
        time=align_to + timedelta(seconds=6),
        items=["fluffy", "burrito", "kathy"],
    ),
    ClickResult(user=2, time=align_to + timedelta(seconds=7), item="fluffy"),
    ClickResult(user=2, time=align_to + timedelta(seconds=8), item="kathy"),
]

# Configuration for the Dataflow 
event_time_config = EventClockConfig(
    dt_getter=lambda e: e.time,
    wait_for_system_duration=timedelta(seconds=1)  
)
# Configuration for the windowing operator
clock_config = SessionWindow(gap=timedelta(seconds=10))

# Create the Dataflow
flow = Dataflow("search_ctr")
# Add input source
inp = op.input("inp", flow, TestingSource(client_events))
# Map user events function
user_event_map = op.map("user_event", inp, user_event)
# Collect windowed data
window = wop.collect_window("windowed_data", \
                            user_event_map, \
                            clock=event_time_config,
                            windower=clock_config)
# Calculate search CTR.
calc = op.map("calc_ctr", window, calc_ctr)
# Output the results
op.output("out", calc, StdOutSink())

