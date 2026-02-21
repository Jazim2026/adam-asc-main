# -*- coding: utf-8 -*-
import base64
import json
from datetime import datetime

from werkzeug.datastructures import FileStorage
from odoo import _, http
from odoo.http import request


class CompanyBranchController(http.Controller):
    """Company Branch Controller"""

    @http.route(['/api/submit/create/company'], type='json', methods=['post'], auth="public", csrf=False)
    def branch_request_submit_api(self, **post):
        post = request.get_json_data()['params']['args'][5][0]
        """This function is used to create a new branch request."""

        def format_date(date_str):
            """Convert date from DD-MM-YYYY to YYYY-MM-DD format."""
            try:
                return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                return False  # Handle invalid date formats gracefully

        datas = {
            'user_id': post.get('user_id'),
            'name': post.get('name'),
            'address_1': post.get('address_1'),
            'phone': post.get('phone'),
            'address_2': post.get('address_2'),
            'mobile': post.get('mobile'),
            'city': post.get('city'),
            'email': post.get('email'),
            'pin_code': post.get('pin_code'),
            'website': post.get('website'),
            'tax_id': post.get('tax_id'),
            'pan_id': post.get('pan_id'),
            'gst_id': post.get('gst_id'),
            'it_card': post.get('it_card'),
            'pan_expiry': format_date(post.get('pan_expiry')),
            'it_expiry': format_date(post.get('it_expiry')),
            'gst_expiry': format_date(post.get('gst_expiry')),
            'pan_copy': post.get('pan_copy'),
            'it_copy': post.get('it_copy'),
            'gst_copy': post.get('gst_copy'),
        }
        pan_copy = request.httprequest.files.get("pan_copy")
        it_copy = request.httprequest.files.get("it_copy")
        gst_copy = request.httprequest.files.get("gst_copy")
        if pan_copy is not None:
            img_pan = base64.b64encode(pan_copy.read())
        if it_copy is not None:
            img_it = base64.b64encode(it_copy.read())
        if gst_copy is not None:
            img_gst = base64.b64encode(gst_copy.read())
        print(datas['name'])
        br_request = request.env['branch.approval'].sudo().create({
            'user_id': datas['user_id'],
            'name': datas['name'],
            'street': datas['address_1'],
            'street2': datas['address_2'],
            'phone': datas['phone'],
            'mobile': datas['mobile'],
            'city': datas['city'],
            'zip': datas['pin_code'],
            'website': datas['website'],
            'vat': datas['tax_id'],
            'pan_id': datas['pan_id'],
            'email': datas['email'] if datas.get('email') else False,
            'gst_id': datas['gst_id'],
            'it_card': datas['it_card'],
            'pan_expiry': datas['pan_expiry'],
            'it_expiry': datas['it_expiry'],
            'gst_expiry': datas['gst_expiry'],
            'branch_manager_id': request.env.user.partner_id.id
        })
        for key, file_storage in request.httprequest.files.items(multi=True):
            if key == 'attachment_ids' and isinstance(file_storage, FileStorage):
                filename = file_storage.filename
                content_type = file_storage.content_type
                request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(file_storage.read()),
                    'res_model': 'branch.approval',
                    'res_id': br_request.id,
                    'mimetype': content_type
                })
        return {
            "record_id": br_request.id
        }

    @http.route('/company/branch/request', type="http", auth="user", website=True)
    def branch_request_form(self):
        """ Returns Branch Creation Form"""
        country = request.env['res.country'].search([])
        state = request.env['res.country.state'].search([])
        return request.render('branch_approval.company_branch_request_view',
                              {'country': country, 'state': state})

    @http.route('/company/branch/request/data', type="http", auth="user", website=True)
    def branch_request_records(self):
        branch_all = request.env['branch.approval'].search([('branch_manager_id', '=', request.env.user.partner_id.id)])
        branch_approve = request.env['branch.approval'].search([('state', '=', 'approve'),('branch_manager_id', '=', request.env.user.partner_id.id)])
        branch_reject = request.env['branch.approval'].search([('state', '=', 'reject'),('branch_manager_id', '=', request.env.user.partner_id.id)])
        return request.render('branch_approval.company_branch_approval_view',
                              {'branch_all': branch_all, 'branch_approve': branch_approve,
                               'branch_reject': branch_reject, 'page_name': "br_requests"})

    @http.route('/company/branch/renewal/data', type="http", auth="user", website=True)
    def branch_request_renewal(self):
        branch_renewal = request.env['res.company'].search([('branch_manager_id', '=', request.env.user.partner_id.id),('active','=',False)])
        return request.render('branch_approval.company_branch_renewal_view',
                              {'branch_renewal': branch_renewal, 'page_name': "br_renewal"})

    @http.route('/company/renewal/submit/<int:record_id>', type="http", auth="user", website=True)
    def company_renewal_submit(self,record_id):
        branch_renewal = request.env['res.company'].browse(record_id)
        return request.render('branch_approval.company_branch_renewal_submit',
                              {'branch_renewal_submit': branch_renewal})

    @http.route(['/submit/create/company'], type='http', methods=['post'], auth="user", website=True)
    def branch_request_submit(self, **post):
        """This function used to create a new branch request"""
        datas = {
            'name': post.get('name'),
            'address_1': post.get('address_1'),
            'phone': post.get('phone'),
            'address_2': post.get('address_2'),
            'mobile': post.get('mobile'),
            'city': post.get('city'),
            'state': post.get('state'),
            'country': post.get('country'),
            'email': post.get('email'),
            'pin_code': post.get('pin_code'),
            'website': post.get('website'),
            'company_id': post.get('company_id'),
            'tax_id': post.get('tax_id'),
            'pan_id': post.get('pan_id'),
            'gst_id': post.get('gst_id'),
            'it_card': post.get('it_card'),
            'pan_expiry': post.get('pan_expiry'),
            'it_expiry': post.get('it_expiry'),
            'gst_expiry': post.get('gst_expiry'),
            'pan_copy': post.get('pan_copy'),
            'it_copy': post.get('it_copy'),
            'gst_copy': post.get('gst_copy'),
        }
        pan_copy = request.httprequest.files.get("pan_copy")
        it_copy = request.httprequest.files.get("it_copy")
        gst_copy = request.httprequest.files.get("gst_copy")
        if pan_copy is not None:
            img_pan = base64.b64encode(pan_copy.read())
        if it_copy is not None:
            img_it = base64.b64encode(it_copy.read())
        if gst_copy is not None:
            img_gst = base64.b64encode(gst_copy.read())
        br_request = request.env['branch.approval'].sudo().create({
            'name': datas['name'],
            'street': datas['address_1'],
            'street2': datas['address_2'],
            'phone': datas['phone'],
            'mobile': datas['mobile'],
            'city': datas['city'],
            'state_id': int(datas['state']),
            'country_id': int(datas['country']),
            'zip': datas['pin_code'],
            'website': datas['website'],
            'company_registry': datas['company_id'],
            'vat': datas['tax_id'],
            'pan_id': datas['pan_id'],
            'email': datas['email'] if datas.get('email') else False,
            'gst_id': datas['gst_id'],
            'it_card': datas['it_card'],
            'pan_expiry': datas['pan_expiry'] if datas.get('pan_expiry') else False,
            'it_expiry': datas['it_expiry'] if datas.get('it_expiry') else False,
            'gst_expiry': datas['gst_expiry'] if datas.get('gst_expiry') else False,
            'pan_copy': img_pan,
            'it_copy': img_it,
            'gst_copy': img_gst,
            'branch_manager_id': request.env.user.partner_id.id
        })
        for key, file_storage in request.httprequest.files.items(multi=True):
            if key == 'attachment_ids' and isinstance(file_storage, FileStorage):
                filename = file_storage.filename
                content_type = file_storage.content_type
                request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(file_storage.read()),
                    'res_model': 'branch.approval',
                    'res_id': br_request.id,
                    'mimetype': content_type
                })
        return request.render("branch_approval.success_page")

    @http.route(['/submit/branch/renewal/<int:record_id>'], type='http', methods=['post'], auth="user", website=True)
    def branch_request_submit_renewal(self, record_id,**post):
        datas = {
            'pan_expiry': post.get('pan_expiry'),
            'it_expiry': post.get('it_expiry'),
            'gst_expiry': post.get('gst_expiry'),
        }
        company = request.env['res.company'].browse(record_id)
        company.sudo().write({
            'pan_expiry': datas['pan_expiry'] if datas.get('pan_expiry') else False,
            'it_expiry': datas['it_expiry'] if datas.get('it_expiry') else False,
            'gst_expiry': datas['gst_expiry'] if datas.get('gst_expiry') else False,
            'active':True
        })
        return request.render("branch_approval.success_page")
