from odoo import models, fields


class DocumentRequestWizard(models.TransientModel):
    _name = 'document.request.wizard'
    _description = 'Document Request Wizard'

    message = fields.Html(string='Message', required=True)
    case_id = fields.Many2one('case.registration', string='Case')

    def action_send(self):
        case = self.case_id
        company = self.env.company

        # Company Logo
        logo = ''
        if company.logo:
            logo = f'<img src="/web/image/res.company/{company.id}/logo" style="max-height:80px;"/>'

        body_html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">

            <!-- Company Logo -->
            <div style="text-align: center; margin-bottom: 20px;">
                {logo}
            </div>

            <!-- Header -->
            <div style="background-color: #3b0764; padding: 15px; text-align: center;">
                <h2 style="color: white; margin: 0;">Document Request</h2>
            </div>

            <!-- Body -->
            <div style="padding: 20px;">
                <p><strong>From:</strong> {company.name}</p>
                <p><strong>Case No:</strong> {case.name}</p>
                <p><strong>Message:</strong></p>
                <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #3b0764;">
                    {self.message}
                </div>

                <!-- Upload Link -->
                <div style="margin-top: 20px; text-align: center;">
                    <p>Please upload the required documents by clicking the button below:</p>
                    <a href="https://app.lawvex.legal/my/legal/case"
                       style="background-color: #3b0764; color: white; padding: 12px 25px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Upload Documents
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div style="margin-top: 30px; text-align: center; color: #888; border-top: 1px solid #ddd; padding-top: 15px;">
                <p>Thank You</p>
                <p style="font-size: 12px;">{company.name} | {company.email or ''} | {company.phone or ''}</p>
            </div>

        </div>
        '''

        main_content = {
            'subject': f'Document Request - {case.name}',
            'body_html': body_html,
            'email_to': case.client_id.email,
        }
        self.env['mail.mail'].sudo().create(main_content).send()
        return {'type': 'ir.actions.act_window_close'}