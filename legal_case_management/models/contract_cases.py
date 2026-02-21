from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta


class ContractCases(models.Model):
    _name = 'contract.cases'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract Cases'

    name = fields.Char(string="Name", readonly=True, default=lambda self: _('New'),
                       help='Trial number')
    case_id = fields.Many2one('case.registration', string="Case",
                              help='Corresponding case',
                              domain="[('state', 'not in',"
                                     "['won', 'lost', 'invoiced'])]")
    client_id = fields.Many2one('res.partner', string="Client",
                                required=True,
                                help='Client of the legal trial')
    lawyer_id = fields.Many2many('hr.employee', string='Lawyer',
                                 domain=[('is_lawyer', '=', True),
                                         ('parent_id', '=', False)],
                                 help="Lawyers in the law firm")
    active = fields.Boolean(string='Active', default=True)

    renewal_period = fields.Selection([
        ('months', 'Month(s)'),
        ('years', 'Year(s)')],
        string="Billing Period",
        default='months',
        help='Select the unit of time for the '
             'renewal period of the contract.')

    state = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Ongoing'), ('stopped', 'Stopped')],
        string='State', default='draft', help="State of contract")

    contract_start_date = fields.Date(readonly=True)
    contract_stop_date = fields.Date(
        required=True)

    next_invoice_date = fields.Date(
        string='Date of Next Invoice',
        readonly=True,
        help="The next invoice will be created on this date then the period will be extended.")
    invoice_count = fields.Integer(string="Invoice Count",
                                   compute='_compute_invoice_count',
                                   help="Count of Invoices")

    def _compute_invoice_count(self):
        """Calculate the count of invoices"""
        for inv in self:
            inv.invoice_count = self.env['account.move'].search_count(
                [('contract_ref', '=', self.name)])

    def check_contract_cron(self):
        today_date = fields.Date.today()
        # today_date = fields.Date.from_string("2024-10-29")

        print(f"Today's date: {today_date}")

        all_contracts = self.env['contract.cases'].search([('state', '=', 'ongoing')])
        print(all_contracts)
        for contract in all_contracts:
            print(f"Contract: {contract}")
            contract_lawyers = contract.lawyer_id

            # Prepare the invoice lines for all the lawyers in the contract
            invoice_lines = []
            for contract_lawyer in contract_lawyers:
                print(contract_lawyer)
                invoice_lines.append((0, 0, {
                    'name': contract_lawyer.name,
                    'quantity': 1,
                    'price_unit': contract_lawyer.wage_per_contract,
                }))
                print(contract.next_invoice_date)

            # Check if the contract is ongoing and today is the next invoice date
            if contract.state == "ongoing" and today_date == contract.next_invoice_date:
                print("here")
                self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'invoice_date': contract.next_invoice_date,
                    'partner_id': contract.client_id.id,
                    'contract_ref': contract.name,
                    'invoice_line_ids': invoice_lines,
                })

                # Adjust next invoice date based on the renewal period
                if contract.renewal_period == 'months':
                    contract.next_invoice_date = contract.next_invoice_date + relativedelta(months=1)
                elif contract.renewal_period == 'years':
                    contract.next_invoice_date = contract.next_invoice_date + relativedelta(years=1)

                # Save the updated contract
                contract.write({
                    'next_invoice_date': contract.next_invoice_date
                })

            # Check if today is the contract stop date, and stop the contract if necessary
            if contract.state == "ongoing" and today_date == contract.contract_stop_date:
                contract.write({
                    'state': 'stopped'
                })

                print(f"Contract ID {contract.id} has been stopped.")

    def action_confirm(self):
        if self.name == 'New':
            self.name = self.env['ir.sequence']. \
                            next_by_code('contract_case') or 'New'
        self.state = 'ongoing'
        self.contract_start_date = fields.Date.today()

        # Calculate the next invoice date based on the renewal period
        if self.renewal_period == 'months':
            self.next_invoice_date = self.contract_start_date + timedelta(days=30)
        elif self.renewal_period == 'years':
            self.next_invoice_date = self.contract_start_date + timedelta(days=365)

    def action_stop_contract(self):
        self.state = 'stopped'

    def action_reset_draft(self):
        self.state = 'draft'

    def get_invoice(self):
        """Get the corresponding invoices"""
        return {
            'name': 'Case Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('contract_ref', '=', self.name)],
        }
