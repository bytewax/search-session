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

Let's start by defining a data model / schema for our incoming events. We'll make a little model class for all the relevant events we'd want to monitor.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L14-L38

In a production system, these might come from external schema or be auto generated.

## Generating Input Data

Now that we've got our schema defined, let's create a class that will emit simulated searches and results into our dataflow.

Our `EventSource` class has a fixed list of events that it will emit, one at a time when Bytewax calls our `next` method. We keep track of which events have been emitted by enumerating our static list of events.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L41-L78

Finally, we need to create a class that manages the creation of our `EventSource` class when called by Bytewax during startup and recovery. In our case, we only have one producer of events, and therefore we only have one partition to return in our `list_parts` method. In the `build_part` method of `SearchSessionInput`, we construct and return our EventSource, passing in the `resume_state` that we got from the invocation of `build_part`.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L81-L92

## Constructing the Dataflow

### High-Level Plan

Let's talk about the high-level plan for how to sessionize:

- Searches are per-user, so we need to divvy up events by user.

- Searches don't span user sessions, so we should calculate user sessions first.

- Sessions without a search shouldn't contribute.

- Calculate one metric: **click through rate** (or **CTR**), if a user clicked on any result in a search.

### The Dataflow

Now that we have some input data, let's start defining the computational steps of our dataflow based on our plan.

We will need to import `bytewax.dataflow.Dataflow`, and then create an empty `bytewax.dataflow.Dataflow` object.

We'll then set our input to be the `SearchSessionInput` class we created above.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L102-L105

Now that we have a Dataflow, and some input, we can add a series of **steps** to the dataflow. Steps are made up of **operators**, that provide a "shape" of transformation, and **logic functions**, that you supply to do your specific transformation. [You can read more about all the operators in our documentation.](https://www.bytewax.io/docs/getting-started/operators)

Our first task is to make sure to group incoming events by user since no session deals with multiple users.

All Bytewax operators that perform grouping require that their input be in the form of a `(key, value)` tuple, where `key` is the string the dataflow will group by before passing to the operator logic.

The operator which modifies all data in the stream, one at a time, is [map](https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.map). The map operator takes a Python function as an argument and that function will transform the data, one at a time.

Here we use the map operator with an `user_event` function that will pull each event's user ID as a string into that key position.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L109-L113

For the value, we're planning ahead to our next task: windowing. We will construct a `SessionWindow`. A `SessionWindow` groups events together by key until no events occur within a gap period. In our example, we want to capture a window of events that approximate an individual search session.

Our aggregation over these events will use the `fold_window` operator, which takes a **builder** and a **folder** function. Our **builder** function will be the built in `list` operator, which creates a new list containing the first element. Our **folder** function, `add_event` will append each new event in a session to the existing window.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L115-L120

We can now move on to our final task: calculating metrics per search session in a map operator.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L123-131

If there's a click during a search, the CTR is 1.0 for that search, 0.0 otherwise. Given those two extreme values, we can do further statistics to get things like CTR per day, etc

Now that our dataflow is done, we can define a function to be called for each output item. In this example, we're just printing out what we've received.

https://github.com/bytewax/search-session/blob/main/dataflow.py#L134

Now we're done with defining the dataflow. Let's run it!

## Execution

[Bytewax provides a few different entry points for executing your dataflow](https://www.bytewax.io/docs/getting-started/execution), but because we're focusing on the dataflow in this example, we're going to use `bytewax.execution.run_main` which is the most basic execution mode running a single worker in the main process.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L127-L128

We can run this file locally by installing bytewax and running the python file. The recommended way is to use docker, you can run the commands in the run.sh script.

https://github.com/bytewax/search-session/blob/a435ce7a720c75d4726032639803dfea5d36b399/run.sh#L1-L5

Let's inspect the output and see if it makes sense.

https://github.com/bytewax/search-session/blob/233501dce47f1e1b1877d722ca27b4657955e7f5/dataflow.py#L130-L133

Since the [capture](/apidocs#bytewax.Dataflow.capture) step is immediately after calculating CTR, we should see one output item for each search session. That checks out! There were three searches in the input: "dogs", "cats", and "fruit". Only the first two resulted in a click, so they contributed `1.0` to the CTR, while the no-click search contributed `0.0`.

## Summary

That’s it, now you have an understanding of how you can build custom session windows, how you can define dataclasses to be used in Bytewax and how to calculate click through rate on a stream of logs.

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the [#troubleshooting Slack channel!](https://join.slack.com/t/bytewaxcommunity/shared_invite/zt-vkos2f6r-_SeT9pF2~n9ArOaeI3ND2w)

See our full gallery of tutorials →

[Share your tutorial progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20data%20streaming%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
