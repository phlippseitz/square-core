import os
import logging
import requests

from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.models.management import GetModelsResult, DeployRequest, DeployResult, RemoveResult, GetModelsHealth, UpdateModel
from app.core.config import settings
from starlette.responses import JSONResponse
from tasks.tasks import deploy_task, remove_model_task

from mongo_access import add_model_db, remove_model_dm, get_models_db, update_model_db, init_db
from docker_access import get_all_model_prefixes


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/deployed-models", response_model=List[GetModelsResult], name="get-deployed-models")
async def get_all_models():  # token: str = Depends(client_credentials)):
    models = await get_models_db()
    result = []
    for m in models:
        result.append(GetModelsResult(
            identifier=m["identifier"],
            model_type=m["MODEL_TYPE"],
            model_name=m["MODEL_NAME"],
            disable_gpu=m["DISABLE_GPU"],
            batch_size=m["BATCH_SIZE"],
            max_input=m["MAX_INPUT_SIZE"],
            model_class=m["MODEL_CLASS"],
            return_plaintext_arrays=m["RETURN_PLAINTEXT_ARRAYS"],
        ))
    return result

@router.get("/deployed-models-health", response_model=List[GetModelsHealth], name="get-deployed-models-health")
async def get_all_models():  # token: str = Depends(client_credentials)):
    port = 8443
    models = await get_models_db()
    lst_models = []
    for m in models:
        r = requests.get(
            url="{}/api/{}/health/heartbeat".format(settings.API_URL, m["identifier"]),
            # headers={"Authorization": f"Bearer {token}"},
            verify=os.getenv("VERIFY_SSL", 1) == 1,
        )
        # if the model-api instance has not finished loading the model it is not available yet
        if r.status_code == 200:
            lst_models.append({"identifier": m["identifier"], "is_alive": r.json()["is_alive"]})
        else:
            lst_models.append({"identifier": m["identifier"], "is_alive": False})

    return lst_models


@router.post("/deploy", name="deploy-model")
async def deploy_new_model(model_params: DeployRequest):
    """
    deploy a new model to the platform
    """
    identifier = model_params.identifier
    env = {
        "MODEL_NAME": model_params.model_name,
        "MODEL_PATH": model_params.model_path,
        "DECODER_PATH": model_params.decoder_path,
        "MODEL_TYPE": model_params.model_type,
        "MODEL_CLASS": model_params.model_class,
        "DISABLE_GPU": model_params.disable_gpu,
        "BATCH_SIZE": model_params.batch_size,
        "MAX_INPUT_SIZE": model_params.max_input,
        "TRANSFORMERS_CACHE": model_params.transformers_cache,
        "RETURN_PLAINTEXT_ARRAYS": model_params.return_plaintext_arrays,
        "PRELOADED_ADAPTERS": model_params.preloaded_adapters,
        # "WEB_CONCURRENCY": 2,  # fixed processes, do not give the control to  end-user
    }

    identifier_new = await(add_model_db(identifier, env))
    if not identifier_new:
        raise HTTPException(status_code=401, detail="A model with that identifier already exists")
    res = deploy_task.delay(identifier, env)
    logger.info(res.id)
    return {"message": f"Queued deploying {identifier}", "task_id": res.id}


@router.post("/remove/{identifier}", name="remove-model")
async def remove_model(identifier):
    """
    Remove a model from the platform
    """
    await(remove_model_dm(identifier))
    res = remove_model_task.delay(identifier)
    return {"message": "Queued removing model.", "task_id": res.id}


@router.post("/update/{identifier}")
async def update_model(identifier: str, update_parameters: UpdateModel):
    await(update_model_db(identifier, update_parameters))
    logger.info("Update parameters Type {},dict  {}".format(type(update_parameters.dict()), update_parameters.dict()))
    r = requests.post(
        url="{}/api/{}/update".format(settings.API_URL, identifier),
        json=update_parameters.dict(),
        # headers={"Authorization": f"Bearer {token}"},
        verify=os.getenv("VERIFY_SSL", 1) == 1,
    )
    return {"status_code": r.status_code, "content": r.json()}


@router.get("/task/{task_id}", name="task-status")
async def get_task_status(task_id):
    task = AsyncResult(task_id)
    if not task.ready():
        return JSONResponse(status_code=202, content={'task_id': str(task_id), 'status': 'Processing'})
    result = task.get()
    return {'task_id': str(task_id), 'status': 'Finished', 'result': result}


@router.post("/db/update")
async def init_db_from_docker():
    lst_prefix, port = get_all_model_prefixes()
    lst_models = []

    for prefix in lst_prefix:
        r = requests.get(
            url="{}{}/stats".format(settings.API_URL, prefix),
            # headers={"Authorization": f"Bearer {token}"},
            verify=os.getenv("VERIFY_SSL", 1) == 1,
        )
        # if the model-api instance has not finished loading the model it is not available yet
        if r.status_code == 200:
            data = r.json()
            logger.info("Response Format {}".format(data))
            lst_models.append({
                "identifier": prefix.split("/")[-1],
                "MODEL_NAME": data["model_name"] ,
                "MODEL_TYPE": data["model_type"],
                "DISABLE_GPU": data["disable_gpu"],
                "BATCH_SIZE": data["batch_size"],
                "MAX_INPUT_SIZE": data["max_input"],
                "MODEL_CLASS": data["model_class"],
                "RETURN_PLAINTEXT_ARRAYS": data["return_plaintext_arrays"],
            })
    added_models = await(init_db(lst_models))
    return {"added": added_models}
