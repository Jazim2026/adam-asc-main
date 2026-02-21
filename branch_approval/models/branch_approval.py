# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo import _, http
from odoo.http import request
import base64
from werkzeug.datastructures import FileStorage

class BranchApproval(models.Model):
    _name = 'branch.approval'
    _description = 'Branch Request'
    _inherit = "mail.thread"

    name = fields.Char(string='Branch Name', required=True)
    street = fields.Char(string='Address 1', required=True)
    street2 = fields.Char(string='Address 2')
    phone = fields.Char(string='Phone', required=True)
    mobile = fields.Char(string='Mobile')
    user_id = fields.Integer(string='Company create user')
    city = fields.Char(string='City', required=True)
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    parent_id = fields.Many2one('res.company', string='Parent Company')
    zip = fields.Char(string='zip', required=True)
    website = fields.Char(string='Website')
    email = fields.Char(string='Email', required=True)
    company_registry = fields.Char(string='Company ID')
    vat = fields.Char(string='Tax ID')
    pan_id = fields.Char("Pan ID", help="Enter the PAN ID (Permanent Account Number, for tax purposes) of the company")
    pan_copy = fields.Binary(
        string='PAN Copy',
        help="Attach the PAN here."
    )
    pan_expiry = fields.Date(string="PAN Expiry Date", help="Enter the expiry date of the company PAN ID")
    it_card = fields.Char("IT Card", help="Enter the IT Card Number")
    it_copy = fields.Binary(
        string='IT Card Copy',
        help="Attach the IT Card here."
    )
    it_expiry = fields.Date(string="IT Card Expiry Date", help="Enter the expiry date of the IT Card")
    gst_id = fields.Char("Gst ID",
                         help="Enter the GST ID (Goods and Services Tax Identification Number, for tax compliance) of the company")
    gst_copy = fields.Binary(
        string='Gst Copy',
        help="Attach the Gst here."
    )
    gst_expiry = fields.Date(string="Gst Expiry Date", help="Enter the expiry date of the company GST")
    state = fields.Selection([("pending", "Pending"), ("approve", "Approved"), ("reject", "Rejected")],
                             default="pending", tracking=True)
    branch_manager_id = fields.Many2one("res.partner","Branch Manager")
    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Shop Images',
        domain=[('res_model', '=', 'branch.approval')],
    )


    def action_approve_request(self):
        """
            Approves the current branch request and creates a new company record based on the request details.

            This method performs the following actions:
            1. Updates the state of the current branch request to 'approve'.
            2. Creates a new company (`res.company`) record using the details provided in the branch request.

            The newly created company will include various fields such as name, address, contact information, tax details,
            and parent company reference. This method uses the `sudo()` privilege to ensure that it has sufficient permissions
            to create a company record, even if the current user does not have access rights to the `res.company` model.
        """
        self.write({'state': 'approve'})
        self.env['res.company'].sudo().create({
            'name': self.name,
            'street': self.street,
            'street2': self.street2,
            'phone': self.phone,
            'mobile': self.mobile,
            'city': self.city,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'zip': self.zip,
            'website': self.website,
            'company_registry':self.company_registry,
            'vat': self.vat,
            'pan_id': self.pan_id,
            'email': self.email,
            'gst_id': self.gst_id,
            'it_card': self.it_card,
            'pan_expiry': self.pan_expiry,
            'it_expiry': self.it_expiry,
            'gst_expiry': self.gst_expiry,
            'pan_copy': self.pan_copy,
            'it_copy': self.it_copy,
            'gst_copy': self.gst_copy,
            'branch_manager_id': self.branch_manager_id.id,
            'parent_id':self.env.company.id,
        })

    def action_reject_request(self):
        """
            Rejects the current branch request by setting its state to 'cancel'.

            This method changes the state of the branch request to 'cancel', indicating that the request has been rejected and
            will not proceed further. No additional records are created or modified beyond the state update of the current
            branch request.

            Returns:
                None

            Example Usage:
                This method can be called when a rejection button is clicked in the branch request form view to mark the
                request as canceled.
        """
        self.write({'state': 'cancel'})



