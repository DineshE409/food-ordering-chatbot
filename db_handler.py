import mysql.connector
from sympy.polys.polyconfig import query
global cnx


cnx = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='Admin@123',
            database='pandeyji_eatery'
)
def get_order_status(order_id):
    cursor = cnx.cursor()

    query = ("SELECT status FROM order_tracking WHERE order_id = %s")
    cursor.execute(query, (order_id,))
    result = cursor.fetchone()

    cursor.close()


    if result is not None:
        return result[0]  # status
    else:
        return "Order ID not found."

def get_next_order_id():
    cursor = cnx.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1

def get_total_order_price(order_id):
    cursor = cnx.cursor()

    # Executing the SQL query to get the total order price
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    return result


def insert_order_item(food, quantity, order_id):
    try:
        cursor = cnx.cursor()
        cursor.callproc("insert_order_item", (food, quantity, order_id))
        cnx.commit()
        cursor.close()
        print('order item inserted')
        return 1
    except mysql.connector.Error as error:
        print(f'Failed to insert order item: {error}')
        cnx.rollback()
        return -1
    except Exception as error:
        print(f'Failed to insert order item: {error}')
        cnx.rollback()
        return -1

def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    cnx.commit()

    # Closing the cursor
    cursor.close()
