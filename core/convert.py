# Make a list that contains the information to draw svg for the cicuit
# from CircuitBoard object.
# 
# 1. Locate primary elements, also put anhors for positioning.
# 2. For each primary element and anchor, connect wires that extend
#    to 8 directions.
# 3. Locate texts that attached to each element.
# 
# Protocal :
#     Centered Drawing SVG code :
#     >> SVG code = 'e', elemCode, x, y, pmove, vmove, direction
#     >> SVG code = 't',     text, x, y, pmove, vmove, direction
#     Path Drawing SVG Objects :
#     >> SVG code = 'w', elemCode, strx, stry, endx, endy
#     pmove, vmove : 
#     |     _______________   
#     |     |             | ^
#     |     |     obj     | | vmove (vertical)
#     |     |_____________|
#     |         ----> pmove (parallel)
#     elemCode :
#         Basically the same as defined in 'construct.py' except :
#         N : hollow node
#         a : arrow with shape 'end' (----->) 
#         g : ground
import numpy as np
import re
# Coordinate :
# -------------------> (+x, +j)
# |          .
# |          .
# |. . . . . o (x, y) 
# |            = blockWidth_*(j, i)
# v (+y, +i)
blockWidth_ = 6
def ij2xy(i, j) :
    return j * blockWidth_, i * blockWidth_
# Direction :
#  3  2  1
#   \ | /
# 4--   --0
#   / | \
#  5  6  7
svgDirc = {
    'R'  : 0, 'RU' : 1, 'U'  : 2, 'LU' : 3,
    'L'  : 4, 'LD' : 5, 'D'  : 6, 'RD' : 7
}
# Offset :
# when being connected by path drawing objects, 
# it experience an offset from its center :
#          <---------> 
#          ___________ ^(primElemWidth)
#          |         | 
# n -------|   obj   |-------n
#          |_________|
#          <--->|<--->
#    (offset)^     ^(offset)  
primElemWidth = 8

class CenteredDrawingObj :
    '''primary elements are draw by a given direction and center position.'''
    def __init__(self, elemObj) :
        self.elemCode = elemObj.elemCode
        self.i        = elemObj.i
        self.j        = elemObj.j
        self.move     = elemObj.move
        self.svgDirc  = svgDirc[elemObj.direction] \
                      if hasattr(elemObj, 'direction') else 0
        self.offset   = np.zeros(8, dtype=object)
        if elemObj.elemCode in 'RLCVvIiabN' or elemObj.elemCode == 'empty':
            # those object occupies the region of a circle.
            if elemObj.elemCode == 'N' : 
                l = primElemWidth/8
                s = np.sqrt(2)
                self.offset[0] =  l,  0
                self.offset[1] =  l/s, -l/s
                self.offset[2] =  0, -l
                self.offset[3] = -l/s, -l/s
                self.offset[4] = -l,  0
                self.offset[5] = -l/s,  l/s
                self.offset[6] =  0,  l
                self.offset[7] =  l/s,  l/s
            # those object occupies the region of a squre.
            else :
                l = primElemWidth / 2
                self.offset[0] =  l,  0  
                self.offset[1] =  l, -l  
                self.offset[2] =  0, -l  
                self.offset[3] = -l, -l  
                self.offset[4] = -l,  0  
                self.offset[5] = -l,  l  
                self.offset[6] =  0,  l  
                self.offset[7] =  l,  l  
        if elemObj.elemCode in ('n', 'anchor', 'A', 'm', 'g', 'O') :
            # those object have zero offset, wires connet to their center
            self.offset[:] = [(0, 0) for _ in range(8)]
class WireDrawingObj :
    '''Wires are drawn by a given starting and ending point'''
    def __init__ (self, elemCode, strPos, endPos) : 
        self.elemCode = elemCode
        self.strPos = strPos
        self.endPos = endPos
class TextDrawingObj :
    '''Texts are drawn by a given reference position, direction, \
       along with horizontail and vertical move from its reference position.'''
    def __init__(self, text, refi, refj, vmove, pmove, refDirection) :
        self.text  = text
        self.refi  = refi
        self.refj  = refj
        self.vmove = vmove
        self.pmove = pmove
        self.refSvgDirc = svgDirc[refDirection]

def make_centeredDrawingObjs(circuitboard) :
    # put primary drawing objects, along with nodes and position anchors.
    def make_centeredWire(elemObj) :
        # some wires are considered as centered drawing object, however it should be
        # acheveie by wire drawing object. (sudo centered drawing object) 
        nonlocal sudoCenteredDrawingObjs
        nonlocal centeredDrawingObjs
        midPos = ij2xy(elemObj.i, elemObj.j)
        l = primElemWidth / 2
        if elemObj.direction in ('R', 'L')   : extend = (l, 0)
        if elemObj.direction in ('U', 'D')   : extend = (0, l)
        if elemObj.direction in ('RU', 'LD') : extend = (l, -l)
        if elemObj.direction in ('LU', 'RD') : extend = (l, l)
        x1, x2 = midPos[0] - extend[0], midPos[0] + extend[0]
        y1, y2 = midPos[1] - extend[1], midPos[1] + extend[1]
        # position adjustment
        x1 += elemObj.move[0]; x2 += elemObj.move[0]
        y1 += elemObj.move[1]; y2 += elemObj.move[1]
        sudoCenteredDrawingObjs.append(WireDrawingObj(elemObj.elemCode, (x1, y1), (x2, y2)))
        # after makeing the wire, left an empty object at this position, it will be remove later
        elemObj.elemCode = 'empty'
        centeredDrawingObjs.append(CenteredDrawingObj(elemObj))
    centeredDrawingObjs = []
    sudoCenteredDrawingObjs = []
    Ae = circuitboard.elemArray
    Nv = circuitboard.Nv
    Nh = circuitboard.Nh
    for i in range(Nv) :
        for j in range(Nh) :
            if circuitboard.haveElem(i, j) :
                elemObj = Ae[i, j]
                # put auto generated nodes and anchors
                if elemObj.elemCode in ('.', ',') :
                    if elemObj.isNode : elemObj.elemCode = 'n'
                    elif elemObj.isPosAnchor : elemObj.elemCode = 'anchor'
                    # skip for unnerbered wires that are not node nor anchor. 
                    else : continue 
                # put centered wires
                elif elemObj.elemCode == 'w' :
                    make_centeredWire(elemObj)
                    if elemObj.isGround == 'T' : elemObj.elemCode = 'g'
                    else : continue
                    # skip thus it is already made as a sudo centered drawing object.
                else :
                    if elemObj.elemCode == 'n' and elemObj.fill == 'F' :
                        # in protocol, n is filled node while N is hollow node.
                        elemObj.elemCode = 'N'
                    if elemObj.elemCode == 'A' and elemObj.shape == 'end' :
                        # in protocol, a is end Arrow while A is mid arrow.
                        elemObj.elemCode = 'a'
                centeredDrawingObjs.append(CenteredDrawingObj(elemObj))
    return centeredDrawingObjs, sudoCenteredDrawingObjs
def make_WireDrawingObjs(circuitboard, centeredDrawingObjs) : 
    #  1. Starts with each element, connect to the nearst anchor or element.
    #  2. Consider anchors, make sure every anchor connects.
    wireDrawingObjs = []
    Ai = circuitboard.elemIDArray
    Ae = circuitboard.elemArray
    Nv = circuitboard.Nv
    Nh = circuitboard.Nh
    connectingBoolArray = np.zeros([Nv, Nh, 8], dtype = bool)
    for i in range(Nv) :
        for j in range(Nh) :
            if circuitboard.haveElem(i, j) :
                connectingBoolArray[i, j, 0] = Ae[i, j].connectR
                connectingBoolArray[i, j, 1] = Ae[i, j].connectRU
                connectingBoolArray[i, j, 2] = Ae[i, j].connectU
                connectingBoolArray[i, j, 3] = Ae[i, j].connectLU
                connectingBoolArray[i, j, 4] = Ae[i, j].connectL
                connectingBoolArray[i, j, 5] = Ae[i, j].connectLD
                connectingBoolArray[i, j, 6] = Ae[i, j].connectD
                connectingBoolArray[i, j, 7] = Ae[i, j].connectRD
            else :
                connectingBoolArray[i, j, :] = [0 for _ in range(8)]
    def canReach(i, j, direction) :
        if i<0 or i>=Nv or j<0 or j>=Nh : return False
        else :
            if direction  < 4 : oppsiteDirection = direction + 4
            if direction >= 4 : oppsiteDirection = direction - 4
            return connectingBoolArray[i, j, oppsiteDirection]
    def find_connectPoint(i, j, direction) :
        def walk(i, j, direction, step) :
            if direction == 0 : move =     0, +step
            if direction == 1 : move = -step, +step
            if direction == 2 : move = -step,     0
            if direction == 3 : move = -step, -step
            if direction == 4 : move =     0, -step
            if direction == 5 : move = +step, -step
            if direction == 6 : move = +step,     0
            if direction == 7 : move = +step, +step
            return i + move[0], j + move[1]
        def check(i, j) :
            # No element or anchor in this position
            if not circuitboard.haveElem(i, j) : 
                return None
            # It connect to element
            elif Ai[i, j][0] not in ('.', 'w', ',') : 
                return True
            # It connect to anchor
            elif Ae[i, j].isPosAnchor : 
                return True
            # Keep finding
            else : return False
        for step in range( max(Nv, Nh) ) :
            destination = walk(i, j, direction, step+1)
            if not canReach(*destination, direction) :
                return None, None
            else :
                result = check(*destination)
                if   result == False : continue # keep going
                elif result == True  : return destination
                elif result == None  : return None, None

    for strObj in centeredDrawingObjs :
        stri = strObj.i
        strj = strObj.j
        for direction in range(8) :
            desi, desj = find_connectPoint(stri, strj, direction)
            if desi != None :
                desObj = [obj for obj in centeredDrawingObjs if \
                            obj.i == desi and obj.j == desj][0]
                endi = desObj.i
                endj = desObj.j
                # make a wire that connects starting point and desination
                strx, stry = ij2xy(stri, strj)
                endx, endy = ij2xy(endi, endj)
                if direction  < 4 : oppsiteDirection = direction + 4
                if direction >= 4 : oppsiteDirection = direction - 4

                strPos = strx + strObj.offset[direction][0], \
                         stry + strObj.offset[direction][1]
                endPos = endx + desObj.offset[oppsiteDirection][0], \
                         endy + desObj.offset[oppsiteDirection][1]
                wireDrawingObjs.append(WireDrawingObj('w', strPos, endPos))
    return wireDrawingObjs
def make_textDrawingObjs(circuitboard) :
    textDrawingObjs = []
    Ai = circuitboard.elemIDArray
    Ae = circuitboard.elemArray
    Nv = circuitboard.Nv
    Nh = circuitboard.Nh
    def to_mathExpr(rawStr) :
        mathExpr = ''
        def process_escapeSequence(s) :
            # !i --> mathit, !r --> mathrm, !b --> mathbf.
            # !s --> mathrm + mathsf. !p{A} --> \phase{A^{\circ}}
            n = 1
            while n > 0:
                s, n = re.subn(r'!i\{(.*?)\}', r'\\mathit{\1}', s)
                s, n = re.subn(r'!r\{(.*?)\}', r'\\mathrm{\1}', s)
                s, n = re.subn(r'!s\{(.*?)\}', r'\\mathrm{\\mathsf{\1}}', s)
                s, n = re.subn(r'!b\{(.*?)\}', r'\\mathbf{\1}', s)
                s, n = re.subn(r'!p\{(.*?)\}', r'∠\\mathrm{\\mathsf{\1}}^{\\circ}', s)
            return s
        if '!' in rawStr :
            # !0{A} make what's inside as raw string.
            if bool(re.search(r"!0\{.*\}", rawStr)) :
                mathExpr = re.sub(r'!0\{(.*?)\}|\{(.*?)\}', r'\1\2', rawStr)
            else :
                mathExpr = '$' + process_escapeSequence(rawStr) + '$'
        else :
            mathExpr = '$' + rawStr + '$'
        # containsSubOrSup = bool(re.search(r"\\mathsf\{.*_.*\}", mathExpr)) or\
        # bool(re.search(r"\\mathsf\{.*\^.*\}", mathExpr))
        # if containsSubOrSup:
        #     raise Exception(r'no subscript and superscript is allowed within \mathsf{}')
        return mathExpr
    def vmoveModification(elemCode, direction) :
        isUD = bool( direction in ('U', 'D') )
        isLR = bool( direction in ('L', 'R') )
        isDiag = (not isUD) and (not isLR) 

        scalar = 1
        if elemCode in ('m', 'b', 'n') :
            scalar = 0
        if elemCode in ('A', 'a') and isLR :
            scalar = 0.6
        if elemCode in ('A', 'a') and isUD :
            scalar = 0.3
        if elemCode in ('A', 'a') and isDiag :
            scalar = 0.6
        if elemCode in ('R', 'L') and isUD :
            scalar = 0.4
        if elemCode == 'C'        and isUD :
            scalar = 0.7
        if elemCode in ('i', 'v', 'I', 'V') and isLR :
            scalar = 1.5
        if elemCode in ('i', 'v') and isUD :
            scalar = 1.2
        if elemCode in ('I', 'V') and isUD :
            scalar = 1.0
        if elemCode in ('i', 'v', 'I', 'V') and isDiag :
            scalar = 1.4
        return scalar
    
    for i in range(Nv):
        for j in range(Nh) :
            if circuitboard.haveElem(i, j) :
                elem = Ae[i, j]
                #### value
                if hasattr(elem, 'value') and elem.value != None and elem.value != '' :
                    rawtext = elem.value
                    # The default setting for values of R L C V I : 
                    # 1. are smooth font.
                    # 2. imaginary number j will be mathit.
                    if '!' not in rawtext and Ai[i, j][0] in ('RLCVI') \
                    and '_' not in rawtext :
                        text = '$\\mathrm{\\mathsf{'+ rawtext + '}}$'
                        text = text.replace('j', '\\mathit{j}\\;')
                        text = text.replace('Ω', '\\;Ω')
                        # due to matplotlib text box error, insert a space infront of 
                        # mathit font 'j' to make it display correctly.
                        text = ' ' + text + ' '
                    else : 
                        text = to_mathExpr(rawtext) 
                    if elem.valuePos == 'RHS' : vmove = 1
                    if elem.valuePos == 'LHS' : vmove = -1
                    # for text attach to object without direction, it's set to be U.
                    direction = elem.direction if hasattr(elem, 'direction') else 'U'
                    vmove *= vmoveModification(elem.elemCode, direction)
                    # position adjustments
                    vmove += elem.valueMove[0]
                    pmove  = elem.valueMove[1]
                    textDrawingObj = TextDrawingObj(text, i, j, vmove, pmove, direction)
                    textDrawingObjs.append( textDrawingObj )
                #### pm with format : sign1, sign2, text
                if hasattr(elem, 'pm') and elem.pm != None and Ae[i, j].pm[1] in ('+', '-') :
                    sign1  = '$' + elem.pm[0] + '$'
                    sign2  = '$' + elem.pm[1] + '$'
                    text   = to_mathExpr(elem.pm[2])
                    if elem.pmPos == 'RHS' : vmove = 1
                    if elem.pmPos == 'LHS' : vmove = -1
                    vmove = vmove * vmoveModification(elem.elemCode, elem.direction)
                    # position adjustments
                    vmove += elem.pmMove[0]
                    pmove  = elem.pmMove[1]
                    sign1Obj = TextDrawingObj(sign1, i, j, vmove, +1+pmove+elem.pmSep, elem.direction)
                    sign2Obj = TextDrawingObj(sign2, i, j, vmove, -1+pmove-elem.pmSep, elem.direction)
                    textObj  = TextDrawingObj( text, i, j, vmove,  pmove, elem.direction)
                    textDrawingObjs.append(sign1Obj)
                    textDrawingObjs.append(sign2Obj)
                    textDrawingObjs.append(textObj)
                #### pm with format : local sign, destination, text
                if hasattr(elem, 'pm') and elem.pm != None and elem.pm[1] not in ('+', '-') :
                    strSign = elem.pm[0]
                    if strSign == '+' : desSign = '-'
                    if strSign == '-' : desSign = '+'
                    strSign =  '$' + strSign + '$'
                    desSign = '$' + desSign   + '$'
                    text    =  to_mathExpr(elem.pm[2])

                    desObjName = Ae[i, j].pm[1]
                    desi, desj = circuitboard.find_elemPos(desObjName)
                    midPoint   = (i+desi) / 2 , (j+desj) / 2
                    pmove = 0
                    if i == desi :   # UD
                        refDirc = 'U'
                        if j > desj :    vmove = -1
                        else :           vmove = 1
                    elif j == desj : # LR
                        refDirc = 'R'
                        if i > desi :    vmove = -1
                        else :           vmove = 1
                    else :           # diagonal
                        refDirc = 'R'
                        if j > desj :    vmove = -1
                        else :           vmove = 1 
                        if i > desi :    pmove = -1
                        else :           pmove = 1
                    vmove = vmove * vmoveModification(elem.elemCode, refDirc)
                    # position adjustment
                    vmove += elem.pmMove[1]
                    pmove += elem.pmMove[0]
                    strSignObj = TextDrawingObj(strSign,    i,    j,  vmove,  +pmove-elem.pmSep, refDirc)
                    desSignObj = TextDrawingObj(desSign, desi, desj, -vmove,  +pmove+elem.pmSep, refDirc)
                    textObj    = TextDrawingObj( text,  *midPoint,    0,       pmove, refDirc)
                    textDrawingObjs.append(strSignObj)
                    textDrawingObjs.append(desSignObj)
                    textDrawingObjs.append(textObj)

    return textDrawingObjs
def make_elemSvgCodes(centeredDrawingObjs) :
    elemSvgCodes = []
    for obj in centeredDrawingObjs :
        posx, posy = ij2xy(obj.i, obj.j)
        vmove, pmove = obj.move[0], obj.move[1]
        #### temparary approach ####
        if obj.elemCode == 'A' : # mid arrow
            elemSvgCode = 'e', obj.elemCode, posx+vmove, posy+pmove, 0, 0, obj.svgDirc
        else :
            elemSvgCode = 'e', obj.elemCode, posx, posy, vmove, pmove, obj.svgDirc
        #### temparary approach ####
        elemSvgCodes.append(elemSvgCode)
    return elemSvgCodes
def make_wireSvgCodes(wireDrawingObjs) :
    wireSvgCodes = set() # use set to avoid duplicated wire drawing.
    for obj in wireDrawingObjs :
        strPos, endPos = list(obj.strPos), list(obj.endPos)
        # make wires draw from smaller x to larger x
        pos1, pos2 = sorted([strPos, endPos], key = lambda x : x[0])
        # if it was vertical or horizontal wire, make sure it comes
        # form up to down, left to right.
        if (pos1[0] == pos2[0]) or (pos1[1] == pos2[1]) :
            pos1[0], pos2[0] = tuple(sorted( [pos1[0], pos2[0]] ) )
            pos1[1], pos2[1] = tuple(sorted( [pos1[1], pos2[1]] ) )
        wireSvgCode = 'e', 'w', pos1[0], pos2[0], pos1[1], pos2[1]
        wireSvgCodes.add(wireSvgCode)
    return list(wireSvgCodes)
def make_textSvgCodes(textDrawingObjs) :
    textSvgCodes = []
    for obj in textDrawingObjs :
        refx, refy = ij2xy(obj.refi, obj.refj)
        textSvgCode = 't', obj.text, refx, refy, obj.vmove, obj.pmove, obj.refSvgDirc
        textSvgCodes.append(textSvgCode)
    return textSvgCodes
def remove_anchor(elemSvgCodes) :
    elemSvgCodes[:] = [c for c in elemSvgCodes if 'anchor' not in c]
def remove_empty(elemSvgCodes) :
    elemSvgCodes[:] = [c for c in elemSvgCodes if 'empty' not in c]


def to_svgCodes(circuitboard, * ,remove_anchors = False,  blockWidth = 6) :
    global blockWidth_
    try :
        float(blockWidth)
    except ValueError :
        raise ValueError(f'{blockWidth} is not a numerical value') from None
    if blockWidth < 2 or blockWidth > 14 :
        raise ValueError('block width must in between 2~14')
    blockWidth_ = float(blockWidth)
    centeredDrawingObjs, sudoCenteredDrawingObjs = make_centeredDrawingObjs(circuitboard)
    WireDrawingObjs = make_WireDrawingObjs(circuitboard, centeredDrawingObjs)
    WireDrawingObjs += sudoCenteredDrawingObjs
    textDrawingObjs = make_textDrawingObjs(circuitboard)
    elemSvgCodes = make_elemSvgCodes(centeredDrawingObjs)
    wireSvgCodes = make_wireSvgCodes(WireDrawingObjs)
    textSvgCodes = make_textSvgCodes(textDrawingObjs)
    if remove_anchors : remove_anchor(elemSvgCodes)
    remove_empty(elemSvgCodes)
    svgCodes = elemSvgCodes + wireSvgCodes + textSvgCodes
    return svgCodes