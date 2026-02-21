# -*- coding:utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
import uuid
from odoo import fields, models
from odoo.addons.test_convert.tests.test_env import record


class ResUsers(models.Model):
    """This class is used to inherit users and add api key generation"""
    _inherit = 'res.users'

    api_key = fields.Char(string="API Key", readonly=True,
                          help="Api key for connecting with the "
                               "Database.The key will be "
                               "generated when authenticating "
                               "rest api.")

    def generate_api(self, username):
        """This function is used to generate api-key for each user"""
        users = self.env['res.users'].sudo().search([('login', '=', username)])
        if not users.api_key:
            users.api_key = str(uuid.uuid4())
            key = users.api_key
        else:
            key = users.api_key
        return key

    def search_case_register(self, login=None, **kwargs):
        partner_id = self.env['res.users'].sudo().browse(int(login)).partner_id
        records = self.env['case.registration'].sudo().search_read(['|', ('client_id', '=', partner_id.id),
                                                                    ('agent_id', '=', partner_id.id)])
        return records

    def is_portal_user(self, user_id):
        user = self.env['res.users'].sudo().browse(user_id)
        return self.env.ref('base.group_portal') in user.groups_id

