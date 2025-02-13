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

class ResCountryState(models.Model):
    _inherit = "res.country.state"

    county_ids = fields.One2many('res.country.county','state_id','County IDS')