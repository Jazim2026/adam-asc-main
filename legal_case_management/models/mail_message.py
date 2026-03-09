# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, _


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        is_lawyer = self.env.user.has_group(
            'legal_case_management.legal_case_management_group_lawyer'
        )
        is_admin = self.env.user.has_group(
            'legal_case_management.legal_case_management_group_admin'
        )

        # Case model മാത്രം intercept ചെയ്യുക
        allowed_models = ['case.registration']
        if self._name not in allowed_models:
            return super()._notify_thread(
                message, msg_vals=msg_vals, **kwargs
            )

        partner_ids = msg_vals.get('partner_ids', []) \
            if msg_vals else []
        is_external = bool(partner_ids or message.partner_ids)

        # Automated system mails skip ചെയ്യുക
        is_automated = message.message_type in (
            'notification', 'auto_comment'
        )

        # Lawyer external mail block ചെയ്യുക
        if is_lawyer and not is_admin \
                and is_external and not is_automated:
            if message.approval_state != 'approved':
                message.sudo().write({
                    'approval_state': 'pending',
                    'submitted_by': self.env.uid,
                })
                message._notify_admins_pending()
                return message  # ← Block!

        return super()._notify_thread(
            message, msg_vals=msg_vals, **kwargs
        )


class MailMessage(models.Model):
    _inherit = 'mail.message'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval State', default='draft')

    rejection_reason = fields.Char(string='Rejection Reason')
    submitted_by = fields.Many2one(
        'res.users', string='Submitted By'
    )

    def _notify_admins_pending(self):
        admin_group = self.env.ref(
            'legal_case_management'
            '.legal_case_management_group_admin'
        )
        admins = self.env['res.users'].search([
            ('groups_id', 'in', admin_group.id)
        ])
        # case model-ന്റെ res_id use ചെയ്യുക
        res_model = self.model or 'mail.message'
        res_id = self.res_id or self.id
        model_id = self.env['ir.model']._get(res_model).id

        submitted_name = self.submitted_by.name \
            if self.submitted_by else 'Lawyer'

        for admin in admins:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': self.env.ref(
                    'mail.mail_activity_data_todo'
                ).id,
                'res_model_id': model_id,
                'res_id': res_id,
                'user_id': admin.id,
                'summary': _('Email Approval Required'),
                'note': _(
                    'Email from <b>%s</b> to client '
                    'is pending your approval.'
                ) % submitted_name,
            })

    def action_approve(self):
        self.ensure_one()
        if not self.env.user.has_group(
            'legal_case_management'
            '.legal_case_management_group_admin'
        ):
            raise exceptions.AccessError(_("Only Admin can approve."))

        self.sudo().write({'approval_state': 'approved'})

        # Client-ന് actual mail send
        self.env['mail.mail'].sudo().create({
            'subject': self.subject or _('Message from Legal Team'),
            'body_html': self.body,
            'email_to': ','.join(
                p.email for p in self.partner_ids if p.email
            ),
            'auto_delete': True,
        }).send()

        self._notify_lawyer(approved=True)

    def action_reject(self):
        self.ensure_one()
        if not self.env.user.has_group(
            'legal_case_management'
            '.legal_case_management_group_admin'
        ):
            raise exceptions.AccessError(_("Only Admin can reject."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Email'),
            'res_model': 'mail.reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message_id': self.id},
        }

    def action_resubmit(self):
        self.ensure_one()
        self.sudo().write({
            'approval_state': 'pending',
            'rejection_reason': False,
        })
        self._notify_admins_pending()

    def _notify_lawyer(self, approved=True, reason=None):
        lawyer = self.submitted_by
        if not lawyer:
            return
        if approved:
            body = _(
                '✅ Your email <b>"%s"</b> approved and sent to client.'
            ) % (self.subject or '')
        else:
            body = _(
                '❌ Your email <b>"%s"</b> rejected.<br/>'
                '<b>Reason:</b> %s'
            ) % (self.subject or '', reason or '-')

        # message_notify പകരം mail.message create
        self.env['mail.message'].sudo().create({
            'message_type': 'notification',
            'body': body,
            'subject': _('Email Approval Update'),
            'partner_ids': [(4, lawyer.partner_id.id)],
            'model': 'res.partner',
            'res_id': lawyer.partner_id.id,
            'subtype_id': self.env.ref('mail.mt_note').id,
            'author_id': self.env.user.partner_id.id,
        })


class MailRejectReasonWizard(models.TransientModel):
    _name = 'mail.reject.reason.wizard'
    _description = 'Email Rejection Reason'

    message_id = fields.Many2one('mail.message', string='Message')
    rejection_reason = fields.Char(
        string='Rejection Reason', required=True
    )

    def action_confirm_reject(self):
        self.message_id.sudo().write({
            'approval_state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        self.message_id._notify_lawyer(
            approved=False,
            reason=self.rejection_reason
        )
        return {'type': 'ir.actions.act_window_close'}