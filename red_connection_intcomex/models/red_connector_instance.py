# -*- coding: utf-8 -*-
#################################################################################
# Author      : RedEcommerce.
# Copyright(c): 2021-Present RedEcommerce.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
import hashlib
import requests

from odoo import api, fields, models
from datetime import datetime

class RedConnectorInstance(models.Model):
    _inherit="red.connector.instance"

    provider_id = fields.Selection(selection_add=[('intcomex','Intcomex')],ondelete={'intcomex':'set default'})
    int_api_key = fields.Char('API Key')
    int_access_key = fields.Char('Access Key')
    int_url_get_products = fields.Char('URL Get Products')
    int_url_get_stock = fields.Char('URL Stock')
    int_url_get_price = fields.Char('URL Price')

    def intcomex_run_process_products(self):
        count_create = 0
        try:
            data,code_response = self.execute_connection_intcomex(self.int_url_get_products)

            if code_response != 200:
                self.create_log_connector(self.id, 'intcomex', 'create_product', 'error', "%s: %s" % (str(code_response), str(data)), 0)
            else:
                # Create Product
                count_create = self.create_products(data)
                # Create Log Connection
                self.create_log_connector(self.id, 'intcomex', 'create_product', 'success', "Products Created", count_create)
        except Exception as ex:
            return self.create_log_connector(self.id, 'intcomex', 'create_product', 'error',"%s" % (str(ex)), 0)

    def intcomex_run_update_process_products(self):
        count_stock = 0
        count_price = 0
        products = self.env['product.template'].search([('provider_id','=','intcomex'),('no_update_byprovider','=',False)])
        products_dict = {pr.sku_provider:[pr.list_price,pr,pr.qty_stock_provider] for pr in products}
        existing_products = {pr.sku_provider:pr for pr in products}
        intcomex_sku_response = []

        #Process Stock
        try:
            data, code_response = self.execute_connection_intcomex(self.int_url_get_stock)

            if code_response != 200:
                # Create Log Connection
                return self.create_log_connector(self.id, 'intcomex', 'update_stock', 'error',"%s: %s" % (str(code_response), str(data)), 0)
            else:
                for item in data:
                    prod_stock = products_dict.get(item['Sku'], False)
                    intcomex_sku_response.append(item['Sku'])
                    if prod_stock:
                        values = {'product':prod_stock,'items':item}
                        # Update Product
                        count_stock += self.update_stock(values, prod_stock[1])
        except Exception as ex:
            # Create Log Connection
            return self.create_log_connector(self.id, 'intcomex', 'update_stock', 'error', "%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'intcomex', 'update_stock', 'success', "Products Stock Updated: %s" % (str(count_stock) if count_stock > 0 else 'No changes for update'), count_stock)

        try:
            #Process Price
            data, code_response = self.execute_connection_intcomex(self.int_url_get_price)

            if code_response != 200:
                # Create Log Connection
                return self.create_log_connector(self.id, 'intcomex', 'update_price', 'error',"%s: %s" % (str(code_response), str(data)), 0)
            else:
                for item in data:
                    prod_price = products_dict.get(item['Sku'], False)
                    intcomex_sku_response.append(item['Sku'])
                    if prod_price:
                        values = {'product': prod_price,'items':item}
                        count_price += self.update_price(values, prod_price[1])
        except Exception as ex:
            # Create Log Connection
           return self.create_log_connector(self.id, 'intcomex', 'update_price', 'error', "%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'intcomex', 'update_price', 'success',"Products Price Updated: %s" % (str(count_price) if count_price > 0 else 'No changes for update'),count_price)

        # Run Unpublished Product Process
        if self.unpublish_product_present:
            self.unpublished_products(existing_products, intcomex_sku_response)

    def intcomex_generate_product_values(self,values):
        # Search Products
        products = self.env['product.template'].search([('provider_id', '=', 'intcomex')]).mapped('sku_provider')

        # Brands
        brands_search = self.env['product.brand'].search([])
        brands = {br.name.upper():br.id for br in brands_search}

        #Tuple Prodcuts
        tuple_products = list()

        for item in values:
            if item['Sku'] not in products:
                # Split Name
                if " - " in item['Description']:
                    name = item['Description'].split(" - ")
                    name_split = " - ".join(name[:3])
                else:
                    name_split = item['Description']

                # Check Brand
                brands, brand_intcomex = self.check_brand(brands, item['Brand']['Description'].strip())

                # Get Price
                price_final = self.calculate_price(item['Price']['UnitPrice'])

                #Add Product to Tupple
                tuple_products.append({
                    'name': name_split,
                    'type': 'product',
                    'website_description': item['Description'],
                    'sku_provider': item['Sku'],
                    'provider_category': item['Category']['Description'] +"/"+ item['Category']['Subcategories'][0]['Description'] if item['Category']['Subcategories'] and item['Category']['Description'] else "",
                    'provider_id': 'intcomex',
                    'instance_id':self.id,
                    'is_published': True if 'InStock' in item and int(item["InStock"]) > 0 else False,
                    'product_brand_id': brand_intcomex,
                    'list_price': price_final,
                    'qty_stock_provider': int(item['InStock']) if 'InStock' in item else 0,
                    'price_sale_provider': item['Price']['UnitPrice'] if 'Price' in item else 1.0,
                    'price_cost_provider': item['Price']['UnitPrice'] if 'Price' in item else 0.0,
                })
        count_create = len(tuple_products)
        return tuple_products

    def intcomex_generate_product_valstock_update(self,values):
        prod_stock = values.get('product')
        item = values.get('items')
        vals_update = {}

        if 'InStock' in item and item["InStock"] != prod_stock[2]:
            if item['InStock'] == None or item['InStock'] == "0":
                vals_update['qty_stock_provider'] = 0
                vals_update['is_published'] = False
            else:
                vals_update['qty_stock_provider'] = int(item['InStock'])
                vals_update['is_published'] = True
        elif not prod_stock[1].is_published and item["InStock"] > 0:
            vals_update['qty_stock_provider'] = int(item['InStock'])
            vals_update['is_published'] = True
        elif prod_stock[1].is_published and item['InStock'] == None or item['InStock'] == "0":
            vals_update['qty_stock_provider'] = 0
            vals_update['is_published'] = False

        return vals_update

    def intcomex_generate_product_valprice_update(self, values):
        product = values['product']
        item = values.get('items')
        vals_update = {}

        # Get Price
        price_final = self.calculate_price(item['Price']['UnitPrice'])

        if price_final != product[0]:
            vals_update.update({
                'list_price': price_final,
                'price_sale_provider': item['Price']['UnitPrice'],
                'price_cost_provider': item['Price']['UnitPrice'],
            })

        return vals_update

    def execute_connection_intcomex(self,int_url):
        #Actual Date
        utcTimeStamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        #URL
        url = int_url + "?utcTimeStamp=" + utcTimeStamp

        #Generate Sign
        sign = '%s,%s,%s' % (self.int_api_key, self.int_access_key, utcTimeStamp)

        # Genero Firma
        hash_object = hashlib.sha256(sign.encode('utf-8'))

        params = {
            'apiKey': self.int_api_key,
            'signature': hash_object.hexdigest(),
            'locale': 'es',
        }

        r = requests.get(url=url, params=params)
        data = r.json()
        code_response = r.status_code

        return data,code_response