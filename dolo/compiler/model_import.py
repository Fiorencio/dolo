
import numpy

from dolo.misc.display import read_file_or_url
import yaml
from collections import OrderedDict

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

# usage example:

def yaml_import(fname, txt=None, return_symbolic=False, check=True, check_only=False):


    if txt is None:
        txt = read_file_or_url(fname)

    if check:
        from dolo.linter import lint
        output = lint(txt)
        print(output)

    if check_only:
        return output

    txt = txt.replace('^', '**')

    return fast_import(txt, return_symbolic=return_symbolic)

def fast_import(txt, return_symbolic=False):

    import yaml
    txt = txt.replace('^','**')
    txt = txt.replace(' = ',' == ')

    # data = yaml.load(txt, loader=ordered_load)
    data = ordered_load(txt)

    name = data['name']
    model_type = data['model_type']
    symbols = data['symbols']
    definitions = data.get('definitions',[])
    equations = data['equations']
    options = data['options']
    calibration = data['calibration']

    fname = '<string>'
    infos = dict()
    infos['filename'] = fname
    infos['name'] = name
    infos['type'] = model_type


    # all symbols are initialized to nan
    # except shocks and markov_states which are initialized to 0
    initial_values = {
        'shocks': 0,
        'markov_states': 0,
        'controls': float('nan'),
        'states': float('nan')
    }

    # variables defined by a model equation default to using these definitions
    initialized_from_model = {
        'auxiliaries': 'auxiliary',
        'values': 'value',
        'expectations': 'expectation',
        'direct_responses': 'direct_response'
    }

    for symbol_group in symbols:
        if symbol_group not in initialized_from_model.keys():
            if symbol_group in initial_values:
                default = initial_values[symbol_group]
            else:
                default =  float('nan')
            for s in symbols[symbol_group]:
                if s not in calibration:
                    calibration[s] = default



    from dolo.compiler.model_symbolic import SymbolicModel
    smodel = SymbolicModel(name, model_type, symbols, equations,
                           calibration, options=options, definitions=definitions)

    if return_symbolic:
        return smodel

    if model_type in ('dtcscc','dtmscc'):
        from dolo.compiler.model_numeric import NumericModel
        model = NumericModel(smodel, infos=infos)
    else:
        from dolo.compiler.model_dynare import DynareModel
        model = DynareModel(smodel, infos=infos)
    return model


if __name__ == "__main__":

    # fname = "../../examples/models/rbc.yaml"
    fname = "examples/models/integration_A.yaml"

    import os
    print(os.getcwd())

    model = yaml_import(fname)

    print("calib")
    # print(model.calibration['parameters'])


    print(model)

    print(model.get_calibration(['beta']))
    model.set_calibration(beta=0.95)

    print( model.get_calibration(['beta']))


    print(model)

    s = model.calibration['states'][None,:]
    x = model.calibration['controls'][None,:]
    e = model.calibration['shocks'][None,:]

    p = model.calibration['parameters'][None,:]

    S = model.functions['transition'](s,x,e,p)
    lb = model.functions['controls_lb'](s,p)
    ub = model.functions['controls_ub'](s,p)


    print(S)

    print(lb)
    print(ub)


    # print(model.calibration['parameters'])
