# WSU SAIL-ON Novelty Generator

The WSU SAIL-ON Novelty Generator (NG) provides a client-server interface for
TA2 agents to interact with the three domains: CartPole, VizDoom, SmartEnv.

The [src](src) directory provides instructions for installing and running the
NG client, as well as a sample client, configuation file, and auxiliary files
for interacting with the NG.

The [domains](domains) directory contains subdirectories for each of the three
domains [cartpole](domains/cartpole), [vizdoom](domains/vizdoom) and
[smartenv](domains/smartenv) that provide more information about the domains.

The [WSU-Portable-Generator](WSU-Portable-Generator) directory contains a
portable mock novelty generator for the cartpole and vizdoom domains. The readme
describes it's use and where to integrate your own TA2 agent.

Contact Larry Holder (holder@wsu.edu) for more information.

