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
from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit="product.template"

    provider_id = fields.Selection([('none','None')],'Provider',default="none")
    sku_provider = fields.Char('SKU Provider')
    qty_stock_provider = fields.Integer('QTY Stock Provider')
    price_sale_provider = fields.Float('Price Sale Provider')
    price_cost_provider = fields.Float('Price Cost Provider')
    provider_category = fields.Char('Provider Category')
    no_update_byprovider = fields.Boolean('No Update By Provider')
    instance_id = fields.Many2one('red.connector.instance','Instance ID',ondelete="restrict")
    image_process_update = fields.Boolean('Image Update by Process?',default=False)