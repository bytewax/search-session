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

*This guide will teach you how to use Bytewax to aggregate on a custom session window on streaming data using reduce and then calculate metrics downstream.*

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

The input of a dataflow expects a generator. This is done by yielding the events one at a time.

https://github.com/bytewax/search-session/blob/1fe98f31a2269c17f65edd7b5d46cb904d812e74/dataflow.py#L44-L64

For the moment, we aren't going to be using our resume state to manage failures, but returning the empty state is a requirement for our input builder.

## Constructing the Dataflow

### High-Level Plan

Let's talk about the high-level plan for how to sessionize:

- Searches are per-user, so we need to divvy up events by user.

- Searches don't span user sessions, so we should calculate user sessions first.

- Sessions without a search shouldn't contribute.

- Calculate one metric: **click through rate** (or **CTR**), if a user clicked on any result in a search.

### The Dataflow

Now that we have some input data, let's start defining the computational steps of our dataflow based on our plan.

We will import the `bytewax.dataflow.Dataflow` and the `bytewax.dataflow.ManualInputConfig` class.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L5-L6

And then, create an empty `bytewax.dataflow.Dataflow` object.

In this case, we'll use a `ManualInputConfig`, which takes the `input_builder` function that we defined above.

https://github.com/bytewax/search-session/blob/1fe98f31a2269c17f65edd7b5d46cb904d812e74/dataflow.py#L108-L109

Now that we have a Dataflow, and some input, we can add a series of **steps** to the dataflow. Steps are made up of **operators**, that provide a "shape" of transformation, and **logic functions**, that you supply to do your specific transformation. [You can read more about all the operators in our documentation.](https://www.bytewax.io/docs/getting-started/operators)

Our first task is to make sure to group incoming events by user since no session deals with multiple users.

All Bytewax operators that perform grouping require that their input be in the form of a `(key, value)` tuple, where `key` is the string the dataflow will group by before passing to the operator logic.

The operator which modifies all data in the stream, one at a time, is [map](https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.map). The map operator takes a Python function as an argument and that function will transform the data, one at a time.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L111-L112

Here we use the map operator with an initial_session function that will pull each event's user ID as a string into that key position.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L67-L68

For the value, we're planning ahead to our next task: sessionization. The operator best shaped for this is the [reduce operator](/apidocs#bytewax.Dataflow.reduce) which groups items by key, then combines them together into an **aggregator** in order. We can think about our reduce step as "combine together sessions if they should be joined". We'll be modeling a session as a list of events, so have the values be a list of a single event `[event]` that we will combine with our reducer function.

Reduce requires two bits of logic:

- How do I combine sessions? Since session are just Python lists, we can use the `+` operator to add them (via the built-in `operator.add` function).

- When is a session complete? In this case, a session is complete when the last item in the session is the app closing. We'll write a `session_has_closed` function to answer that.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L71-L74

Reduce also takes a unique **step ID** to help organize the state saved internally.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L114-L115

We had to group by user because sessions were per-user, but now that we have sessions, the grouping key is no longer necessary for metrics. We can write a function that will remove the key.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L81-L83

And then add the transformation to our dataflow with a map operator.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L116-L117

Our next task is to split user sessions into search sessions. To do that, we'll use the [flat map operator](/apidocs#bytewax.Dataflow.flat_map), that allows you to emit multiple items downstream (search sessions) for each input item (user session).

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L120

We walk through each user session's events, then whenever we encounter a search, emit downstream the previous events. This works just like `str.split` but with objects.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L86-L98

The [filter operator](https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.filter) allows us to remove any items from a stream that don't match a specific criteria. It is used in conjunction with a Python function that describes the rules.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L121

In this case, we can use it to get rid of all search sessions that don't contain searches and shouldn't contribute to metrics.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L86-L87

We can now move on to our final task: calculating metrics per search session in a map operator. 

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L123

If there's a click during a search, the CTR is 1.0 for that search, 0.0 otherwise. Given those two extreme values, we can do further statistics to get things like CTR per day, etc

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L101-L105

Now that our dataflow is done, we can define a function to be called for each output item. In this example, we're just printing out what we've received.

https://github.com/bytewax/search-session/blob/94f8f84be881e15c431b29dfd86bd347c6387a06/dataflow.py#L124

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
