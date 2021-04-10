#! /usr/bin/env python3
# Author: Izaak Neutelings (April 2021)
# Description: Script to test integer mapping.
import json, jsonschema
_highlight = False # global setting


def bold(string):
    """Highlight in bold."""
    return f"\033[1m{string}\033[0m" if _highlight else str(string)
    

def validate(fname,sname=f"../src/correctionlib/schemav{version}.json"):
    """Validate file according to JSON schema."""
    with open(fname,'r') as file:
        data = json.load(file)
    assert isinstance(data,dict), "Invalid schema: Did not find a dictionary."
    assert 'schema_version' in data, "Invalid schema: Did not find 'schema_version'."
    version = data['schema_version']
    with open(sname,'r') as file:
        schema = json.load(file)
    out = jsonschema.validate(data,schema)
    print(out)
    

def dumpplain_content(data,depth=0,indent="  "):
    """Summarize Correction content in plain text."""
    ntype = data['nodetype']
    if ntype=='binning':
        input = data['input']
        print(f"{indent}{ntype}:{bold(input)}")
    elif ntype=='multibinning':
        input = ','.join(data['inputs'])
        print(f"{indent}{ntype}:{bold(input)}")
    elif ntype=='category':
        input = data['input']
        print(f"{indent}{ntype}:{bold(input)}")
        if depth==0:
            keys = ', '.join(bold(i['key']) for i in data['content'])
            print(f"{indent}keys: {keys}")
        else:
            for item in data['content']:
                print(f"{indent}  key:{bold(item['key'])}")
                if isinstance(item['value'],dict):
                    dumpplain_content(item['value'],depth=depth-1,indent=indent+"    ")
        return
    elif ntype=='formula':
        input = ','.join(data['variables'])
        print(f"{indent}{ntype}:{bold(input)}")
        return
    elif ntype=='transform':
        input = data['input']
        print(f"{indent}{ntype}:{bold(input)}")
    else:
        print(f"{indent}{ntype}")
    if depth!=0 and isinstance(data['content'],dict):
        dumpplain_content(data['content'],depth=depth-1,indent=indent+"  ")
    return
    

def dumpplain(fname,depth=0,indent="  "):
    """Summarize Correction content in plain text."""
    print(f"{fname}")
    with open(fname,'r') as file:
        data = json.load(file)
    corrs = data.get('corrections',[data]) # assume either CorrectionSet or Correction
    for corr in corrs:
        print(f"{indent}{bold(corr['name'])}")
        indent_ = indent+"  "
        if depth==0:
            for input in corr['inputs']:
                print(f"{indent_}{input['type']}:{bold(input['name'])} {input.get('description','')}")
        else:
            print(f"{indent_}input:")
            for input in corr['inputs']:
                print(f"{indent_}  {input['type']}:{bold(input['name'])} {input.get('description','')}")
            output = corr['output']
            print(f"{indent_}output:")
            print(f"{indent_}  {output['type']}:{bold(output['name'])} {output.get('description','')}")
            dumpplain_content(corr['data'],depth=depth-1,indent=indent_+"  ")
    

def main(args):
    for fname in args.fnames:
        if args.format=="plain":
            dumpplain(fname,depth=args.maxdepth)
        else:
            print(f"{format} format not implemented... Yet!")
    

if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser
    argv = sys.argv
    description = """Summarize JSON file's content."""
    parser = ArgumentParser(prog="summary",description=description,epilog="Succes!")
    parser.add_argument("fnames", nargs='+', help="JSON file to summarize")
    parser.add_argument("--format", choices=["plain","html","markdown"], default="plain", help="format of summary")
    parser.add_argument("-d", "--maxdepth", type=int, default=0, help="maximum depth in correction object (-1 = infinite)")
    parser.add_argument("-l", "--highlight", action="store_true", help="highlight user input")
    args = parser.parse_args()
    _highlight = args.highlight
    main(args)
    
