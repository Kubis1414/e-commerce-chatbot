from promptflow import tool


class Customer:
    def __init__(self, customer: dict):
        self.customer_id = customer.get("customer_id")
        self.name = customer.get("name")
        self.vokative = customer.get("vokative")
        self.email = customer.get("email")
        self.trust_bucket = customer.get("trust_bucket")
        self.favorite_brands = customer.get("favorite_brands")


@tool
def get_customer_info(customer_dict: dict) -> Customer:
    customer = Customer(customer_dict)
    
    return customer
