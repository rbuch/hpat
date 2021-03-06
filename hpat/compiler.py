from __future__ import print_function, division, absolute_import

from .pio import PIO
from .distributed import DistributedPass

def stage_io_pass(pipeline):
    """
    Convert IO calls
    """
    # Ensure we have an IR and type information.
    assert pipeline.func_ir
    io_pass = PIO(pipeline.func_ir, pipeline.locals)
    io_pass.run()

def stage_distributed_pass(pipeline):
    """
    parallelize for distributed-memory
    """
    # Ensure we have an IR and type information.
    assert pipeline.func_ir
    dist_pass = DistributedPass(pipeline.func_ir,
        pipeline.type_annotation.typemap, pipeline.type_annotation.calltypes)
    dist_pass.run()
    # unset user pipeline function after last pass so recursive jit in lowering
    # wouldn't run HPAT passes
    from numba import set_user_pipeline_func
    set_user_pipeline_func(None)

def add_hpat_stages(pipeline_manager, pipeline):
    pp = pipeline_manager.pipeline_stages['nopython']
    new_pp = []
    for (func,desc) in pp:
        if desc=='nopython frontend':
            new_pp.append((lambda:stage_io_pass(pipeline), "replace IO calls"))
        if desc=='nopython mode backend':
            new_pp.append((lambda:stage_distributed_pass(pipeline), "convert to distributed"))
        new_pp.append((func,desc))
    pipeline_manager.pipeline_stages['nopython'] = new_pp
