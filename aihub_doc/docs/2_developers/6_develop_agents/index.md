Ok here I want to descriibt the minimal developer setup that is needed to develope own agents.

If you want to develop your own agents in your own repo create a file structure as the following:

create a base folder "agents" in your repo. in there create a new poetry project.
in this folder you can create your own agents. create a new folder for each agent. Use snake case for the folder name.

for each agent you need a Dockerfile and a main.py as well as a MyCustomAgent folder with MyCustomAgent.py and MyCustomAgentConfig.py in it.

in the MyCustomAgent.py you can create your own agent by defining and combining your steps. if you define your own steps 
place them in /events in MyCustomAgent folder.

in the pyproject.toml in the agetns folder you manage the dependencies that you need for your agents. We advise to share and therefore enfoce to sync the dependencies of the agents
As update in the ai-hub core repo should propagate to all agents simultaneously as otherwise collaboration between agents might not be guaranteed as some agents break due to missmatch to core components as for example the api.

To run and test your agents you can use the docker-compose.local.yml file from the aihub_core repo. Just copy it to your project root.
Please take note of the versions used for the images, especially for the aihub core images. 
They should match the version of the aihub core sdk package that you are using.

!!! NOTE: maybe provide command in package to generate/update docker-compose to sync with sdk version

also create a second docker-compose file called docker-compose-agents.dev.yml in which you define your agent services.
In this compose file reference your agents Dockerfiles.
When you want to test your agent you up docker-compose.local.yml as well as the docker-compose-agents.dev.yml