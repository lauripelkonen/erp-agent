create a new file which creates a purchase order always for the recommended products:

- must follow the api request formula from @how-to-create-purchase-order-api.md . 
- must keep the exact product name and extra name, price etc
- must utilise our customer details based on the target warehouse number:

supplier (customer_number) ALWAYS:
customer_number: 100001
customer_name1: ESPOO PÄÄVARASTO, LVI-WaBeK Oy
customer_address1: Koskelontie 22
customer_address3: 02920  ESPOO
customer_contact: TOMI LÄHTEENMÄKI
person_buyer_number": 212,



target warehouse contacts:

IF target warehouse = 402:
delivery_customer_number: 100008


ELIF target warehouse = 407:
      "delivery_customer_address1": "VASARAKATU 23B",
      "delivery_customer_address2": "",
      "delivery_customer_address3": "40320  JYVÄSKYLÄ",
      "delivery_customer_contact": "Leo Lahtinen",
      "delivery_customer_country": "",
      "delivery_customer_name1": "WACENTER JYVÄSKYLÄ",
      "delivery_customer_name2": "",
      "delivery_customer_number": 100007,
      "delivery_term": 0,
      "delivery_term_info": "",
      "delivery_text": "",
      "deliverynotes": "",
      "description": "Jyväskylä",
      "note": "HUOM. TAVARAN VASTAANOTTOAIKA KLO. 9-14 !",

ELIF target warehouse = 405:
      "delivery_customer_address1": "SUUTARILANTIE 61",
      "delivery_customer_address2": "",
      "delivery_customer_address3": "00750  HELSINKI",
      "delivery_customer_contact": "Ilpo Paasela",
      "delivery_customer_country": "",
      "delivery_customer_name1": "WACENTER SUUTARILA",
      "delivery_customer_name2": "",
      "delivery_customer_number": 100005,
      "delivery_term": 0,
      "delivery_term_info": "",
      "delivery_text": "",
      "deliverynotes": "",
      "description": "KOSKELO -> SUUTARILA 8.7.25",
      "note": "HUOM. TAVARAN VASTAANOTTOAIKA KLO. 9-14 !",

IF target warehouse = 406:
      "delivery_customer_address1": "KALLIOKUMMUNTIE 2",
      "delivery_customer_address2": "",
      "delivery_customer_address3": "37570  LEMPÄÄLÄ",
      "delivery_customer_contact": "Jesse Santamaa",
      "delivery_customer_country": "",
      "delivery_customer_name1": "WACENTER LEMPÄÄLÄ",
      "delivery_customer_name2": "",
      "description": "Espoo-Lempäälä 8.7",
      "note": "HUOM. TAVARAN VASTAANOTTOAIKA KLO. 9-14 !",
      "delivery_term": 0,
      "delivery_term_info": "",
      "delivery_text": "",
      "deliverynotes": "",
