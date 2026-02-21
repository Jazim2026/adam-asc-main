# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pan_id = fields.Char("Pan ID",help="Enter the PAN ID (Permanent Account Number, for tax purposes) of the company")
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
    gst_id = fields.Char("Gst ID", help="Enter the GST ID (Goods and Services Tax Identification Number, for tax compliance) of the company")
    gst_copy = fields.Binary(
        string='Gst Copy',
        help="Attach the Gst here."
    )
    gst_expiry = fields.Date(string="Gst Expiry Date", help="Enter the expiry date of the company GST")
    branch_manager_id = fields.Many2one("res.partner","Branch Manager")

    def run_company_expiry_check(self):
        company = self.env['res.company'].search([('parent_id','!=',False)])
        today_date = fields.Date.today()
        for rec in company:
            if rec.gst_expiry == today_date + timedelta(days=1) or rec.pan_expiry == today_date + timedelta(days=1) or rec.it_expiry == today_date + timedelta(days=1):
                email_values = {
                    'email_cc': False,
                    'email_to': rec.partner_id.email,
                    'subject': "Documents: Expiry Reminder Mail"
                }
                mail_template = self.env.ref(
                    'branch_approval.branch_documents_expiry_reminder')
                context = {
                    'gst': rec.gst_expiry == today_date + timedelta(days=1),
                    'pan':rec.pan_expiry == today_date + timedelta(days=1),
                    'it':rec.it_expiry == today_date + timedelta(days=1)
                }
                mail_template.with_context(context).send_mail(rec.id,
                                                              email_values=email_values,
                                                              force_send=True)

    def run_company_archive_expired(self):
        company = self.env['res.company'].search([('parent_id', '!=', False)])
        today_date = fields.Date.today()
        for rec in company:
            gst_expired = rec.gst_expiry and rec.gst_expiry > today_date
            pan_expired = rec.pan_expiry and rec.pan_expiry > today_date
            it_expired = rec.it_expiry and rec.it_expiry > today_date

            if gst_expired or pan_expired or it_expired:
                email_values = {
                    'email_cc': False,
                    'email_to': rec.partner_id.email,
                    'subject': "Document Expired"
                }
                mail_template = self.env.ref('branch_approval.branch_documents_expired')
                context = {
                    'gst': gst_expired,
                    'pan': pan_expired,
                    'it': it_expired
                }
                mail_template.with_context(context).send_mail(rec.id,
                                                              email_values=email_values,
                                                              force_send=True)
                rec.active = False
