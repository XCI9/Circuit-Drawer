# import numpy as np
# import pandas as pd
# import sympy as sym
# import re
import pathlib
import xml.etree.ElementTree as ET
import matplotlib as mpl
from matplotlib import mathtext, font_manager
from io import BytesIO
from typing import Union

def text2svg(s, font):
    bio = BytesIO()
    with mpl.rc_context({'savefig.transparent': True}):
        mathtext.math_to_image(s, bio, prop=font, format='svg')
    root = ET.parse(BytesIO(bio.getvalue())).getroot()
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
    # ET.register_namespace('rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    # ET.register_namespace('cc', "http://creativecommons.org/ns#")
    # ET.register_namespace('dc', "http://purl.org/dc/elements/1.1/")
    # ET.register_namespace('resource', "http://purl.org/dc/dcmitype/StillImage")
    root.remove(root.find('metadata', {'': 'http://www.w3.org/2000/svg'}))
    root.attrib['width'] = root.attrib['width'][:-2]
    root.attrib['height'] = root.attrib['height'][:-2]
    return root


class svgGenerator:
    """Generate SVG from given svg_elements"""

    def __init__(self, elements: Union[list, tuple], setting: dict = None):
        """
        elements: A list or tuple. Every items must be follow the following formats
            ('e', {'w'/'W'}, x1, x2, y1, y2)  -- wire

            ({'t'/'e'}, {element/text}, x, y, c, d, direction)  -- element and text, without wire

            # direction: 
            #  3  2  1
            #   \ | /
            # 4--   --0
            #   / | \
            #  5  6  7
            # element: 
            #   'w': wire
            #   'W': wire(gray)
            #   'n': node(solid, black)
            #   'N': node(hollow, gray)
            #   'A': current direction
            #   'L': inductor
            #   'R': resistor
            #   'C': capacotor
            #   'V': independent voltage source
            #   'v': dependent voltage source
            #   'I': independent current source
            #   'i': dependent current source
            #   'b': block
            #   'g': ground
            #   'm': mesh current
            #   'a': element current(outside)
            #   'anchor': wire converge point

        setting: SVG setting
            Definition:
                o---------|---MVM---|---------o

                一個電路的基本單位是一個網格，每個基本的網格都是一個正方形，上圖是一個往個的其中一邊。
                定義每邊(一根線)有三個部分，左右是導線(denote: W)，中間是元件(包含導線填補)(denote: E)。
                注意：長度分為兩種形式，'a', 'c', 'd'是px；'unit'則是自定義的單位


            'a'  -- a*2 是實際E長度，a只能大於等於28，小於28時可能會出錯
            'c'  -- c位移的長度
            'd'  -- d位移的長度
            'scaler'  -- 
            'unit'  -- E的長度，預設是2，代表2單位
            'font'  -- set by "font_manager.FontProperties" class
        """


        svg_template_path = pathlib.Path(__file__).parent / 'template_v2.svg'
        # default setting
        self._setting = {
            'a': 29,
            'c': 29,
            'd': 29,
            'scaler': 1,
            'unit': 2,
            'font': font_manager.FontProperties(size=20, family='serif', math_fontfamily='stix'),
            'template' : svg_template_path
        }
        # svg elements setting
        self._svgID = {
            'L': "#inductor",
            'R': "#resistor",
            'C': "#capacitor",
            'V': "#ind_v",
            'v': "#d_v",
            'I': "#ind_c",
            'i': "#d_c",
            'g': "#ground",
            'a': "#current_dir",
            'm': "#mesh_current"
        }
        self._elemSizeP = {  # for padding
            'L': 26,
            'R': 21,
            'C': 4,
            'V': 24.5,
            'v': 29,
            'I': 24.5,
            'i': 29,
            'b_width': 21,
            'b_height': 19
        }
        # self._elemSizeP = {  # for padding
        #    'L': 26,
        #    'R': 21,
        #    'C': 3.5,
        #    'V': 24.5,
        #    'v': 29,
        #    'I': 24.5,
        #    'i': 29,
        #    'b_width': 21,
        #    'b_height': 19
        # }
        # self._elemSizeW = { # for padding c
        #     'L': 26,
        #     'R': 21,
        #     'C': 10.5,
        #     'V': 24.5,
        #     'v': 28,
        #     'I': 24.5,
        #     'i': 28,
        #     'b_width': 21,
        #     'b_height': 19
        # }
        # check input
        if not isinstance(elements, (tuple, list)):
            raise Exception("Input argument 'elements' is not tuple or list.")
        for i in elements:
            if len(i) == 6:
                if i[0] != 'e' or (i[1] not in {'w', 'W'}):
                    raise Exception(
                        f"Invalid: element format must be ('e', {{'w'/'W'}}, x1, x2, y1, y2), {i}")
                for j in range(2, 6):
                    if not isinstance(i[j], (int, float)):
                        raise Exception(
                            f"Invalid: x1, x2, y1, y2 must be int or float, {i}")
            elif len(i) == 7:
                if (i[0] not in {'t', 'e'}):
                    raise Exception(
                        f"Invalid: element type must be {{'t'/'e'}}, {i}")
                if i[0] == 'e' and (i[1] not in {'w', 'W', 'n', 'N', 'A', 'L', 'R', 'C', 'V', 'v', 'I', 'i', 'b', 'g', 'm', 'a', 'anchor'}):
                    raise Exception(f"Invalid: circuit element, {i}")
                for j in range(2, 6):
                    if not isinstance(i[j], (int, float)) or not isinstance(i[j], (int, float)):
                        raise Exception(
                            f"Invalid: Inside x, y, c, d must be int or float, {i}")
                if i[6] not in {0, 1, 2, 3, 4, 5, 6, 7}:
                    raise Exception(
                        f"Input elements's element error. Invalid: direction, {i}")
            else:
                raise Exception(
                    f"Input argument 'elements''s element format is invalid. Invalid: length, {i}")
        self.elements = elements

        self.settings(setting)

        # sort, wire first, then elements
        elements_w = []
        elements_else = []
        for elem in self.elements.copy():
            if elem[0] == 'e' and (elem[1] in {'w', 'W'}):
                for i in range(2, 6):
                    elem = list(elem)
                    elem[i] = elem[i]/(self._setting['unit'] / 2)
                elements_w.append(tuple(elem))
            else:
                elem = list(elem)
                elem[2] = elem[2]/(self._setting['unit'] / 2)
                elem[3] = elem[3]/(self._setting['unit'] / 2)
                elements_else.append(tuple(elem))
        self.elements.clear()
        self.elements.extend(elements_w)
        self.elements.extend(elements_else)

        self._desc = ""

    def settings(self, setting: dict = None):
        """return setting if no input. change setting if 'setting' given"""
        if setting is None:
            return self._setting
        if isinstance(setting, dict):
            if set(setting).issubset(self._setting):
                self._setting.update(setting)
            else:
                raise Exception(
                    f"settings is only available for {set(self._setting.keys())} keywords")
        else:
            raise Exception("setting must be dict")

    def description(self, desc: str = ""):
        """Add description in SVG file. (In 'desc' tag)
        return description if no input
        """
        if desc == '':
            return self._desc
        else:
            self._desc = str(desc)

    def generate(self, filename, debug=False):
        """Generate svg, and save as file.

        if debug==True : show text anchor

        """
        def patch(delta_a, delta_e, direction, xa, ya):
            maxX, maxY, minX, minY = 0, 0, 0, 0
            if direction in {0, 4}:
                dpath1 = f'M {xa+delta_e},{ya} {xa+delta_a},{ya}'
                dpath2 = f'M {xa-delta_e},{ya} {xa-delta_a},{ya}'
                maxX, minX = xa+delta_a, xa-delta_a
            elif direction in {1, 5}:
                delta_e /= 2**0.5
                dpath1 = f'M {xa+delta_e},{ya-delta_e} {xa+delta_a},{ya-delta_a}'
                dpath2 = f'M {xa-delta_e},{ya+delta_e} {xa-delta_a},{ya+delta_a}'
                maxX, minX = xa+delta_a, xa-delta_a
                maxY, minY = ya+delta_a, ya-delta_a
            elif direction in {2, 6}:
                dpath1 = f'M {xa},{ya+delta_e} {xa},{ya+delta_a}'
                dpath2 = f'M {xa},{ya-delta_e} {xa},{ya-delta_a}'
                maxY, minY = ya+delta_a, ya-delta_a
            else:
                delta_e /= 2**0.5
                dpath1 = f'M {xa+delta_e},{ya+delta_e} {xa+delta_a},{ya+delta_a}'
                dpath2 = f'M {xa-delta_e},{ya-delta_e} {xa-delta_a},{ya-delta_a}'
                maxX, minX = xa+delta_a, xa-delta_a
                maxY, minY = ya+delta_a, ya-delta_a
            svg_Element1 = ET.Element(
                'path', {"d": dpath1, "stroke": "black", "stroke-width": "3.0"})
            svg_Element2 = ET.Element(
                'path', {"d": dpath2, "stroke": "black", "stroke-width": "3.0"})
            root.append(svg_Element1)
            root.append(svg_Element2)
            return maxX, maxY, minX, minY

        def translate_cd(x, y, dc, dd, direction):
            delta_c = c * dc
            delta_d = d * dd
            if direction in {0, 4}:
                X = x + delta_d
                Y = y + delta_c
            elif direction in {1, 5}:
                X = x + (delta_c - delta_d)/(2**0.5)
                Y = y + (delta_c + delta_d)/(2**0.5)
            elif direction in {2, 6}:
                X = x + delta_c
                Y = y + delta_d
            else:
                X = x + (delta_c + delta_d)/(2**0.5)
                Y = y + (-delta_c + delta_d)/(2**0.5)
            return X, Y

        def extremeX(maxX, minX, *val):
            maxX = max(maxX, *val)
            minX = min(minX, *val)
            return maxX, minX

        def extremeY(maxY, minY, *val):
            maxY = max(maxY, *val)
            minY = min(minY, *val)
            return maxY, minY

        a = self._setting['a']
        c = self._setting['c']
        d = self._setting['d']
        root = ET.parse(self._setting['template']).getroot()
        maxX, maxY = 0, 0
        minX, minY = 0, 0

        for elem in self.elements:
            if elem[0] == 'e':  # element
                circuit_elem = elem[1]
                if circuit_elem in {'w', 'W'}:
                    x1, x2, y1, y2 = elem[2:]
                    x1 *= a
                    x2 *= a
                    y1 *= a
                    y2 *= a
                    dpath = f'M {x1},{y1} {x2},{y2}'
                    color = {'w': "black", 'W': "#afb0b4"}[circuit_elem]
                    svg_Element = ET.Element(
                        'path', {"d": dpath, "stroke": color, "stroke-width": "3.0"})
                    root.append(svg_Element)
                    maxX, minX = extremeX(maxX, minX, x1+3, x1-3, x2+3, x2-3)
                    maxY, minY = extremeY(maxY, minY, y1+3, y1-3, y2+3, y2-3)
                elif circuit_elem in {'n', 'N'}:
                    x, y = elem[2:4]
                    xa = x * a
                    ya = y * a
                    if circuit_elem == 'n':
                        svg_Element = ET.Element('circle', {"cx": str(xa), "cy": str(
                            ya), "r": "4.5", "stroke": "black", "stroke-width": "1", "fill": "black"})
                    else:  # 'N'
                        svg_Element = ET.Element('circle', {"cx": str(xa), "cy": str(
                            ya), "r": "6", "stroke": "black", "stroke-width": "3", "fill": "white"})
                    root.append(svg_Element)
                    maxX, minX = extremeX(maxX, minX, xa+7.5, xa-7.5)
                    maxY, minY = extremeY(maxY, minY, ya+7.5, ya-7.5)
                elif circuit_elem == 'b':
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svg_Element = ET.Element('rect', {"x": str(xa-40/2), "y": str(
                        ya-35/2), "width": "40", "height": "35", "stroke-width": "3", "stroke": "#000000", "fill": "none"})
                    root.append(svg_Element)
                    if direction in {0, 4}:
                        size = self._elemSizeP['b_width']
                    elif direction in {2, 6}:
                        size = self._elemSizeP['b_height']
                    else:  # not define
                        size = self._elemSizeP['b_width']
                        print('Warning: box can not place at diagonal.')
                    maxX0, maxY0, minX0, minY0 = patch(
                        a, size, direction, xa, ya)
                    maxX, minX = extremeX(
                        maxX, minX, xa+22, xa-22, maxX0, minX0)
                    maxY, minY = extremeY(
                        maxY, minY, ya+20, ya-20, maxY0, minY0)
                elif circuit_elem == 'A':
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    angle = -direction * 45
                    svg_Element = ET.Element(
                        'g', {"transform": f"translate({xa},{ya}) rotate({angle})"})
                    svg_Element.append(ET.Element('polygon', {
                                       "points": "6,0 -6,4 -6,-4", "style": "fill:black;stroke:black;stroke-width:1"}))
                    root.append(svg_Element)
                    maxX, minX = extremeX(maxX, minX, xa+10, xa-10)
                    maxY, minY = extremeY(maxY, minY, ya+10, ya-10)
                elif circuit_elem == 'a':
                    x, y, dc, dd = elem[2:6]
                    direction = elem[6]
                    svgId = self._svgID['a']
                    angle = -direction * 45
                    x_tot, y_tot = translate_cd(x*a, y*a, dc, dd, direction)
                    transform = f'rotate({angle},{x_tot},{y_tot})'
                    svg_Element = ET.Element('use', {"href": svgId, "x": str(
                        x_tot), "y": str(y_tot), "transform": transform})
                    root.append(svg_Element)
                    if direction in {0, 4}:
                        maxX, minX = extremeX(maxX, minX, x_tot+34, x_tot-34)
                        maxY, minY = extremeY(maxY, minY, y_tot+5, y_tot-5)
                    elif direction in {2, 6}:
                        maxX, minX = extremeX(maxX, minX, x_tot+5, x_tot-5)
                        maxY, minY = extremeY(maxY, minY, y_tot+34, y_tot-34)
                    else:
                        maxX, minX = extremeX(maxX, minX, x_tot+25, x_tot-25)
                        maxY, minY = extremeY(maxY, minY, y_tot+25, y_tot-25)
                elif circuit_elem in {'L', 'R', 'C'}:
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svgId = self._svgID[circuit_elem]
                    angle = -direction * 45
                    transform = f'rotate({angle},{xa},{ya})'
                    svg_Element = ET.Element('use', {"href": svgId, "x": str(
                        xa), "y": str(ya), "transform": transform})
                    root.append(svg_Element)
                    maxX0, maxY0, minX0, minY0 = patch(
                        a, self._elemSizeP[circuit_elem], direction, xa, ya)
                    maxX, minX = extremeX(maxX, minX, maxX0, minX0)
                    maxY, minY = extremeY(maxY, minY, maxY0, minY0)
                    if direction in {0, 4}:
                        maxY, minY = extremeY(maxY, minY, ya+30, ya-30)
                    elif direction in {2, 6}:
                        maxX, minX = extremeX(maxX, minX, xa+30, xa-30)
                elif circuit_elem in {'V', 'v', 'I', 'i'}:
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svgId = self._svgID[circuit_elem]
                    angle = -direction * 45 + 90
                    transform = f'rotate({angle},{xa},{ya})'
                    svg_Element = ET.Element('use', {"href": svgId, "x": str(
                        xa), "y": str(ya), "transform": transform})
                    root.append(svg_Element)
                    maxX0, maxY0, minX0, minY0 = patch(
                        a, self._elemSizeP[circuit_elem], direction, xa, ya)
                    maxX, minX = extremeX(maxX, minX, maxX0, minX0)
                    maxY, minY = extremeY(maxY, minY, maxY0, minY0)
                    if direction in {0, 4}:
                        maxY, minY = extremeY(maxY, minY, ya+30, ya-30)
                    elif direction in {2, 6}:
                        maxX, minX = extremeX(maxX, minX, xa+30, xa-30)
                elif circuit_elem == 'g':
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svgId = self._svgID['g']
                    angle = -direction * 45 + 270
                    transform = f'rotate({angle},{xa},{ya})'
                    svg_Element = ET.Element('use', {"href": svgId, "x": str(
                        xa), "y": str(ya), "transform": transform})
                    root.append(svg_Element)
                    if direction == 0:
                        maxX, minX = extremeX(maxX, minX, xa, xa+32)
                        maxY, minY = extremeY(maxY, minY, ya+10, ya-10)
                    elif direction == 1:
                        maxX, minX = extremeX(maxX, minX, xa, xa+32)
                        maxY, minY = extremeY(maxY, minY, ya, ya-32)
                    elif direction == 2:
                        maxX, minX = extremeX(maxX, minX, xa+10, xa-10)
                        maxY, minY = extremeY(maxY, minY, ya, ya-32)
                    elif direction == 3:
                        maxX, minX = extremeX(maxX, minX, xa, xa-32)
                        maxY, minY = extremeY(maxY, minY, ya, ya-32)
                    elif direction == 4:
                        maxX, minX = extremeX(maxX, minX, xa, xa-32)
                        maxY, minY = extremeY(maxY, minY, ya+10, ya-10)
                    elif direction == 5:
                        maxX, minX = extremeX(maxX, minX, xa, xa-32)
                        maxY, minY = extremeY(maxY, minY, ya, ya+32)
                    elif direction == 6:
                        maxX, minX = extremeX(maxX, minX, xa+10, xa-10)
                        maxY, minY = extremeY(maxY, minY, ya, ya+32)
                    else :
                        maxX, minX = extremeX(maxX, minX, xa, xa+32)
                        maxY, minY = extremeY(maxY, minY, ya, ya+32)
                elif circuit_elem == 'm' :
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svgId = self._svgID['m']
                    if direction == 4 :
                        transform = f"scale(-1,1) translate({-xa*2},0)"
                        svg_Element = ET.Element('use', {"href": svgId, "x": str(
                            xa), "y": str(ya), "transform": transform})
                    else:
                        svg_Element = ET.Element(
                            'use', {"href": svgId, "x": str(xa), "y": str(ya)})
                    root.append(svg_Element)
                    maxX, minX = extremeX(maxX, minX, xa+69, xa-69)
                    maxY, minY = extremeY(maxY, minY, ya+69, ya-69)
                elif circuit_elem == 'anchor':
                    x, y = elem[2:4]
                    direction = elem[6]
                    xa = x * a
                    ya = y * a
                    svg_Element = ET.Element('circle', {"cx": str(
                        xa), "cy": str(ya), "r": "1.5", "fill": "black"})
                    root.append(svg_Element)
                else:  # not define
                    pass
            else:  # text
                text, x, y, dc, dd, direction = elem[1:]
                str_elem = text2svg(text, self._setting['font'])
                str_elem_attr = str_elem.attrib
                size_x, size_y = float(str_elem_attr['width']), float(
                    str_elem_attr['height'])
                x_tot, y_tot = translate_cd(x*a, y*a, dc, dd, direction)
                X = x_tot - size_x/2
                Y = y_tot - size_y/2
                # translate if text with a vertical elements
                if direction in {2, 6}:
                    if dc > 0:
                        X += size_x/2
                    if dc < 0:
                        X -= size_x/2
                # print(X, Y, x_tot, y_tot, size_x, size_y)
                transform = f"translate({X},{Y})"
                # transform = ""
                svg_Element = ET.Element('g', {"transform": transform})
                svg_Element.append(str_elem)
                root.append(svg_Element)
                maxX, minX = extremeX(maxX, minX, X, X+size_x)
                maxY, minY = extremeY(maxY, minY, Y, Y+size_y)
                if debug:
                    svg_Element = ET.Element('circle', {"cx": str(x_tot), "cy": str(
                        y_tot), "r": "2", "stroke": "black", "stroke-width": "1", "fill": "red"})
                    root.append(svg_Element)

        root[0].text = self._desc
        # root.set("width", str(maxX-minX+a))
        # root.set("height", str(maxY-minY+a))
        root.set("viewBox", f"{minX-2} {minY-2} {maxX-minX+10} {maxY-minY+2}")
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        ET.ElementTree(root).write(filename)
