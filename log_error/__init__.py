"""Azure Function to log ingestion errors.

"""
import logging

import azure.functions as func


def main(req: func.HttpRequest, outputblob: func.Out[bytes]) -> func.HttpResponse:
    """Create an error file in Azure Blob Storage.
        The file gets an random name and is saved under
        'errors/{run_pipeline_id}/
        The content of the file is the request body content.

        {run_pipeline_id} is required and must be an Azure Data Factory Run ID.
        The request body is expected to be a JSON representation of the
        error (utils.ErrorContext)

    Args:
        req (func.HttpRequest): Function inputs
        outputblob (): The output Azure Blob

    Raises:
        Exception: Log any exception

    Returns:
        func.HttpResponse: A 200 status, a 400 status code and an error
            description if the input is in incorrect format or a 500
            status code and an error description for any other error.
    """
    try:
        pipeline_run_id = req.params.get('pipeline_run_id')

        if not pipeline_run_id:
            raise ValueError(("The Azure Data Factory Pipeline Run ID must be "
                             "passed as pipeline_run_id"))

        outputblob.set(req.get_body())

        return func.HttpResponse(
            status_code=200
        )
    except (Exception) as ex:
        if isinstance(
            ex,
            (ValueError,
             AttributeError)):
            error_message = f'Input format error: {repr(ex)}'
            logging.error(str(error_message))
            return func.HttpResponse(
                str(error_message),
                status_code=400
            )
        else:
            raise ex
