get /api/purchase-invoice
Get a list of purchase invoices

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
filter.invoice_type	
query	integer
filter.invoice_state	
query	integer
filter.customer_number	
query	integer
filter.exported_bit	
query	boolean
filter.description	
query	string
filter.created_before	
query	date-time
filter.created_after	
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













post /api/purchase-invoice

{
  "id": 0,
  "type": 0,
  "invoice_state": {
    "state": 0,
    "description": "string"
  },
  "number": 0,
  "date": "2025-07-02T06:31:07.671Z",
  "description": "string",
  "totalsum": 0,
  "payment_total": 0,
  "note": "string",
  "note_type": 0,
  "note_text": "string",
  "taxtype": true,
  "currency_code": "string",
  "currency_rate": 0,
  "reference": "string",
  "supplier_number": "string",
  "purchase_order_number": "string",
  "payment_term": 0,
  "duedate": "2025-07-02T06:31:07.671Z",
  "exported_bit": true,
  "state_payed": true,
  "travelexpense_number": 0,
  "project_invoice_number": 0,
  "project_invoice_bit": true,
  "payment_ban_bit": true,
  "total_net": 0,
  "total_tax": 0,
  "customer_number": 0,
  "customer_name": "string",
  "customer_name_additional": "string",
  "street_address": "string",
  "street_address_additional": "string",
  "city": "string",
  "customer_country": "string",
  "account": "string",
  "swift": "string",
  "bank": "string",
  "bank2": "string",
  "bank3": "string",
  "bank4": "string",
  "contractnumber": "string",
  "payment_type": 0,
  "payment_share": 0,
  "foreign_share": "string",
  "foreign_type": "string",
  "clearing": "string",
  "www_link": "string",
  "online_url": "string",
  "modified_date": "2025-07-02T06:31:07.671Z",
  "value_date": "2025-07-02T06:31:07.671Z",
  "cash_date": "2025-07-02T06:31:07.671Z",
  "cash_date2": "2025-07-02T06:31:07.671Z",
  "cash_date3": "2025-07-02T06:31:07.671Z",
  "cash_amount": 0,
  "cash_amount2": 0,
  "cash_amount3": 0,
  "circulation_ready": true,
  "purchase_invoice_payments": [
    {
      "id": 0,
      "invoice_id": 0,
      "date": "2025-07-02T06:31:07.671Z",
      "total": 0,
      "total_incurrency": 0,
      "currency_rate": 0,
      "accountlist_account": "string",
      "account_currency": "string",
      "costcenter_code": "string",
      "batch": 0,
      "taxrate": 0,
      "description": "string",
      "identifier": "string",
      "project": 0,
      "lta": "string",
      "type": 0
    }
  ],
  "purchase_invoice_rows": [
    {
      "id": 0,
      "invoice_id": 0,
      "row_number": 0,
      "accountlist_account": "string",
      "row_net": 0,
      "taxrate": 0,
      "taxamount": 0,
      "total": 0,
      "description": "string",
      "description2": "string",
      "codelist_costcenter": "string",
      "project_number": 0,
      "project_phase": {
        "id": 0,
        "phase_number": 0,
        "header": "string",
        "description": "string",
        "phase_code": "string"
      },
      "codelist_worknumber": 0,
      "purchaseorder_number": 0,
      "delivery_customer_number": 0,
      "person_number": 0,
      "note": "string",
      "innernote": "string",
      "project_invoice_bit": true,
      "project_invoice_number": 0,
      "assets_id": 0,
      "blocking": 0,
      "productcode": "string",
      "productdescription": "string",
      "discount": 0,
      "deliverydate": "2025-07-02T06:31:07.671Z",
      "amount": 0,
      "unit": "string",
      "unitprice": 0,
      "expensegroup": 0,
      "lta": "string",
      "ean_code": "string",
      "worksitecode": "string",
      "worksitenumber": "string",
      "receiptnumber": 0,
      "worksite_bit": true,
      "reporttull_bit": true,
      "buyer_article_identifier": "string"
    }
  ],
  "purchase_invoice_circulations": [
    {
      "id": 0,
      "invoice_id": 0,
      "circulation_state": {
        "state": 0,
        "description": "string"
      },
      "circulation_person": {
        "number": 0,
        "name": "string"
      },
      "circulation_type": {
        "type": 0,
        "description": "string"
      },
      "note": "string",
      "notification": true,
      "circulation_checker": {
        "number": 0,
        "name": "string"
      },
      "timestamp": "2025-07-02T06:31:07.671Z",
      "order": 0,
      "feedback": "string",
      "checker_text": "string",
      "returned": true
    }
  ]
}

put /api/purchase-invoice

{
  "id": 0,
  "type": 0,
  "invoice_state": {
    "state": 0,
    "description": "string"
  },
  "number": 0,
  "date": "2025-07-02T06:31:07.679Z",
  "description": "string",
  "totalsum": 0,
  "payment_total": 0,
  "note": "string",
  "note_type": 0,
  "note_text": "string",
  "taxtype": true,
  "currency_code": "string",
  "currency_rate": 0,
  "reference": "string",
  "supplier_number": "string",
  "purchase_order_number": "string",
  "payment_term": 0,
  "duedate": "2025-07-02T06:31:07.679Z",
  "exported_bit": true,
  "state_payed": true,
  "travelexpense_number": 0,
  "project_invoice_number": 0,
  "project_invoice_bit": true,
  "payment_ban_bit": true,
  "total_net": 0,
  "total_tax": 0,
  "customer_number": 0,
  "customer_name": "string",
  "customer_name_additional": "string",
  "street_address": "string",
  "street_address_additional": "string",
  "city": "string",
  "customer_country": "string",
  "account": "string",
  "swift": "string",
  "bank": "string",
  "bank2": "string",
  "bank3": "string",
  "bank4": "string",
  "contractnumber": "string",
  "payment_type": 0,
  "payment_share": 0,
  "foreign_share": "string",
  "foreign_type": "string",
  "clearing": "string",
  "www_link": "string",
  "online_url": "string",
  "modified_date": "2025-07-02T06:31:07.679Z",
  "value_date": "2025-07-02T06:31:07.679Z",
  "cash_date": "2025-07-02T06:31:07.679Z",
  "cash_date2": "2025-07-02T06:31:07.679Z",
  "cash_date3": "2025-07-02T06:31:07.679Z",
  "cash_amount": 0,
  "cash_amount2": 0,
  "cash_amount3": 0,
  "circulation_ready": true,
  "purchase_invoice_payments": [
    {
      "id": 0,
      "invoice_id": 0,
      "date": "2025-07-02T06:31:07.679Z",
      "total": 0,
      "total_incurrency": 0,
      "currency_rate": 0,
      "accountlist_account": "string",
      "account_currency": "string",
      "costcenter_code": "string",
      "batch": 0,
      "taxrate": 0,
      "description": "string",
      "identifier": "string",
      "project": 0,
      "lta": "string",
      "type": 0
    }
  ],
  "purchase_invoice_rows": [
    {
      "id": 0,
      "invoice_id": 0,
      "row_number": 0,
      "accountlist_account": "string",
      "row_net": 0,
      "taxrate": 0,
      "taxamount": 0,
      "total": 0,
      "description": "string",
      "description2": "string",
      "codelist_costcenter": "string",
      "project_number": 0,
      "project_phase": {
        "id": 0,
        "phase_number": 0,
        "header": "string",
        "description": "string",
        "phase_code": "string"
      },
      "codelist_worknumber": 0,
      "purchaseorder_number": 0,
      "delivery_customer_number": 0,
      "person_number": 0,
      "note": "string",
      "innernote": "string",
      "project_invoice_bit": true,
      "project_invoice_number": 0,
      "assets_id": 0,
      "blocking": 0,
      "productcode": "string",
      "productdescription": "string",
      "discount": 0,
      "deliverydate": "2025-07-02T06:31:07.679Z",
      "amount": 0,
      "unit": "string",
      "unitprice": 0,
      "expensegroup": 0,
      "lta": "string",
      "ean_code": "string",
      "worksitecode": "string",
      "worksitenumber": "string",
      "receiptnumber": 0,
      "worksite_bit": true,
      "reporttull_bit": true,
      "buyer_article_identifier": "string"
    }
  ],
  "purchase_invoice_circulations": [
    {
      "id": 0,
      "invoice_id": 0,
      "circulation_state": {
        "state": 0,
        "description": "string"
      },
      "circulation_person": {
        "number": 0,
        "name": "string"
      },
      "circulation_type": {
        "type": 0,
        "description": "string"
      },
      "note": "string",
      "notification": true,
      "circulation_checker": {
        "number": 0,
        "name": "string"
      },
      "timestamp": "2025-07-02T06:31:07.679Z",
      "order": 0,
      "feedback": "string",
      "checker_text": "string",
      "returned": true
    }
  ]
}