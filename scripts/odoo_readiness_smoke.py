"""Run with Odoo shell on the confirmed development build; commits labelled test data."""
import json
from pathlib import Path

from odoo import fields

TARGET = 'odolution-com-arab-insurance-19-10-26-40105896'
assert env.cr.dbname == TARGET
env = env(context=dict(env.context, mail_notify_force_send=False, mail_create_nosubscribe=True, tracking_disable=True))
mail_ids_before = env['mail.mail'].search([]).ids
company = env.company
assert company.currency_id.name == 'KWD' and company.country_id.code == 'KW'
assert not env['insurance.policy'].search([('policy_number', '=', 'READINESS-20261110')]), 'Do not duplicate the smoke test'
company.enable_aib_accounting = True
company.commission_eligibility_rule_id = env.ref('aib_commission_engine.commission_rule_enterprise_policy_issued')
admin = env.ref('base.user_admin')
admin.write({'group_ids': [(4, env.ref('aib_base.group_insurance_administrator').id)]})
customer = env['res.partner'].create({'name': 'READINESS TEST - Client'})
insurer_partner = env['res.partner'].create({'name': 'READINESS TEST - Insurer', 'is_company': True, 'email': 'readiness-insurer@example.test'})
insurer = env['insurance.company'].create({'name': 'READINESS TEST - Insurer', 'short_code': 'RDY', 'partner_id': insurer_partner.id, 'email': 'readiness-insurer@example.test'})
kind = env.ref('aib_base.insurance_type_motor')
policy_class = env.ref('aib_base.policy_class_corporate')
today = fields.Date.today()
lead = env['crm.lead'].create({
    'name': 'READINESS TEST - CRM to partial payment', 'partner_id': customer.id,
    'insurance_type_id': kind.id, 'policy_class_id': policy_class.id,
    'business_type': 'new', 'estimated_premium': 6000.0,
    'expected_commission_percentage': 10.0,
})
placement = env['insurance.market.placement'].create_from_lead(lead.id)
line = env['insurance.market.insurer'].create({'placement_id': placement.id, 'insurance_company_id': insurer.id})
quote = env['insurance.quotation'].create({
    'placement_id': placement.id, 'market_insurer_id': line.id,
    'quote_date': today, 'validity_date': fields.Date.add(today, days=30),
    'insurer_quote_reference': 'READINESS-QUOTE-20261110',
    'base_premium': 6000.0, 'commission_percentage': 10.0,
})
quote.action_mark_received()
quote.action_start_technical_review()
quote.action_start_commercial_review()
quote.action_approve()
comparison = env['insurance.comparison'].create_from_placement(placement)
comparison.action_prepare_comparison()
comparison.selected_quotation_id = quote
comparison.action_select_quotation()
policy = env['insurance.policy'].create_from_comparison(comparison)
policy.write({'policy_number': 'READINESS-20261110', 'policy_start_date': today, 'policy_end_date': fields.Date.add(today, years=1), 'expiry_date': fields.Date.add(today, years=1)})
policy.action_request_issuance()
policy.action_mark_issued()
policy.action_activate()
assert policy.policy_source == 'crm_market'
assert policy.total_premium_amount == quote.total_premium == 6000.0
due = policy.premium_statement_due_move_id
assert due and due.state == 'draft'
client_collection = env['insurance.client.collection'].create({
    'policy_id': policy.id, 'partner_id': customer.id, 'insurance_company_id': insurer.id,
    'amount': 3000.0, 'currency_id': company.currency_id.id, 'company_id': company.id,
    'payment_reference': 'READINESS-PREMIUM-3000',
})
client_collection.action_confirm()
assert due.state == client_collection.premium_statement_move_id.state == 'posted'
client_account = company.default_client_premium_statement_account_id
insurer_account = company.default_insurer_premium_statement_account_id
assert client_account != insurer_account
statement_lines = (due | client_collection.premium_statement_move_id).line_ids
client_balance = sum(statement_lines.filtered(lambda item: item.account_id == client_account).mapped('balance'))
insurer_balance = sum(statement_lines.filtered(lambda item: item.account_id == insurer_account).mapped('balance'))
assert client_balance == 3000.0 and insurer_balance == -3000.0
commission = env['insurance.commission'].search([('policy_id', '=', policy.id)])
assert len(commission) == 1 and commission.state == 'eligible'
commission.action_approve_commission()
commission.action_mark_receivable()
invoice = commission.invoice_id
assert invoice and invoice.amount_total == 600.0
invoice.action_post()
collection = env['insurance.collection'].create({
    'insurance_company_id': insurer.id, 'received_amount': 300.0,
    'currency_id': company.currency_id.id, 'company_id': company.id,
    'payment_journal_id': company.default_inbound_payment_journal_id.id,
    'payment_reference': 'READINESS-COMMISSION-300',
    'line_ids': [(0, 0, {'commission_id': commission.id, 'allocated_amount': 300.0})],
})
collection.action_confirm()
collection.action_allocate()
payment = collection.payment_id
assert payment and payment.move_id and payment.move_id.state == 'posted'
assert invoice.amount_residual == 300.0
assert commission.commission_received_amount == 300.0
assert commission.commission_outstanding_amount == 300.0
assert invoice.line_ids.filtered(lambda item: item.account_type == 'asset_receivable').matched_credit_ids
renewal = env['insurance.renewal'].create_from_policy(policy)
claim = env['insurance.claim'].create({'policy_id': policy.id, 'incident_date': today, 'claim_type': 'motor'})
claim.action_report_claim()
endorsement = env['insurance.policy.endorsement'].create({
    'policy_id': policy.id, 'endorsement_type': 'customer_information_change',
    'effective_date': today, 'change_description': 'READINESS TEST - non-financial endorsement',
    'insurer_endorsement_number': 'READINESS-END-001',
})
endorsement.action_request_endorsement()
endorsement.request_mail_id.write({'state': 'cancel'})
endorsement.action_confirm_issued()
endorsement.action_mark_done()
views = []
for model in ['crm.lead', 'insurance.market.placement', 'insurance.quotation', 'insurance.comparison', 'insurance.policy', 'insurance.client.collection', 'insurance.commission', 'insurance.collection', 'insurance.renewal', 'insurance.claim', 'insurance.policy.endorsement']:
    env[model].with_user(admin).check_access('read')
    for view_type in ['list', 'form']:
        assert env[model].with_user(admin).get_view(view_type=view_type)['arch']
        views.append(f'{model}:{view_type}')
config = env['insurance.regulatory.configuration'].search([('company_id', '=', company.id), ('active', '=', True)], limit=1)
test_emails = env['mail.mail'].search([('id', 'not in', mail_ids_before), ('state', '=', 'outgoing')])
test_emails.write({'state': 'cancel'})
result = {
    'database': env.cr.dbname, 'currency': company.currency_id.name,
    'lead_id': lead.id, 'placement_id': placement.id, 'quotation_id': quote.id,
    'comparison_id': comparison.id, 'policy_id': policy.id, 'policy_reference': policy.name,
    'client_collection_id': client_collection.id,
    'client_premium_outstanding': client_balance, 'insurer_premium_outstanding': insurer_balance,
    'commission_id': commission.id, 'invoice_id': invoice.id, 'invoice_number': invoice.name,
    'invoice_total': invoice.amount_total, 'invoice_residual': invoice.amount_residual,
    'collection_id': collection.id, 'payment_id': payment.id, 'payment_name': payment.name,
    'payment_amount': payment.amount, 'payment_move_id': payment.move_id.id,
    'payment_move_state': payment.move_id.state, 'renewal_id': renewal.id,
    'claim_id': claim.id, 'endorsement_id': endorsement.id, 'views_checked': views,
    'official_report_template_present': bool(config.workbook_template_attachment_id),
}
env.cr.commit()
Path('/home/odoo/tmp/operational-readiness-20261110/smoke-result.json').write_text(json.dumps(result, indent=2))
print('READINESS_SMOKE_PASSED', json.dumps(result))
