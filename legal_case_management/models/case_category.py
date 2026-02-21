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
from odoo.exceptions import UserError
from random import randint


class CaseCategory(models.Model):
    """Create case category"""
    _name = 'case.category'
    _description = 'Case Category'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Case Category", required=True, translate=True,
                       help='Name of the case category')
    color = fields.Integer('Color', default=_get_default_color)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Prevent the deletion of a case category if it is used in any
         cases. """
        cases = self.sudo().env['case.registration'].search_count([
            ('case_category_id', 'in', self.ids),
            ('state', 'not in', ['draft'])
        ])
        if cases:
            raise UserError(_("You can not delete a case category,"
                              " because it is used in case"))
