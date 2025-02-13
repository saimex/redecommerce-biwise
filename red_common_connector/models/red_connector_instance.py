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
import math

from odoo import api, fields, models

class RedConnectorInstance(models.Model):
    _name = "red.connector.instance"
    _description = "Red Ecommerce Connector Instances"

    name = fields.Char('Name',required=True)
    provider_id = fields.Selection([('none','None')],'Provider',default="none",required=True)
    ttype_connection = fields.Selection([('api','API'),
                                        ('ftp','FTP')],'Type Connection',required=False)
    product_ids = fields.One2many('product.template','instance_id','Total Products')
    logs_ids = fields.One2many('red.integration.logs','name','Log Ids')
    url_test = fields.Char('URL Test')
    sku_test = fields.Char('SKU Test')
    products_count = fields.Integer('Products Count',computed="_get_total_products")
    products_count_published = fields.Integer('Products Count Published',computed="_get_total_products")
    products_count_no_published = fields.Integer('Products Count No Published', computed="_get_total_products")
    currency_rate = fields.Float("Currency Rate")
    imp_product = fields.Float("Tax IVA")
    imp_utility = fields.Float("Utility")
    set_image_create = fields.Boolean('Set Image in Create Process?')
    max_image_process = fields.Integer('Max Image by Process')
    unpublish_product_present = fields.Boolean('Unpublish Product if not Present?')

    def _get_total_products(self):
        for record in self:
            record.products_count = len(record.product_ids)
            record.products_count_published = len(record.product_ids.filtered(lambda x: x.is_published)) if 'is_published' in self._fields else 0
            record.products_count_published = len(record.product_ids.filtered(lambda x: not x.is_published)) if 'is_published' in self._fields else 0

    #Function process
    def create_products(self,values):
        cust_method_name = '%s_generate_product_values' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)
            if values:
                self.env['product.template'].create(values)
                return len(values)
        return 0

    def update_product(self, values,product):
        cust_method_name = '%s_generate_product_values_update' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)
            if values:
                product.write(values)
                return 1
        return 0

    def update_stock(self,values,product):
        cust_method_name = '%s_generate_product_valstock_update' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)
            if values:
                product.write(values)
                return 1
        return 0

    def update_price(self,values,product):
        cust_method_name = '%s_generate_product_valprice_update' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)
            if values:
                product.write(values)
                return 1
        return 0

    def update_image(self,values,product):
        cust_method_name = '%s_generate_product_image_update' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method(values)
            if values:
                product.write(values)
                return 1
        return 0

    #Button process
    def run_process(self):
        cust_method_name = '%s_run_process_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    def run_update_process(self):
        cust_method_name = '%s_run_update_process_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    def run_update_stock(self):
        cust_method_name = '%s_run_update_stock_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    def run_update_pricess(self):
        cust_method_name = '%s_run_update_price_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    def run_update_images(self):
        cust_method_name = '%s_run_update_image_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    def test_process(self):
        cust_method_name = '%s_test_process_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()

    #Cron Process
    def cron_create_products(self,id):
        instance = self.search([('id','=',id)])
        instance.run_process()

    def cron_update_products(self,id):
        instance = self.search([('id','=',id)])
        instance.run_update_process()

    def cron_update_stock(self,id):
        instance = self.search([('id','=',id)])
        instance.run_update_stock()

    def cron_update_price(self,id):
        instance = self.search([('id','=',id)])
        instance.run_update_pricess()

    def cron_update_images(self,id):
        instance = self.search([('id','=',id)])
        instance.run_update_images()

    #Log Process
    def create_log_connector(self,name,provider,ttype_process,state,messsage,total_processed):
        values = {
                'name':name,
                'provider_id':provider,
                'ttype_process':ttype_process,
                'state':state,
                'messsage': messsage,
                'total_processed':total_processed
            }
        self.env['red.integration.logs'].create(values)

    #Price Process
    def calculate_price(self, unit_price=0):
        price_final = 0

        #Calculate Price
        if self.imp_product:
            price_final = float(unit_price) + ( (unit_price * float(self.imp_product)) / 100)

        #Currency Rate
        if self.currency_rate:
            price_final = price_final * float(self.currency_rate)

        #Utility
        if self.imp_utility:
            price_final = price_final + ((price_final * float(self.imp_utility)) / 100)

        if price_final:
            price_final = int(math.ceil(price_final / 100.0)) * 100
        else:
            price_final = unit_price if unit_price else 1.0

        return price_final

    #Check Brand
    def check_brand(self,values,brand_name):
        if brand_name:
            # Actual Brand
            brand = values.get(brand_name.upper(), False)

            # Create Brand if nor exists
            if not brand:
                brand = self.env['product.brand'].create({'name': brand_name.upper()}).id
                values.update({brand_name.upper():brand})
            else:
                brand = brand
        else:
            values = values
            brand = False
        return values, brand

    #Unpublished Products
    def unpublished_products(self,existing_products,dict_processed):
        cust_method_name = '%s_unpublished_products' % (self.provider_id)
        if hasattr(self, cust_method_name):
            method = getattr(self, cust_method_name)
            values = method()
        else:
            # Hide Products is not present in Odoo
            for sku, product in existing_products.items():
                if sku not in dict_processed:
                    if product.is_published:
                        product.update({'is_published': False})


