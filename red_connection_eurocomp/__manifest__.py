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
    'name': 'RED EUROCOMP CONNECTOR',
    'version': '18.0.0.1',
    'summary': 'Module to integrate eurocomp products with systems.',
    'description': 'Module to integrate eurocomp products with systems.',
    'category': 'Product',
    'author': 'RED ECOMMERCE',
    'website': 'www.ecommerce.cr',
    'license': 'LGPL-3',
    'depends': ['red_common_connector'],
    'data': [
        'views/red_connector_instance.xml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['suds','xmltodict'],
    }
}