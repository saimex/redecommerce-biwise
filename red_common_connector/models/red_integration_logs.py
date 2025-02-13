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

class RedIntegrationLogs(models.Model):
    _name="red.integration.logs"
    _description = "Red Integration Logs"
    _order = "create_date DESC"

    name = fields.Many2one('red.connector.instance','Instance',required=True)
    provider_id = fields.Selection([('none','None')],'Provider',default="none",required=True)
    ttype_process = fields.Selection([('create_product','Create Products'),
                                      ('update_product','Update Products'),
                                      ('update_price','Update Price'),
                                      ('update_stock','Update Stock'),
                                      ('update_image','Update Image')],'Process',required=True)
    state = fields.Selection([('in_process','In Process'),
                              ('success','Success'),
                              ('error','Error')],'State',required=True,default='in_process')
    messsage = fields.Text('Message')
    total_processed = fields.Integer('Total Processed')