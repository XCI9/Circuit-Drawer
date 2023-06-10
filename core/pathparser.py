import re


class Action:
    def __init__(self, parameters, last_actions=[]):
        if len(last_actions) == 0:
            self.start_point = (0, 0)
        else:
            self.start_point = last_actions[-1].getEndPoint()
        self.type = parameters[0]
        self.parameters = parameters[1:]
        self.parameters = list(map(float, self.parameters))

        # convert relative coords to absolute
        if self.type.islower():
            if self.type == 'h' :
                self.parameters[0] += self.start_point[0]
            elif self.type == 'v' :
                self.parameters[0] += self.start_point[1]
            elif self.type == 'a' :
                self.parameters[5] += self.start_point[0]
                self.parameters[6] += self.start_point[1]
            elif self.type != 'z' :
                for i in range(0, len(self.parameters)-1, 2):
                    self.parameters[i] += self.start_point[0]
                    self.parameters[i+1] += self.start_point[1]

            self.type = self.type.upper()

        if self.type == 'H' :
            self.end_point = (self.parameters[0], self.start_point[1])
        elif self.type == 'V' :
            self.end_point = (self.start_point[0], self.parameters[0])
        elif self.type == 'Z' :
            # find last M or Z
            for action in reversed(last_actions):
                if action.type in 'MZ':
                    self.end_point = action.getStartPoint()
        else:
            self.end_point = (self.parameters[-2], self.parameters[-1])

        self.optimizeVerticalHorizontalLine()

    def getEndPoint(self):
        return self.end_point

    def getStartPoint(self):
        return self.start_point

    def optimizeVerticalHorizontalLine(self):
        if self.type == 'L':
            # vertical line
            if self.start_point[0] == self.end_point[0]:
                self.type = 'V'
                del self.parameters[0]
            elif self.start_point[1] == self.end_point[1]:
                self.type = 'H'
                del self.parameters[1]

    def formatFloat(self, f):
        f = f'{f:.2f}'.rstrip('0').rstrip('.')
        if f.startswith('0.'):
            f = f[1:]
        elif f.startswith('-0.'):
            f = '-' + f[2:]
        return f

    def getRelativeStr(self):
        output = self.type.lower()

        if self.type == 'V':
            output += self.formatFloat(
                self.parameters[0] - self.start_point[1])
        elif self.type == 'H':
            output += self.formatFloat(
                self.parameters[0] - self.start_point[0])
        elif self.type == 'Z':
            pass
        elif self.type == 'A':
            output += self.formatFloat(self.parameters[0])
            output += self.formatFloat(self.parameters[1]) + ' '
            output += self.formatFloat(self.parameters[2]) + ' '
            output += self.formatFloat(self.parameters[3]) + ' '
            output += self.formatFloat(self.parameters[4]) + ' '
            output += self.formatFloat(
                self.parameters[5] - self.start_point[0]) + ' '
            output += self.formatFloat(
                self.parameters[6] - self.start_point[0]) + ' '
        else:
            for i in range(0, len(self.parameters)-1, 2):
                output += self.formatFloat(
                    self.parameters[i] - self.start_point[0]) + ' '
                output += self.formatFloat(
                    self.parameters[i+1] - self.start_point[1]) + ' '
            output = output.rstrip(' ')

        output = output.replace(' -', '-')
        return output

    def getAbsoluteStr(self):
        output = self.type

        for i in range(len(self.parameters)):
            output += self.formatFloat(self.parameters[i]) + ' '
        output = output.rstrip(' ')
        output = output.replace(' -', '-')

        return output

    def __str__(self):
        relativeCoordStr = self.getRelativeStr()
        absoluteCoordStr = self.getAbsoluteStr()

        if len(absoluteCoordStr) <= len(relativeCoordStr):
            return absoluteCoordStr
        else:
            return relativeCoordStr


def simplifyCmd(string):
    lastCmd = 'w'  # init with impossible cmd
    i = 0
    while i < len(string) - 1:
        if string[i+1] == '-':
            if string[i] == lastCmd \
                    or (string[i] == 'l' and lastCmd == 'm') \
                    or (string[i] == 'L' and lastCmd == 'M'):
                lastCmd = string[i]
                string = string[:i]+string[i+1:]
            elif string[i].isalpha():
                lastCmd = string[i]
        elif string[i].isalpha():
            lastCmd = string[i]
        i += 1
    return string


def pathparser(d):
    parameters = re.findall(
        r'[-+]?\d*\.?\d+(?:e[+-]?\d+)?|[A-Za-z]', d)

    actions = []
    i = 0
    while i < len(parameters):
        action = [parameters[i]]
        i += 1
        while i < len(parameters) and not parameters[i].isalpha():
            action.append(parameters[i])
            i += 1

        actions.append(action)

    i = 0
    while i < len(actions):
        type = actions[i][0]

        def split(coord_count, split_type):
            nonlocal i, actions
            coord_count += 1  # type parameter
            while len(actions[i]) > coord_count:
                actions.insert(i+1, [split_type] + actions[i][coord_count:])
                actions[i] = actions[i][:coord_count]
                i += 1
        if type in 'ML':
            split(2, 'L')
        elif type in 'ml':
            split(2, 'l')
        elif type in 'HhVv':
            split(1, type)
        elif type in 'Cc':
            split(6, type)
        elif type in 'SsQq':
            split(4, type)
        elif type in 'Tt':
            split(2, type)
        elif type in 'Aa':
            split(7, type)

        i += 1

    # first m -> M
    if len(actions) > 0 and actions[0][0] == 'm':
        actions[0][0] = 'M'

    action_object_list = []
    for action in actions:
        obj = Action(action, action_object_list)
        action_object_list.append(obj)

    output = ""
    for obj in action_object_list:
        output += str(obj)

    output = simplifyCmd(output)
    return output


if __name__ == '__main__':
    print(pathparser(input()))
