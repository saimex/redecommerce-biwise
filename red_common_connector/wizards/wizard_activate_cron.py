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

class WizardActivateCron(models.TransientModel):
    _name="wizard.activate.cron"

    instance_id = fields.Many2one('red.connector.instance','Instance ID',required=True)
    create_cron = fields.Boolean('Create Cron')
    update_cron = fields.Boolean('Update Cron')
    update_stock = fields.Boolean('Update Stock')
    update_price = fields.Boolean('Update Price')
    update_image = fields.Boolean('Update Image')

    def create_process_cron(self):
        self.check_cron_exists()

        if not self.create_cron and not self.update_cron and not self.update_stock and not self.update_price:
            return True

        name_cron = ""
        code = ""
        if self.create_cron:
            code = "cron_create_products(%i)"  %(self.instance_id.id)
            name = "%s: Create Products"
        if self.update_cron:
            code = "cron_update_products(%i)"  %(self.instance_id.id)
            name = "%s: Update Products" %(self.instance_id.provider_id)
        if self.update_stock:
            code = "cron_update_stock(%i)" %(self.instance_id.id)
            name = "%s: Update Stock" %(self.instance_id.provider_id)
        if self.update_price:
            code = "cron_update_price(%i)" %(self.instance_id.id)
            name = "%s: Update Prise" %(self.instance_id.provider_id)
        if self.update_image:
            code = "cron_update_images(%i)" % (self.instance_id.id)
            name = "%s: Update Image" % (self.instance_id.provider_id)

        name = name_cron
        code = "model.%s" %(code)
        crone_rec = self.env["ir.cron"].sudo().create({
                "name": name,
                "model_id": self.instance_id._model.id,
                "state": "code",
                "numbercall": -1,
                "instance_id":self.instance_id.id,
                "code": code,
                "doall": False
            })

    def check_cron_exists(self):
        if self.create_cron:
            code = "cron_create_products(%i)"  %(self.instance_id.id)
            ir_cron = self.env['ir.cron'].sudo().search([('code','=',code),('instance_id','=',self.instance_id.id)])
            if ir_cron:
                self.create_cron = False
        if self.update_cron:
            code = "cron_update_products(%i)"  %(self.instance_id.id)
            ir_cron = self.env['ir.cron'].sudo().search([('code', '=', code), ('instance_id', '=', self.instance_id.id)])
            if ir_cron:
                self.update_cron = False
        if self.update_stock:
            code = "cron_update_stock(%i)" %(self.instance_id.id)
            ir_cron = self.env['ir.cron'].sudo().search([('code', '=', code), ('instance_id', '=', self.instance_id.id)])
            if ir_cron:
                self.update_stock = False
        if self.update_price:
            code = "cron_update_price(%i)" %(self.instance_id.id)
            ir_cron = self.env['ir.cron'].sudo().search([('code', '=', code), ('instance_id', '=', self.instance_id.id)])
            if ir_cron:
                self.update_price = False
        if self.update_image:
            code = "cron_update_images(%i)" % (self.instance_id.id)
            ir_cron = self.env['ir.cron'].sudo().search([('code', '=', code), ('instance_id', '=', self.instance_id.id)])
            if ir_cron:
                self.update_image = False
