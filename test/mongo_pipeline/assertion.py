from typing import Dict, Union, Any


def get_assert(output, context) -> Union[bool, float, Dict[str, Any]]:
    enable_test = context["vars"]["enable_test"]
    if enable_test.upper() == "FALSE":
        return {
            "pass": True,
            "score": 1,
            "reason": "Test case is disabled. Set 'enable_test' to 'True' to enable it.",
        }

    is_pipeline_generated = context["vars"]["is_pipeline_generated"].upper() == "TRUE"
    pipeline = output["pipeline"]
    # ensure that the pipeline is only generated when we expect it to
    if (pipeline is not None) != is_pipeline_generated:
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
