get /api/customers
Returns a list of customers for given customer id

Implementation Notes
Can be filtered using CustomerFilter

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
filter.name	
query	string
filter.search_name	
query	string
filter.email	
query	string
filter.contact_email	
query	string
filter.phone	
query	string
filter.vat	
query	string
filter.modified_before	
query	date-time
filter.modified_after	
query	date-time
filter.has_email	
query	integer
filter.is_customer	
query	integer
filter.is_supplier	
query	integer
filter.customer_number	
Provide multiple values in new lines.
query	Array[integer]
filter.group	
query	integer
filter.type	
query	integer
filter.created_before	
query	date-time
filter.created_after	
query	date-time
filter.updated_before	
query	date-time
filter.updated_after	
query	date-time
filter.attribute_ids	
Provide multiple values in new lines.
query	Array[integer]
filter.object_ids	
Provide multiple values in new lines.
query	Array[integer]
filter.page	
Page number. If not provided, using default value of 1

query	integer
filter.page_size	
Page size. If not provided, using default value of 10

query	integer
filter.search	
query	string


post /api/customers
Create a customer

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
customer	
(required)

Parameter content type: 
application/json
A customer payload

body	
ModelExample Value
{
  "searchname": "string",
  "email": "string",
  "currency_code": "string",
  "attributes": [
    {
      "id": 0,
      "name": "string",
      "selected": true
    }
  ],
  "contacts": [
    {
      "id": 0,
      "customer_id": 0,
      "name": "string",
      "attributes": [
        {
          "id": 0,
          "name": "string",
          "selected": true,
          "contact_id": 0
        }
      ],
      "street": "string",
      "street2": "string",
      "department": "string",
      "email": "string",
      "fax": "string",
      "gsm": "string",
      "note": "string",
      "phone": "string",
      "postal_city": "string",
      "postal_code": "string",
      "city": "string",
      "title": "string"
    }
  ],
  "texts": [
    {
      "id": 0,
      "header_number": 0,
      "note": "string"
    }
  ],
  "costcenter": "string",
  "delivery_code": "string",
  "invoicing_customer_number": 0,
  "orderer_customer_number": 0,
  "is_customer": true,
  "is_nonactive": true,
  "is_prospect": true,
  "is_supplier": true,
  "created": "2025-06-30T13:43:45.390Z",
  "modified": "2025-06-30T13:43:45.390Z",
  "delivery_method_number": 0,
  "delivery_term": 0,
  "payment_term_number": 0,
  "interest": 0,
  "sales_account": "string",
  "purchase_account": "string",
  "receivables_account": "string",
  "accountspayable_account": "string",
  "customer_edi": "string",
  "invoice_method_id": 0,
  "invoice_code": "string",
  "finvoice_address": "string",
  "reference": "string",
  "creditlimit": 0,
  "deny_credit": true,
  "reseller": 0,
  "default_reference": "string",
  "prevent_delivery": true,
  "partial_delivery_disabled": true,
  "invoiceperiod": 0,
  "invoicedates": "string",
  "due_invoice_sum": 0,
  "open_invoice_sum": 0,
  "agreements": [
    {
      "products": [
        {
          "agreement_product_id": 0,
          "agreement_id": 0,
          "product_code": "string",
          "product_description": "string",
          "product_description2": "string",
          "product_serialnumber": "string",
          "product_amount": 0,
          "product_unit": "string",
          "product_price": 0,
          "product_type": 0,
          "product_unitprice": 0,
          "product_discount": 0,
          "product_amount2": 0,
          "product_blocking": 0,
          "product_notes": "string",
          "warranty_ends": "2025-06-30T13:43:45.390Z",
          "product_sales_price": 0,
          "service_interval": 0,
          "calibration_interval": 0,
          "product_project_id": 0,
          "product_project_phase_id": 0
        }
      ],
      "id": 0,
      "type": 0,
      "date": "2025-06-30T13:43:45.390Z",
      "invoicing_customer": 0,
      "notes": "string",
      "period_length": 0,
      "description": "string",
      "startdate": "2025-06-30T13:43:45.390Z",
      "enddate": "2025-06-30T13:43:45.390Z",
      "checkdate": "2025-06-30T13:43:45.390Z",
      "install_date": "2025-06-30T13:43:45.390Z",
      "invoiced_date": "2025-06-30T13:43:45.390Z",
      "mark": "string",
      "invoice_text": "string",
      "order_number": "string",
      "blocking": 0,
      "responsible_person": 0,
      "invoice_travelling_bit": true,
      "auto_renew_bit": true,
      "service_person_number": 0,
      "backup_service_person_number": 0,
      "response_time": 0,
      "leasing_number": "string",
      "leasing_start_date": "2025-06-30T13:43:45.390Z",
      "leasing_end_date": "2025-06-30T13:43:45.390Z",
      "leasing_value": 0,
      "leasing_end_value": 0,
      "automation_weekday": 0,
      "automation_month": 0,
      "automation_markdate": "2025-06-30T13:43:45.390Z",
      "location": "string",
      "email": "string",
      "phone": "string",
      "no_charges": true,
      "travel_time_percent": 0,
      "master": 0,
      "balancing_period": 0,
      "balanced_date": "2025-06-30T13:43:45.390Z",
      "payment_term": 0,
      "based_charges": true,
      "no_crediting": true,
      "pricelist": 0,
      "show_included_amount": true
    }
  ],
  "accounts": [
    {
      "account_id": 0,
      "customer_id": 0,
      "account_number": "string",
      "bank_name": "string",
      "bank_address": "string",
      "bank_address2": "string",
      "bank_country_code": "string",
      "bank_info": "string",
      "bic": "string",
      "iban": "string",
      "foreign_type": "string",
      "foreign_share": "string",
      "clearing": "string"
    }
  ],
  "circulations": [
    {
      "id": 0,
      "customer_id": 0,
      "person_number": 0,
      "circulation_type": 0
    }
  ],
  "dimension": {
    "Area_code": 0,
    "Chain_code": 0,
    "Turnover_code": 0,
    "Employer_quantity_code": 0,
    "Customer_segment_code": 0,
    "Customer_abc": 0,
    "Mainbusiness_code": 0,
    "Branch_classification1": "string",
    "Branch_classification2": "string",
    "Branch_classification3": "string",
    "Customergroup_id": 0,
    "Business_activity_areacode": 0,
    "Customer_class_id": 0,
    "Customer_quality_system_bit": true,
    "Customer_reference_bit": true,
    "Customer_dimension_started": "2025-06-30T13:43:45.390Z",
    "Customer_dimension_turnover": 0,
    "Customer_costcenter": "string",
    "Customer_lta": "string",
    "Customer_quality_system_name": "string",
    "Customer_reference_note": "string",
    "Transaction_type": 0
  },
  "person_responsible_number": 0,
  "id": 0,
  "number": 0,
  "name": "string",
  "name2": "string",
  "phone": "string",
  "vat": "string",
  "street": "string",
  "street2": "string",
  "city": "string",
  "postal_code": "string",
  "country": "string",
  "www": "string",
  "language_code": "string",
  "group": 0,
  "customer_group_id": 0,
  "invoicing_name": "string",
  "invoicing_name2": "string",
  "invoicing_address": "string",
  "invoicing_postaladdress": "string",
  "invoicing_postal_code": "string",
  "invoicing_city": "string",
  "type": 0,
  "seller_number": 0,
  "fax": "string"
}


get /api/customers/base
Returns a list of customers with only basic information

Implementation Notes
Can be filtered using CustomerFilter

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
filter.name	
query	string
filter.search_name	
query	string
filter.email	
query	string
filter.contact_email	
query	string
filter.phone	
query	string
filter.vat	
query	string
filter.modified_before	
query	date-time
filter.modified_after	
query	date-time
filter.has_email	
query	integer
filter.is_customer	
query	integer
filter.is_supplier	
query	integer
filter.customer_number	
Provide multiple values in new lines.
query	Array[integer]
filter.group	
query	integer
filter.type	
query	integer
filter.created_before	
query	date-time
filter.created_after	
query	date-time
filter.updated_before	
query	date-time
filter.updated_after	
query	date-time
filter.attribute_ids	
Provide multiple values in new lines.
query	Array[integer]
filter.object_ids	
Provide multiple values in new lines.
query	Array[integer]
filter.page	
Page number. If not provided, using default value of 1

query	integer
filter.page_size	
Page size. If not provided, using default value of 10

query	integer
filter.search	
query	string



get /api/customers/{customer_id}
Get single customer

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
customer_id	
(required)
customer id

path	integer











put /api/customers/{customer_id}
Update a customer

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
customer_id	
(required)
Customer ID given in route

path	integer
customer	
(required)

Parameter content type: 
application/json
A customer payload

body	
ModelExample Value
{
  "searchname": "string",
  "email": "string",
  "currency_code": "string",
  "attributes": [
    {
      "id": 0,
      "name": "string",
      "selected": true
    }
  ],
  "contacts": [
    {
      "id": 0,
      "customer_id": 0,
      "name": "string",
      "attributes": [
        {
          "id": 0,
          "name": "string",
          "selected": true,
          "contact_id": 0
        }
      ],
      "street": "string",
      "street2": "string",
      "department": "string",
      "email": "string",
      "fax": "string",
      "gsm": "string",
      "note": "string",
      "phone": "string",
      "postal_city": "string",
      "postal_code": "string",
      "city": "string",
      "title": "string"
    }
  ],
  "texts": [
    {
      "id": 0,
      "header_number": 0,
      "note": "string"
    }
  ],
  "costcenter": "string",
  "delivery_code": "string",
  "invoicing_customer_number": 0,
  "orderer_customer_number": 0,
  "is_customer": true,
  "is_nonactive": true,
  "is_prospect": true,
  "is_supplier": true,
  "created": "2025-06-30T13:43:45.406Z",
  "modified": "2025-06-30T13:43:45.406Z",
  "delivery_method_number": 0,
  "delivery_term": 0,
  "payment_term_number": 0,
  "interest": 0,
  "sales_account": "string",
  "purchase_account": "string",
  "receivables_account": "string",
  "accountspayable_account": "string",
  "customer_edi": "string",
  "invoice_method_id": 0,
  "invoice_code": "string",
  "finvoice_address": "string",
  "reference": "string",
  "creditlimit": 0,
  "deny_credit": true,
  "reseller": 0,
  "default_reference": "string",
  "prevent_delivery": true,
  "partial_delivery_disabled": true,
  "invoiceperiod": 0,
  "invoicedates": "string",
  "due_invoice_sum": 0,
  "open_invoice_sum": 0,
  "agreements": [
    {
      "products": [
        {
          "agreement_product_id": 0,
          "agreement_id": 0,
          "product_code": "string",
          "product_description": "string",
          "product_description2": "string",
          "product_serialnumber": "string",
          "product_amount": 0,
          "product_unit": "string",
          "product_price": 0,
          "product_type": 0,
          "product_unitprice": 0,
          "product_discount": 0,
          "product_amount2": 0,
          "product_blocking": 0,
          "product_notes": "string",
          "warranty_ends": "2025-06-30T13:43:45.406Z",
          "product_sales_price": 0,
          "service_interval": 0,
          "calibration_interval": 0,
          "product_project_id": 0,
          "product_project_phase_id": 0
        }
      ],
      "id": 0,
      "type": 0,
      "date": "2025-06-30T13:43:45.406Z",
      "invoicing_customer": 0,
      "notes": "string",
      "period_length": 0,
      "description": "string",
      "startdate": "2025-06-30T13:43:45.406Z",
      "enddate": "2025-06-30T13:43:45.406Z",
      "checkdate": "2025-06-30T13:43:45.406Z",
      "install_date": "2025-06-30T13:43:45.406Z",
      "invoiced_date": "2025-06-30T13:43:45.406Z",
      "mark": "string",
      "invoice_text": "string",
      "order_number": "string",
      "blocking": 0,
      "responsible_person": 0,
      "invoice_travelling_bit": true,
      "auto_renew_bit": true,
      "service_person_number": 0,
      "backup_service_person_number": 0,
      "response_time": 0,
      "leasing_number": "string",
      "leasing_start_date": "2025-06-30T13:43:45.406Z",
      "leasing_end_date": "2025-06-30T13:43:45.406Z",
      "leasing_value": 0,
      "leasing_end_value": 0,
      "automation_weekday": 0,
      "automation_month": 0,
      "automation_markdate": "2025-06-30T13:43:45.406Z",
      "location": "string",
      "email": "string",
      "phone": "string",
      "no_charges": true,
      "travel_time_percent": 0,
      "master": 0,
      "balancing_period": 0,
      "balanced_date": "2025-06-30T13:43:45.406Z",
      "payment_term": 0,
      "based_charges": true,
      "no_crediting": true,
      "pricelist": 0,
      "show_included_amount": true
    }
  ],
  "accounts": [
    {
      "account_id": 0,
      "customer_id": 0,
      "account_number": "string",
      "bank_name": "string",
      "bank_address": "string",
      "bank_address2": "string",
      "bank_country_code": "string",
      "bank_info": "string",
      "bic": "string",
      "iban": "string",
      "foreign_type": "string",
      "foreign_share": "string",
      "clearing": "string"
    }
  ],
  "circulations": [
    {
      "id": 0,
      "customer_id": 0,
      "person_number": 0,
      "circulation_type": 0
    }
  ],
  "dimension": {
    "Area_code": 0,
    "Chain_code": 0,
    "Turnover_code": 0,
    "Employer_quantity_code": 0,
    "Customer_segment_code": 0,
    "Customer_abc": 0,
    "Mainbusiness_code": 0,
    "Branch_classification1": "string",
    "Branch_classification2": "string",
    "Branch_classification3": "string",
    "Customergroup_id": 0,
    "Business_activity_areacode": 0,
    "Customer_class_id": 0,
    "Customer_quality_system_bit": true,
    "Customer_reference_bit": true,
    "Customer_dimension_started": "2025-06-30T13:43:45.406Z",
    "Customer_dimension_turnover": 0,
    "Customer_costcenter": "string",
    "Customer_lta": "string",
    "Customer_quality_system_name": "string",
    "Customer_reference_note": "string",
    "Transaction_type": 0
  },
  "person_responsible_number": 0,
  "id": 0,
  "number": 0,
  "name": "string",
  "name2": "string",
  "phone": "string",
  "vat": "string",
  "street": "string",
  "street2": "string",
  "city": "string",
  "postal_code": "string",
  "country": "string",
  "www": "string",
  "language_code": "string",
  "group": 0,
  "customer_group_id": 0,
  "invoicing_name": "string",
  "invoicing_name2": "string",
  "invoicing_address": "string",
  "invoicing_postaladdress": "string",
  "invoicing_postal_code": "string",
  "invoicing_city": "string",
  "type": 0,
  "seller_number": 0,
  "fax": "string"
}




post /api/customers/{customer_id}/accounts
Add new account

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
customer_id	
(required)
Customer ID given in route

path	integer
account	
(required)

Parameter content type: 
application/json
A account payload

body	
ModelExample Value
{
  "account_id": 0,
  "customer_id": 0,
  "account_number": "string",
  "bank_name": "string",
  "bank_address": "string",
  "bank_address2": "string",
  "bank_country_code": "string",
  "bank_info": "string",
  "bic": "string",
  "iban": "string",
  "foreign_type": "string",
  "foreign_share": "string",
  "clearing": "string"
}



InvoiceShow/HideList OperationsExpand Operations
get /api/invoices
Get a list of invoices

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
filter.numbers	
Provide multiple values in new lines.
query	Array[integer]
filter.customer_number	
query	integer
filter.delivery_customer_number	
query	integer
filter.type	
query	integer
filter.invoice_date_before	
query	date-time
filter.invoice_date_after	
query	date-time
filter.updated_before	
query	date-time
filter.updated_after	
query	date-time
filter.object_ids	
Provide multiple values in new lines.
query	Array[integer]
filter.page	
Page number. If not provided, using default value of 1

query	integer
filter.page_size	
Page size. If not provided, using default value of 10

query	integer
filter.search	
query	string