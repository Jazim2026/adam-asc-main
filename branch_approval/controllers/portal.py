# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class FieldServiceRequestCount(CustomerPortal):
    """Extends CustomerPortal to display the count of branch approval requests
    for the current user."""

    def _prepare_home_portal_values(self, counters):
        """Prepare values for the home portal page."""
        vals = super()._prepare_home_portal_values(counters)
        if 'br_req_count' in counters:
            vals['br_req_count'] = request.env['branch.approval'].sudo().search_count(
                [('branch_manager_id', '=', request.env.user.partner_id.id)])
        if 'br_req_renew_count' in counters:
            vals['br_req_renew_count'] = request.env['res.company'].sudo().search_count(
                [('branch_manager_id', '=', request.env.user.partner_id.id),('active','=',False)])
        return vals
