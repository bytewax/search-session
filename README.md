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
4. Creating a dataflow that incorporates windowing to process the incoming event stream.
5. Executing the dataflow to generate actionable insights.

## Assumptions

* Searches are per-user, so we need to divvy up events by user.
* Searches don't span user sessions, so we should calculate user sessions first.
* Sessions without a search shouldn't contribute.
* Calculate one metric: **click through rate** (or **CTR**), if a user clicked on any result in a search.

## Imports and Setup

Before we begin, let's import the necessary modules and set up the environment for building the dataflow.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L1-L11

In this example, we will define a data model for the incoming events, generate input data to simulate user interactions, and implement logic functions to calculate the Click-Through Rate (CTR) for each search session. We will then create a dataflow to process the incoming event stream and execute it to generate actionable insights.

## Data Model

Let's start by defining a data model / schema for our incoming events. We'll make model classes for all the relevant events we'd want to monitor.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L13-L36

In a production system, these might come from external schema or be auto generated.

Once the data model is defined, we can move on to generating input data to simulate user interactions. This will allow us to test our dataflow and logic functions before deploying them in a live environment. Let's create 2 users and simulate their click activity as follows:

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L38-L58

The client events will constitute the data input for our dataflow, simulating user interactions with the search engine. The events will include user IDs, search queries, search results, and click activity. This data will be used to calculate the Click-Through Rate (CTR) for each search session.

## Defining user events, adding events and calculating CTR

We will define three helper functions: `user_event`, `add_event`, and `calculate_ctr` to process the incoming events and calculate the CTR for each search session.

1. The `user_event` function will extract the user ID from the incoming event and use it as the key for grouping the events by user.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L60-62


3. The `calculate_ctr` function will calculate the Click-Through Rate (CTR) for each search session based on the click activity in the session. 

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L64-75

## Creating our Dataflow

A dataflow is the unit of work in Bytewax. Dataflows are data-parallel directed acyclic graphs that are made up of processing steps.

Let's start by creating an empty dataflow.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L77-78

### Generating Input Data

Bytewax has a `TestingSource` class that takes an enumerable list of events that it will emit, one at a time into our dataflow. `TestingSource` will be initialized with the list of events we created earlier in the variable `client_events`.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L79-80


### Mapping user events

We can use the `op` class along with `op.map("user_event", inp, user_event)` - this takes each event from the input and applies the `user_event` function. This function is transforming each event into a format suitable for grouping by user (key-value pairs where the key is the user ID).

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L81-82

### The role of windowed data in analysis for CTR

We will now turn our attention to windowing the data. In a dataflow pipeline, the role of collecting windowed data, particularly after mapping user events, is crucial for segmenting the continuous stream of events into manageable, discrete chunks based on time or event characteristics. This step enables the aggregation and analysis of events within specific time frames or sessions, which is essential for understanding patterns, behaviors, and trends over time.

After user events are mapped, typically transforming each event into a tuple of (user_id, event_data), the next step is to group these events into windows. In this example, we will use a `SessionWindow` to group events by user sessions. We will also use an `EventClockConfig` to manage the timing and order of events as they are processed through the dataflow.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L83-90

* The `EventClockConfig` is responsible for managing the timing and order of events as they are processed through the dataflow. It's crucial for ensuring that events are handled accurately in real-time or near-real-time streaming applications.

* The `SessionWindow` specifies how to group these timestamped events into sessions. A session window collects all events that occur within a specified gap of each other, allowing for dynamic window sizes based on the flow of incoming data

These configurations ensure that your dataflow can handle streaming data effectively, capturing user behavior in sessions and calculating relevant metrics like CTR in a way that is timely and reflective of actual user interactions. This setup is ideal for scenarios where user engagement metrics over time are critical, such as in digital marketing analysis, website optimization, or interactive application monitoring.

Once the events are grouped into windows, further processing can be performed on these grouped events, such as calculating metrics like CTR within each session. This step often involves applying additional functions to the windowed data to extract insights, such as counting clicks and searches to compute the CTR.

We can do this as follows:

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L92-97

In here, we are setting up data windowing as a step in the dataflow after the user events were created. We can then calculate the CTR using our function on the windowed data. 

### Returning results

Finally, we can add an output step to our dataflow to return the results of the CTR calculation. This step will emit the CTR for each search session, providing a comprehensive overview of user engagement with search results.

https://github.com/bytewax/search-session/blob/e27a0e116c8ca6f073e2278302d6128795d8ac37/dataflow.py#L98-99


Now we're done with defining the dataflow. Let's run it!

``` python
> python -m bytewax.run dataflow:flow
>> User 1: 1 searches, 1 clicks
>> User 2: 1 searches, 2 clicks
>>('1', 1.0)
>>('2', 2.0)
```


## Summary

That’s it, now you have an understanding of how you can build custom session windows, how you can define dataclasses to be used in Bytewax and how to calculate click through rate on a stream of logs.

## We want to hear from you!

If you have any trouble with the process or have ideas about how to improve this document, come talk to us in the [#troubleshooting Slack channel!](https://join.slack.com/t/bytewaxcommunity/shared_invite/zt-vkos2f6r-_SeT9pF2~n9ArOaeI3ND2w)

See our full gallery of tutorials →

[Share your tutorial progress!](https://twitter.com/intent/tweet?text=I%27m%20mastering%20data%20streaming%20with%20%40bytewax!%20&url=https://bytewax.io/tutorials/&hashtags=Bytewax,Tutorials)
