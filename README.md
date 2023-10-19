# Circuit Drawer - A tool to draw svg circuit diagrams
In this project, user can make circuit diagram scheme by a string 
then apply setting on each element. The input is an svg diagram.
# Installation

### Python 
- require 3.11.4+

### Install reuqired package
- To install the required package run the command below.
```
pip install -r requirements.txt
```

# How to use
Draw a circuit scheme by declare a string as below.
```python
circuit = '''\
.. .. L1 .. .. A1 .. .. n1
.. ,,       ..    ..
Va    R1    C1    i1
..       ,, ..    ..
.. .. C0 .. .. .. .. .. n2
#'''
```
Then write a setting sheet as below:
```python
setting = '''\
R1 : pvMove    = 0 0.1
n1 : pm        = - n2 v_o
i1 : direction = D
i1 : value     = 2I_x
A1 : value     = I_x
C  : values    = 2\\muF 4\\muF
#'''
```
See user manual for more detail.
