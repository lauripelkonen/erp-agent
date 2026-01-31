get /api/products
Get a list of products

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
filter.sku	
Provide multiple values in new lines.
query	Array[string]
filter.ean	
Provide multiple values in new lines.
query	Array[string]
filter.modified_before	
query	date-time
filter.modified_after	
query	date-time
filter.attribute_id	
query	integer
filter.extra_name	
query	string
filter.category_id	
query	integer
filter.group_code	
query	string
filter.show_models	
query	boolean
filter.show_nonactive	
query	boolean
filter.show_nonstock	
query	boolean
filter.shelf	
query	string
filter.shelf_stock	
query	integer
filter.stock	
query	integer
filter.sort_by_sku	
query	boolean
filter.search_words	
Provide multiple values in new lines.
query	Array[string]
filter.is_sales	
Vain myytävät tuotteet

query	boolean
filter.is_purchase	
Vain ostettavat tuotteet

query	boolean
filter.only_with_balance	
Vain saldolliset

query	boolean
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


# EXAMPLE RESPONSE

Request URL
https://lvirdsh1.lvi-keskus.local/LemonRest/api/products?filter.sku=2213020
Response Body
{
  "results": [
    {
      "id": 35784,
      "name": "KULMAYHDE 200 X 88.5",
      "extra_name": "",
      "sku": "2213020",
      "price": 82.84,
      "price_includes_tax": false,
      "texts": [
        {
          "id": 179758,
          "language_code": "",
          "header_number": 0,
          "text": "",
          "text_plain": ""
        },
        {
          "id": 118553,
          "language_code": "",
          "header_number": 3,
          "text": "PVC-muovista valmistettu kulmayhde maaviemäriputkille tiivisteellä. Valmistettu ympäristöystävällisesti käyttäen lyijyn sijaan kalsium-sinkki -stabilointia. Putki on kestävä ja pitkäikäinen. Viemäriveden pH: 2-12. Vetolujuus: 50-60Nm/mm2. Lämmönjohtavuus: 0.15 W/mK. Pituuden lämpötilakerroin: 0.8 x 10-4 1/K. Väri: oranssin ruskea RAL 8023. Valmistettu DIN EN 1401 mukaisesti. Tiivisteet EN 681-1 mukaisia. Kemiallinen kestävyys DIN 8061-1 mukainen.",
          "text_plain": "PVC-muovista valmistettu kulmayhde maaviemäriputkille tiivisteellä. Valmistettu ympäristöystävällisesti käyttäen lyijyn sijaan kalsium-sinkki -stabilointia. Putki on kestävä ja pitkäikäinen. Viemäriveden pH: 2-12. Vetolujuus: 50-60Nm/mm2. Lämmönjohtavuus: 0.15 W/mK. Pituuden lämpötilakerroin: 0.8 x 10-4 1/K. Väri: oranssin ruskea RAL 8023. Valmistettu DIN EN 1401 mukaisesti. Tiivisteet EN 681-1 mukaisia. Kemiallinen kestävyys DIN 8061-1 mukainen."
        },
        {
          "id": 132076,
          "language_code": "ENG",
          "header_number": 3,
          "text": "A PVC plastic bend with a seal for underground sewer pipes. Manufactured by environmentally friendly methods, by using calcium-zinc stabilisation instead of lead. The pipe is durable has a long service life. Sewage water pH: 2-12. Tensile strength: 50-60Nm/mm². Thermal conductivity: 0.15W/mK. Lengthwise thermal expansion coefficient: 0.8x10-4 1/K. Colour: orange-brown RAL8023. Manufactured in compliance with the DIN EN1401 standard. Seals in compliance with the EN681-1 standard. Chemical resistance in compliance with the DIN8061-1 standard.",
          "text_plain": "A PVC plastic bend with a seal for underground sewer pipes. Manufactured by environmentally friendly methods, by using calcium-zinc stabilisation instead of lead. The pipe is durable has a long service life. Sewage water pH: 2-12. Tensile strength: 50-60Nm/mm². Thermal conductivity: 0.15W/mK. Lengthwise thermal expansion coefficient: 0.8x10-4 1/K. Colour: orange-brown RAL8023. Manufactured in compliance with the DIN EN1401 standard. Seals in compliance with the EN681-1 standard. Chemical resistance in compliance with the DIN8061-1 standard."
        },
        {
          "id": 144937,
          "language_code": "SWE",
          "header_number": 3,
          "text": "En PVC-plastkrök med en tätning för avloppsrör under mark. Tillverkad med miljövänliga metoder, med användning av kalcium-zinkstabilisator iställer för bly. Röret är beständigt och har en lång livstid. Avloppsvatten pH: 2-12. Draghållfasthet: 50-60Nm/mm². Värmeledningsförmåga: 0.15W/mK. Längsgående värmeexpansionskoefficient: 0.8x10-4 1/K. Färg: orange-brun RAL8023. Tillverkad i överensstämmelse med standard DIN EN1401. Tätningar som följer standard EN681-1. Kemisk resistens som följer standard DIN8061-1.",
          "text_plain": "En PVC-plastkrök med en tätning för avloppsrör under mark. Tillverkad med miljövänliga metoder, med användning av kalcium-zinkstabilisator iställer för bly. Röret är beständigt och har en lång livstid. Avloppsvatten pH: 2-12. Draghållfasthet: 50-60Nm/mm². Värmeledningsförmåga: 0.15W/mK. Längsgående värmeexpansionskoefficient: 0.8x10-4 1/K. Färg: orange-brun RAL8023. Tillverkad i överensstämmelse med standard DIN EN1401. Tätningar som följer standard EN681-1. Kemisk resistens som följer standard DIN8061-1."
        }
      ],
      "units": [
        {
          "id": 158254,
          "product_id": 35784,
          "package": 0,
          "unit": "1",
          "amount": 1,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": true,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 1.9,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 291621,
          "product_id": 35784,
          "package": 0,
          "unit": "3",
          "amount": 3,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 5.7,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 232665,
          "product_id": 35784,
          "package": 0,
          "unit": "30",
          "amount": 30,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 30,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 57,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 232664,
          "product_id": 35784,
          "package": 0,
          "unit": "5",
          "amount": 5,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 5,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 9.5,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 291622,
          "product_id": 35784,
          "package": 0,
          "unit": "546",
          "amount": 546,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 1037.4,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 127491,
          "product_id": 35784,
          "package": 0.033333,
          "unit": "KPL",
          "amount": 1,
          "code": "",
          "default_amount": 1,
          "discount": 0,
          "price": 0,
          "price_per": 1,
          "use_for_pricing": true,
          "use_for_purchase": true,
          "use_for_sales": true,
          "use_for_stock": true,
          "volume": 0,
          "weight": 1.9,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 1,
          "handling_cost_id": 0
        },
        {
          "id": 359397,
          "product_id": 35784,
          "package": 0,
          "unit": "KPL1",
          "amount": 1,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 1.9,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 560916,
          "product_id": 35784,
          "package": 0,
          "unit": "KPL3",
          "amount": 3,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 5.7,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 384399,
          "product_id": 35784,
          "package": 0,
          "unit": "KPL5",
          "amount": 5,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 9.5,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 560917,
          "product_id": 35784,
          "package": 0,
          "unit": "KPL546",
          "amount": 546,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 1037.4,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 324125,
          "product_id": 35784,
          "package": 1,
          "unit": "LAVA",
          "amount": 30,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0.0333,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 56.4,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 594363,
          "product_id": 35784,
          "package": 0,
          "unit": "OSTOERÄ",
          "amount": 0,
          "code": "",
          "default_amount": 1,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 0,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        },
        {
          "id": 127492,
          "product_id": 35784,
          "package": 1,
          "unit": "P1_LTK",
          "amount": 30,
          "code": "",
          "default_amount": 0,
          "discount": 0,
          "price": 0,
          "price_per": 0,
          "use_for_pricing": false,
          "use_for_purchase": false,
          "use_for_sales": false,
          "use_for_stock": false,
          "volume": 0,
          "weight": 57,
          "package_weight": 0,
          "use_intrastat": false,
          "intrastat_amount": 0,
          "default_amount_purchase": 0,
          "default_amount_production": 0,
          "handling_cost_id": 0
        }
      ],
      "dimensions": "200",
      "is_inactive": false,
      "is_non_stock": false,
      "is_sellable": true,
      "is_purchase_product": true,
      "search_code": "",
      "size_type": 0,
      "type": 0,
      "type_description": "Nimikkeet",
      "stock_unit": "",
      "sales_price_taxful": 103.9642,
      "sales_price_taxless": 82.84,
      "sales_account": "",
      "taxrate_code": 0,
      "cost_center": "134999",
      "unit_id": 0,
      "color_code": 158,
      "mark_code": 1,
      "model_code": 0,
      "person_responsible_number": 223,
      "stocks": [
        {
          "id": 1224265,
          "number": 10,
          "free_saldo": 6,
          "saldo_incoming": 0,
          "saldo_out": 0,
          "is_default": true,
          "in_stock": 6,
          "in_stock_min": 5,
          "Stock_inward": 0,
          "stock_outward": 0,
          "stock_outward_production": 0,
          "previous_shelf": "",
          "stock_description": "ESPOO",
          "stock_average_prchase_price": 6.831,
          "stock_inventory_date": "2020-12-31T00:00:00",
          "stock_shelf_type": -1,
          "sizes": [],
          "shelves": [
            {
              "id": 183631,
              "product_id": 35784,
              "stock_number": 10,
              "stock_shelf": "",
              "in_stock": 6,
              "in_date": "2024-05-17T11:36:35.457",
              "out_date": "2024-08-19T11:58:28.417",
              "inventory_tmp": 0,
              "inventory_bit": false,
              "inventory_date": null,
              "shelf_type": 0,
              "shelf_instock_min": 0
            }
          ]
        },
        {
          "id": 1586749,
          "number": 403,
          "free_saldo": 0,
          "saldo_incoming": 0,
          "saldo_out": 1,
          "is_default": false,
          "in_stock": 1,
          "in_stock_min": 1,
          "Stock_inward": 0,
          "stock_outward": 1,
          "stock_outward_production": 0,
          "previous_shelf": "LATTIAPAIKKA",
          "stock_description": "TAMPERE",
          "stock_average_prchase_price": 6.83,
          "stock_inventory_date": "2023-10-13T12:50:14",
          "stock_shelf_type": -1,
          "sizes": [],
          "shelves": [
            {
              "id": 544316,
              "product_id": 35784,
              "stock_number": 403,
              "stock_shelf": "LATTIAPAIKKA",
              "in_stock": 1,
              "in_date": "2024-08-20T14:23:19.427",
              "out_date": "2024-08-07T14:44:16.213",
              "inventory_tmp": 0,
              "inventory_bit": false,
              "inventory_date": null,
              "shelf_type": 0,
              "shelf_instock_min": 0
            }
          ]
        },
        {
          "id": 1583725,
          "number": 405,
          "free_saldo": 0,
          "saldo_incoming": 0,
          "saldo_out": 0,
          "is_default": false,
          "in_stock": 0,
          "in_stock_min": 0,
          "Stock_inward": 0,
          "stock_outward": 0,
          "stock_outward_production": 0,
          "previous_shelf": "",
          "stock_description": "SUUTARILA",
          "stock_average_prchase_price": 0,
          "stock_inventory_date": "2023-12-15T23:59:59",
          "stock_shelf_type": -1,
          "sizes": [],
          "shelves": [
            {
              "id": 541059,
              "product_id": 35784,
              "stock_number": 405,
              "stock_shelf": "",
              "in_stock": 0,
              "in_date": null,
              "out_date": null,
              "inventory_tmp": 0,
              "inventory_bit": false,
              "inventory_date": "2023-12-15T23:59:59",
              "shelf_type": 0,
              "shelf_instock_min": 0
            }
          ]
        },
        {
          "id": 1511348,
          "number": 406,
          "free_saldo": 2,
          "saldo_incoming": 0,
          "saldo_out": 0,
          "is_default": false,
          "in_stock": 2,
          "in_stock_min": 2,
          "Stock_inward": 0,
          "stock_outward": 0,
          "stock_outward_production": 0,
          "previous_shelf": "HäkkiA11",
          "stock_description": "LEMPÄÄLÄ LIIKEKULMA",
          "stock_average_prchase_price": 6.83,
          "stock_inventory_date": "2023-11-13T14:01:58",
          "stock_shelf_type": -1,
          "sizes": [],
          "shelves": [
            {
              "id": 389789,
              "product_id": 35784,
              "stock_number": 406,
              "stock_shelf": "HäkkiA11",
              "in_stock": 2,
              "in_date": "2024-05-21T10:47:27.647",
              "out_date": "2024-09-03T10:29:55.163",
              "inventory_tmp": 0,
              "inventory_bit": false,
              "inventory_date": null,
              "shelf_type": 0,
              "shelf_instock_min": 0
            }
          ]
        }
      ],
      "cn_code": "39174000",
      "ean_code": "6415895159711",
      "group_code": 104110,
      "ser_code": 0,
      "height": 0,
      "length": 0,
      "width": 0,
      "manufacturer": 0,
      "origin": "PL",
      "reference": "",
      "warranty": 0,
      "version": "D /  Z / 3",
      "drawing_number": "",
      "machine": {
        "code": "",
        "description": ""
      },
      "attribute_data": [
        {
          "id": 0,
          "name": "",
          "product_id": 0,
          "codelist_id": 0,
          "value": 0,
          "min": 0,
          "max": 0,
          "type": 0
        }
      ],
      "suppliers": [
        {
          "supplier_id": 35361,
          "product_id": 35784,
          "name": "MAGNAPLAST",
          "is_default": false,
          "number": 150034,
          "code": "23140",
          "delivery_days": 28,
          "note": "",
          "url": "",
          "description": "Bend 200 x 88,5 SN8",
          "description2": "",
          "price": 0,
          "stock_amount": 0,
          "purchase_price": 5.06,
          "purchase_price_in_currency": 0,
          "currency_code": "EUR",
          "discount": 0,
          "discount_code": "",
          "price_update_date": "2024-05-08T00:00:00",
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 1.35,
          "pricefactor_purchase_invoices": 1.35
        },
        {
          "supplier_id": 74767,
          "product_id": 35784,
          "name": "ONNINEN OY",
          "is_default": false,
          "number": 9007,
          "code": "",
          "delivery_days": 0,
          "note": "",
          "url": "",
          "description": "",
          "description2": "",
          "price": 65.6,
          "stock_amount": 0,
          "purchase_price": 0,
          "purchase_price_in_currency": 0,
          "currency_code": "",
          "discount": 42,
          "discount_code": "A7F",
          "price_update_date": null,
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 0,
          "pricefactor_purchase_invoices": 0
        },
        {
          "supplier_id": 118288,
          "product_id": 35784,
          "name": "ONNINEN OY",
          "is_default": false,
          "number": 9007,
          "code": "23140",
          "delivery_days": 0,
          "note": "",
          "url": "",
          "description": "Bend 200 x 88,5 SN8",
          "description2": "",
          "price": 65.6,
          "stock_amount": 0,
          "purchase_price": 0,
          "purchase_price_in_currency": 0,
          "currency_code": "",
          "discount": 42,
          "discount_code": "A7F",
          "price_update_date": null,
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 0,
          "pricefactor_purchase_invoices": 0
        },
        {
          "supplier_id": 157278,
          "product_id": 35784,
          "name": "DAHL OY",
          "is_default": false,
          "number": 9006,
          "code": "DS08",
          "delivery_days": 0,
          "note": "",
          "url": "",
          "description": "",
          "description2": "",
          "price": 33.32,
          "stock_amount": 0,
          "purchase_price": 0,
          "purchase_price_in_currency": 0,
          "currency_code": "",
          "discount": 71,
          "discount_code": "006200",
          "price_update_date": "2013-05-21T00:00:00",
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 0,
          "pricefactor_purchase_invoices": 0
        },
        {
          "supplier_id": 224562,
          "product_id": 35784,
          "name": "Wavin Finland Oy",
          "is_default": false,
          "number": 10949,
          "code": "3072519",
          "delivery_days": 28,
          "note": "",
          "url": "",
          "description": "",
          "description2": "",
          "price": 0,
          "stock_amount": 0,
          "purchase_price": 10.11,
          "purchase_price_in_currency": 0,
          "currency_code": "EUR",
          "discount": 0,
          "discount_code": "",
          "price_update_date": "2024-03-01T00:00:00",
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 1,
          "pricefactor_purchase_invoices": 1
        },
        {
          "supplier_id": 250294,
          "product_id": 35784,
          "name": "AHLSELL OY",
          "is_default": false,
          "number": 9003,
          "code": "",
          "delivery_days": 0,
          "note": "",
          "url": "",
          "description": "",
          "description2": "",
          "price": 72.69,
          "stock_amount": 0,
          "purchase_price": 19.48,
          "purchase_price_in_currency": 0,
          "currency_code": "",
          "discount": 0,
          "discount_code": "P22040",
          "price_update_date": "2021-10-06T00:00:00",
          "stock_date": null,
          "origin": "",
          "pricefactor_orders": 1.03,
          "pricefactor_purchase_invoices": 1.03
        },
        {
          "supplier_id": 361061,
          "product_id": 35784,
          "name": "TOLAGO",
          "is_default": true,
          "number": 15291,
          "code": "0710252390",
          "delivery_days": 40,
          "note": "",
          "url": "",
          "description": "PP bend with 1 socket 200x87,5°",
          "description2": "",
          "price": 0,
          "stock_amount": 0,
          "purchase_price": 5.68,
          "purchase_price_in_currency": 0,
          "currency_code": "",
          "discount": 0,
          "discount_code": "",
          "price_update_date": "2024-11-28T00:00:00",
          "stock_date": null,
          "origin": "SE",
          "pricefactor_orders": 1.16,
          "pricefactor_purchase_invoices": 1.16
        }
      ],
      "languages": [
        {
          "id": 5657,
          "product_id": 35784,
          "code": "",
          "name": "",
          "extra_name": ""
        },
        {
          "id": 18788,
          "product_id": 35784,
          "code": "ENG",
          "name": "PVC-U ELBOW 200 X 88.5",
          "extra_name": ""
        },
        {
          "id": 25755,
          "product_id": 35784,
          "code": "SWE",
          "name": "VINKELKOPPLING NAL PVC 200 X 88,5",
          "extra_name": ""
        }
      ],
      "attributes": [
        {
          "id": 1,
          "name": "1. Valmistus",
          "selected": false
        },
        {
          "id": 2,
          "name": "2. Valmistus, puolivalmiste",
          "selected": false
        },
        {
          "id": 3,
          "name": "3. Raaka-aine",
          "selected": false
        },
        {
          "id": 4,
          "name": "4. Osto-osa",
          "selected": false
        },
        {
          "id": 5,
          "name": "5. Pikavalintatuote (kassa)",
          "selected": false
        },
        {
          "id": 6,
          "name": "6. Varastoyksikkö=>myyntiyksikkö",
          "selected": false
        },
        {
          "id": 7,
          "name": "7. Resurssi",
          "selected": false
        },
        {
          "id": 8,
          "name": "8. Työ",
          "selected": false
        },
        {
          "id": 9,
          "name": "9. Puolivalmisteet tuotantoon",
          "selected": false
        },
        {
          "id": 10,
          "name": "10. Web-tuote",
          "selected": true
        },
        {
          "id": 11,
          "name": "11. Tuotetarra",
          "selected": false
        },
        {
          "id": 12,
          "name": "12. Alihankinta",
          "selected": false
        },
        {
          "id": 13,
          "name": "13. Kiinnitetty tuoterakenne",
          "selected": false
        },
        {
          "id": 14,
          "name": "14. Kulukorvaus",
          "selected": false
        },
        {
          "id": 15,
          "name": "15. Vuokratuote 5 pv",
          "selected": false
        },
        {
          "id": 16,
          "name": "16. Vuokratuote 7 pv",
          "selected": false
        },
        {
          "id": 17,
          "name": "17. Web-helpdesk",
          "selected": false
        },
        {
          "id": 18,
          "name": "18. Sopimustuote",
          "selected": false
        },
        {
          "id": 19,
          "name": "19. Rakenneotsikko",
          "selected": false
        },
        {
          "id": 20,
          "name": "20. Hyvityksessä ostohinta",
          "selected": false
        },
        {
          "id": 21,
          "name": "21. Kuljetus/pakkausyksikkö",
          "selected": false
        },
        {
          "id": 22,
          "name": "22. Kanta-asiakastuote",
          "selected": false
        },
        {
          "id": 23,
          "name": "23. Kampanjapaketti",
          "selected": false
        },
        {
          "id": 24,
          "name": "24. Väri",
          "selected": false
        },
        {
          "id": 25,
          "name": "25. Raaka-arkki",
          "selected": false
        },
        {
          "id": 26,
          "name": "26. Ei ABC-ryhmän päivitystä",
          "selected": false
        },
        {
          "id": 27,
          "name": "27. Ei hälytysrajan päivitystä",
          "selected": false
        },
        {
          "id": 28,
          "name": "28. Optimoi nimike aina",
          "selected": false
        },
        {
          "id": 29,
          "name": "29. Ei Kerättävä",
          "selected": false
        },
        {
          "id": 30,
          "name": "30. POISTUVA TUOTE",
          "selected": false
        },
        {
          "id": 31,
          "name": "31. HINNASTOTUOTE",
          "selected": true
        },
        {
          "id": 32,
          "name": "32. PROJEKTITUOTE",
          "selected": false
        },
        {
          "id": 33,
          "name": "33. VARASTOTUOTE",
          "selected": true
        },
        {
          "id": 34,
          "name": "34. I",
          "selected": false
        },
        {
          "id": 35,
          "name": "35. K",
          "selected": false
        },
        {
          "id": 36,
          "name": "36. LV",
          "selected": false
        },
        {
          "id": 37,
          "name": "37. VERKKOKAUPPANOSTO ETUSIVU",
          "selected": false
        },
        {
          "id": 38,
          "name": "38. VERKKOKAUPPA KATEGORIANOSTO",
          "selected": false
        },
        {
          "id": 39,
          "name": "39. KATALOGITUOTE",
          "selected": true
        },
        {
          "id": 40,
          "name": "40. EI VUOSIHYVITETTÄ",
          "selected": false
        },
        {
          "id": 41,
          "name": "41. SUPERSERVICE",
          "selected": false
        },
        {
          "id": 42,
          "name": "42. VAIN NOUTO SALLITTU",
          "selected": false
        },
        {
          "id": 43,
          "name": "43. TARVII.FI",
          "selected": true
        }
      ],
      "categories": [],
      "is_serialnumber_followup": false,
      "serialnumber_type": 0,
      "is_batchfollowup": false,
      "links": [
        {
          "id": 21089,
          "application_id": 2,
          "object_id": 35784,
          "target": "\\\\lvisrv07\\Yhteiset\\LVI-WaBek Oy\\Tuotetiedot\\Tiedostot\\products\\4110\\",
          "description": "Sertifikaatit",
          "type": "",
          "codelist_type": 1
        }
      ],
      "abc": 0,
      "vak": "",
      "un": "",
      "handedness": "",
      "material": "",
      "family": 10411001,
      "lta": "",
      "pricing": {
        "average_price": 15.7134,
        "previous_price": 6.83,
        "previous_purchase_price": 6.83,
        "net_price": 4.7407
      },
      "purchase_account": "",
      "purchase_account_tax_rate": null,
      "default_discount": 0
    }
  ],
  "result_count": 1,
  "has_next_page": false,
  "has_errors": false,
  "errors": []
}


post /api/products
Create a product

{
  "id": 0,
  "name": "string",
  "extra_name": "string",
  "sku": "string",
  "price": 0,
  "price_includes_tax": true,
  "texts": [
    {
      "id": 0,
      "language_code": "string",
      "header_number": 0,
      "text": "string",
      "text_plain": "string"
    }
  ],
  "units": [
    {
      "id": 0,
      "product_id": 0,
      "package": 0,
      "unit": "string",
      "amount": 0,
      "code": "string",
      "default_amount": 0,
      "discount": 0,
      "price": 0,
      "price_per": 0,
      "use_for_pricing": true,
      "use_for_purchase": true,
      "use_for_sales": true,
      "use_for_stock": true,
      "volume": 0,
      "weight": 0,
      "package_weight": 0,
      "use_intrastat": true,
      "intrastat_amount": 0,
      "default_amount_purchase": 0,
      "default_amount_production": 0,
      "handling_cost_id": 0
    }
  ],
  "dimensions": "string",
  "is_inactive": true,
  "is_non_stock": true,
  "is_sellable": true,
  "is_purchase_product": true,
  "search_code": "string",
  "size_type": 0,
  "type": 0,
  "type_description": "string",
  "stock_unit": "string",
  "sales_price_taxful": 0,
  "sales_price_taxless": 0,
  "sales_account": "string",
  "taxrate_code": 0,
  "cost_center": "string",
  "unit_id": 0,
  "color_code": 0,
  "mark_code": 0,
  "model_code": 0,
  "person_responsible_number": 0,
  "stocks": [
    {
      "id": 0,
      "number": 0,
      "free_saldo": 0,
      "saldo_incoming": 0,
      "saldo_out": 0,
      "is_default": true,
      "in_stock": 0,
      "in_stock_min": 0,
      "Stock_inward": 0,
      "stock_outward": 0,
      "stock_outward_production": 0,
      "previous_shelf": "string",
      "stock_description": "string",
      "stock_average_prchase_price": 0,
      "stock_inventory_date": "2025-07-04T14:59:14.130Z",
      "stock_shelf_type": 0,
      "sizes": [
        {
          "id": 0,
          "stock_id": 0,
          "size": "string",
          "in_stock": 0,
          "in_stock_min": 0,
          "inward": 0,
          "outward": 0,
          "sort_order": 0
        }
      ],
      "shelves": [
        {
          "id": 0,
          "product_id": 0,
          "stock_number": 0,
          "stock_shelf": "string",
          "in_stock": 0,
          "in_date": "2025-07-04T14:59:14.130Z",
          "out_date": "2025-07-04T14:59:14.130Z",
          "inventory_tmp": 0,
          "inventory_bit": true,
          "inventory_date": "2025-07-04T14:59:14.130Z",
          "shelf_type": 0,
          "shelf_instock_min": 0
        }
      ]
    }
  ],
  "cn_code": "string",
  "ean_code": "string",
  "group_code": 0,
  "ser_code": 0,
  "height": 0,
  "length": 0,
  "width": 0,
  "manufacturer": 0,
  "origin": "string",
  "reference": "string",
  "warranty": 0,
  "version": "string",
  "drawing_number": "string",
  "machine": {
    "code": "string",
    "description": "string"
  },
  "attribute_data": [
    {
      "id": 0,
      "name": "string",
      "product_id": 0,
      "codelist_id": 0,
      "value": 0,
      "min": 0,
      "max": 0,
      "type": 0
    }
  ],
  "suppliers": [
    {
      "supplier_id": 0,
      "product_id": 0,
      "name": "string",
      "is_default": true,
      "number": 0,
      "code": "string",
      "delivery_days": 0,
      "note": "string",
      "url": "string",
      "description": "string",
      "description2": "string",
      "price": 0,
      "stock_amount": 0,
      "purchase_price": 0,
      "purchase_price_in_currency": 0,
      "currency_code": "string",
      "discount": 0,
      "discount_code": "string",
      "price_update_date": "2025-07-04T14:59:14.131Z",
      "stock_date": "2025-07-04T14:59:14.131Z",
      "origin": "string",
      "pricefactor_orders": 0,
      "pricefactor_purchase_invoices": 0
    }
  ],
  "languages": [
    {
      "id": 0,
      "product_id": 0,
      "code": "string",
      "name": "string",
      "extra_name": "string"
    }
  ],
  "attributes": [
    {
      "id": 0,
      "name": "string",
      "selected": true
    }
  ],
  "categories": [
    {
      "id": 0,
      "parent_id": 0,
      "name": "string",
      "type": 0,
      "is_web": true,
      "is_member": true
    }
  ],
  "is_serialnumber_followup": true,
  "serialnumber_type": 0,
  "is_batchfollowup": true,
  "links": [
    {
      "id": 0,
      "application_id": 0,
      "object_id": 0,
      "target": "string",
      "description": "string",
      "type": "string",
      "codelist_type": 0
    }
  ],
  "abc": 0,
  "vak": "string",
  "un": "string",
  "handedness": "string",
  "material": "string",
  "family": 0,
  "lta": "string",
  "pricing": {
    "average_price": 0,
    "previous_price": 0,
    "previous_purchase_price": 0,
    "net_price": 0
  },
  "purchase_account": "string",
  "purchase_account_tax_rate": 0,
  "default_discount": 0
}


put /api/products
Update product

{
  "id": 0,
  "name": "string",
  "extra_name": "string",
  "sku": "string",
  "price": 0,
  "price_includes_tax": true,
  "texts": [
    {
      "id": 0,
      "language_code": "string",
      "header_number": 0,
      "text": "string",
      "text_plain": "string"
    }
  ],
  "units": [
    {
      "id": 0,
      "product_id": 0,
      "package": 0,
      "unit": "string",
      "amount": 0,
      "code": "string",
      "default_amount": 0,
      "discount": 0,
      "price": 0,
      "price_per": 0,
      "use_for_pricing": true,
      "use_for_purchase": true,
      "use_for_sales": true,
      "use_for_stock": true,
      "volume": 0,
      "weight": 0,
      "package_weight": 0,
      "use_intrastat": true,
      "intrastat_amount": 0,
      "default_amount_purchase": 0,
      "default_amount_production": 0,
      "handling_cost_id": 0
    }
  ],
  "dimensions": "string",
  "is_inactive": true,
  "is_non_stock": true,
  "is_sellable": true,
  "is_purchase_product": true,
  "search_code": "string",
  "size_type": 0,
  "type": 0,
  "type_description": "string",
  "stock_unit": "string",
  "sales_price_taxful": 0,
  "sales_price_taxless": 0,
  "sales_account": "string",
  "taxrate_code": 0,
  "cost_center": "string",
  "unit_id": 0,
  "color_code": 0,
  "mark_code": 0,
  "model_code": 0,
  "person_responsible_number": 0,
  "stocks": [
    {
      "id": 0,
      "number": 0,
      "free_saldo": 0,
      "saldo_incoming": 0,
      "saldo_out": 0,
      "is_default": true,
      "in_stock": 0,
      "in_stock_min": 0,
      "Stock_inward": 0,
      "stock_outward": 0,
      "stock_outward_production": 0,
      "previous_shelf": "string",
      "stock_description": "string",
      "stock_average_prchase_price": 0,
      "stock_inventory_date": "2025-07-04T14:59:14.215Z",
      "stock_shelf_type": 0,
      "sizes": [
        {
          "id": 0,
          "stock_id": 0,
          "size": "string",
          "in_stock": 0,
          "in_stock_min": 0,
          "inward": 0,
          "outward": 0,
          "sort_order": 0
        }
      ],
      "shelves": [
        {
          "id": 0,
          "product_id": 0,
          "stock_number": 0,
          "stock_shelf": "string",
          "in_stock": 0,
          "in_date": "2025-07-04T14:59:14.215Z",
          "out_date": "2025-07-04T14:59:14.215Z",
          "inventory_tmp": 0,
          "inventory_bit": true,
          "inventory_date": "2025-07-04T14:59:14.215Z",
          "shelf_type": 0,
          "shelf_instock_min": 0
        }
      ]
    }
  ],
  "cn_code": "string",
  "ean_code": "string",
  "group_code": 0,
  "ser_code": 0,
  "height": 0,
  "length": 0,
  "width": 0,
  "manufacturer": 0,
  "origin": "string",
  "reference": "string",
  "warranty": 0,
  "version": "string",
  "drawing_number": "string",
  "machine": {
    "code": "string",
    "description": "string"
  },
  "attribute_data": [
    {
      "id": 0,
      "name": "string",
      "product_id": 0,
      "codelist_id": 0,
      "value": 0,
      "min": 0,
      "max": 0,
      "type": 0
    }
  ],
  "suppliers": [
    {
      "supplier_id": 0,
      "product_id": 0,
      "name": "string",
      "is_default": true,
      "number": 0,
      "code": "string",
      "delivery_days": 0,
      "note": "string",
      "url": "string",
      "description": "string",
      "description2": "string",
      "price": 0,
      "stock_amount": 0,
      "purchase_price": 0,
      "purchase_price_in_currency": 0,
      "currency_code": "string",
      "discount": 0,
      "discount_code": "string",
      "price_update_date": "2025-07-04T14:59:14.215Z",
      "stock_date": "2025-07-04T14:59:14.215Z",
      "origin": "string",
      "pricefactor_orders": 0,
      "pricefactor_purchase_invoices": 0
    }
  ],
  "languages": [
    {
      "id": 0,
      "product_id": 0,
      "code": "string",
      "name": "string",
      "extra_name": "string"
    }
  ],
  "attributes": [
    {
      "id": 0,
      "name": "string",
      "selected": true
    }
  ],
  "categories": [
    {
      "id": 0,
      "parent_id": 0,
      "name": "string",
      "type": 0,
      "is_web": true,
      "is_member": true
    }
  ],
  "is_serialnumber_followup": true,
  "serialnumber_type": 0,
  "is_batchfollowup": true,
  "links": [
    {
      "id": 0,
      "application_id": 0,
      "object_id": 0,
      "target": "string",
      "description": "string",
      "type": "string",
      "codelist_type": 0
    }
  ],
  "abc": 0,
  "vak": "string",
  "un": "string",
  "handedness": "string",
  "material": "string",
  "family": 0,
  "lta": "string",
  "pricing": {
    "average_price": 0,
    "previous_price": 0,
    "previous_purchase_price": 0,
    "net_price": 0
  },
  "purchase_account": "string",
  "purchase_account_tax_rate": 0,
  "default_discount": 0
}


get /api/products/{id}
Get product
Parameters
Parameter
id	
(required)







get /api/products/transactions
Get stock transactions by filters

Response Class (Status 200)
OK

ModelExample Value
{}


Response Content Type 
application/json
Parameters
Parameter	Value	Description	Parameter Type	Data Type
filter.id	
query	integer
filter.product_code	
query	string
filter.stock_number	
query	integer
filter.modified_before	
query	date-time
filter.modified_after	
query	date-time
filter.transaction_date_before	
query	date-time
filter.transaction_date_after	
query	date-time
filter.page	
query	integer
filter.page_size	
query	integer
filter.type	
query	integer
filter.source	
query	integer
filter.search	
query	string
filter.person	
query	integer
filter.work_number	
query	integer
filter.getSalesOrderNumber	
query	boolean










post /api/products/transactions
Create new stock transaction


{
  "id": 0,
  "description": "string",
  "net_price": 0,
  "person": 0,
  "product_code": "string",
  "sales_price": 0,
  "sec_type": 0,
  "shelf": "string",
  "source": 0,
  "stock_number": 0,
  "stock_number_in": 0,
  "supplier": 0,
  "type": 0,
  "type_description": "string",
  "worknumber": 0,
  "amount": 0,
  "costcenter": "string",
  "date": "2025-07-04T14:59:17.063Z",
  "price_type": 0,
  "project_number": 0,
  "project_phase_id": 0,
  "default_shelf": "string",
  "stock_unit": "string",
  "batch_numbers": [
    {
      "batchnr_amount": 0,
      "batchnr_best_before": "2025-07-04T14:59:17.063Z",
      "batchnr_dimension": "string",
      "batchnr_height": 0,
      "batchnr_id": 0,
      "batchnr_info1": "string",
      "batchnr_info2": "string",
      "batchnr_info3": "string",
      "batchnr_info4": "string",
      "batchnr_length": 0,
      "batchnr_product_code": "string",
      "batchnr_saldo": 0,
      "batchnr_state": 0,
      "batchnr_suppliercode": "string",
      "batchnr_tmp_amount": 0,
      "batchnr_width": 0,
      "stock_transaction_id": 0,
      "batchnr_stock_number": 0,
      "batchnr_stock_shelf": "string",
      "batchnr_pallet_id": 0,
      "batchnr_inventory_tmp": 0,
      "batchno_inventory_bit": true
    }
  ],
  "serial_numbers": [
    {
      "serialnr_id": 0,
      "stock_transaction_id": 0,
      "serialnr_product_code": "string",
      "serialnr_code": "string",
      "serialnr_father_serial": "string",
      "serialnr_description": "string",
      "serialnr_state": 0,
      "serialnr_stock_number": 0,
      "serialnr_inventory_tmp": 0
    }
  ],
  "sizes": [
    {
      "id": 0,
      "row_id": 0,
      "size": "string",
      "ean": "string",
      "amount": 0,
      "dlvr_amount": 0,
      "total_dlvr_amount": 0,
      "sort_order": 0
    }
  ],
  "fail_codes": [
    {
      "id": 0,
      "codelist_id": 0,
      "transaction_id": 0,
      "description": "string"
    }
  ],
  "shelves": [
    {
      "id": 0,
      "stock_transaction_id": 0,
      "shelf": "string",
      "amount": 0,
      "shelf_and_saldo": "string",
      "is_inventory": true
    }
  ]
}