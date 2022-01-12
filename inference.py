import json
import os
from io import BytesIO
import pickle as pkl
import numpy as np
import sagemaker_xgboost_container.encoder as xgb_encoders
import xgboost as xgb
from os import listdir
from scipy import sparse


# Load your model
def model_fn(model_dir):
    """
    Deserialize and return fitted model.
    """

    model_file_name = "stroom-xgboost-model"
    booster = pkl.load(open(os.path.join(model_dir, model_file_name), "rb"))

    return booster


# Here is where you define how your input data. It tries to validate your input data.
# override this method so now you can pass in your original string and perform encoding here
def input_fn(request_body, request_content_type):
    """
    The SageMaker XGBoost model server receives the request data body and the content type,
    and invokes the `input_fn`.

    Return a DMatrix (an object that can be passed to predict_fn).
    """

    if request_content_type == "text/csv":

        values = [i for i in request_body.split(',')]

        values = [val.strip() for val in values]

        npm = np.matrix(values)

        return npm

    if request_content_type == "text/libsvm":

        return xgb_encoders.libsvm_to_dmatrix(request_body)

    else:

        raise ValueError("Content type {} is not supported.".format(request_content_type))


# Run Predictions
def predict_fn(input_data, model):
    """
    SageMaker XGBoost model server invokes `predict_fn` on the return value of `input_fn`.

    Return a two-dimensional NumPy array where the first columns are predictions
    and the remaining columns are the feature contributions (SHAP values) for that prediction.
    """

    xgtest = xgb.DMatrix(input_data)

    prediction = model.predict(xgtest, validate_features=False)

    feature_contribs = model.predict(xgtest, pred_contribs=True, validate_features=False)

    output = np.hstack((prediction[:, np.newaxis], feature_contribs))

    return output


def output_fn(predictions, content_type):
    """
    After invoking predict_fn, the model server invokes `output_fn`.
    """
    if content_type == "text/csv":
        return ",".join(str(x) for x in predictions[0])
    else:
        raise ValueError("Content type {} is not supported.".format(content_type))
