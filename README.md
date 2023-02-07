# Building Sessions from Search Logs

- Skill level
    
    **Basic, no prior knowledge requirements**
    
- Time to complete
    
    **Approx. 25 min**
    

Introduction: *Here is a basic example of using Bytewax to turn an incoming stream of event logs from a hypothetical search engine into metrics over search sessions. In this example, we're going to focus on the dataflow itself and aggregating state, and gloss over details of building this processing into a larger system.*

## ****Prerequisites****

**Python modules**
bytewax

## Your Takeaway

*This guide will teach you how to use bytewax to aggregate on a custom session window and calculate metrics*

## Table of content

- Resources
- Data Model
- Input Data
- Constructing the Dataflow
- Execution
- Summary

## Resources

[Github link](https://github.com/bytewax/search-session)

## Data Model

Let's start by defining a data model / schema for our incoming events. We'll make a little model class for all the relevant events we'd want to monitor.

https://github.com/bytewax/search-session/blob/1fe98f31a2269c17f65edd7b5d46cb904d812e74/dataflow.py#L11-L41

In a more mature system, these might come from external schema or be auto generated.

## Generating Input Data

Now that we've got those, here's a small dump of some example data you could imagine coming from your app's events infrastructure.

The input of a dataflow expects a generator. Let's write a function that will yield one of these events at a time into our dataflow.

```python
IMAGINE_THESE_EVENTS_STREAM_FROM_CLIENTS = [
    AppOpen(user=1),
    Search(user=1, query="dogs"),
    # Eliding named args...
    Results(1, ["fido", "rover", "buddy"]),
    ClickResult(1, "rover"),
    Search(1, "cats"),
    Results(1, ["fluffy", "burrito", "kathy"]),
    ClickResult(1, "fluffy"),
    AppOpen(2),
    ClickResult(1, "kathy"),
    Search(2, "fruit"),
    AppClose(1),
    AppClose(2),
]


def input_builder(worker_index, worker_count, resume_state):
    state = resume_state or None
    for line in IMAGINE_THESE_EVENTS_STREAM_FROM_CLIENTS:
        yield (state, line)
```

For the moment, we aren't going to be using our resume state to manage failures, but returning the empty state is a requirement for our input builder.

## Constructing the Dataflow

### High-Level Plan

Let's talk about the high-level plan for how to sessionize:

- Searches are per-user, so we need to divvy up events by user.

- Searches don't span user sessions, so we should calculate user
  sessions first.

- Sessions without a search shouldn't contribute.

- Calculate one metric: **click through rate** (or **CTR**), if a user
  clicked on any result in a search.

### The Dataflow

Now that we have some input data, let's start defining the
computational steps of our dataflow based on our plan.

To start, create an empty `bytewax.dataflow.Dataflow` object.

In this case, we'll use a `ManualInputConfig`, which takes the
`input_builder` function that we defined above.

```python
from bytewax.inputs import ManualInputConfig
from bytewax.dataflow import Dataflow

flow = Dataflow()
flow.input("input", ManualInputConfig(input_builder))
```


## Summary

That’s it, you are awesome and we are going to rephrase our takeaway paragraph

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the #troubleshooting Slack channel!

## Where to next?

- Relevant explainer video
- Relevant case study
- Relevant blog post
- Another awesome tutorial

See our full gallery of tutorials →

[Share your tutorial progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20data%20streaming%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
