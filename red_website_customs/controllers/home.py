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
from odoo.addons.web.controllers.home import Home, SIGN_UP_REQUEST_PARAMS

class CustomHome(Home):

    def __init__(self):
        super(CustomHome, self).__init__()
        SIGN_UP_REQUEST_PARAMS.update({'first_name','last_name','surname'})
