# Building Sessions from Search Logs

- Skill level
    
    **Basic, no prior knowledge requirements**
    
- Time to complete
    
    **Approx. 25 min**
    

Introduction: *Here is a basic example of using Bytewax to turn an incoming stream of event logs from a hypothetical search engine into metrics over search sessions. In this example, we're going to focus on the dataflow itself and aggregating state.*

## ****Prerequisites****

**Python modules**
* bytewax==0.19.*

## Your Takeaway

*This guide will teach you how to use Bytewax to detect and calculate the Click-Through Rate (CTR) on a custom session window on streaming data using a window and then calculate metrics downstream.*

## Table of content

- Resources
- Data Model
- Input Data
- Constructing the Dataflow
- Execution
- Summary

## Resources

[Github link](https://github.com/bytewax/search-session)

## Introduction and problem statement 

 One of the most critical metrics in evaluating the effectiveness of online platforms, particularly search engines, is the Click-Through Rate (CTR). The CTR is a measure of how frequently users engage with search results or advertisements, making it an indispensable metric for digital marketers, web developers, and data analysts.

 This relevance of CTR extends to any enterprise aiming to understand user behavior, refine content relevancy, and ultimately, increase the profitability of online activities. As such, efficiently calculating and analyzing CTR is not only essential for enhancing user experience but also for driving strategic business decisions. The challenge, however, lies in accurately aggregating and processing streaming data to generate timely and actionable insights.

Our focus on developing a dataflow using Bytewax—an open-source Python framework for streaming data processing—addresses this challenge head-on. Bytewax allows for the real-time processing of large volumes of event data, which is particularly beneficial for organizations dealing with continuous streams of user interactions. This tutorial is specifically relevant for:

* Digital Marketers: Who need to analyze user interaction to optimize ad placements and content strategy effectively.
* Data Analysts and Scientists: Who require robust tools to process and interpret user data to derive insights that drive business intelligence.
* Web Developers: Focused on improving site architecture and user interface to enhance user engagement and satisfaction.
* Product Managers: Who oversee digital platforms and are responsible for increasing user engagement and retention through data-driven methodologies.

## Strategy

In this tutorial, we will demonstrate how to build a dataflow using Bytewax to process streaming data from a hypothetical search engine. The dataflow will be designed to calculate the Click-Through Rate (CTR) for each search session, providing a comprehensive overview of user engagement with search results. The key steps involved in this process include:

1. Defining a data model/schema for incoming events.
2. Generating input data to simulate user interactions.
3. Implementing logic functions to calculate CTR for each search session.
4. Creating a dataflow to process the incoming event stream.
5. Executing the dataflow to generate actionable insights.

## Imports and Setup

Before we begin, let's import the necessary modules and set up the environment for building the dataflow.

https://github.com/bytewax/search-session/blob/c5ff19b7731edf9f551f3c2c6d5dee6f21e04f4a/dataflow.py#L1-L11

In this example, we will define a data model for the incoming events, generate input data to simulate user interactions, and implement logic functions to calculate the Click-Through Rate (CTR) for each search session. We will then create a dataflow to process the incoming event stream and execute it to generate actionable insights.

## Data Model

Let's start by defining a data model / schema for our incoming events. We'll make model classes for all the relevant events we'd want to monitor.

https://github.com/bytewax/search-session/blob/c5ff19b7731edf9f551f3c2c6d5dee6f21e04f4a/dataflow.py#L13-L36

In a production system, these might come from external schema or be auto generated.

Once the data model is defined, we can move on to generating input data to simulate user interactions. This will allow us to test our dataflow and logic functions before deploying them in a live environment.

https://github.com/bytewax/search-session/blob/c5ff19b7731edf9f551f3c2c6d5dee6f21e04f4a/dataflow.py#L63-L80

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
