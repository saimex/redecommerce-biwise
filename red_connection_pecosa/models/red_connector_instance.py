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
import logging
import base64
import requests
import time

from odoo import api, fields, models
from datetime import datetime
from urllib.request import urlopen
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)

class RedConnectorInstance(models.Model):
    _inherit="red.connector.instance"

    provider_id = fields.Selection(selection_add=[('pecosa','Pecosa')],ondelete={'pecosa':'set default'})
    pecosa_path = fields.Char('Path File')

    def pecosa_run_process_products(self):
        count_create = 0
        try:
            data = self.execute_connection_pecosa()
            # Create Product
            count_create = self.create_products(data)
            # Create Log Connection
            self.create_log_connector(self.id, 'pecosa', 'create_product', 'success', "Products Created", count_create)
        except Exception as ex:
            return self.create_log_connector(self.id, 'pecosa', 'create_product', 'error',"%s" % (str(ex)), 0)

    def pecosa_run_update_process_products(self):
        count_update = 0
        products = self.env['product.template'].search([('provider_id','=','pecosa'),('no_update_byprovider','=',False)])
        products_dict = {pr.sku_provider:[pr.list_price,pr,pr.qty_stock_provider] for pr in products}
        existing_products = {pr.sku_provider:pr for pr in products}
        pecosa_sku_response = []

        try:
            data = self.execute_connection_pecosa()
            # Get values
            for item in data.findall('item'):
                sku_element = item.find('sku')
                if sku_element is not None and sku_element.text:
                    product = products_dict.get(item.find('sku').text.strip(), False)
                    pecosa_sku_response.append(item.find('sku').text.strip())
                    if product:
                        values = {'product': product, 'items': item}
                        # Update Product
                        count_update += self.update_product(values,product[1])

            #Run Unpublished Product Process
            if self.unpublish_product_present:
                self.unpublished_products(existing_products,pecosa_sku_response)

        except Exception as ex:
            return self.create_log_connector(self.id, 'pecosa', 'update_product', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'pecosa', 'update_product', 'success',"Products Price/Stock Updated: %s" % (str(count_update) if count_update > 0 else 'No changes for update'), count_update)

    def pecosa_run_update_image_products(self):
        count_image = 0
        products =  self.env['product.template'].search([('provider_id', '=', 'pecosa'), ('no_update_byprovider', '=', False),('image_process_update','=',False)],limit=self.max_image_process)
        products_dict = {pr.sku_provider: pr for pr in products}

        try:
            data = self.execute_connection_pecosa()
            # Get values
            for item in data.findall('item'):
                sku_element = item.find('sku')
                if sku_element is not None and sku_element.text:
                    product = products_dict.get(sku_element.text.strip(), False)
                    if product:
                        values = {'product':product,'image':item.find('IMAGEN').text}
                        # Update Product
                        count_image += self.update_image(values,product)
        except Exception as ex:
            return self.create_log_connector(self.id, 'pecosa', 'update_image', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'pecosa', 'update_image', 'success',"Products Image Updated: %s" % (str(count_image) if count_image > 0 else 'No changes for update'), count_image)

    def pecosa_generate_product_values(self,values):
        # Search Products
        products = self.env['product.template'].search([('provider_id', '=', 'pecosa')]).mapped('sku_provider')

        # Brands
        brands_search = self.env['product.brand'].search([])
        brands = {br.name.upper():br.id for br in brands_search}

        #Tuple Prodcuts
        tuple_products = list()

        for item in values.findall('item'):
            sku = item.find('sku')
            inStock = int(item.find('inStock').text)
            unit_price = float(item.find('unit_price').text)
            name = "%s %s" %(item.find('name').text, '-'+item.find('presentation').text if item.find('presentation') else "")
            brand = item.find('brand').text.strip()
            category = item.find('Categoria').text
            img = item.find('IMAGEN').text
            description = item.find('use_mode').text
            image_base64 = False
            image_process_update = False

            if sku is not None and sku.text and sku.text.strip() not in products:
                sku = sku.text.strip()

                #Check Brand
                brands, brand_pecosa = self.check_brand(brands,brand)

                #Get Price
                price_final = self.calculate_price(unit_price)

                if self.set_image_create:
                    #Get Image
                    if img:
                        try:
                            response = requests.get(img)
                            if response.status_code == 200:
                                image_base64 = base64.b64encode(response.content).decode('utf-8')
                                image_process_update = True
                        except Exception as ex:
                            _logger.info('Error processing Image Pecosa in Product with SKU: %s. Error: %s' % (sku, str(ex)))
                            pass

                #Add Product to Tupple
                tuple_products.append({
                    'name': name,
                    'type': 'product',
                    'website_description': description,
                    'sku_provider': sku,
                    'provider_category': category,
                    'provider_id': 'pecosa',
                    'is_published': True if inStock else False,
                    'product_brand_id': brand_pecosa,
                    'instance_id': self.id,
                    'list_price': price_final,
                    'qty_stock_provider': inStock if inStock else 0,
                    'price_sale_provider': unit_price,
                    'price_cost_provider': unit_price,
                    'image_1920':image_base64,
                    'image_process_update':image_process_update,
                })
        return tuple_products

    def pecosa_generate_product_values_update(self,values):
        product = values.get('product')
        item = values.get('items')
        inStock = int(item.find('inStock').text)
        vals_update = {}

        # Get Price
        price_final = self.calculate_price(round(float(item.find('unit_price').text)))

        if inStock != product[2]:
            vals_update.update({'qty_stock_provider': 0 if not inStock else inStock,'is_published': True if inStock else False})

        if price_final != round(product[0]):
            vals_update.update({
                'list_price': price_final,
                'price_sale_provider': item.find('unit_price').text,
                'price_cost_provider': item.find('unit_price').text
            })

        return vals_update

    def pecosa_generate_product_image_update(self,values):
        product = values.get('product')
        img = values.get('image')
        vals_update = {}

        if img:
            try:
                response = requests.get(img)
                if response.status_code == 200:
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    vals_update.update({'image_1920': image_base64, 'image_process_update': True})
            except Exception as ex:
                _logger.info('Error processing Image Pecosa in Product with ID: %s. Error: %s' %(str(product.id),str(ex)))
                pass

        return vals_update

    def execute_connection_pecosa(self):
        tree = ET.parse(self.pecosa_path)
        root = tree.getroot()
        return root