from odoo import models, fields

class DocumentRequestWizard(models.TransientModel):
    _name = 'document.request.wizard'
    _description = 'Document Request Wizard'

    message = fields.Html(string='Message', required=True)
    case_id = fields.Many2one('case.registration', string='Case')

    def action_send(self):
        case = self.case_id
        main_content = {
            'subject': 'Document Request',
            'body_html': self.message,
            'email_to': case.client_id.email,
        }
        self.env['mail.mail'].sudo().create(main_content).send()
        return {'type': 'ir.actions.act_window_close'}
