# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64

from odoo import http
from odoo.http import request


class LegalCaseController(http.Controller):
    """Legal Case Controller"""

    @http.route('/legal/case/register', type="http", auth="user", website=True)
    def legal_case_register(self):
        """ Returns Case Registration Form"""
        return request.render(
            'legal_case_management.legal_case_register_view')

    @http.route('/submit/create/case', type="http", methods=['POST'], website=True, auth='user')
    def create_case_register(self, **kw):
        """Creation of Cases"""
        # attached_files = request.httprequest.files.getlist('attachments[0][0]')
        attached_files = []
        # Loop through `kw` to find keys that match the 'attachments' pattern
        for key, file in kw.items():
            if key.startswith('attachments'):
                attached_files.append(file)
        case = request.env['case.registration'].sudo().create({
            'client_id': request.env.user.partner_id.id,
            'email': request.env.user.partner_id.email,
            'contact_no': kw.get('contact'),
            'description': kw.get('description'),
            'case_category_id': int(kw.get('case_category')) if kw.get('case_category') else False,
            'company_id': request.env.company.id,
        })
        for attachment in attached_files:
            request.env['ir.attachment'].sudo().create({
                'name': attachment.filename,
                'res_model': 'case.registration',
                'res_id': case.id,
                'type': 'binary',
                'datas': base64.b64encode(attachment.read())
            })
            # Admin-ന് mail അയക്കുക
            template = request.env.ref('legal_case_management.case_submitted_admin_mail')
            template.sudo().send_mail(case.id, force_send=True)
        return request.render("legal_case_management.thanks_page")

    @http.route('/api/submit/create/case', type="json", methods=['POST'], auth='public', csrf=False)
    def create_case_register_app(self, **kw):
        kw = request.get_json_data()['params']['args'][5][0]
        """Creation of Cases"""
        # attached_files = request.httprequest.files.getlist('attachments[0][0]')
        attached_files = []
        # Loop through `kw` to find keys that match the 'attachments' pattern
        for key, file in kw.items():
            if key.startswith('attachments'):
                attached_files.append(file)
        case = request.env['case.registration'].sudo().create({
            'client_id': kw.get('client_id'),
            'email': kw.get('email'),
            'contact_no': kw.get('contact'),
            'description': kw.get('description'),
            'case_category_id': int(kw.get('case_category')) if kw.get('case_category') else False,
            'company_id': kw.get('company_id') or request.env.company.id,
        })
        for attachment in attached_files:
            request.env['ir.attachment'].sudo().create({
                'name': attachment.filename,
                'res_model': 'case.registration',
                'res_id': case.id,
                'type': 'binary',
                'datas': base64.b64encode(attachment.read())
            })
