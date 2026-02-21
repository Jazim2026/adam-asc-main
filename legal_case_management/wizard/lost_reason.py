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
from odoo import fields, models, Command


class LostReason(models.TransientModel):
    """ This is used to Full Settlement"""
    _name = 'lost.reason'
    _description = 'Lost Reason'


    case_ids = fields.Many2many('case.registration',string='Cases')
    reason = fields.Text(string='Reason',
                              required=True,
                              help='Lost Reason')
    lost_date = fields.Date(string='Date', default=fields.date.today(),
                                help='Lost Date')

    def action_appeal(self):
        template_id = self.env.ref('legal_case_management.case_final_status_mail')
        case_data = []
        case_ids = []
        for case in self.case_ids:
            case.lawyer_id.not_available = False
            case.write({
                'lost_reason': self.reason,
                'end_date': self.lost_date,
                'state': 'lost'
            })
            case_data.append(case.name)
            case_ids.append(Command.link(case.id))
            template_id.with_context().send_mail(case.id, force_send=True)
        description = 'Take reference from cases: %s ' % ', '.join(case_data) if case_data else ''
        self.env['case.registration'].create({
            'client_id': self.case_ids[0].client_id.id,
            'case_category_id': self.case_ids[0].case_category_id.id,
            'case_ids':case_ids,
            'description': description
        })

