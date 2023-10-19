# Circuit Drawer

# Installation

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
