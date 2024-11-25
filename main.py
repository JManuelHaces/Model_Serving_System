# Libraries
import os
import json
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

# Local Classes
from src.auth import authenticate
from src.redis import RedisManager
from src.aws import S3Manager
from src.pydantic import generate_pydantic_model
from src.sqlite_manager import SqliteLogsManager
from src.models import ModelManager, ModelMetadataManager
from src.middleware.Metrics import MetricsMiddleware

# Initializing all the classes
RedisManager_C = RedisManager()
SqliteLogsManager_C = SqliteLogsManager()
ModelManager_C = ModelManager()
ModelMetadataManager_C = ModelMetadataManager()
S3Manager_C = S3Manager(bucket_name='entrevista-rac')

# Initialize FastAPI
app = FastAPI()

app.add_middleware(MetricsMiddleware)

Instrumentator().instrument(app).expose(app)

# Home Endpoint
@app.get("/")
async def root():
    return {"response": "POC *Model Serving System Design* by José Manuel Haces.",
            "status": "OK"}

@app.post("/predict")
async def predict(input_data: dict, api_key: str = Depends(authenticate)):
    await S3Manager_C.compare_and_download(
        local_file_path='./src/models/Models/model_metadata.json',
        s3_key='model_metadata.json',
        download_path='./src/models/Models/model_metadata.json'
    )
    active_model_metadata = await ModelMetadataManager_C.get_active_model()
    model_name = active_model_metadata['file']
    model_type = active_model_metadata['type']

    await ModelManager_C.check_model_version(model_name=model_name)

    cache_key = f"{model_name}_{json.dumps(input_data)}"
    cached_result = await RedisManager_C.get_from_cache(cache_key)
    if cached_result:
        return {"response": cached_result, "cache": True, "status": "OK"}

    try:
        model = await ModelManager_C.load_model(model_name=model_name)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Model file '{model_name}' not found.")

    input_schema = active_model_metadata.get("inputs", {})
    input_model =  generate_pydantic_model(inputs=input_schema, model_name=model_name, data=input_data)
    if isinstance(input_model, str):
        raise HTTPException(status_code=422, detail=input_model)

    input_df = pd.DataFrame([input_model.dict()])
    try:
        prediction = model.predict(input_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

    warnings = []
    warnings.append(ModelMetadataManager_C.check_model_constrains(
        model_name=model_name,
        model_type=model_type,
        inputs=input_model
    ))

    response = {
        "model": active_model_metadata['file'],
        "version": active_model_metadata['version'],
        "prediction": prediction.tolist()[0],
        "dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if warnings:
        response['warnings'] = warnings

    await RedisManager_C.save_to_cache(key=cache_key, value=response)
    await SqliteLogsManager_C.save_log(
        model=model_name,
        input_data=input_model.dict(),
        prediction=prediction.tolist()[0]
    )

    return {"response": response, "cache": False, "status": "OK"}

@app.post("/predict/{model_type}")
async def predict_with_model(model_type: str, input_data: dict, api_key: str = Depends(authenticate)):
    await S3Manager_C.compare_and_download(
        local_file_path='./src/models/Models/model_metadata.json',
        s3_key='model_metadata.json',
        download_path='./src/models/Models/model_metadata.json'
    )
    model_metadata = await ModelMetadataManager_C.get_active_model(model_type=model_type, sorted_by_accuracy=False)
    if model_metadata is None:
        raise HTTPException(status_code=404, detail=f"Model type '{model_type}' not found in metadata.")
    model_name = model_metadata['file']
    model_type = model_metadata['type']
    input_schema = model_metadata.get("inputs", {})

    await ModelManager_C.check_model_version(model_name=model_name)

    cache_key = f"{model_name}_{json.dumps(input_data)}"
    cached_result = await RedisManager_C.get_from_cache(cache_key)
    if cached_result:
        return {"response": cached_result, "cache": True, "status": "OK"}

    try:
        model = await ModelManager_C.load_model(model_name=model_name)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Model file '{model_name}' not found.")

    input_model = generate_pydantic_model(inputs=input_schema, model_name=model_name, data=input_data)
    if isinstance(input_model, str):
        raise HTTPException(status_code=422, detail=input_model)

    input_df = pd.DataFrame([input_model.dict()])
    try:
        prediction = model.predict(input_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

    warnings = []
    warning_temp = ModelMetadataManager_C.check_model_constrains(
        model_name=model_name,
        model_type=model_type,
        inputs=input_model
    )
    if warning_temp is not None:
        warnings.append(warning_temp)

    response = {
        "model": model_name,
        "version": model_metadata['version'],
        "prediction": prediction.tolist()[0],
        "warnings": warnings,
        "dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    await RedisManager_C.save_to_cache(key=cache_key, value=response)
    await SqliteLogsManager_C.save_log(
        model=model_name,
        input_data=input_model.dict(),
        prediction=prediction.tolist()[0]
    )

    return {"response": response, "cache": False, "status": "OK"}

@app.post("/predict/{model_type}/{version}")
async def predict_with_model(model_type: str, input_data: dict, version: str, api_key: str = Depends(authenticate)):
    # Comparar y descargar los metadatos desde S3
    await S3Manager_C.compare_and_download(
        local_file_path='./src/models/Models/model_metadata.json',
        s3_key='model_metadata.json',
        download_path='./src/models/Models/model_metadata.json'
    )

    # Cargar los metadatos del modelo
    model_metadata = await ModelMetadataManager_C.get_model_version(model_type=model_type, version=version)
    if model_metadata is None:
        raise HTTPException(status_code=404, detail=f"Model type '{model_type}' not found in metadata.")

    model_name = model_metadata['file']
    model_type = model_metadata['type']
    input_schema = model_metadata.get("inputs", {})

    # Verificar la versión del modelo
    await ModelManager_C.check_model_version(model_name=model_name)

    # Crear clave para el cache
    cache_key = f"{model_name}_{json.dumps(input_data)}"
    cached_result = await RedisManager_C.get_from_cache(cache_key)
    if cached_result:
        return {"response": cached_result, "cache": True, "status": "OK"}

    # Validar los datos de entrada con el esquema del modelo
    input_model = generate_pydantic_model(inputs=input_schema, model_name=model_name, data=input_data)
    if isinstance(input_model, str):  # Si devuelve un error de validación
        raise HTTPException(status_code=422, detail=input_model)

    # Convertir los datos de entrada a DataFrame
    input_df = pd.DataFrame([input_model.dict()])

    # Realizar la predicción
    try:
        model = await ModelManager_C.load_model(model_name=model_name)
        prediction = model.predict(input_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

    # Convertir predicción a lista serializable
    prediction_result = prediction.tolist()

    # Revisar restricciones
    warnings = []
    warning_temp = ModelMetadataManager_C.check_model_constrains(
        model_name=model_name,
        model_type=model_type,
        inputs=input_model
    )
    if warning_temp is not None:
        warnings.append(warning_temp)

    # Construir respuesta
    response = {
        "model": model_name,
        "version": model_metadata['version'],
        "prediction": prediction_result[0],  # Toma el primer elemento
        "warnings": warnings,
        "dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Guardar en cache
    await RedisManager_C.save_to_cache(key=cache_key, value=response)

    # Guardar en logs
    await SqliteLogsManager_C.save_log(
        model=model_name,
        input_data=input_model.dict(),
        prediction=prediction_result[0]
    )

    return {"response": response, "cache": False, "status": "OK"}

@app.get('/logs')
async def get_logs(n_limit: int, api_key: str = Depends(authenticate)):
    try:
        logs = await SqliteLogsManager_C.get_logs(limit=n_limit)
        return {"response": logs,
                "status": "OK",
                "dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        return {"response": str(e),
                "status": "Error",
                "dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.delete("/delete-models")
async def delete_models(api_key: str = Depends(authenticate)):
    files = os.listdir('./src/models/Models/')
    deleted_files = []
    for file in files:
        if file == 'model_metadata.json':
            continue
        file_path = os.path.join('./src/models/Models/', file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            deleted_files.append(file_path)
    if not deleted_files:
        return {"response": "No files to delete.", "status": "OK"}
    return {"response": f"Deleted files: {deleted_files}", "status": "OK"}
