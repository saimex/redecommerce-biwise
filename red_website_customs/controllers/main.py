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

from collections import defaultdict
import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_decode, url_encode, url_parse

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.fields import Command
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale
from odoo.osv import expression
from odoo.tools import lazy
from odoo.tools.safe_eval import safe_eval
from odoo.tools.json import scriptsafe as json_scriptsafe

_logger = logging.getLogger(__name__)

class WebsiteSale(WebsiteSale):

    def __init__(self):
        super(WebsiteSale, self).__init__()
        WebsiteSale.WRITABLE_PARTNER_FIELDS.extend(['first_name','last_name','surname','county_id','district_id','identification_id','mobile'])

    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        domains = super()._get_search_domain(search, category, attrib_values, search_in_description)

        #SHOW IN CUSTOM SEARCH
        if request.website.domain_website and request.website.custom_domain_website:
            domains = expression.AND([domains,safe_eval(request.website.domain_website)])

        #SHOW BY CUSTOM CATEGORIES
        if not category and request.website.categories_available_ids:
            domains = expression.AND([domains,[('public_categ_ids', 'child_of', request.website.categories_available_ids.ids)]])

        return domains

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super().shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price,
                                ppg=ppg, **post)

        Category = request.env['product.public.category']

        #Restrict Categories
        if category:
            if request.website.categories_available_ids:
                category = Category.search([('id', '=', int(category))], limit=1)
                categories_ava = Category.search([('id', 'child_of', request.website.categories_available_ids.ids)])
                if not category or category.id not in categories_ava.ids:
                    raise NotFound()
            else:
                category = Category.search([('id', '=', int(category))], limit=1)
                if not category or not category.can_access_from_current_website():
                    raise NotFound()
        else:
            if request.website.categories_available_ids:
                categories_ava = Category.search([('id', 'in', request.website.categories_available_ids.ids)])
                response.qcontext.update(categories=categories_ava)
            category = Category

        response.qcontext.update(
            category = category,
        )
        return response

    def _get_country_related_render_values(self, kw, render_values):
        """ Provide the fields related to the country to render the website sale form """
        mode = render_values['mode']
        values = render_values['checkout']
        res = super(WebsiteSale,self)._get_country_related_render_values(kw, render_values)
        #Search Country
        country_id = request.env['res.country'].search([('code','=','CR')],limit=1)
        country = country_id
        #Search County
        state_counties = request.env['res.country.county'].sudo().search([])
        #Search Districts
        county_districts = request.env['res.country.district'].sudo().search([])

        #Check State
        state = 'state_id' in values and values['state_id'] != '' and request.env['res.country.state'].browse(int(values['state_id']))
        state = state and state.exists() or False

        #Check County
        county = 'county_id' in values and values['county_id'] != '' and request.env['res.country.county'].browse(int(values['county_id']))
        county = state and state.exists() or False

        res.update({
            'country': country,
            'state':state,
            'county':county,
            'state_counties':state_counties,
            'county_districts':county_districts,
            'country_states': country.get_website_sale_states(mode=mode[1]),
            'countries': country_id,
        })
        return res

    @http.route()
    def address(self, **kw):
        # Modificar 'callback' antes de llamar a la función original
        if 'callback' in kw and kw['callback'] == '/shop/checkout':
            kw['callback'] = '/shop/address'
        res = super(WebsiteSale, self).address(**kw)
        indentifications = request.env['identification.type'].sudo().search([])
        res.qcontext.update({
            'indentifications':indentifications,
        })
        if isinstance(res, http.Response) and res.location == '/shop/checkout':
            res.location = '/shop/address'
        return res

    def _get_mandatory_fields_billing(self, country_id=False):
        res = super(WebsiteSale,self)._get_mandatory_fields_billing(country_id=country_id)
        res += ["first_name", "last_name", "surname", "state_id","county_id","district_id","phone","mobile"]
        res.remove('name') if "name" in res else None
        res.remove('city') if "city" in res else None
        res.remove('zip') if "zip" in res else None
        return res

    def _get_mandatory_fields_shipping(self, country_id=False):
        res = super(WebsiteSale, self)._get_mandatory_fields_shipping(country_id=country_id)
        res += ["first_name", "last_name", "surname", "state_id","county_id", "district_id", "phone","mobile"]
        res.remove('name') if "name" in res else None
        res.remove('city') if "city" in res else None
        res.remove('zip') if "zip" in res else None
        return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        res = super(WebsiteSale,self).values_postprocess(order, mode, values, errors, error_msg)
        res[0].update({k:v for k,v in values.items() if k in ['first_name','last_name','surname','mobile','county_id','district_id']})
        return res

    #Get State Info
    @http.route(['/shop/state_infos/<model("res.country.state"):state_id>'], type='json', auth="public", methods=['POST'],
                website=True)
    def state_infos(self, state_id,**kw):
        return dict(
            counties=[(st.id, st.name, st.code) for st in state_id.sudo().county_ids],
        )

    #Get County Info
    @http.route(['/shop/county_infos/<model("res.country.county"):county_id>'], type='json', auth="public", methods=['POST'],
                website=True)
    def county_infos(self, county_id,**kw):
        return dict(
            districts=[(st.id, st.name, st.code) for st in county_id.sudo().district_ids],
        )

    @http.route()
    def checkout(self, **post):
        res = super(WebsiteSale, self).checkout(**post)
        if isinstance(res, http.Response) and res.location == '/shop/checkout':
            res.location = '/shop/address'
        return res