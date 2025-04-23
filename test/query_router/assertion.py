from typing import Dict, Union, Any


def get_assert(output, context) -> Union[bool, float, Dict[str, Any]]:
    enable_test = context["vars"]["enable_test"]
    if enable_test.upper() == "FALSE":
        return {
            "pass": True,
            "score": 1,
            "reason": "Test case is disabled. Set 'enable_test' to 'True' to enable it.",
        }

    expected = context["vars"]["is_pipeline_generated"].upper() == "TRUE"
    actual = output["route"] == "nosql"
    # ensure that the pipeline is only generated when we expect it to
    if actual != expected:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected is_pipeline_generated to be {expected} but pipeline is {actual}",
        }

    return {
        "pass": True,
        "score": 1,
        "reason": "All tests passed!",
    }
