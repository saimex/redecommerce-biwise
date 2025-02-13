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
    _inherit="red.integration.logs"

    provider_id = fields.Selection(selection_add=[('intcomex', 'Intcomex')], ondelete={'intcomex': 'set default'})