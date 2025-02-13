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
    'name': 'RED WEBSITE CUSTOMS',
    'version': '18.0.0.1',
    'summary': 'Module to add modifications in website sale.',
    'description': 'Module to add modifications in website sale.',
    'category': 'Website',
    'author': 'RED ECOMMERCE',
    'website': 'www.ecommerce.cr',
    'license': 'LGPL-3',
    'depends': ['website_sale','red_ecommerce_base'],
    'data': [
        'views/auth_signup_login_templates.xml',
        'views/website.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'red_website_customs/static/src/js/website_sale.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}