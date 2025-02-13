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

class Website(models.Model):
    _inherit="website"

    custom_domain_website = fields.Boolean('Custom Domain Website')
    domain_website = fields.Char('Custom Domain Website')
    categories_available_ids = fields.Many2many('product.public.category', string="Categories Available",
                                                relation='categories_availables_website_public_rel')