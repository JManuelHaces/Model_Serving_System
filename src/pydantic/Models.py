from pydantic import BaseModel, create_model
from typing import Dict, Any

def generate_pydantic_model(inputs: Dict[str, Any], model_name: str, data: Dict[str, Any]) -> Any:
    """
    Generates a dynamic Pydantic model and validates the provided data against it.
    Args:
        inputs (Dict[str, Any]): Dictionary of inputs with their types (e.g., {"field_name": int}).
        model_name (str): Name of the model.
        data (Dict[str, Any]): Data to validate against the model fields.
    Returns:
        Any: Error message if validation fails or the Pydantic model if successful.
    """
    # Check for extra fields in the provided data
    extra_fields = set(data.keys()) - set(inputs.keys())
    if extra_fields:
        accepted_fields = ", ".join(inputs.keys())
        return f"Error: The model '{model_name}' only accepts the following fields: {accepted_fields}. Extra fields: {', '.join(extra_fields)}"

    # Generate the dynamic model
    fields = {field_name: (field_type, ...) for field_name, field_type in inputs.items()}
    model = create_model(
        model_name,
        __config__=type("Config", (), {"extra": "forbid"}),  # Forbid extra fields at model level
        **fields
    )
    return model(**data)  # Return the validated model instance
