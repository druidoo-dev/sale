##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class SaleAdvancePaymentInvWizard(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    amount_total = fields.Float(
        string='Down Payment Amount With Taxes',
        compute='_compute_amount_total',
        inverse='_inverse_amount_total',
        digits=dp.get_precision('Account'),
    )

    @api.onchange('amount_total', 'deposit_taxes_id')
    def _inverse_amount_total(self):
        self.ensure_one()
        if any(x.amount_type != 'percent' for x in self.deposit_taxes_id):
            raise ValidationError(_(
                'You can only set amount total if taxes are of type '
                'percentage'))
        tax_percent = sum(
            [x.amount for x in self.deposit_taxes_id if not x.price_include])
        total_percent = (1 + tax_percent / 100) or 1.0
        self.amount = self.amount_total / total_percent

    @api.depends('deposit_taxes_id', 'amount')
    def _compute_amount_total(self):
        """
        For now we implement inverse only for percent taxes. We could extend to
        other by simulating tax.price_include = True, computing tax and
        then restoring tax.price_include = False.
        """
        sale_obj = self.env['sale.order']
        order = sale_obj.browse(self._context.get('active_ids'))[0]

        if self.deposit_taxes_id:
            taxes = self.deposit_taxes_id.compute_all(
                self.amount, order.company_id.currency_id,
                1.0, product=self.product_id,
                partner=order.partner_id)
            self.amount_total = taxes['total_included']
        else:
            self.amount_total = self.amount
