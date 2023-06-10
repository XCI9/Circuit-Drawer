if __name__ == '__main__':
    print('Initializing ...')
from core.svgkit import svgGenerator
import sys
import pathlib
from core.convert import to_svgCodes
from core.construct import CircuitBoard, to_txt
from core.postprocessing import postprocessing
from tqdm import tqdm
import argparse
print_detail = False


class Path_parser:
    svg_template_path = pathlib.Path(__file__).parent / 'core/template_v2.svg'

    def __init__(self, path):
        self.raw_path = path
        pathobj = pathlib.Path(self.raw_path)
        self.path = pathobj.as_posix()
        self.exists = pathobj.exists()
        self.is_file = None
        self.dirname = None
        self.filename = None
        self.name = None
        self.ext = None
        self.parts = None
        self.dirlist = None
        if self.exists:
            self.is_file = pathobj.is_file()
            self.parts = pathobj.parts
            if self.is_file:
                self.dirname = pathobj.parent.as_posix()
                self.filename = pathobj.name
                self.name = pathobj.stem
                self.ext = pathobj.suffix
            else:
                self.dirname = pathobj.as_posix()
                self.dirlist = list(
                    map(lambda x: x.as_posix(), pathobj.iterdir()))


def build(circuit, setting, log: tqdm, autoNode=True, blockWidth=6,
          svg_filepath='output.svg', name='circuit'):
    if print_detail:
        log.write('Creating circuit board ...')
    board = CircuitBoard(circuit, setting, autoNode=autoNode)
    if print_detail:
        log.write('Converting to SVG protocal ...')
    svgCodes = to_svgCodes(board, blockWidth=blockWidth)
    if print_detail:
        log.write('Drawing SVG ...')
    svgGenObj = svgGenerator(svgCodes, {'unit': 8})
    svgGenObj.generate(svg_filepath)
    if print_detail:
        log.write('optimizing SVG file size ...')
    postprocessing(svg_filepath)


def dirParser(pathObj: Path_parser):
    txtfiles = []
    for dir_ in pathObj.dirlist:
        pathObj_ = Path_parser(dir_)
        if pathObj_.is_file:
            if pathObj_.ext.lower() == '.txt':
                txtfiles.append(pathObj_.path)
            else:
                print('>>> Error : Accept txt file only.')
        else:
            txtfiles += dirParser(pathObj_)
    return txtfiles


def txtParser(pathObj: Path_parser):
    if pathObj.ext.lower() == '.txt':
        return pathObj.path
    else:
        print('>>> Error : Accept txt file only.')


def pathParser(pathObj: Path_parser):
    txtfiles = []
    if pathObj.exists:
        if pathObj.is_file:
            txtfiles.append(txtParser(pathObj))
        else:
            txtfiles += dirParser(pathObj)
    else:
        print('>>> Error : Path does not exist.')

    return txtfiles


def main():
    # if len(sys.argv) < 2:
    #    print('>>> Error : Please provide txt files or folders with txt files.')
    #    input('')
    #    return

    args = argparse.ArgumentParser()
    args.add_argument("files", type=str, nargs='+')
    args.add_argument("-o", "--output", type=str,
                      default="", help="the output folder, empty if output to input folder")
    args.add_argument("-l", "--log", type=bool, default=False,
                      help="Output more details log.")
    args = args.parse_args()
    args = vars(args)

    print_detail = args['log']
    paths = args['files']
    txtfiles = []
    for path in paths:
        pathObj = Path_parser(path)

        txtfiles += pathParser(pathObj)

    # creat SVG ouput folder is there is not one
    output_folder = args['output']
    output_folder_path = pathlib.Path(output_folder)
    if not output_folder_path.exists():
        output_folder_path.mkdir()
    # start drawing svgs
    count = 0
    for txtfile in (pbar := tqdm(txtfiles)):
        fileObj = Path_parser(txtfile)
        pbar.set_description(fileObj.name)
        if print_detail:
            pbar.write(f'Open file : {fileObj.path}')

        if args['output'] == "":
            svg_dir = pathlib.Path(Path_parser(
                sys.argv[0]).dirname, fileObj.dirname)
        else:
            svg_dir = pathlib.Path(Path_parser(
                sys.argv[0]).dirname, args['output'])
        svg_dir.mkdir(exist_ok=True)
        svg_filepath = svg_dir.joinpath(f'{fileObj.name}.svg').as_posix()
        if print_detail:
            pbar.write(f'SVG file path : {svg_filepath}')
        with open(fileObj.path, 'r') as f:
            contents = f.read()

        if print_detail:
            pbar.write('Evaluating variables ...')
        exec(contents, globals())
        circuit = globals()['circuit']
        setting = globals()['setting']
        autoNode = globals()['autoNode']
        blockWidth = globals()['blockWidth']
        build(circuit, setting, pbar, autoNode,
              blockWidth, svg_filepath, fileObj.name)
        count += 1
        pbar.write('>>> ' + fileObj.name + ' is drawn.')

    if count < 2:
        print('>>> The svg figure is drawn.')
    if count >= 2:
        print(f'>>> {count} svg figures are drawn.')
    input('')


if __name__ == '__main__':
    main()
