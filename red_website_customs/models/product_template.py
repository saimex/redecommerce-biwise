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
from odoo import api, fields, models,_
from odoo.tools.safe_eval import safe_eval

class ProductTemplate(models.Model):
    _inherit ="product.template"

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        # SHOW IN CUSTOM SEARCH
        if website.domain_website and website.custom_domain_website:
            res['base_domain'].append(safe_eval(website.domain_website))

        # SHOW BY CUSTOM CATEGORIES
        if website.categories_available_ids:
            res['base_domain'].append([('public_categ_ids', 'child_of', website.categories_available_ids.ids)])

        return res