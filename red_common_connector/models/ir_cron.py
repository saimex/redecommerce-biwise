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

class IrCron(models.Model):
    _inherit="ir.cron"

    instance_id = fields.Many2one('red.connector.instance','Instance ID')