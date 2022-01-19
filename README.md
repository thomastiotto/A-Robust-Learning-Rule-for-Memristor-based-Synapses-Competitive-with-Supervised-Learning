# Learning Nonlinear Functions on Vectors using Nb Doped SrTiO3 Memristors


## Paper
TBA

## Abstract
Memristive  devices  are  a  class  of  circuit  elementsthat  shows  great  promise  as  future  building  block  for  brain-inspired  computing.  One  influential  view  in  theoretical  neuro-science  sees  the  brain  as  a  function-computing  device:  giveninput  signals,  the  brain  applies  a  function  in  order  to  generatenew  internal  states  and  motor  outputs.  Therefore,  being  able  toapproximate functions is a fundamental axiom to build upon forfuture brain research and to derive more efficient computationalmachines. In this work we apply a novel supervised learning algo-rithm  -  based  on  controlling  niobium-doped  strontium  titanatememristive  synapses  -  to  learning  non-trivial  multidimensionalfunctions.  By  implementing  our  method  into  the  spiking  neuralnetwork   simulator   Nengo,   we   show   that   we   are   able   to   atleast  match  the  performance  of  the  standard  Prescribed  ErrorSensitivity  learning  rule,  which  is  similar  to  the  delta  rule  inclassical  neural  networks.
## Folders
* ``experiments``: various executables used to explore the properties of the memristors
* ``memristor_nengo``: library containing the learning algorithms running in Nengo Core and NengoDL backends, together with extra useful functions
* ``tests``: simple tests for specific functionalities

## Running the code
1. Clone [this](https://github.com/Tioz90/Memristor-Nengo) repository for the library code and add it to your PYTHONPATH
2. Run the experiments:
   * ``memristor_evolution_test.py`` runs mPES on randomly initialised models and calculates their learning performance statistics
   * ``learn_multidimensional_functions.py`` runs mPES, and PES learning alongside NEF by using the simulated 
     memristors in the ``memristor_nengo`` library. 
     * Learn the product of 2-D input components (x1 * x2). 
     * Learn the combined product (x1 * x2 + x3 * x4). 
     * Learn the separate 3-D products [x1 * x2, x1 * x3, x2 * x3]. 
     * Learn the 2-D circular convolution [x1, x2] x [x3, x4]. 
     * Learn the 3-D circular convolution [x1, x2, x3] x [x4, x5, x6].