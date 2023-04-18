# Building Sessions from Search Logs

- Skill level
    
    **Basic, no prior knowledge requirements**
    
- Time to complete
    
    **Approx. 25 min**
    

Introduction: *Here is a basic example of using Bytewax to turn an incoming stream of event logs from a hypothetical search engine into metrics over search sessions. In this example, we're going to focus on the dataflow itself and aggregating state.*

## ****Prerequisites****

**Python modules**
bytewax

## Your Takeaway

*This guide will teach you how to use Bytewax to aggregate on a custom session window on streaming data using a window and then calculate metrics downstream.*

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

Let's start by defining a data model / schema for our incoming events. We'll make model classes for all the relevant events we'd want to monitor.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L13-L37

In a production system, these might come from external schema or be auto generated.

## Creating our Dataflow

A dataflow is the unit of work in Bytewax. Dataflows are data-parallel directed acyclic graphs that are made up of processing steps.

Let's start by creating an empty dataflow.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L40-L42

## Generating Input Data

Bytewax has a `TestingInput` class that takes an enumerable list of events that it will emit, one at a time into our dataflow.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L47-L66

Note: `TestingInput` shouldn't be used when writing your production Dataflow. See the documentation for [Bytewax.inputs](https://bytewax.io/apidocs/bytewax.inputs) to see which input class will work for your use-case.

### High-Level Plan

Let's talk about the high-level plan for how to sessionize:

- Searches are per-user, so we need to divvy up events by user.

- Searches don't span user sessions, so we should calculate user sessions first.

- Sessions without a search shouldn't contribute.

- Calculate one metric: **click through rate** (or **CTR**), if a user clicked on any result in a search.

### The Dataflow

Now that we have a Dataflow, and some input, we can add a series of **steps** to the dataflow. Steps are made up of **operators**, that provide a "shape" of transformation, and **logic functions**, that you supply to do your specific transformation. [You can read more about all the operators in our documentation.](https://www.bytewax.io/docs/getting-started/operators)

Our first task is to make sure to group incoming events by user since no session deals with multiple users.

All Bytewax operators that perform grouping require that their input be in the form of a `(key, value)` tuple, where `key` is the string the dataflow will group by before passing to the operator logic.

The operator which modifies all data in the stream, one at a time, is [map](https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.map). The map operator takes a Python function as an argument and that function will transform the data, one at a time.

Here we use the map operator with an `user_event` function that will pull each event's user ID as a string into that key position.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L70-L75

For the value, we're planning ahead to our next task: windowing. We will construct a `SessionWindow`. A `SessionWindow` groups events together by key until no events occur within a gap period. In our example, we want to capture a window of events that approximate an individual search session.

Our aggregation over these events will use the `fold_window` operator, which takes a **builder** and a **folder** function. Our **builder** function will be the built in `list` operator, which creates a new list containing the first element. Our **folder** function, `add_event` will append each new event in a session to the existing window.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L78-L88

We can now move on to our final task: calculating metrics per search session in a map operator.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L91-L99

If there's a click during a search, the CTR is 1.0 for that search, 0.0 otherwise. Given those two extreme values, we can do further statistics to get things like CTR per day, etc

Now that our dataflow is done, we can define a function to be called for each output item. In this example, we're just printing out what we've received.

https://github.com/bytewax/search-session/blob/2052472a6e963c4be8bc1a3e23ac9d84f4e65eff/dataflow.py#L102

Now we're done with defining the dataflow. Let's run it!

``` python
> python -m bytewax.run dataflow:flow
```

Since the [output](/apidocs#bytewax.Dataflow.output) step is immediately after calculating CTR, we should see one output item for each search session. That checks out! There were three searches in the input: "dogs", "cats", and "fruit". Only the first two resulted in a click, so they contributed `1.0` to the CTR, while the no-click search contributed `0.0`.

## Summary

That’s it, now you have an understanding of how you can build custom session windows, how you can define dataclasses to be used in Bytewax and how to calculate click through rate on a stream of logs.

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the [#troubleshooting Slack channel!](https://join.slack.com/t/bytewaxcommunity/shared_invite/zt-vkos2f6r-_SeT9pF2~n9ArOaeI3ND2w)

See our full gallery of tutorials →

[Share your tutorial progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20data%20streaming%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
