from typing import Dict, Union, Any


def get_assert(output, context) -> Union[bool, float, Dict[str, Any]]:

    is_pipeline_generated = context["vars"]["is_pipeline_generated"]
    pipeline = output["pipeline"]
    # ensure that the pipeline is only generated when we expect it to
    if (pipeline is None and is_pipeline_generated) or (
        pipeline is not None and not is_pipeline_generated
    ):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected is_pipeline_generated to be {is_pipeline_generated} but pipeline is {pipeline}",
        }

    return {
        "pass": True,
        "score": 1,
        "reason": "All tests passed!",
    }
