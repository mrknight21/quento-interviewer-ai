from typing import List

ACTION_TYPES = ["#NEXTQUESTION", "#STARTING", "#FOLLOWUPQUESTION", "#ASKAGAIN", "#COMPLETING"]
class LLMOutSchemaMisalignmentError(Exception):
    """Exception raised when the LLM output does not fit with the predefined schema.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, output: object, field: object) -> object:
        self.output = output
        self.field = field
        self.message = "The LLM output: {} \n The invalid field: {}.".format(output, field)
        super().__init__(self.message)


def select_next_speaker(step: int, agents) -> int:
    idx = (step) % len(agents)
    return idx

def get_field_value(field_string, field_name):
    extracted_filed_name = field_string[:field_string.index(":")].replace('"', '')
    if extracted_filed_name != field_name:
        raise LLMOutSchemaMisalignmentError(field_string, field_name)
    else:
        value = field_string[field_string.index(":") + 2:].replace('"', '').strip()
        return value

def parsing_response(output):
    output_fields = output.split("\n")
    parsed_output = {
        "action_type": None,
        "response": None
    }
    try:
        if len(output_fields) != 2:
            raise LLMOutSchemaMisalignmentError(output, "")
        parsed_output["action_type"] = get_field_value(output_fields[0], "action_type")
        parsed_output["response"] = get_field_value(output_fields[1], "response")
        if not parsed_output["action_type"] in ACTION_TYPES:
            raise LLMOutSchemaMisalignmentError(output_fields[0], "action_type")
        return parsed_output
    except LLMOutSchemaMisalignmentError:
        return None

