# Construct a CircuitBoard object from circuit string and setting sheet.
# CircuitBoard object have Ai (elemIDArray), Ae (elemArray) that stores 
# element ID and correspond objects.
# 
# Each object stores some critical information about the element, like the value
# that will be display as text beside the object, the direction an element points
# to, directions that is allowed to make connection, (+ -) pair beside it, etc...
# Basically, construct a "ready to draw blue print" for further use.
#
# Element code (elemCode) : 
#       R : resistor
#       L : inductor
#       C : capacitor
#       I : independent current source
#       i : dependent   current cource 
#       V : independent voltage source
#       v : dependent   volatge cource
#       O : opertional amplifier
#       A : arrow
#       b : box
#       n : Node
#       m : mesh current
#       w : numbered wire
#       g : ground
#       . : unnumbered wire
#       , : diagonal only unnumbered wire
#   Element label (label): 
#       Besides unnerbered wires, each element are given a one character lable.
#       It can be any character and can be duplicat.
#   Element ID (elemID):
#       Element ID is elemCode + label. 
#       Ex : R1, L2, Va, m1 ... etc.

import numpy as np
class PosAdjustable :
    def __init__(self) :
        self.valuePos   = 'RHS'
        self.pmPos      = 'LHS'
        self.move       = 0, 0
        self.pmMove     = 0, 0
        self.valueMove  = 0, 0
        self.pmSep      = 0

    def _check_posInput(self, side) :
        if side not in ('RHS', 'LHS') :
            raise ValueError(f'{side} is not an avaliable position. Support : \'RHS\', \'LHS\'')
    def _check_lengthInput(self, *lengths) :
        try :
            for l in lengths : float(l)
        except ValueError :
            raise ValueError(f'{l} is not an numeric value.') from None
    def set_valuePos(self, side) :
        self._check_posInput(side)
        if side == 'RHS' : self.pmPos = 'LHS'
        elif side == 'LHS' : self.pmPos = 'RHS'
        self.valuePos = side
    def set_pmPos(self, side) :
        self._check_posInput(side)
        self.pmPos = side
    def set_pmSep(self, sep) :
        self.sep = float(sep)
    def set_move(self, pmove, vmove) :
        self._check_lengthInput(pmove, vmove)
        self.move = float(pmove), float(vmove)
    def set_pmMove(self, pmove, vmove) :
        self._check_lengthInput(pmove, vmove)
        self.pmMove = float(pmove), float(vmove)
    def set_valueMove(self, pmove, vmove) :
        self._check_lengthInput(pmove, vmove)
        self.valueMove = float(pmove), float(vmove)
    def set_pmSep(self, separation) :
        self._check_lengthInput(separation)
        self.pmSep = float(separation)
    
class Element(PosAdjustable) : 
    def __init__(self, elemID, board, i, j) :
        '''Value of an element is automatically set as its element code.\
           However, wires, nodes and grounds and OP are not.'''
        self.elemCode  = elemID[0]
        self.board     = board
        self.i, self.j = i, j
        if self.elemCode[0] not in ('.', ',', 'w', 'n', 'g', 'O') :
            self.label    = elemID[1]
            self.value    = elemID[0] + '_' + elemID[1]
            self.pm       = None
        else :
            self.label    = None
            self.value    = None
        self.connectU    = False
        self.connectD    = False
        self.connectL    = False
        self.connectR    = False
        self.connectRU   = False
        self.connectRD   = False
        self.connectLU   = False
        self.connectLD   = False
        PosAdjustable.__init__(self)

    def print_info(self) :
        print('elemCode  : ', self.elemCode)
        print('label     : ', self.label)
        print('board     : ', self.board)
        print('i, j      : ', self.i, self.j)
        print('value     : ', self.value)
        print('valuePos  : ', self.valuePos)
        print('connectU  : ', self.connectU)
        print('connectD  : ', self.connectD)
        print('connectL  : ', self.connectL)
        print('connectR  : ', self.connectR)
        print('connectRU : ', self.connectRU)
        print('connectRD : ', self.connectRD)
        print('connectLU : ', self.connectLU)
        print('connectLD : ', self.connectLD)
    def set_value(self, value) :
        '''Value is the primary physical quantity for an element.\
        e.g. resistance for R, current for I, voltage for n.'''
        self.value = value
    def set_pm(self, first, second, value) :
        '''\
        Format 1 : (sign1, sign2, text),
        Format 2 : (local sign, destination sign, text),
        Ex       : ('+', '-', 'v_o'), ('+', n2, 'v_i')\
        '''
        self.pm = first, second, value

class ConnectingElement(Element) :
    '''Connecting Elements are those that can connect to mutiple direction,\
    includes nunumered wire and nodes. It has no direction.'''
    def __init__(self, elemID, board, i, j) :
        self.direction = 'U'
        self.isPosAnchor = False
        self.isNode      = False
        super().__init__(elemID, board, i, j)
    def print_info(self) :
        print('isPosAnchor : ', self.isPosAnchor)
        print('isNode    : ', self.isNode)
        super().print_info()

class PrimaryElement(Element):
    '''Primary elements can only connect to a pair of opite directions i.e.\
       up and down, left and right. It has direction.'''
    def __init__(self, elemID, board, i, j):
        self.direction = 'U'
        self.pm        = None
        super().__init__(elemID, board, i, j)
    def set_direction(self, direction) :
        CircuitBoard._directionFormate(self.board, self.i, self.j, direction)
    def print_info(self) :
        print('direction : ', self.direction)
        print('pm        : ', self.pm)
        super().print_info()

class Container :
    '''Container contains elements with label from 1 to N.\
       It can set value / valuePos / direction for mutiple elments at once.'''
    def __init__(self, elements) :
        self.storage = tuple(elements)
    def _call_storageMethod(self, method, arguments) :
        if len(arguments) < len(self.storage) : 
            message = f'warning : For container \"{self.storage[0].elemCode}\", \
arguments provided are not enough for every element in the storage.'
            print(message)
        if len(arguments) > len(self.storage) :
            raise IndexError(f'Too many arguments are provided for container \"{self.storage[0].elemCode}\"')
        for i in range(len(arguments)) :
            method(self.storage[i], arguments[i])
    def set_values(self, *values) :
        method = Element.set_value
        self._call_storageMethod(method, values)
    def set_valuePoss(self, *sides) :
        method = Element.set_valuePos
        self._call_storageMethod(method, sides)
    def set_directions(self, *directions) :
        method = PrimaryElement.set_direction
        self._call_storageMethod(method, directions)
    def set_fills(self, *fills) :
        method = Node.set_fill
        self._call_storageMethod(method, fills)
    def set_allValueMove(self, pmove, vmove) :
        method = Element.set_valueMove
        for i in range(len(self.storage)) :
            method(self.storage[i], pmove, vmove)

class Resistor(PrimaryElement)  : pass
class Inductor(PrimaryElement)  : pass
class Capacitor(PrimaryElement) : pass
class IndCurt(PrimaryElement)   : pass
class DepCurt(PrimaryElement)   : pass
class IndVolt(PrimaryElement)   : pass
class DepVolt(PrimaryElement)   : pass
class Box(PrimaryElement)       : pass
class Mesh(PrimaryElement)      : pass
class OperationalAmplifier(PrimaryElement)      : pass
class Ground(ConnectingElement)      : pass
class UnNumberedWire(ConnectingElement) : pass
class Arrow(PrimaryElement) :
    shape = 'mid'
    def set_shape(self, shape) :
        self.shape = shape
class Wire(PrimaryElement) :
    isGround = 'F'
    def set_ground(self, isGround) :
        self.isGround = isGround
class Node(ConnectingElement) :
    fill = 'T'
    def set_fill(self, fill) :
        self.fill = fill

def make_elemIDArray(circuitCode) :
    '''Return an array that store element ID at each ition.'''
    lines = circuitCode.split('\n')
    Nv = 0
    maxLength = 0
    for line in lines :
        if len(line) == 0 or line[0] != '#' :
            Nv += 1
            if len(line.rstrip()) > maxLength :
                maxLength = len(line.rstrip())
    Nh = ( maxLength + 1 ) // 3
    output = np.empty([Nv, Nh], dtype = object)
    for i in range(Nv):
        for j in range(Nh) :
            contains = lines[i][3*j : 3*j+2]
            if contains in ('', ' ') : output[i, j] = '  '
            else : output[i, j] = lines[i][3*j : 3*j+2]
    return output
def make_elemArray(board, elemIDArray) :
    '''Return an array that store element object at each ition'''
    Nv = elemIDArray.shape[0]
    Nh = elemIDArray.shape[1]
    def make_element(elemCode, i, j) :
        if elemCode[0] == 'R' : return Resistor(elemCode, board, i, j)
        if elemCode[0] == 'L' : return Inductor(elemCode, board, i, j)
        if elemCode[0] == 'C' : return Capacitor(elemCode, board, i, j)
        if elemCode[0] == 'I' : return IndCurt(elemCode, board, i, j)
        if elemCode[0] == 'i' : return DepCurt(elemCode, board, i, j)
        if elemCode[0] == 'V' : return IndVolt(elemCode, board, i, j)
        if elemCode[0] == 'v' : return DepVolt(elemCode, board, i, j)
        if elemCode[0] == 'm' : return Mesh(elemCode, board, i, j)
        if elemCode[0] == 'n' : return Node(elemCode, board, i, j)
        if elemCode[0] == 'A' : return Arrow(elemCode, board, i, j)
        if elemCode[0] == 'w' : return Wire(elemCode, board, i, j)
        if elemCode[0] == 'b' : return Box(elemCode, board, i, j)
        if elemCode[0] == 'g' : return Ground(elemCode, board, i, j)
        if elemCode[0] == 'O' : return OperationalAmplifier(elemCode, board, i, j)
    
    elemArray = np.empty([Nv, Nh], dtype = object)
    for i in range(Nv):
        for j in range(Nh) :
            if elemIDArray[i, j] in ('..', ',,') :
                elemArray[i, j] = UnNumberedWire('..', board, i, j)
            elif elemIDArray[i, j] != '  ' :
                elemArray[i, j] = make_element(elemIDArray[i, j], i, j)
            else : 
                elemArray[i, j] = None
    return elemArray
def decode(settingSheetStr) :
    lines = settingSheetStr.split('\n')
    try :
        commandCount = sum(1 for line in lines if line[0] != "#")
    except IndexError :
        raise IndexError('setting sheet is incorrectly formatted') from None
    if commandCount == 0 : return None
    def parse_line(s):
        # replace escape sequence as __xx__ 
        s = s.replace('! ', '__sp__') # space
        s = s.replace('!!', '__ex__') # exclamation mark
        s = s.replace('!n', '__NU__') # null
        s = s.replace('!N', '__NU__') # null
        # tear apart elemCode, setting and argument
        try :
            parts = s.split(':', 1)
            elemCode = parts[0].strip()
            setting, arguments = parts[1].strip().split('=', 1)
        except ValueError :
            raise ValueError('setting sheet is incorrectly formatted') from None
        return elemCode, setting.strip(), arguments.strip()
    
    commands = np.zeros([len(lines), 3], dtype=object)
    for i in range(commandCount) :
        commands[i, :] = parse_line(lines[i])
    # command[i, 0] : elemCode
    # command[i, 1] : setting
    # command[i, 2] : arguments
    processedCommands = []
    for i in range(commandCount) :
        arguments = commands[i][2].split()
        arguments = [argument.replace('__sp__', ' ') for argument in arguments]
        arguments = [argument.replace('__ex__', '!') for argument in arguments]
        arguments = [argument.replace('__NU__', '')  for argument in arguments]
        processedCommands.append( (commands[i][0], commands[i][1], arguments) )
    return processedCommands

class CircuitBoard :
    def _dirc2ij(self, i, j, direction) :
        if direction == 'U' :  return i-1, j
        if direction == 'D' :  return i+1, j
        if direction == 'L' :  return i, j-1
        if direction == 'R' :  return i, j+1
        if direction == 'RU' : return i-1, j+1
        if direction == 'RD' : return i+1, j+1
        if direction == 'LU' : return i-1, j-1
        if direction == 'LD' : return i+1, j-1
        if direction == None : return i, j
    def haveElem(self, i, j, direction = None) :
        Desi, Desj = self._dirc2ij(i, j, direction)
        if Desi<0 or Desi>=self.Nv or Desj<0 or Desj>=self.Nh : return False
        else : return self.haveElemBoolArray[Desi, Desj]
    def haveDiagOnlyElem(self, i, j, direction = None) :
        Desi, Desj = self._dirc2ij(i, j, direction)
        if Desi<0 or Desi>=self.Nv or Desj<0 or Desj>=self.Nh : return False
        else : return self.haveDiagOnlyElemBoolArray[Desi, Desj]  
    def _directionFormate(self, i, j, direction, disconnectAll = False) :
        '''First clear every connection that involve this primary element.\
           Then make connection on the correspond direction.'''
        if self.Ai[i, j][0] != 'g' :
            self.Ae[i, j].connectD = False
            self.Ae[i, j].connectU = False
            self.Ae[i, j].connectR = False
            self.Ae[i, j].connectL = False
            self.Ae[i, j].connectLD = False
            self.Ae[i, j].connectRU = False
            self.Ae[i, j].connectLU = False
            self.Ae[i, j].connectRD = False
            if self.haveElem(i, j, 'U') : self.Ae[self._dirc2ij(i, j, 'U')].connectD = False
            if self.haveElem(i, j, 'D') : self.Ae[self._dirc2ij(i, j, 'D')].connectU = False
            if self.haveElem(i, j, 'L') : self.Ae[self._dirc2ij(i, j, 'L')].connectR = False
            if self.haveElem(i, j, 'R') : self.Ae[self._dirc2ij(i, j, 'R')].connectL = False
            if self.haveElem(i, j, 'RU') : self.Ae[self._dirc2ij(i, j, 'RU')].connectLD = False
            if self.haveElem(i, j, 'LD') : self.Ae[self._dirc2ij(i, j, 'LD')].connectRU = False
            if self.haveElem(i, j, 'RD') : self.Ae[self._dirc2ij(i, j, 'RD')].connectLU = False
            if self.haveElem(i, j, 'LU') : self.Ae[self._dirc2ij(i, j, 'LU')].connectRD = False
        
        if not disconnectAll :
            self.Ae[i, j].direction = direction
            if direction in ('U', 'D') : 
                self.Ae[i, j].connectU = True
                self.Ae[i, j].connectD = True
                if self.haveElem(i, j, 'U') : self.Ae[self._dirc2ij(i, j, 'U')].connectD = True
                if self.haveElem(i, j, 'D') : self.Ae[self._dirc2ij(i, j, 'D')].connectU = True
            if direction in ('L', 'R') :  
                self.Ae[i, j].connectL = True
                self.Ae[i, j].connectR = True
                if self.haveElem(i, j, 'L') : self.Ae[self._dirc2ij(i, j, 'L')].connectR = True
                if self.haveElem(i, j, 'R') : self.Ae[self._dirc2ij(i, j, 'R')].connectL = True
            if direction in ('RU', 'LD') :
                self.Ae[i, j].connectRU = True
                self.Ae[i, j].connectLD = True
                if self.haveElem(i, j, 'RU') : self.Ae[self._dirc2ij(i, j, 'RU')].connectLD = True
                if self.haveElem(i, j, 'LD') : self.Ae[self._dirc2ij(i, j, 'LD')].connectRU = True
            if direction in ('RD', 'LU') :
                self.Ae[i, j].connectRD = True
                self.Ae[i, j].connectLU = True
                if self.haveElem(i, j, 'RD') : self.Ae[self._dirc2ij(i, j, 'RD')].connectLU = True
                if self.haveElem(i, j, 'LU') : self.Ae[self._dirc2ij(i, j, 'LU')].connectRD = True

    def _autoFormate(self, * ,setAnchorAndNodeOnly = False, autoNode) :
        '''\
        1. Auto generated nodes will be located.
        2. The ition anchors (used in drawing wires) will be located.
        3. The avalibale connecting directions of all elements will be set.
        4. The direction of pirmary elements will be adjust according to avalibale connection.'''    
        def set_possibleConnections(i, j) :
            # every diagonal connection must contain at least one diagonal wire. 
            # diagonal wire can not have connection on U D L R directions.
            if not self.haveDiagOnlyElem(i, j) :
                if self.haveElem(i, j, 'U') and not self.haveDiagOnlyElem(i, j, 'U') : self.Ae[i, j].connectU  = True
                if self.haveElem(i, j, 'D') and not self.haveDiagOnlyElem(i, j, 'D') : self.Ae[i, j].connectD  = True
                if self.haveElem(i, j, 'L') and not self.haveDiagOnlyElem(i, j, 'L') : self.Ae[i, j].connectL  = True
                if self.haveElem(i, j, 'R') and not self.haveDiagOnlyElem(i, j, 'R') : self.Ae[i, j].connectR  = True
                if self.haveElem(i, j, 'LU') and self.haveDiagOnlyElem(i, j, 'LU')   : self.Ae[i, j].connectLU = True
                if self.haveElem(i, j, 'RU') and self.haveDiagOnlyElem(i, j, 'RU')   : self.Ae[i, j].connectRU = True
                if self.haveElem(i, j, 'RD') and self.haveDiagOnlyElem(i, j, 'RD')   : self.Ae[i, j].connectRD = True
                if self.haveElem(i, j, 'LD') and self.haveDiagOnlyElem(i, j, 'LD')   : self.Ae[i, j].connectLD = True
            if self.haveDiagOnlyElem(i, j) :
                if self.haveElem(i, j, 'LU') : self.Ae[i, j].connectLU = True
                if self.haveElem(i, j, 'RU') : self.Ae[i, j].connectRU = True
                if self.haveElem(i, j, 'RD') : self.Ae[i, j].connectRD = True
                if self.haveElem(i, j, 'LD') : self.Ae[i, j].connectLD = True
        def modify_connection(i, j) :
            haveElemAt = {
                'U'  : self.haveElem(i, j, 'U'),
                'D'  : self.haveElem(i, j, 'D'),
                'L'  : self.haveElem(i, j, 'L'),
                'R'  : self.haveElem(i, j, 'R'),
                'RU' : self.haveElem(i, j, 'RU'),
                'LU' : self.haveElem(i, j, 'LU'),
                'RD' : self.haveElem(i, j, 'RD'),
                'LD' : self.haveElem(i, j, 'LD')
            }    
            #    (1)         (2)         (3)         (4)
            #    .. .. ..    ,, xx ..    .. xx ,,    .. .. ..
            #    .. oo xx    xx oo ..    .. oo xx    xx oo ..
            #    .. xx ,,    .. .. ..    .. .. ..    ,, xx ..
            #
            #    (5)         (6)         (7)         (8)
            #    ,, xx xx    xx xx ,,    .. .. ..    .. .. ..
            #    xx oo xx    xx oo xx    xx oo xx    xx oo xx
            #    .. .. ..    .. .. ..    ,, xx xx    xx xx ,,
            
            case1 =     haveElemAt['LU'] and     haveElemAt['U'] and     haveElemAt['RU'] and \
                        haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                        haveElemAt['LD'] and not haveElemAt['D'] and     haveElemAt['RD'] 
            case2 =     haveElemAt['LU'] and not haveElemAt['U'] and     haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and     haveElemAt['R'] and \
                        haveElemAt['LD'] and     haveElemAt['D'] and     haveElemAt['RD'] 
            case3 =     haveElemAt['LU'] and not haveElemAt['U'] and     haveElemAt['RU'] and \
                        haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                        haveElemAt['LD'] and     haveElemAt['D'] and     haveElemAt['RD']
            case4 =     haveElemAt['LU'] and     haveElemAt['U'] and     haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and     haveElemAt['R'] and \
                        haveElemAt['LD'] and not haveElemAt['D'] and     haveElemAt['RD']
            case5 =     haveElemAt['LU'] and not haveElemAt['U'] and not haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                        haveElemAt['LD'] and     haveElemAt['D'] and     haveElemAt['RD']
            case6 = not haveElemAt['LU'] and not haveElemAt['U'] and     haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                        haveElemAt['LD'] and     haveElemAt['D'] and     haveElemAt['RD']
            case7 =     haveElemAt['LU'] and     haveElemAt['U'] and     haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                        haveElemAt['LD'] and not haveElemAt['D'] and not haveElemAt['RD']
            case8 =     haveElemAt['LU'] and     haveElemAt['U'] and     haveElemAt['RU'] and \
                    not haveElemAt['L']  and        True         and not haveElemAt['R'] and \
                    not haveElemAt['LD'] and not haveElemAt['D'] and     haveElemAt['RD']
            # remove connection to up
            if case1 or case4 or case7 or case8 :
                if self.haveElem(i, j, 'U') : 
                    self.Ae[self._dirc2ij(i, j, 'U')].connectD = False
                    self.Ae[i, j].connectU = False
            # remove connection to down
            if case2 or case3 or case5 or case6 :
                if self.haveElem(i, j, 'D') : 
                    self.Ae[self._dirc2ij(i, j, 'D')].connectU = False
                    self.Ae[i, j].connectD = False
            # remove connection to left
            if case1 or case3 :
                if self.haveElem(i, j, 'L') : 
                    self.Ae[self._dirc2ij(i, j, 'L')].connectR = False
                    self.Ae[i, j].connectL = False
            # remove connection to right
            if case2 or case4 :
                if self.haveElem(i, j, 'R') : 
                    self.Ae[self._dirc2ij(i, j, 'R')].connectL = False
                    self.Ae[i, j].connectR = False
            # remove connection of LU-RD connection 
            if case1 or case2 or case5 or case8:
                self.Ae[i, j].connectRU,  self.Ae[i, j].connectLD = False, False
                if self.haveElem(i, j, 'RU') : self.Ae[self._dirc2ij(i, j, 'RU')].connectLD = False
                if self.haveElem(i, j, 'LD') : self.Ae[self._dirc2ij(i, j, 'LD')].connectRU = False; 
            # remove connection of LD-RU connection 
            if case3 or case4 or case6 or case7:
                self.Ae[i, j].connectLU,  self.Ae[i, j].connectRD = False, False
                if self.haveElem(i, j, 'LU') : self.Ae[self._dirc2ij(i, j, 'LU')].connectRD = False
                if self.haveElem(i, j, 'RD') : self.Ae[self._dirc2ij(i, j, 'RD')].connectLU = False                
        def set_anchorAndNode(i, j) :
            connectN, connectDircN = 0, 0
            haveElemUD, haveElemLR, haveElemLURD, haveElemRULD = False, False, False, False
            if self.Ae[i, j].connectU and self.haveElem(i, j, 'U') \
               and self.Ae[self._dirc2ij(i, j, 'U')].connectD :
                connectN+=1; haveElemUD = True
            if self.Ae[i, j].connectD and self.haveElem(i, j, 'D') \
               and self.Ae[self._dirc2ij(i, j, 'D')].connectU :
                connectN+=1; haveElemUD = True
            if self.Ae[i, j].connectL and self.haveElem(i, j, 'L') \
               and self.Ae[self._dirc2ij(i, j, 'L')].connectR :
                connectN+=1; haveElemLR = True
            if self.Ae[i, j].connectR and self.haveElem(i, j, 'R') \
               and self.Ae[self._dirc2ij(i, j, 'R')].connectL :
                connectN+=1; haveElemLR = True
            if self.Ae[i, j].connectRU and self.haveElem(i, j, 'RU') \
               and self.Ae[self._dirc2ij(i, j, 'RU')].connectLD: 
                connectN+=1; haveElemRULD = True
            if self.Ae[i, j].connectRD and self.haveElem(i, j, 'RD') \
               and self.Ae[self._dirc2ij(i, j, 'RD')].connectLU : 
               connectN+=1; haveElemLURD = True
            if self.Ae[i, j].connectLU and self.haveElem(i, j, 'LU') \
               and self.Ae[self._dirc2ij(i, j, 'LU')].connectRD : 
               connectN+=1; haveElemLURD = True
            if self.Ae[i, j].connectLD and self.haveElem(i, j, 'LD') \
               and self.Ae[self._dirc2ij(i, j, 'LD')].connectRU :
               connectN+=1; haveElemRULD = True
            if haveElemUD : connectDircN += 1
            if haveElemLR : connectDircN += 1
            if haveElemRULD : connectDircN += 1
            if haveElemLURD : connectDircN += 1

            self.Ae[i, j].isPosAnchor = False
            if autoNode : self.Ae[i, j].isNode      = False
            # is end point 
            if connectN == 1 :
                self.Ae[i, j].isPosAnchor = True 
            # is intersection or turning point
            if connectDircN >= 2 : 
                self.Ae[i, j].isPosAnchor = True
                # is intersection
                if connectN >= 3 and autoNode: self.Ae[i, j].isNode = True 
        def set_priObjDirc(i, j) :
            isEndPoint = True
            # UD LR have higher proprity then diagonal direction
            if self.haveElem(i, j, 'RU') and self.haveElem(i, j, 'LD') : 
                self.Ae[i, j].set_direction('RU'); isEndPoint = False
            if self.haveElem(i, j, 'LU') and self.haveElem(i, j, 'RD') : 
                self.Ae[i, j].set_direction('RD'); isEndPoint = False
            if self.haveElem(i, j, 'U') and self.haveElem(i, j, 'D') : 
                self.Ae[i, j].set_direction('U'); isEndPoint = False
            if self.haveElem(i, j, 'L') and self.haveElem(i, j, 'R') : 
                self.Ae[i, j].set_direction('R'); isEndPoint = False
            if isEndPoint :
                if self.haveElem(i, j, 'RU') or self.haveElem(i, j, 'LD') : 
                    self.Ae[i, j].set_direction('RU')
                if self.haveElem(i, j, 'LU') or self.haveElem(i, j, 'RD') : 
                    self.Ae[i, j].set_direction('RD')
                if self.haveElem(i, j, 'U') or self.haveElem(i, j, 'D') : 
                    self.Ae[i, j].set_direction('U')
                if self.haveElem(i, j, 'L') or self.haveElem(i, j, 'R') : 
                    self.Ae[i, j].set_direction('R')

        if not setAnchorAndNodeOnly :
            for i in range(self.Nv):
                for j in range(self.Nh) :
                    if self.haveElem(i, j) :
                        set_possibleConnections(i, j)
            for i in range(self.Nv):
                for j in range(self.Nh) :
                    if self.haveElem(i, j) and not self.Ai[i, j] == '..':
                        modify_connection(i, j)
            for i in range(self.Nv):
                for j in range(self.Nh) :
                    # unnermered wire and node has no direction
                    if self.Ai[i, j][0] not in (' ', ',', '.', 'n', 'g') : 
                        set_priObjDirc(i, j)
        for i in range(self.Nv):
            for j in range(self.Nh) :
                if self.haveElem(i, j) :
                    if self.Ai[i, j][0] == 'm' or \
                    (self.Ai[i, j][0] == 'A' and self.Ae[i, j].shape =='end') :
                        self._directionFormate(i, j, None, disconnectAll = True)
        for i in range(self.Nv):
            for j in range(self.Nh) :
                if self.haveElem(i, j) :
                    set_anchorAndNode(i, j)
            
    def _prepare_kitForSetting(self) :
        self.Ae = self.elemArray
        self.Ai = self.elemIDArray
        self.Nv = self.Ae.shape[0]
        self.Nh = self.Ae.shape[1]
        self.haveElemBoolArray = np.zeros([self.Nv, self.Nh], dtype = bool)
        for i in range(self.Nv) :
            for j in range(self.Nh) :
                if self.Ai[i, j] != '  ' : self.haveElemBoolArray[i, j] = True
        # element code ',,' is for the wire that can only connect diagonally.
        self.haveDiagOnlyElemBoolArray = np.zeros([self.Nv, self.Nh], dtype = bool)
        for i in range(self.Nv):
            for j in range(self.Nh) :
                if self.Ai[i, j] == ',,' : self.haveDiagOnlyElemBoolArray[i, j] = True

    def _make_objRef(self) :
        self.objRef = {}
        def make_containerObjRef(elemCode, refs) :
            if len(refs) < 2 : return 
            refs = sorted(refs, key = lambda x : x[1])
            self.objRef[elemCode] = Container([self.objRef[ref] for ref in refs])
        RRefs = []
        LRefs = []
        CRefs = []
        IRefs = []
        iRefs = []
        VRefs = []
        vRefs = []
        mRefs = []
        nRefs = []
        ARefs = []
        wRefs = []
        bRefs = []
        gRefs = []
        for i in range(self.Nv):
            for j in range(self.Nh) :
                if self.Ai[i, j] not in ('  ', '..', ',,') :
                    if self.Ai[i, j][0] == 'R' : RRefs.append(self.Ai[i, j])
                    if self.Ai[i, j][0] == 'L' : LRefs.append(self.Ai[i, j])
                    if self.Ai[i, j][0] == 'C' : CRefs.append(self.Ai[i, j])
                    if self.Ai[i, j][0] == 'I' : IRefs.append(self.Ai[i, j])
                    if self.Ai[i, j][0] == 'i' : iRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'V' : VRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'v' : vRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'm' : mRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'n' : nRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'A' : ARefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'w' : wRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'b' : bRefs.append(self.Ai[i, j]) 
                    if self.Ai[i, j][0] == 'g' : gRefs.append(self.Ai[i, j]) 
                    self.objRef[self.Ai[i, j]] = self.Ae[i, j]
        make_containerObjRef('R', RRefs)
        make_containerObjRef('L', LRefs)
        make_containerObjRef('C', CRefs)
        make_containerObjRef('I', IRefs)
        make_containerObjRef('i', iRefs)
        make_containerObjRef('V', VRefs)
        make_containerObjRef('v', vRefs)
        make_containerObjRef('m', mRefs)
        make_containerObjRef('n', nRefs)
        make_containerObjRef('A', ARefs)
        make_containerObjRef('w', wRefs)
        make_containerObjRef('b', bRefs)
        make_containerObjRef('g', gRefs)

    def find_elemPos(self, objectName) :
        for i in range(self.Nv):
            for j in range(self.Nh) :
                if self.Ai[i, j] == objectName : return i, j

    _settingMethod = {
        'value'      : Element.set_value,
        'values'     : Container.set_values,
        'direction'  : PrimaryElement.set_direction,
        'directions' : Container.set_directions,
        'pm'         : Element.set_pm,
        'shape'      : Arrow.set_shape,
        'fill'       : Node.set_fill,
        'fills'      : Container.set_fills,
        'ground'     : Wire.set_ground,
        'valuePos'   : PosAdjustable.set_valuePos,
        'valuePoss'  : Container.set_valuePoss,
        'pmPos'      : PosAdjustable.set_pmPos,
        'move'       : PosAdjustable.set_move,
        'valueMove'  : PosAdjustable.set_valueMove,
        'allValueMove' : Container.set_allValueMove,
        'pmMove'     : PosAdjustable.set_pmMove,
        'pmSep'      : PosAdjustable.set_pmSep,
    }
    def _apply_setting(self) :
        commands = decode(self.settingSheetStr)
        if commands == None : return
        for command in commands :
            objName = command[0]
            setting = command[1]
            arguments = command[2]
            try :
                method = self._settingMethod[setting]
            except KeyError :
                raise KeyError(f'{setting} is not an available setting.') from None
            try :
                method(self.objRef[objName], *arguments)
            except KeyError :
                raise KeyError(f'element or container {objName} does not exist.') from None
            except AttributeError :
                raise AttributeError(f'{objName} have no setting about {setting}') from None

    def __init__(self, circuitCodeStr, settingSheetStr, autoNode = True) :
        self.circuitCodeStr = circuitCodeStr
        self.elemIDArray = make_elemIDArray(circuitCodeStr)
        self.elemArray = make_elemArray(self, self.elemIDArray)
        self._prepare_kitForSetting()
        self.settingSheetStr = settingSheetStr
        self._make_objRef()
        self._autoFormate(autoNode = autoNode)
        self._apply_setting()
        self._autoFormate(setAnchorAndNodeOnly=True, autoNode = autoNode)

def to_txt(circuitBoard, filename, * ,autoNode = True, blockWidth = 6) :
    '''Store circuit code string and setting sheet in an txt file.'''
    circuitTxt = open(filename, 'w')
    circuitTxt.write("circuit = '''\\\n")
    circuitTxt.write(circuitBoard.circuitCodeStr.replace('\\', '\\\\'))
    circuitTxt.write("'''\nsetting = '''\\\n")
    circuitTxt.write(circuitBoard.settingSheetStr.replace('\\', '\\\\'))
    circuitTxt.write("'''\n")
    circuitTxt.write("autoNode = ")
    circuitTxt.write(str(autoNode))
    circuitTxt.write("\nblockWidth = ")
    circuitTxt.write(str(blockWidth))
    circuitTxt.close()