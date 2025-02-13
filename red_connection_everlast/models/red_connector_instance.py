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
import os

from odoo import api, fields, models,_
from datetime import datetime
from urllib.request import urlopen
from odoo.exceptions import UserError
from io import BytesIO
from PIL import Image

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

_logger = logging.getLogger(__name__)

class RedConnectorInstance(models.Model):
    _inherit="red.connector.instance"

    provider_id = fields.Selection(selection_add=[('everlast','Everlast')],ondelete={'everlast':'set default'})
    everlast_path = fields.Char('Path File')
    everlast_image_path = fields.Char('Everlast Image Path')

    def everlast_run_process_products(self):
        count_create = 0
        try:
            data = self.execute_connection_everlast()
            # Create Product
            count_create = self.create_products(data)
            # Create Log Connection
            self.create_log_connector(self.id, 'everlast', 'create_product', 'success', _("Products Created"), count_create)
        except Exception as ex:
            return self.create_log_connector(self.id, 'everlast', 'create_product', 'error',"%s" % (str(ex)), 0)

    def everlast_run_update_process_products(self):
        count_update = 0
        products = self.env['product.template'].search([('provider_id','=','everlast'),('no_update_byprovider','=',False)])
        products_dict = {pr.sku_provider:[pr.list_price,pr,pr.qty_stock_provider] for pr in products}
        existing_products = {pr.sku_provider:pr for pr in products}
        everlast_sku_response = []

        try:
            data = self.execute_connection_everlast()
            # Get values
            for item in data:
                sku_element = item.get('COD_PROV',False).strip()
                if sku_element:
                    product = products_dict.get(sku_element, False)
                    everlast_sku_response.append(sku_element)
                    if product:
                        values = {'product': product, 'items': item}
                        # Update Product
                        count_update += self.update_product(values,product[1])

            #Run Unpublished Product Process
            if self.unpublish_product_present:
                self.unpublished_products(existing_products,everlast_sku_response)

        except Exception as ex:
            return self.create_log_connector(self.id, 'everlast', 'update_product', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'everlast', 'update_product', 'success',"Products Price Updated: %s" % (str(count_update) if count_update > 0 else 'No changes for update'), count_update)

    def everlast_run_update_image_products(self):
        count_image = 0
        products =  self.env['product.template'].search([('provider_id', '=', 'everlast'), ('no_update_byprovider', '=', False),('image_process_update','=',False)],limit=self.max_image_process)
        products_dict = {pr.sku_provider: pr for pr in products}

        extensions_images = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg','.webp']

        try:
            data = self.execute_connection_everlast()
            # Get values
            for prod in products:
                image_base64 = self.get_image_everlast(prod.sku_provider,extensions_images)
                if image_base64:
                    values = {'image_1920':image_base64,'image_process_update':True}
                    # Update Product
                    count_image += self.update_image(values,prod)
        except Exception as ex:
            return self.create_log_connector(self.id, 'everlast', 'update_image', 'error',"%s" % (str(ex)), 0)

        # Create Success Log
        self.create_log_connector(self.id, 'everlast', 'update_image', 'success',"Products Image Updated: %s" % (str(count_image) if count_image > 0 else 'No changes for update'), count_image)

    def everlast_generate_product_values(self,values):
        # Search Products
        products = self.env['product.template'].search([('provider_id', '=', 'everlast')]).mapped('sku_provider')

        # Brands
        brands_search = self.env['product.brand'].search([])
        brands = {br.name.upper():br.id for br in brands_search}

        #Tuple Prodcuts
        tuple_products = list()

        for item in values:
            sku = item.get('COD_PROV',False).strip()
            inStock = int(item.get('CANTD',0))
            unit_price = 0 if item.get('PRECIOD') == '' else float(item.get('PRECIOD',0))
            name = item.get('DESCRIPCIO').strip()
            brand = item.get('MARCA').strip()
            category = item.get('CATEGORIA').strip()
            image_base64 = False
            image_process_update = False

            if sku:
                #Check Brand
                brands, brand_everlast = self.check_brand(brands,brand)

                #Get Price
                price_final = self.calculate_price(unit_price)

                if self.set_image_create:
                    extensions_images = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp']
                    #Get Image Base64
                    image_base64 = self.get_image_everlast(sku,extensions_images)

                #Add Product to Tupple
                tuple_products.append({
                    'name': name,
                    'type': 'product',
                    'website_description': name,
                    'sku_provider': sku,
                    'provider_category': category,
                    'provider_id': 'everlast',
                    'is_published': True if inStock else False,
                    'product_brand_id': brand_everlast,
                    'instance_id': self.id,
                    'list_price': price_final,
                    'qty_stock_provider': inStock if inStock else 0,
                    'price_sale_provider': unit_price,
                    'price_cost_provider': unit_price,
                    'image_1920':image_base64,
                    'image_process_update':True if image_base64 else False,
                })
        return tuple_products

    def everlast_generate_product_values_update(self,values):
        product = values.get('product')
        item = values.get('items')
        unit_price = 0 if item.get('PRECIOD') == '' else float(item.get('PRECIOD',0))
        inStock = int(item.get('CANTD'))
        vals_update = {}

        # Get Price
        price_final = self.calculate_price(round(unit_price))

        if inStock != product[2]:
            vals_update.update({'qty_stock_provider': 0 if not inStock else inStock,'is_published': True if inStock else False})

        if price_final != round(product[0]):
            vals_update.update({
                'list_price': price_final,
                'price_sale_provider': unit_price,
                'price_cost_provider': unit_price
            })

        return vals_update

    def everlast_generate_product_image_update(self,values):

        return values

    def execute_connection_everlast(self):
        try:
            workbook = xlrd.open_workbook(self.everlast_path)
            sheet = workbook.sheet_by_index(0)
        except Exception as ex:
            raise UserError(_("Error load the template please check the template file. Error: '%s'" % (str(ex))))

        values = []

        # First Row
        rows = sheet.nrows
        first_row = sheet.row(0)
        header = [c.value.upper() for c in first_row]

        for rw in range(1, rows):
            row = sheet.row(rw)
            lines = [cell.value if cell.value else '' for cell in row]
            "Generate Dict From values"
            values_dict = {}

            for index, line in enumerate(lines):
                values_dict.update({header[index]: line})

            if values_dict:
                values.append(values_dict)

        return values

    def get_image_everlast(self,code_product,extension_images):
        image_base64 = False
        image_path = self.search_image(code_product,extension_images)
        if image_path:
            image_base64 = self.imagen_a_base64(image_path)
            size_base64 = len(image_base64) * 3 // 4

            if size_base64 > 600 * 1024:
                buffer = self.compress_image(image_path, 600)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    def compress_image(self,image_route, max_kb):
        img = Image.open(image_route)
        buffer = BytesIO()
        quality = 85
        img.save(buffer, format=img.format, quality=quality)

        while buffer.tell() > max_kb * 1024 and quality > 10:
            buffer = BytesIO()
            quality -= 5
            img.save(buffer, format=img.format, quality=quality)

        return buffer

    def imagen_a_base64(self,image_route):
        with open(image_route, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        return False

    def search_image(self,code_product, extension_images):
        for extension in extension_images:
            image_route = os.path.join(self.everlast_image_path, f'{code_product}{extension}')
            if os.path.exists(image_route):
                return image_route
        return False