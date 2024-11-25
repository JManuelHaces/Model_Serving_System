# Libraries
import os
import json
import joblib

from typing import Dict, Union

# Class
from src.aws import S3Manager
from src.pydantic.Models import generate_pydantic_model


class ModelMetadataManager:
    def __init__(self) -> None:
        with open('./src/models/Models/model_metadata.json', "r") as f:
            self.metadata = json.load(f)
    
    def find_model_by_file(self, model_type: str, model_file) -> Union[Dict, None]:
        """
        Finds a model in the given data by its file.
        Args:
            models_data (list): List of models (dictionaries).
            model_id (str): ID of the model to find.
        Returns:
            Union[dict, None]: The model dictionary if found, otherwise None.
        """
        for model in self.metadata[model_type]:
            if model['file'] == model_file:
                return model
        return None
    
    def check_model_constrains(self, model_type: str, model_name: str, inputs: generate_pydantic_model) -> Union[str, None]:
        model_metadata = self.find_model_by_file(model_type=model_type, model_file=model_name)
        model_constrains = model_metadata['inputs_constrains']
        # Checking each input
        str_warnings = []
        for i in model_constrains:
            input_value = getattr(inputs, i)
            if (input_value < model_constrains[i]['min']) | (input_value > model_constrains[i]['max']):
                str_warnings.append(i)
        if len(str_warnings) == 0:
            return None
        elif len(str_warnings) == 1:
            return f"Warning: The model has not been trained with this magnitude of data for the column: {str_warnings[0]}"
        else:
            return f"Warnings: The model has not been trained with this magnitude of data for the columns: {', '.join(str_warnings).strip()} "
    
    async def get_active_model(self, model_type=None, sorted_by_accuracy: bool = True):
        """
        Retrieve the active model from the metadata or the latest version
        Args:
            model_name (str, optional): Name of the specific model to look for. If None, checks all models.
        Returns:
            dict: The active model's metadata, or None if no active model is found.
        """
        active_models = []
        if model_type:
            # Look for the active models under the specified model_name
            models = self.metadata.get(model_type, [])
            active_models = [model for model in models if model.get("status") == "active"]
        else:
            # Look globally for any active model
            for models in self.metadata.values():
                active_models.extend(model for model in models if model.get("status") == "active")
        # If no active models are found, return None
        if not active_models:
            return None
        if sorted_by_accuracy:
            best_model = max(active_models, key=lambda model: model.get("accuracy", 0))
        else:
            # Select the model with the highest accuracy
            best_model = max(active_models, key=lambda model: model.get("version", 0))
        return best_model
    
    async def get_model_version(self, model_type: str, version: float) -> Union[Dict, None]:
        """
        Retrieves the metadata of a specific model based on its type and version.
        Args:
            model_type (str): The type of the model (e.g., "Logistic_Regression" or "XGBoost").
            version (float): The version of the model.
        Returns:
            dict: The metadata of the model if found.
            None: If the model is not found.
        """
        # Retrieve all models of the specified type
        models = self.metadata.get(model_type, [])
        if not models:
            return None
        # Search for the model with the specified version
        for model in models:
            if model["version"] == version:
                return model
        # Return None if no model with the specified version is found
        return None


class ModelManager:
    def __init__(self) -> None:
        self.s3_manager = S3Manager(bucket_name='entrevista-rac')
        
    async def check_model_version(self, model_name: str) -> None:
        """If the model from the bucket is different from the local one, it downloads it
        Args:
            model_name (str): Name of the file from the bucket
        """
        path_model = f'./src/models/Models/{model_name}'
        if os.path.exists(path=path_model):
            self.s3_manager.compare_and_download(local_file_path=path_model,
                                                s3_key=f'ML_Models/{model_name}',
                                                download_path=path_model)
        else:
            self.s3_manager.download_file(s3_key=f'ML_Models/{model_name}',
                                          file_path=path_model)
        
    @staticmethod
    async def load_model(model_name: str):
        """
        Load a model from the local directory.
        Args:
            model_name (str): Name of the model file to load.
        Returns:
            Loaded model object.
        """
        model_path = f'./src/models/Models/{model_name}'
        try:
            # Cargar el modelo desde el archivo .pkl
            model = joblib.load(model_path)
            print(f"Model '{model_name}' loaded successfully.")
            return model
        except Exception as e:
            return Exception(f"An error occurred while loading the model '{model_name}': {e}")
    