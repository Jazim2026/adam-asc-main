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
from odoo import api, fields, models, _
from odoo import Command

class ResPartner(models.Model):
    """Inherit res partner"""
    _inherit = 'res.partner'

    client_referral = fields.Selection([('no_referral', 'No Referral'), ('by_agent', 'By Agent'),
                                        ('by_junior_lawyer', 'By Junior Lawyers')],
                                       default='no_referral')

    junior_lawyer_id = fields.Many2one('hr.employee', string='Junior Lawyer',
                                       help='Juniors lawyers in the law firm')

    agent_id = fields.Many2one('res.partner', string='Agent',
                               domain=[('is_agent', '=', True),('agent_status', 'in', ['confirm'])],
                               help="Agents for reference")

    is_judge = fields.Boolean(string='Is Judge', help='Is this person a Judge?')
    is_judge_unavailable = fields.Boolean(
        string="Judge Available?",
        default=False,
        help="Indicates whether the judge is available"
    )
    commission_per_case = fields.Float(string="Commission Per Case", help='Commission per Case',)
    is_agent = fields.Boolean(string="Is Agent", help='Is this person an Agent?')
    agent_status = fields.Selection(selection=[
        ('draft', "In Process"),
        ('confirm', "Agent")], string='Agent Status',
        help="Status of Agent Creation", default='draft')
    agent_case_count = fields.Integer(
        string="Case Count",
        help='Number of cases referred by the agent',
        compute='_compute_case_count',
    )
    Wages_of_agent = fields.Float(
        string="Amount",
        help='Amount to pay the agent',
        compute="compute_agent_amount",
    )
    agent_code = fields.Char(string='Agent DSE Code', readonly=True,
                       default=lambda self: _('New'),
                       copy=False,
                       help='Agent number')

    def get_cases(self):
        """
        Return an action dictionary to display the cases related to the current agent.

        The returned dictionary will be used to open a tree view of the 'case.registration' model,
        filtered to show cases where the 'agent_id' matches the current record's ID. The context
        is set to prevent creating new records.

        Returns:
            dict: Action dictionary to open the cases in a tree view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cases',
            'view_mode': 'tree,form',
            'res_model': 'case.registration',
            'domain': [('agent_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('agent_case_count')
    def _compute_case_count(self):
        """
        Compute and update the count of cases assigned to each agent.

        This method will count the number of cases where 'agent_id' is equal to the current agent's ID
        and update the 'agent_case_count' field accordingly.
        """
        for record in self:
            record.agent_case_count = self.env['case.registration'].search_count(
                [('agent_id', '=', record.id)]
            )

    @api.depends('commission_per_case')
    def compute_agent_amount(self):
        """
        Compute and update the total wages of the agent based on the number of in-progress cases.

        This method will calculate the total wages by multiplying the number of in-progress cases
        assigned to the agent by the 'commission_per_case' and update the 'Wages_of_agent' field.

        The calculation considers only cases with a state of 'in_progress'.
        """
        for record in self:
            case_count = self.env['case.registration'].search_count(
                [('agent_id', '=', record.id), ('state', '=', 'in_progress')]
            )
            record.Wages_of_agent = record.commission_per_case * case_count

    def action_create_invoice(self):
        """
               Create an invoice for the current record based on the case count and commission.

               This method will:
               - Calculate the invoiced quantity by summing up the quantities of existing invoices.
               - Create a new invoice for the difference between the case count and the invoiced quantity.
               - Return an action to open the newly created invoice.
               """
        # Calculate total invoiced quantity for the current partner
        invoiced_count = 0
        for rec in self.env['account.move'].search([
            ('is_case_invoice', '=', True),
            ('partner_id', '=', self.id)
        ]):
            for line in rec.invoice_line_ids:
                invoiced_count += line.quantity

        # Create a new invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.id,
            'is_case_invoice': True,
            'invoice_line_ids': [(0, 0, {
                'name': 'Case Commission',
                'quantity': self.agent_case_count - invoiced_count,
                'price_unit': self.commission_per_case,
            })]
        })

        # Return an action to open the created invoice
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_confirm_agent(self):
        """Confirmation of agent"""
        if self.agent_code == 'New':
            self.agent_code = self.env['ir.sequence']. \
                            next_by_code('agent_code') or 'New'
        self.agent_status = 'confirm'


    def create_users_sign_up(self,name,email,password,phone):
        partner_id = self.env['res.partner'].create({'name': name, 'email':email, 'phone':phone})
        group_portal = self.env.ref('base.group_portal')
        user = self.env['res.users'].create({
            'name': partner_id.name,
            'login': partner_id.email,
            'partner_id': partner_id.id,
            'password': password,
            'groups_id': [(4, group_portal.id)]
        })
        return {
            'partner_name': partner_id.name,
            'partner_email': partner_id.email,
            'user_name': user.name
        }

    def search_case_register(self, login=None, **kwargs):
        user = self.env['res.users'].sudo().browse(login)
        partner_id = user.partner_id
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        records = []
        domain = ['|', ('client_id', '=', partner_id.id),('agent_id', '=', partner_id.id)]
        if employee_id:
            domain = [ ('lawyer_id', '=', employee_id.id)]
        if user.has_group('legal_case_management.legal_case_management_group_admin'):
            records = self.env['case.registration'].sudo().search_read([])
        elif partner_id:
            records = self.env['case.registration'].sudo().search_read(domain)
        return records
