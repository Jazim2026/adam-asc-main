# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Gayathri V (odoo@cybrosys.com)
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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request
from datetime import date
import json


class PortalLegalCase(CustomerPortal):
    """Customer Portal"""

    def _prepare_home_portal_values(self, counters):
        """Returns the portal values"""
        values = super()._prepare_home_portal_values(counters)
        case_registration_model = request.env['case.registration'].sudo()

        if 'case_count' in counters:
            values['case_count'] = request.env[
                'case.registration'].sudo().search_count(
                [('state', '!=', 'invoiced'), '|',
                 ('client_id.id', '=', request.env.user.partner_id.id),
                 ('agent_id.id', '=', request.env.user.partner_id.id)]) \
                if request.env['case.registration'].sudo(). \
                check_access_rights('read', raise_exception=False) else 0
        return values

    @http.route('/my/legal/case',
                type='http', auth="user", website=True)
    def legal_cases(self):
        """Returns the case Records"""
        if request.env.user.partner_id.is_agent:
            records = request.env['case.registration'].sudo(). \
                search(['|', ('client_id', '=', request.env.user.partner_id.id),
                        ('agent_id', '=', request.env.user.partner_id.id)])
        else:
            records = request.env['case.registration'].sudo().search(
                [('client_id', '=', request.env.user.partner_id.id)])
        values = {
            'records': records,
            'page_name': 'case'
        }
        return request.render(
            "legal_case_management.portal_my_legal_case_requests",
            values)

    @http.route(['/my/cases/<int:case_id>'], type='http', auth="public",
                website=True)
    def portal_my_details_detail(self, case_id):
        """ Returns the Portal details"""
        case_record = request.env['case.registration'].sudo().browse(case_id)
        evidences = request.env['legal.evidence'].sudo().search(
            [('client_id', '=', case_record.client_id.id),
             ('case_id', '=', case_record.id)])
        trials = request.env['legal.trial'].sudo().search(
            [('client_id', '=', case_record.client_id.id),
             ('case_id', '=', case_record.id)])
        records = {
            'case_record': case_record,
            'evidence': evidences,
            'trial': trials,
            'page_name': 'case'
        }
        return request.render("legal_case_management.portal_legal_case_page",
                              records)

    @http.route('/my/cases/<int:case_id>/upload',
                type='http', auth='user', methods=['POST'], website=True)
    def upload_case_document(self, case_id, **kwargs):
        """Client upload cheyta files save cheyyuka"""
        import base64
        case = request.env['case.registration'].sudo().browse(case_id)
        attachment_file = kwargs.get('attachment')

        if attachment_file and case:
            request.env['ir.attachment'].sudo().create({
                'name': attachment_file.filename,
                'res_model': 'case.registration',
                'res_id': case_id,
                'datas': base64.b64encode(attachment_file.read()),
                'mimetype': attachment_file.content_type,
            })
        return request.redirect('/my/cases/%s' % case_id)

class LegalCaseMeeting(http.Controller):

    @http.route(['/my/cases/schedule_meeting/<int:case_id>'], type='http', auth="user", website=True)
    def schedule_meeting(self, case_id, **kw):
        case_record = request.env['case.registration'].sudo().browse(case_id)
        request.env['mail.activity'].sudo().create({
            'activity_type_id': request.env.ref('mail.mail_activity_data_meeting').id,
            'res_model': 'case.registration',
            'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'case.registration')]).id,
            'res_id': case_record.id,
            'summary': 'Meeting scheduled for case %s' % case_record.name,
            'date_deadline': date.today(),  # Example of setting the deadline to today
            'user_id': request.env.user.id,  # Assign to the current user
        })
        return request.redirect('/my/cases/%d' % case_id)