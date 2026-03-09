# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, exceptions, _

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        if self.env.context.get('mail_approval_processing'):
            return super()._notify_thread(
                message, msg_vals=msg_vals, **kwargs
            )

        is_lawyer = self.env.user.has_group(
            'legal_case_management.legal_case_management_group_lawyer'
        )
        is_admin = self.env.user.has_group(
            'legal_case_management.legal_case_management_group_admin'
        )

        allowed_models = ['case.registration']
        if self._name not in allowed_models:
            return super()._notify_thread(
                message, msg_vals=msg_vals, **kwargs
            )

        partner_ids = msg_vals.get('partner_ids', []) \
            if msg_vals else []
        is_external = bool(partner_ids or message.partner_ids)
        is_automated = message.message_type in (
            'notification', 'auto_comment'
        )

        if is_lawyer and not is_admin \
                and is_external and not is_automated:
            if message.approval_state != 'approved':
                message.sudo().write({
                    'approval_state': 'pending',
                    'submitted_by': self.env.uid,
                })
                message.with_context(
                    mail_approval_processing=True
                )._notify_admins_pending()
                return message

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

    def _get_client_email(self):
        """Case registration-ലെ client email എടുക്കുക"""
        email_list = []

        # Internal users (lawyers/admins) partner ids
        internal_partner_ids = self.env['res.users'].sudo().search([
            ('share', '=', False)
        ]).mapped('partner_id.id')

        # 1. Message partner_ids-ൽ നിന്ന് — internal users exclude
        for partner in self.partner_ids:
            if partner.email \
                    and partner.id not in internal_partner_ids:
                email_list.append(partner.email)

        # 2. Fallback — case record-ലെ client_id email
        if not email_list and self.res_id \
                and self.model == 'case.registration':
            case = self.env['case.registration'].sudo().browse(
                self.res_id
            )
            if case.client_id and case.client_id.email:
                email_list.append(case.client_id.email)
                _logger.info(
                    "Email Approval: Using client_id email: %s",
                    case.client_id.email
                )

        return email_list

    def _notify_admins_pending(self):
        admin_group = self.env.ref(
            'legal_case_management'
            '.legal_case_management_group_admin'
        )
        admins = self.env['res.users'].search([
            ('groups_id', 'in', admin_group.id)
        ])
        res_model = self.model or 'mail.message'
        res_id = self.res_id or self.id
        model_id = self.env['ir.model']._get(res_model).id
        submitted_name = self.submitted_by.name \
            if self.submitted_by else 'Lawyer'

        for admin in admins:
            self.env['mail.activity'].with_context(
                mail_approval_processing=True
            ).sudo().create({
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

        email_to_list = self._get_client_email()

        if not email_to_list:
            _logger.warning(
                "Email Approval: No client email found "
                "for message id=%s subject=%s model=%s res_id=%s",
                self.id, self.subject, self.model, self.res_id
            )
            self._notify_lawyer(
                approved=False,
                reason="No client email found. "
                       "Please add client email."
            )
            return

        self.env['mail.mail'].sudo().create({
            'subject': self.subject or _('Message from Legal Team'),
            'body_html': self.body,
            'email_to': ','.join(email_to_list),
            'auto_delete': True,
        }).send()

        _logger.info(
            "Email Approval: Mail sent to %s for message id=%s",
            email_to_list, self.id
        )

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
        self.with_context(
            mail_approval_processing=True
        )._notify_admins_pending()

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

        self.env['mail.message'].with_context(
            mail_approval_processing=True
        ).sudo().create({
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