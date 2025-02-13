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
import xmltodict
import requests
import base64
import logging

from odoo import api, fields, models
from datetime import datetime
from suds.client import Client

_logger = logging.getLogger(__name__)

class RedConnectorInstance(models.Model):
    _inherit="red.connector.instance"

    provider_id = fields.Selection(selection_add=[('eurocomp','Eurocomp')],ondelete={'eurocomp':'set default'})
    eurocomp_url = fields.Char('URL Service')
    eurocomp_ws_cid = fields.Integer('WS CID')
    eurocomp_ws_passwd = fields.Char('Password')
    eurocomp_bid = fields.Integer('Warehouse ID')
    eurocomp_url_image = fields.Char('Image URL')

    def eurocomp_run_process_products(self):
        count_create = 0
        try:
            data = self.execute_connection_eurocomp()
            # Create Product
            count_create = self.create_products(data)
            # Create Log Connection
            self.create_log_connector(self.id, 'eurocomp', 'create_product', 'success', "Products Created", count_create)
        except Exception as ex:
            return self.create_log_connector(self.id, 'eurocomp', 'create_product', 'error',"%s" % (str(ex)), 0)

    def eurocomp_run_update_image_products(self):
        count_image = 0
        products =  self.env['product.template'].search([('provider_id', '=', 'eurocomp'), ('no_update_byprovider', '=', False),('image_process_update','=',False)],limit=self.max_image_process)
        products_dict = {pr.sku_provider: pr for pr in products}

        try:
            data = self.execute_connection_eurocomp()
            # Get values
            for item in data:
                sku_element = item['codigo']['#text'].strip()
                if sku_element:
                    product = products_dict.get(sku_element, False)
                    if product:
                        image_url = item['image_url']['#text'] if '#text' in item['image_url'] else ''
                        if image_url:
                            values = {'product':product,'image':self.eurocomp_url_image+image_url}
                            # Update Product
                            count_image += self.update_image(values,product)
        except Exception as ex:
            return self.create_log_connector(self.id, 'eurocomp', 'update_image', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'eurocomp', 'update_image', 'success',"Products Image Updated: %s" % (str(count_image) if count_image > 0 else 'No changes for update'), count_image)

    def eurocomp_run_update_process_products(self):
        count_update = 0
        products = self.env['product.template'].search([('provider_id','=','eurocomp'),('no_update_byprovider','=',False)])
        products_dict = {pr.sku_provider:[pr.list_price,pr,pr.qty_stock_provider] for pr in products}
        existing_products = {pr.sku_provider:pr for pr in products}
        eurocomp_sku_response = []

        #Process Update
        try:
            data = self.execute_connection_eurocomp()
            for item in data:
                product = products_dict.get(item['codigo']['#text'].strip(), False)
                eurocomp_sku_response.append(item['codigo']['#text'].strip())
                if product:
                    values = {'product':product,'items':item}
                    # Update Product
                    count_update += self.update_product(values, product[1])
        except Exception as ex:
            # Create Log Connection
            return self.create_log_connector(self.id, 'eurocomp', 'update_product', 'error', "%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'eurocomp', 'update_product', 'success', "Products Stock Updated: %s" % (str(count_update) if count_update > 0 else 'No changes for update'), count_update)

        # Run Unpublished Product Process
        if self.unpublish_product_present:
            self.unpublished_products(existing_products, eurocomp_sku_response)

    def eurocomp_generate_product_values(self,values):
        image_base64 = False
        # Search Products
        products = self.env['product.template'].search([('provider_id', '=', 'eurocomp')]).mapped('sku_provider')

        # Brands
        brands_search = self.env['product.brand'].search([])
        brands = {br.name.upper():br.id for br in brands_search}
        brand_eurocomp = False

        #Tuple Prodcuts
        tuple_products = list()

        for item in values:
            sku = item['codigo']['#text'].strip()
            name = item['descripcion']['#text']
            category = item['familia']['#text'] if '#text' in item['familia'] else ''
            brand = item['marca']['#text'].strip() if '#text' in item['marca'] else ''
            price = float(item['precio']['#text'])
            stock = int(float(item['stock']['#text']))
            image_url = item['image_url']['#text'] if '#text' in item['image_url'] else ''

            if sku not in products:
                if brand:
                    # Check Brand
                    brands, brand_eurocomp = self.check_brand(brands, brand)

                # Get Price
                price_final = self.calculate_price(price)

                #Get Image
                if self.set_image_create and image_url:
                    image_base64 = self.eurocomp_get_image_base64(self.eurocomp_url_image+image_url)

                #Add Product to Tupple
                tuple_products.append({
                    'name': name,
                    'type': 'product',
                    'website_description': name,
                    'sku_provider': sku,
                    'provider_category': category,
                    'provider_id': 'eurocomp',
                    'instance_id':self.id,
                    'image_1920':image_base64,
                    'image_process_update':True if image_base64 else False,
                    'is_published': True if stock else False,
                    'product_brand_id': brand_eurocomp,
                    'list_price': price_final,
                    'qty_stock_provider': stock,
                    'price_sale_provider': price,
                    'price_cost_provider': price,
                })
        count_create = len(tuple_products)
        return tuple_products

    def eurocomp_generate_product_values_update(self,values):
        product = values.get('product')
        item = values.get('items')
        price = float(item['precio']['#text'])
        stock = int(float(item['stock']['#text']))
        vals_update = {}

        if stock != product[2]:
            if not stock:
                vals_update['qty_stock_provider'] = 0
                vals_update['is_published'] = False
            else:
                vals_update['qty_stock_provider'] = stock
                vals_update['is_published'] = True
        elif not product[1].is_published and stock > 0:
            vals_update['qty_stock_provider'] = stock
            vals_update['is_published'] = True
        elif product[1].is_published and not stock:
            vals_update['qty_stock_provider'] = 0
            vals_update['is_published'] = False

        # Get Price
        price_final = self.calculate_price(price)

        if price_final != product[0]:
            vals_update.update({
                'list_price': price_final,
                'price_sale_provider': price,
                'price_cost_provider': price,
            })

        return vals_update

    def eurocomp_generate_product_image_update(self, values):
        img = values.get('image')
        vals_update = {}

        image_base64 = self.eurocomp_get_image_base64(img)
        if image_base64:
            vals_update.update({'image_1920': image_base64, 'image_process_update': True})

        return vals_update

    def eurocomp_get_image_base64(self,image_url):
        image_base64 = False

        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                return image_base64
        except Exception as ex:
            _logger.info('Error processing Image Eurocomp in Product with Error: %s' % (str(ex)))
            return image_base64

    def execute_connection_eurocomp(self):
        client_response = Client(self.eurocomp_url, retxml=True)
        response = xmltodict.parse(client_response.service.wsc_request_bodega_all_items(ws_cid=self.eurocomp_ws_cid, ws_passwd=self.eurocomp_ws_passwd, bid=self.eurocomp_bid))
        data = response['SOAP-ENV:Envelope']['SOAP-ENV:Body']['ns1:wsc_request_bodega_all_itemsResponse']['data']['item']
        return data