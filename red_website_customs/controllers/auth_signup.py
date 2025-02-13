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
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

class AuthSignupHome(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        res = super(AuthSignupHome,self)._prepare_signup_values(qcontext)
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password','first_name', 'last_name','surname')}
        values['name'] = values['first_name'] + ' ' + values['last_name'] + ' ' + values['surname']
        res.update(values)
        return res