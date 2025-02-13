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
{
    'name': 'RED COMMON CONNECTOR',
    'version': '18.0.0.1',
    'summary': 'Module base to integrate others providers products with systems.',
    'description': 'Module base to integrate others providers products with systems.',
    'category': 'Product',
    'author': 'RED ECOMMERCE',
    'website': 'www.ecommerce.cr',
    'license': 'LGPL-3',
    'depends': ['product','stock','product_brand','website_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizards/wizard_activate_cron.xml',
        'views/product_template.xml',
        'views/red_connector_instance.xml',
        'views/red_integration_logs.xml',
    ],
    'installable': True,
    'auto_install': False,
}