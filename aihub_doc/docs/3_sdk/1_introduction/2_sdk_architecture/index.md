---
title: "SDK Architecture"
index: 2
---
[@mhoegger](https://github.com/mhoegger)
[WIP]

the swiss AIHub SDK consists of 4 key modules. the aihub_lib, the aihub_agents, the aihub_pipelines and the aihub_process

The aihub_agents is a package that provides a set of tools and utilities for building and managing AI agents. An agent in the work of 
the swiss AI Hub is a workflow with steps. each steps defined what it needs as input and what it produces as output. 
These inputs and outputs are events and can happen at any point in time. like that the agents are asynchronous and event driven and can be working over a long period of time.
a step waits for it's execution until all it's inputs are available. once a step is executed it produces outputs that can be consumed by other steps.

The aihub_agent sdk package mainly provides you with the framework for running these agents. like the agent runner and also woth object like the RunContext or the ThreadContext which act as cross step storage of information.
The aihub_agents package also provides you with some general Agents that can be use out of the box like the LLMWrappingAgent or the RagAgent. If using one of these agents you don't need to implement it by yourself. you can just configure it 
on how it should be have by for example adjsuting the systemprompt or adjusting some parameters.
Waht the aihub_agent package does not provide are fully finished steps and Events. This is because when building agents 
the events and the steps are what defines the agent and therefor what remains in your responsibility when using the sdk.

however for ever repeating and generic logic of step implementation the aihub_lib package comes into play. it provides you with a lot of useful methods and functions that 
you can use when implementing your steps. for example the aihub_lib provides you with methods to interact with the platform services like the vector database or the document storage.
Other functionalities are handing and managing chat histories or guards. So when you develop you agent you have to define the step yourself but in the implementation you can rely on provided methods from the aihub_lib.
This is structured in this way because such methods can also be relevant for the other sdk packages like the aihub_pipelines or the aihub_process.

The aihub_pipelines package is similar to the aihub_agents package. it also provides you with a framework for building pipelines. Pipelines are also workflows that are aimed to
process data. they usually connect a datasource relevant for agents and process the data to transfor it into a format that is useful and accessible for agents. 
for example a pipeline can be used to ingest documents from a sharepoint, process them and store them in the vector database.
Now you probably see the similarity to agents and how it is very common that agents and pipeline might use the same methods from the aihub_lib package.