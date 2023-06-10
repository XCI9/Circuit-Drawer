import re
from lxml import etree
from copy import deepcopy
import numpy as np
from core.pathparser import pathparser

namespace = '{http://www.w3.org/2000/svg}'


def formatFloat(f):
    return f'{f:.2f}'.rstrip('0').rstrip('.')


def postprocessing(filename='output.svg'):
    tree = etree.parse(filename)
    root = tree.getroot()
    defs = root.find(f'{namespace}defs')

    for child in root.findall(f'.//{namespace}g[@id="text_1"]/{namespace}g'):
        for path in child.findall(f'.//{namespace}path'):
            # move transform attribute in use tag to path tag and remove use tag
            uses = child.xpath(f'*[@*="#{path.attrib["id"]}"]')

            del path.attrib['id']

            for use in uses:
                if 'transform' in use.attrib:
                    transform = use.attrib['transform']
                else:
                    transform = f'translate(0)'

                child.remove(use)

                # move path out of defs
                g = etree.SubElement(child, f'{namespace}g', {
                                     'transform': transform})
                g.append(deepcopy(path))

        # remove defs
        d = child.find(f'{namespace}defs')
        child.remove(d)

        # move data output of svg and remove it
        removed = child.getparent().getparent().getparent()  # svg
        parent = removed.getparent()
        parent.remove(removed)
        parent.append(child)
        parent.attrib['id'] = 'pin'

    for child in root.findall(f'.//{namespace}defs/{namespace}style/..'):
        child.getparent().remove(child)

    # move path tag to top
    for path in root.findall(f'{namespace}path'):
        if 'stroke' in path.attrib and path.attrib['stroke'] == 'black':
            del path.attrib['stroke']
        if 'stroke-width' in path.attrib and path.attrib['stroke-width'] == '3.0':
            del path.attrib['stroke-width']

        root.remove(path)
        root[:0] = [path]

    # move style to top
    style = root.find(f'{namespace}style')
    root.remove(style)
    #root[:0] = [style]

    # remove desc
    for desc in root.findall(f'{namespace}desc'):
        desc.getparent().remove(desc)

    # edge circle
    for circle in root.findall(f'{namespace}circle[@r="1.5"]'):
        # use = etree.Element('use', {'href': '#round',
        #                             'x': f'{circle.attrib["cx"]}',
        #                             'y': f'{circle.attrib["cy"]}'})
        circle.getparent().remove(circle)
        # root.append(use)

    # hollow node
    for circle in root.findall(f'{namespace}circle[@fill="white"]'):
        use = etree.Element('use', {'href': '#ring',
                                    'x': f'{circle.attrib["cx"]}',
                                    'y': f'{circle.attrib["cy"]}'})
        circle.getparent().remove(circle)
        root.append(use)

    # filled node
    for circle in root.findall(f'{namespace}circle[@fill="black"]'):
        use = etree.Element('use', {'href': '#node',
                                    'x': f'{circle.attrib["cx"]}',
                                    'y': f'{circle.attrib["cy"]}'})
        circle.getparent().remove(circle)
        root.append(use)

    # arrow
    for polygon in root.findall(f'{namespace}g/{namespace}polygon[@points="6,0 -6,4 -6,-4"]'):
        parent = polygon.getparent()
        transform = parent.attrib['transform']
        x, y = re.search(
            r'translate\(([0-9.-]*),([0-9.-]*)\)', transform).groups()
        deg = float(re.search(r'rotate\(([0-9.-]*)\)', transform).groups()[0])
        if deg < 0:
            deg += 360

        if abs(deg) > 0.01:
            use = etree.Element('use', {'href': '#arrow',
                                        'x': f'{x}',
                                        'y': f'{y}',
                                        'transform': f'rotate({deg},{x},{y})'})
        else:
            use = etree.Element('use', {'href': '#arrow',
                                        'x': f'{x}',
                                        'y': f'{y}'})
        parent.getparent().remove(parent)
        root.append(use)

    # box
    for rect in root.findall(f'{namespace}rect[@width="40"][@height="35"]'):
        use = etree.Element('use', {'href': '#box',
                                    'x': f'{rect.attrib["x"]}',
                                    'y': f'{rect.attrib["y"]}'})
        rect.getparent().remove(rect)
        root.append(use)

    def getTransform(string):
        def getCoord(target):
            if f'{target}(' in string:
                coords = string.split(f'{target}(')[1].split(')')[0]
                if ',' in coords:
                    s = coords.split(',')
                else:
                    s = coords.split(' ')
                if len(s) == 2:
                    return [float(s[0]), float(s[1])]
                elif target == 'scale':
                    return [float(s[0]), float(s[0])]
                else:
                    return [float(s[0]), 0.]
            else:
                return None

        return getCoord('translate'), getCoord('scale')

    new_g = etree.SubElement(
        defs, f'{namespace}g', {'id': 'txt'})
    # swap transform order, then merge trasnlate so that same transform can be simplify
    # g@transform[translate] > g@transform[translate(0 14)scale(0.2 -0.2)] > g@transform > path@transform[translate(??)scale(0.015625)]
    # to
    # g@transform[translate(0 14)scale(3125e-6 -3125e-6)] > g@transform[translate] > g@transform >path@transform[translate(??)]
    for mid_g in root.findall(f'{namespace}g[@id="pin"]/{namespace}g'):
        outer_g = mid_g.getparent()

        mid_translate, mid_scale = getTransform(mid_g.attrib['transform'])
        outer_translate, _ = getTransform(outer_g.attrib['transform'])

        mid_translate[0] *= 1/mid_scale[0]
        mid_translate[1] *= 1/mid_scale[1]

        outer_translate[0] *= 1/mid_scale[0]
        outer_translate[1] *= 1/mid_scale[1]

        # print(mid_g.attrib['transform'])
        outer_g.attrib['transform'] = re.search(
            r'scale\(.*\)', mid_g.attrib['transform']).group()
        mid_translate = [outer_translate[0] + mid_translate[0],
                         outer_translate[1] + mid_translate[1]]

        del outer_g.attrib['id']

        for inner_g in mid_g.getchildren():
            # remove @transform[scale(0.015625)]
            path = inner_g.getchildren()[0]
            transform = path.attrib['transform']
            path.attrib['transform'] = re.sub(r'scale\(.*\)', '', transform)

            inner_translate, inner_scale = getTransform(
                inner_g.attrib['transform'])

            translate_x = formatFloat(
                (inner_translate[0] + mid_translate[0])/0.015625)
            translate_y = formatFloat(
                (inner_translate[1] + mid_translate[1])/0.015625)

            inner_g.attrib['transform'] = f'translate({translate_x} {translate_y})'

            if inner_scale is not None:
                scale_x = formatFloat(inner_scale[0])
                scale_y = formatFloat(inner_scale[1])
                if scale_x == scale_y:
                    scale_y = ""
                path.attrib['transform'] += f'scale({scale_x} {scale_y})'
            if path.attrib['transform'] == "":
                del path.attrib['transform']

            new_g.append(inner_g)
        outer_g.attrib['id'] = 'old'

    for old_g in root.findall(f'.//{namespace}g[@id="old"]'):
        old_g.getparent().remove(old_g)

    # get all wire path
    wire_list = []
    for path in root.findall(f'{namespace}path'):
        path.getparent().remove(path)

        coord = path.attrib['d'].split('M')[1]
        if coord[0] == " ":
            coord = coord[1:]
        start, end = coord.split(' ')
        start_x, start_y, end_x, end_y = map(
            float, start.split(',')+end.split(','))
        wire_list.append(((start_x, start_y), (end_x, end_y)))

    # print(len(wire_list))

    # merge two wire if they are directly connect and have same direction
    current = 0
    while current < len(wire_list):
        def getSlope(point1, point2):
            if point1[0] - point2[0] == 0:
                return float('inf')
            return (point1[1]-point2[1]) / (point1[0]-point2[0])

        def getIntercept(slope, point):
            if slope == float('inf'):
                return point[0]
            # y = sx + b
            # b = y - sx
            return point[1] - slope*point[0]
        current_start, current_end = wire_list[current]
        current_slope = getSlope(current_start, current_end)  # dy/dx
        current_intercept = getIntercept(current_slope, current_start)
        new_wire = None
        for other in range(current+1, len(wire_list)):
            start, end = wire_list[other]
            slope = getSlope(start, end)  # dy/dx
            intercept = getIntercept(slope, start)

            if (current_slope == slope or abs(current_slope - slope) < 0.000001) and \
                    abs(current_intercept - intercept) < 0.000001:
                point_list = np.array([start, end, current_start, current_end])
                if slope == float('inf'):  # vertical, x same
                    sort_seq = np.argsort(point_list[:, 1], kind='stable')
                else:
                    sort_seq = np.argsort(point_list[:, 0], kind='stable')

                # lines with same end point should merge
                if sort_seq[0]+sort_seq[1] in [1, 5] and \
                        np.array_equal(point_list[sort_seq[1]], point_list[sort_seq[2]]):
                    sort_seq[1], sort_seq[2] = sort_seq[2], sort_seq[1]

                # two lines are not overlap
                if not sort_seq[0]+sort_seq[1] in [1, 5]:
                    new_wire = (point_list[sort_seq[0]],
                                point_list[sort_seq[3]])

            if new_wire is not None:
                del wire_list[other]
                break
        if new_wire is not None:
            wire_list[current] = new_wire
            continue
        current += 1
    # print(len(wire_list))
    new_wire_list = []
    for wire_coord in wire_list:
        start_x, start_y, end_x, end_y = [
            formatFloat(coord) for coord_pair in wire_coord for coord in coord_pair]
        new_wire = etree.Element(
            f'{namespace}path', {'d': f'M{start_x},{start_y} {end_x},{end_y}'})
        new_wire_list.append(new_wire)
    root[:0] = new_wire_list

    # remove same element, use `use` tag instead
    i = 0
    text_g = root.find(f'.//{namespace}g[@id="txt"]')
    text_container = etree.SubElement(
        root, 'g', {'transform': 'scale(3125e-6 -3125e-6)'})
    small_text_container = etree.SubElement(
        text_container, 'g', {'transform': 'scale(.7)'})
    for path in text_g.findall(f'.//{namespace}g/{namespace}path'):
        if 'd' in path.attrib:
            d = path.attrib['d']
        else:
            parent = path.getparent()
            parent.getparent().remove(parent)
            continue
        path.attrib['id'] = f'txt{i}'
        finds = text_g.findall(f'.//{namespace}g/{namespace}path[@d="{d}"]')
        if len(finds) == 0:
            continue
        for find in finds:
            parent = find.getparent()
            translate, scale = getTransform(parent.attrib['transform'])
            assert(scale is None, 'parent should not have scale')

            if 'transform' in find.attrib and \
                    find.attrib['transform'] == 'scale(0.7 )':
                x = formatFloat(translate[0]/0.7)
                y = formatFloat(translate[1]/0.7)
                use = etree.SubElement(small_text_container, f'{namespace}use',
                                       {'href': f'#txt{i}',
                                        'x': x, 'y': y})
            else:
                x = formatFloat(translate[0])
                y = formatFloat(translate[1])
                use = etree.SubElement(text_container, f'{namespace}use',
                                       {'href': f'#txt{i}',
                                        'x': x, 'y': y})
            text_g.remove(parent)

        if 'transform' in path.attrib and \
                path.attrib['transform'] == 'scale(0.7 )':
            del path.attrib['transform']
            #path.attrib['class'] = 's'
        text_g.append(path)
        i += 1

    if len(text_g.getchildren()) == 0:
        text_g.getparent().remove(text_g)

    # remove useless components
    for component in root.findall(f'.//{namespace}defs/'):
        id = component.attrib['id']
        if id != "txt" and len(root.findall(f'.//*[@href="#{id}"]')) == 0:
            component.getparent().remove(component)

    if len(small_text_container.getchildren()) == 0:
        text_container.remove(small_text_container)
    if len(text_container.getchildren()) == 0:
        root.remove(text_container)
    if len(defs.getchildren()) == 0:
        root.remove(defs)

    # set css style
    style.text = "*{fill:none;stroke:black}"
    if len(root.findall(f'{namespace}path')) > 0:
        style.text += "svg>path{stroke-linecap:round}"
    if len(root.findall(f'.//{namespace}path')) > 0:
        style.text += "path{stroke-width:3}"
    if text_g is not None and len(text_g.findall(f'.//{namespace}path')) > 0:
        style.text += "#txt path{fill:black;stroke-width:0}"
    if len(root.findall(f'.//*[@class="v"]')) > 0:
        style.text += ".v>*{stroke:#d12938;stroke-width:2.55}"
    if len(root.findall(f'.//*[@class="v"]/{namespace}path')) > 0:
        style.text += ".v>path{stroke-width:1.5;fill:#7b1d23}"
    if len(root.findall(f'.//*[@class="c"]')) > 0:
        style.text += ".c>*{stroke:#7b1d23;stroke-width:2.55}"
    if len(root.findall(f'.//*[@class="c"]/{namespace}path')) > 0:
        style.text += ".c>path{stroke-width:0;fill:#7b1d23}"
    if len(root.findall(f'.//*[@id="ground"]/{namespace}path')) > 0:
        style.text += "#ground>path{stroke-width:2.61;stroke-linecap:round}"
    current_dir = root.xpath(f'.//*[@id="current_dir"]')
    mesh_current = root.xpath(f'.//*[@id="mesh_current"]')
    if len(current_dir) > 0 and len(mesh_current) > 0:
        style.text += "#current_dir,#mesh_current{stroke:none;fill:#7b1d23}"
    elif len(current_dir) > 0:
        current_dir[0].attrib['style'] = "stroke:none;fill:#7b1d23"
    elif len(mesh_current) > 0:
        mesh_current[0].attrib['style'] = "stroke:none;fill:#7b1d23"

    root[:0] = [style]

    # d tag
    pathes = root.findall(f'.//{namespace}path')
    for path in root.findall(f'.//{namespace}path'):
        if 'd' in path.attrib:
            d = path.attrib['d']
            d = d.replace(',', ' ')
            d = pathparser(d)
            # remove space after alphabet
            d = re.sub(r'([a-zA-Z]) *', r'\1', d)
            # remove space before alphabet
            d = re.sub(r' *([a-zA-Z-])', r'\1', d)
            path.attrib['d'] = d

    # remove useless rotate
    for use in root.findall(f'.//{namespace}use') + root.findall(f'.//{namespace}g'):
        if 'transform' in use.attrib:
            transform = use.attrib['transform']
            if 'rotate' in transform:
                pretransform, rotate, posttransform = re.search(
                    r'(.*)rotate\((.*)\)(.*)', transform).groups()
                rotate += ','
                deg = float(rotate.split(',')[0])
                if deg == 0:
                    use.attrib['transform'] = pretransform + posttransform
                    if use.attrib['transform'] == "":
                        del use.attrib['transform']

    et = etree.ElementTree(root)
    string = etree.tostring(et).decode('utf8')
    string = string.replace('&gt;', '>')

    # strip space like char(' ', '\n')
    string = string.replace('\n', '')
    string = " ".join(string.split())  # multiple space to one
    string = re.sub(r'([{}();:,]) ', r'\1', string)
    string = re.sub(r' ([{}();:,"])', r'\1', string)
    string = string.replace(';}', '}')
    string = string.replace('> <', '><')

    # simply float
    output = ""
    isDecimal = False
    numberString = ""
    for char in string:
        if char.isdigit():
            numberString += char
        elif not isDecimal and char == '.':
            isDecimal = True
            numberString += char
        else:
            if len(numberString) > 0:
                # avoid w3 in url
                if numberString != '.' and not (numberString == '3.' and output[-1] == 'w'):
                    number = float(numberString)
                    number_str = f'{number:.6f}'.rstrip('0').rstrip('.')
                    if number_str.startswith("0."):
                        number_str = number_str[1:]
                    output += number_str

                    isDecimal = False
                    numberString = ""
                else:
                    output += numberString
            output += char
            numberString = ""

    if len(numberString) > 0:
        number = float(numberString)
        number_str = f'{number:.6f}'.rstrip('0').rstrip('.')
        if number_str.startswith("0."):
            number_str = number_str[1:]
        output += number_str

        isDecimal = False
        numberString = ""

    with open(filename, 'w') as outFile:
        outFile.write(output)
