# -*- coding: utf-8 -*-
{
    "name": "Company Branch Approval",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "summary": """This app helps to create branches for companies and tfor branch approval""",
    "description": """This application enables companies to create and manage their branches efficiently. 
    It includes a streamlined approval process to ensure each branch meets the required standards before 
    being registered. The system provides real-time tracking of branch approval status, making it easy to 
    oversee branch-related activities.""",
    "depends": ['base', 'website', 'web'],
    "data": [
        'security/ir.model.access.csv',
        'data/branch_request_menu.xml',
        'data/ir_cron_data.xml',
        'data/mail_template.xml',
        'views/res_company_views.xml',
        'views/company_branch_template.xml',
        'views/branch_approval_views.xml',
        'views/company_branch_approval_template.xml',
        'views/branch_request_portal_template.xml',
        'views/company_branch_renewal_template.xml',
        'views/company_renewal_template_submit.xml',
        'views/successfull_page.xml',
        'views/branch_menu.xml'
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
