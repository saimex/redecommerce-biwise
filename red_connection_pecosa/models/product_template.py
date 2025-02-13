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

class ProdcutTempalte(models.Model):
    _inherit = "product.template"

    provider_id = fields.Selection(selection_add=[('pecosa', 'Pecosa')], ondelete={'pecosa': 'set default'})