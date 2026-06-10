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
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CaseRegistration(models.Model):
    """Case registration and invoice for trials and case"""
    _name = 'case.registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Case Register'

    name = fields.Char(string='Case No', readonly=True,
                       default=lambda self: _('New'),
                       copy=False,
                       help='Case number')
    client_id = fields.Many2one('res.partner', string='Client', required=True,
                                help='Clients in the law firm')
    email = fields.Char(related="client_id.email", required=True,
                        string='Email',
                        help='Email of client', readonly=False)
    contact_no = fields.Char(related="client_id.phone", required=True,
                             string='Contact No', readonly=False,
                             help='Contact number')
    payment_method = fields.Selection(selection=[
        ('trial', "Per Trial"),
        ('case', "Per Case"),
        ('per_contract', "Per Contract"),
        ('out_of_court', "Out of Court")], string='Payment Method',
        help="Payment method to select one method")

    lawyer_wage = fields.Char(string="Lawyer Wage", help="wage of the lawyers",
                              invisible=True)
    lawyer_id = fields.Many2one('hr.employee', string='Lawyer',
                                domain=[('is_lawyer', '=', True),
                                        ('parent_id', '=', False)],
                                help="Lawyers in the law firm")
    lawyer_unavailable = fields.Boolean(string="Is Unavailable",
                                        help="Which is used to identify the "
                                             "available lawyers",
                                        default=False)
    junior_lawyer_id = fields.Many2one('hr.employee', string='Junior Lawyer',
                                       help='Juniors lawyers in the law firm')

    court_id = fields.Many2one('legal.court', string='Court',
                               help="Name of courts")
    court_no_required = fields.Boolean(string="Is Court Number Required",
                                       help='Makes court as Not required field',
                                       default=True)
    judge_id = fields.Many2one(related='court_id.judge_id', string='Judge',
                               store=True, help="Available judges")
    register_date = fields.Date(string='Registration Date', required=True,
                                default=fields.Date.today,
                                help='Case registration date')
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    end_date = fields.Date(string='End Date')
    case_category_id = fields.Many2one('case.category', string='Case Category',
                                       required=True,
                                       help="Category of case")
    description = fields.Html(string='Description', required=True,
                              help="Case Details")
    opposition_name = fields.Char(string='Name', help="Name of Opposite Party")
    opposite_lawyer = fields.Char(string='Lawyer', help="Name of opposite "
                                                        "Lawyer")
    opp_party_contact = fields.Char(string='Contact No',
                                    hel='Contact No for opposite party')
    Witness_ids = fields.One2many('case.witness', 'registration_id',
                                  help="List of Witness")
    sitting_detail_ids = fields.One2many('case.sitting', 'case_id')
    evidence_count = fields.Integer(string="Evidence Count",
                                    compute='_compute_evidence_count',
                                    help="Count of evidence")
    case_attachment_count = fields.Integer(string="Case Attachment Count",
                                           compute='_compute_case_attachment_count',
                                           help="Count of attachments")
    trial_count = fields.Integer(string="Trial Count",
                                 compute='_compute_trial_count',
                                 help="Count of trials")
    invoice_count = fields.Integer(string="Invoice Count",
                                   compute='_compute_invoice_count',
                                   help="Count of Invoices")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval', 'Waiting For Approval'), ('in_progress', 'In Progress'),
         ('invoiced', 'Invoiced'), ('reject', 'Reject'), ('out_of_court_settlement', 'Out Of Court settlement'),
         ('won', 'Won'), ('lost', 'Lost'), ('cancel', 'Cancel'), ('contract_finished', 'Contract Finished'), ],
        string='State', default='draft', help="State of case")
    company_id = fields.Many2one("res.company", string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True,
                                 help="Company in which the case done")
    case_serial_number = fields.Char(string="Case Serial No", help="Court Case number", tracking=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    agent_id = fields.Many2one('res.partner', string='Agent',
                               domain=[('is_agent', '=', True), ('agent_status', 'in', ['confirm'])],
                               help="Agents for reference")
    needed_doc = fields.Text(string='Document Needed', default=" ",
                             help="Document needed by requestor")
    is_non_billable_case = fields.Boolean(string="Non-Billable Case",
                                          default=False)
    contract_id = fields.Many2one('contract.cases')
    lost_reason = fields.Text(string='Lost Reason', help="Lost Reason")
    case_ids = fields.Many2many(
        'case.registration',
        'rel_case_registration',
        'case_id',
        'ref_case_id',
        string='Reference Cases',
        help='Reference cases'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'case_registration_attachment_rel',
        'case_id',
        'attachment_id',
        string='Attachments'
    )
    is_court_out_of_settlement = fields.Boolean(string="Court Out of Settlement", default=False,
                                                help="Indicates whether the case is outside the settlement process.")

    def action_approve(self):
        self.state = 'in_progress'
        template = self.env.ref('legal_case_management.case_approved_client_mail')
        template.sudo().send_mail(self.id, force_send=True)

    def action_restart_contract(self):
        self.state = 'in_progress'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'info',
                'sticky': False,
                'message': _("Please Review your Current Contract's stop date")

            }
        }

    @api.onchange('client_id')
    def update_referral(self):
        if self.client_id:

            # By Agent
            if self.client_id.client_referral == "by_agent":
                self.agent_id = self.client_id.agent_id
            else:
                self.agent_id = False

            # By Junior Lawyer
            if self.client_id.client_referral == "by_junior_lawyer":
                self.junior_lawyer_id = self.client_id.junior_lawyer_id
            else:
                self.junior_lawyer_id = False

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        """Court not required based on,
         - if payment method = out of court
         - if invoice through full settlement"""
        if self.payment_method == 'out_of_court':
            self.court_no_required = False
        else:
            self.court_no_required = True

    @api.onchange('lawyer_id')
    def _onchange_lawyer_id(self):
        """Lawyer unavailable warning and lists his juniors"""
        cases = self.sudo().search(
            [('lawyer_id', '=', self.lawyer_id.id), ('state', '!=', 'draft'),
             ('id', '!=', self._origin.id)])
        self.lawyer_id.not_available = False
        self.lawyer_unavailable = False
        if self.lawyer_id:
            for case in cases:
                if case.end_date and case.end_date <= fields.Date.today():
                    self.lawyer_id.not_available = False
                    self.lawyer_unavailable = False
                else:
                    self.lawyer_id.not_available = True
                    self.lawyer_unavailable = True
                    break
            if self.lawyer_unavailable:
                return {
                    'domain': {
                        'junior_lawyer_id': [('parent_id', '=',
                                              self.lawyer_id.id),
                                             ('is_lawyer', '=', True)],
                    },
                }

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Records can be deleted only draft and cancel state"""
        case_records = self.filtered(
            lambda x: x.state not in ['draft', 'cancel'])
        if case_records:
            raise UserError(_(
                "You can not delete a Approved Case."
                " You must first cancel it."))

    def action_full_settlement(self):
        """Returns the full settlement view"""
        self.court_no_required = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'full.settlement',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id}
        }

    def action_cancel(self):
        """State changed to cancel"""
        self.write({'state': 'cancel'})
        self.lawyer_id.not_available = False
        self.end_date = fields.Date.today()

    def action_reset_to_draft(self):
        """ Stage reset to draft"""
        self.write({'state': 'draft'})

    def action_confirm(self):
        """Confirmation of Cases"""
        if self.is_non_billable_case:
            self.state = 'waiting_approval'
        else:
            self.state = 'in_progress'
        if self.name == 'New':
            self.name = self.env['ir.sequence']. \
                            next_by_code('case_registration') or 'New'
            template = self.env.ref('legal_case_management.case_submitted_admin_mail')
            template.sudo().send_mail(self.id, force_send=True)

    def action_reject(self):
        """Rejection of Cases"""
        self.write({'state': 'reject'})

    def validation_case_registration(self):
        """Show Validation Until The Lawyer Details are Filled"""
        if not self.lawyer_id:
            raise ValidationError(_(
                """Please assign a lawyer for the case"""
            ))

    def action_invoice(self):
        """Button method to show invoice wizard"""
        if not self.payment_method:
            raise ValidationError(_(
                """Please select a payment method for create invoice"""
            ))
        if self.payment_method == 'case':
            self.lawyer_wage = self.lawyer_id.wage_per_case
        elif self.payment_method == 'trial':
            self.lawyer_wage = self.lawyer_id.wage_per_trial
        elif self.payment_method == 'per_contract':
            self.lawyer_wage = self.lawyer_id.wage_per_contract
        else:
            self.lawyer_wage = ''
        self.validation_case_registration()
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id,
                        'default_cost': self.lawyer_wage}
        }

    def action_evidence(self):
        """Button to add evidence"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'form',
            'res_model': 'legal.evidence',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def action_lawyer_notice(self):
        """Button to add evidence"""
        partner_ids = []
        if self.agent_id:
            partner_ids.append(self.agent_id.id)
        if self.lawyer_id:
            partner_ids.append(self.env['res.partner'].sudo().search([('employee_ids', 'in', [self.lawyer_id.id])]).id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': 'Lawyer Notice for ' + self.name,
                'default_partner_ids': partner_ids
            }
        }

    def get_attachments(self):
        """Show attachments in smart tab which added in chatter"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', self._name)],
            'context': {'create': False}
        }

    def _compute_case_attachment_count(self):
        """Compute the count of attachments"""
        for attachment in self:
            attachment.case_attachment_count = self.env['ir.attachment']. \
                sudo().search_count([('res_id', '=', self.ids),
                                     ('res_model', '=', self._name)])

    def action_won(self):
        """Changed to won state"""
        self.state = 'won'
        self.end_date = fields.Date.today()
        self.lawyer_id.not_available = False
        attachments = self.env['ir.attachment'].search(
            [('res_id', '=', self.id), ('res_model', '=', self._name)])
        if attachments:
            attachments.write({'is_won': True})
        evidence = self.env['legal.evidence'].search([('client_id', '=', self.client_id.id), ('case_id', '=', self.id)])
        if evidence:
            evidence.write({'is_won': True})
        invoices = self.env['account.move'].search([('case_ref', '=', self.name)])
        if invoices:
            invoices.write({'is_won': True})
        trials = self.env['legal.trial'].search([('client_id', '=', self.client_id.id), ('case_id', '=', self.id)])
        if trials:
            trials.write({'is_won': True})

        template_id = self.env.ref('legal_case_management.case_final_status_mail')
        template_id.with_context().send_mail(self.id, force_send=True)

    def action_lost(self):
        """Changed to lost state"""
        if not self and len(self) <= 1:
            return

        client_ids = self.mapped('client_id')
        case_category_ids = self.mapped('case_category_id')
        if len(client_ids) > 1:
            raise ValidationError(_('All selected records must have the same client.'))
        if len(case_category_ids) > 1:
            raise ValidationError(_('All selected records must have the same case category.'))
        case_ids = self.ids
        return {
            'name': 'Lost Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'lost.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_case_ids': case_ids, }
        }

    def _compute_evidence_count(self):
        """Computes the count of evidence"""
        for case in self:
            case.evidence_count = case.env['legal.evidence'].search_count(
                [('client_id', '=', case.client_id.id),
                 ('case_id', 'in', self.ids)])

    def _compute_trial_count(self):
        """Compute the count of trials"""
        for case in self:
            case.trial_count = case.env['legal.trial']. \
                search_count([('client_id', '=', case.client_id.id),
                              ('case_id', 'in', self.ids)])

    def action_trial(self):
        """Button to add trial"""
        self.validation_case_registration()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'form',
            'res_model': 'legal.trial',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def _compute_invoice_count(self):
        """Calculate the count of invoices"""
        for inv in self:
            inv.invoice_count = self.env['account.move'].search_count(
                [('case_ref', '=', inv.name)])

    def get_invoice(self):
        """Get the corresponding invoices"""
        return {
            'name': 'Case Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('case_ref', '=', self.name)],
        }

    def get_evidence(self):
        """Returns the evidences"""
        evidence_ids_list = self.env['legal.evidence']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'tree,form',
            'res_model': 'legal.evidence',
            'domain': [('id', 'in', evidence_ids_list)],
            'context': "{'create': False}"
        }

    def get_trial(self):
        """Returns the Trials"""
        trial_ids_list = self.env['legal.trial']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'tree,form',
            'res_model': 'legal.trial',
            'domain': [('id', 'in', trial_ids_list)],
            'context': "{'create': False}"
        }

    def action_send_document_request(self):
        """Open wizard for document request email"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Request',
            'res_model': 'document.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id},
        }

    def action_case_details(self):
        """Button to open eCourts case status page"""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index',
            'target': 'new',
        }

    def action_out_of_court_settlement(self):
        default_document_mode = self.env.context.get('default_document_mode',
                                                     self.env.context.get('composition_mode', 'comment'))
        doc_context = dict(default_document_mode=default_document_mode, default_model='case.registration',
                           mail_tz=self.env.user.tz,
                           )
        self.write({'is_court_out_of_settlement': True})
        self.write({'state': 'out_of_court_settlement'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Close reason',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': doc_context,
        }

    def search_case_register(self, userId=None, **kwargs):
        user_records = self.env['res.users'].sudo().search_read([('id', '=', userId)])
        case_records = self.env['case.registration'].sudo().search([('client_id', '=', user_records.partner_id[0])])

        return case_records

    def search_branch_register(self, userId=None, **kwargs):
        user = self.env['res.users'].sudo().browse(userId)
        branch_records = []
        if user.has_group('legal_case_management.legal_case_management_group_admin'):
            branch_records = self.env['branch.approval'].sudo().search_read([])
        else:
            branch_records = self.env['branch.approval'].sudo().search_read([('user_id', '=', user.id)])
        return branch_records

    def search_case_category(self, userId=None, **kwargs):
        case_category_records = self.env['case.category'].sudo().search_read([], ['name', 'id'])
        return case_category_records

    def search_company_name(self, login=None, **kwargs):
        user_data = self.env['res.users'].sudo().search_read([('id', '=', login)], ['company_id'])
        company_id = user_data[0]['company_id'][0]
        company_data = self.env['res.company'].sudo().search_read([('id', '=', company_id)], ['name', 'id'])
        return company_data

    def search_partner(self, login=None, **kwargs):
        user_data = self.env['res.users'].sudo().search_read([('id', '=', login)], ['partner_id'])
        partner_id = user_data[0]['partner_id'][0]
        partner_data = self.env['res.partner'].sudo().search_read([('id', '=', partner_id)], ['name', 'id'])
        return partner_data

    def search_agent(self, login=None, **kwargs):
        agent_data = self.env['res.partner'].sudo().search_read([('is_agent', '=', True)], ['id', 'name'])
        return agent_data

    def search_country_name(self, login=None, **kwargs):
        country_id = self.env['res.country'].sudo().search_read([], ['id', 'name'])
        return country_id
