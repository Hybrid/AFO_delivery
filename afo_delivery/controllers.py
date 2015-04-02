# -*- coding: utf-8 -*-
from openerp import http

# class AfoDelivery(http.Controller):
#     @http.route('/afo_delivery/afo_delivery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/afo_delivery/afo_delivery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('afo_delivery.listing', {
#             'root': '/afo_delivery/afo_delivery',
#             'objects': http.request.env['afo_delivery.afo_delivery'].search([]),
#         })

#     @http.route('/afo_delivery/afo_delivery/objects/<model("afo_delivery.afo_delivery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('afo_delivery.object', {
#             'object': obj
#         })