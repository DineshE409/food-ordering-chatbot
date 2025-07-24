from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_handler
import generic_handler

app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_handler.extract_session_id(output_contexts[0]['name'])

    print(f"[DEBUG] Received intent: {intent}")

    intent_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order,
        'new.order': start_new_order
    }

    if intent in intent_dict:
        return intent_dict[intent](parameters, session_id)
    else:
        print(f"[WARNING] Unrecognized intent: {intent}")
        return JSONResponse(content={"fulfillmentText": f"Unhandled intent: {intent}"})

def add_to_order(parameters: dict,session_id: str):
    food_items = parameters['food-item']
    quantities = parameters['number']

    if len(food_items) != len(quantities):
        fulfillment_text = "Please mention the food items and the quantities clearly"
    else:
        #fulfillment_text = f"you order is {food_items} and {quantities}"
        food = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current = inprogress_orders[session_id]
            current.update(food)
            inprogress_orders[session_id] = current
        else:
            inprogress_orders[session_id] = food

        order_str = generic_handler.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f'so far {order_str} Do you need anything else?'
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
    })

def start_new_order(parameters: dict, session_id: str):
    if session_id in inprogress_orders:
        print(f"[DEBUG] Clearing previous order for session: {session_id}")
        del inprogress_orders[session_id]

    inprogress_orders[session_id] = {}

    return JSONResponse(content={
        "fulfillmentText": "Sure! Let's start a new order. What would you like to have? we have only the following items on our menu: Pav Bhaji, Chole Bhature, Pizza, Mango Lassi, Masala Dosa, Biryani, Vada Pav, Rava Dosa, and Samosa."
    })


def remove_from_order(parameters: dict,session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillment_text" : "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    food_items = parameters['food-item']
    current = inprogress_orders[session_id]

    removed_item = []
    no_such_item = []

    for item in food_items:
        if item not in current:
            no_such_item.append(item)
        else:
            removed_item.append(item)
            del current[item]

        if len(removed_item) > 0:
            fulfillment_text = f'Removed {",".join(removed_item)} from your order!'

        if len(no_such_item) > 0:
            fulfillment_text = f' Your current order does not have {",".join(no_such_item)}'

        if len(current.keys()) == 0:
            fulfillment_text += " Your order is empty!"
        else:
            order_str = generic_handler.get_str_from_food_dict(current)
            fulfillment_text += f" Here is what is left in your order: {order_str}"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })




def complete_order(parameters: dict,session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "Sorry, the order is incomplete please place the order again"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = "Sorry, the order is incomplete." \
                                "Please place the order again"
        else:
            order_total = db_handler.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. " \
                               f"Here is your order id # {order_id}. " \
                               f"Your order total is {order_total} which you can pay at the time of delivery!"
        del inprogress_orders[session_id]
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def save_to_db(order: dict):
    next_order_id = db_handler.get_next_order_id()

    for food, quantity in order.items():
        rcode = db_handler.insert_order_item(
            food, quantity, next_order_id
        )
        if rcode == -1:
            return -1

    db_handler.insert_order_tracking(next_order_id, "in progress")
    return next_order_id


def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['order_id'])
    order_status = db_handler.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"the order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
    })

