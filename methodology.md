First of all, define a framework for process modeling

We need to model:

Processing stations

Parts and assemblies

So...

Station: basic system unit that can fit different functions

Storage: It is a module placed in a station that can store parts

Parts: parts are the objects that are processed by the activities

Activities: activities are the actions that are performed on the parts

Transformations: transformations are the changes that are made to one or several parts to become other parts

Transport: transportation is the movement of parts from one storage to another



Also, we need to model transportations between stations

The transportation time is the time that takes to move a part from one storage in one station to another storage in another station

So, we can calculate performance of a station configuration if the time to do each activity and transportation is known.

The time to do each transportation can be estimated using the distance between the storage elements in the stations, and the speed of the transportation system.

So, each storage place position has to be defined.

The position of the robot is importante for the real time spent in the transformation, but we could consider an approximation. An option would be to consider a ratio of the distance between the robot and the storage places. It would be a "robot position factor", artificially helping to make distributions with the robot more close to the storage places more efficient.

So, considerin the stations models above, we need to define the storage places positions.


Concepts such as robot singularity or stiffness won't be considered to reduce the problem complexity.

# Important stuff

Our objective is to build the characteristics and boundary conditions of a flexible manufacturing system automaticaly, to the be able to apply any or some optimization algorithms to find the optimum value of the variables.

The difficulty in these processes is that the problem has to be transformced in a way that it can be optimized with well-known techniques. The objective of this works is to build a modeling framework in a way that it can be used easily for problem description, and it could also be transformed to a contrained optimization algorithm.

The main problem is, based on a 2D layout, we need to define a set of constrains based on the process requirements and stations characteristics, that ensure that the process task can be completed. 

We need to obtain a representation of something like:

The press requires that the parts used by it can be reached by a robot. At the same time, this robot has to be able to put this parts in the InOut station. It could also place the parts in a storage station, but then, simultaneously, that storage location requires a transport robot in scope, and it has to be able to reach the InOut station. Or again, another storge location with the same characterisctics, recursively.




Stations size:
  X: 0.8
  Y: 0.8

Origin:
  Storage:
    - Type:
      - Part1
      Place:
        X: 0.3
        Y: 0.3
    - Type: Part2
      Place:
        X: -0.3
        Y: 0.3

Destination:
  Storage:
    - Type:
      - Part3
      Place:
        X: 0.3
        Y: 0.3

PartsStorage:
  Storage:
    - Type:
      - Part1
      Place:
        X: 0.3
        Y: 0.3
      Input: 1
      Output: 1
    - Type:
      - Part2
      Place:
        X: -0.3
        Y: 0.3
      Input: 1
      Output: 1
    - Type:
      - Part3
      Place:
        X: 0.3
        Y: -0.3
      Input: 1
      Output: 1

Robot1:
  Transport:
    Range: 1.4
    Parts:
      - Part1
      - Part2
      - Part3

Robot2:
  Transport:
    Range: 1.4
    Parts:
      - Part1
      - Part2
      - Part3


Press:
  Storage:
    - Type:
      - Part1
      Place:
        X: 0.3
        Y: 0.3
      Enables:
        - Storage:
          - Type:
            - Part2
            Place:
              X: 0.3
              Y: 0.3
            Enables:
              - Activity:
                - Activity1
  Activity:
    Activity1:
      Uses:
        - Part1
        - Part2
      Returns:
        - Part3
      TimeSpend: 3.0
