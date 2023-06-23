"""Azure Function to send messages to the Dynamics Customer Sync
    Service Bus topic.

"""
import os
import json
import logging
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    """ Send the input messages to the Dynamics Customer Sync Service Bus.

    Args:
        req (func.HttpRequest): Function inputs
        session_id (str): The session id to use for the messages

    Returns:
        func.HttpResponse: A comma separated list of sequence_id
            (AIS_STG_PAR_SEQNO) that were successfully sent to the
            Service Bus topic.
    """
    session_id = req.params.get('session_id')
    req_body = req.get_json()

    updated_ids = set()

    try:
        servicebus_client = ServiceBusClient.from_connection_string(
            conn_str=os.environ['service_bus_connection'],
            logging_enable=True)

        with servicebus_client:
            sender = servicebus_client.get_topic_sender(
                topic_name=os.environ['service_bus_topic'])

            with sender:
                messages = dict()

                for item in reversed(req_body):
                    customer_ref = item['PAR_REFNO']
                    if customer_ref not in messages:
                        messages[customer_ref] = item

                for item in reversed(messages):
                    msg = ServiceBusMessage(json.dumps(messages[item]),
                                            session_id=session_id)

                    sender.send_messages(msg)

                    ids = [str(it['SEQUENCE_ID']) for it in req_body
                           if it['PAR_REFNO'] == messages[item]['PAR_REFNO']]
                    for id in ids:
                        updated_ids.add(id)

        return ','.join(updated_ids)
    except (Exception) as ex:
        logging.error(f"Error: {ex}")
        return ','.join(updated_ids)
