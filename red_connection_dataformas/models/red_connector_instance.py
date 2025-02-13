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

    provider_id = fields.Selection(selection_add=[('dataformas','Dataformas')],ondelete={'dataformas':'set default'})
    dataformas_url = fields.Char('URL Service')
    dataformas_token = fields.Char('Token')

    def dataformas_run_process_products(self):
        count_create = 0
        try:
            data = self.execute_connection_dataformas()
            # Create Product
            count_create = self.create_products(data)
            # Create Log Connection
            self.create_log_connector(self.id, 'dataformas', 'create_product', 'success', "Products Created", count_create)
        except Exception as ex:
            return self.create_log_connector(self.id, 'dataformas', 'create_product', 'error',"%s" % (str(ex)), 0)

    def dataformas_run_update_image_products(self):
        count_image = 0
        products =  self.env['product.template'].search([('provider_id', '=', 'dataformas'), ('no_update_byprovider', '=', False),('image_process_update','=',False)],limit=self.max_image_process)
        products_dict = {pr.sku_provider: pr for pr in products}

        try:
            data = self.execute_connection_dataformas()
            # Get values
            for item in data:
                sku_element = item['Sku'].strip()
                if sku_element:
                    product = products_dict.get(sku_element, False)
                    if product:
                        images = [item['Image1'],item['Image2'],item['Image3']]
                        if images:
                            values = {'product':product,'image':images}
                            # Update Product
                            count_image += self.update_image(values,product)
        except Exception as ex:
            return self.create_log_connector(self.id, 'dataformas', 'update_image', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'dataformas', 'update_image', 'success',"Products Image Updated: %s" % (str(count_image) if count_image > 0 else 'No changes for update'), count_image)

    def dataformas_run_update_process_products(self):
        count_update = 0
        products = self.env['product.template'].search([('provider_id','=','dataformas'),('no_update_byprovider','=',False)])
        products_dict = {pr.sku_provider:[pr.list_price,pr,pr.qty_stock_provider] for pr in products}
        existing_products = {pr.sku_provider:pr for pr in products}
        dataformas_sku_response = []

        #Process Update
        try:
            data = self.execute_connection_dataformas()
            for item in data:
                product = products_dict.get(item['Sku'].strip(), False)
                dataformas_sku_response.append(item['Sku'].strip())
                if product:
                    values = {'product':product,'items':item}
                    # Update Product
                    count_update += self.update_product(values, product[1])
        except Exception as ex:
            # Create Log Connection
            return self.create_log_connector(self.id, 'dataformas', 'update_product', 'error', "%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'dataformas', 'update_product', 'success', "Products Stock/Price Updated: %s" % (str(count_update) if count_update > 0 else 'No changes for update'), count_update)

        # Run Unpublished Product Process
        if self.unpublish_product_present:
            self.unpublished_products(existing_products, dataformas_sku_response)

    def dataformas_generate_product_values(self,values):
        image_base64 = False
        # Search Products
        products = self.env['product.template'].search([('provider_id', '=', 'dataformas')]).mapped('sku_provider')

        # Brands
        brands_search = self.env['product.brand'].search([])
        brands = {br.name.upper():br.id for br in brands_search}
        brand_dataformas = False

        #Tuple Prodcuts
        tuple_products = list()

        for item in values:
            sku = item['Sku'].strip()
            name = item['ItemName']
            category = item['Categoria']
            brand = item['Marca']
            price = float(item['Precio'])
            stock = int(float(item['OnHand']))
            image_url = item['Image1']
            images_tuple = []

            if sku not in products:
                if brand:
                    # Check Brand
                    brands, brand_dataformas = self.check_brand(brands, brand)

                # Get Price
                price_final = self.calculate_price(price)

                #Get Image
                images = [item['Image1'], item['Image2'], item['Image3']]

                if self.set_image_create and images:
                    for img in images:
                        if not image_base64:
                            image_base64 = self.dataformas_get_image_base64(img)
                        else:
                            imaget = self.dataformas_get_image_base64(img)
                            images_tuple.append((0,0,{'image_1920':imaget, 'name':'Imagen'}))

                #Add Product to Tupple
                tuple_products.append({
                    'name': name,
                    'type': 'product',
                    'website_description': name,
                    'sku_provider': sku,
                    'provider_category': category,
                    'provider_id': 'dataformas',
                    'instance_id':self.id,
                    'image_1920':image_base64,
                    'image_process_update': True if image_base64 else False,
                    'is_published': True if stock else False,
                    'product_brand_id': brand_dataformas,
                    'list_price': price_final,
                    'product_template_image_ids':images_tuple if images_tuple else False,
                    'qty_stock_provider': stock,
                    'price_sale_provider': price,
                    'price_cost_provider': price,
                })
        count_create = len(tuple_products)
        return tuple_products

    def dataformas_generate_product_values_update(self,values):
        product = values.get('product')
        item = values.get('items')
        price = float(item['Precio'])
        stock = int(float(item['OnHand']))
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

    def dataformas_generate_product_image_update(self, values):
        images = values.get('image')
        vals_update = {}

        for img in images:
            image_base64 = self.dataformas_get_image_base64(img)
            if image_base64:
                if 'image_1920' not in vals_update:
                    vals_update.update({'image_1920': image_base64, 'image_process_update': True})
                elif 'product_template_image_ids' not in vals_update:
                    vals_update.update({'product_template_image_ids':[(0,0,{'image_1920': image_base64, 'name':'Image'})]})
                else:
                    vals_update['product_template_image_ids'].append((0, 0, {'image_1920': image_base64, 'name': 'Image'}))


        return vals_update

    def dataformas_get_image_base64(self,image_url):
        image_base64 = False

        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                return image_base64
        except Exception as ex:
            _logger.info('Error processing Image dataformas in Product with Error: %s' % (str(ex)))
            return image_base64

    def execute_connection_dataformas(self):
        response = self.get_api_dataformas()
        next_page = False
        data = []

        if not response.get('Articulos'):
            return {}
        else:
            data += response.get('Articulos')

        if response.get('NextPage'):
            next_page = True

        while next_page:
            response = self.get_api_dataformas(response.get('NextPage'))
            if response.get('Articulos'):
                data += response.get('Articulos')
            if response.get('NextPage'):
                next_page = True
            else:
                next_page = False

        return data

    def get_api_dataformas(self,next_page=False):
        headers = {
            'Authorization': 'Bearer {}'.format(self.dataformas_token),
            'Content-Type': 'application/json',
        }

        if not next_page:
            response = requests.get(self.dataformas_url, headers=headers)
        else:
            response = requests.get(next_page, headers=headers)

        return response.json()