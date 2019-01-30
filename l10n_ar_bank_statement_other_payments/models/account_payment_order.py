##############################################################################
#
#    Copyright (C) 2010-2014 Eynes - Ingeniería del software All Rights Reserved
#    Copyright (c) 2014 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models


class AccountPaymentOrder(models.Model):

    _inherit = 'account.payment.order'

    @api.multi
    def proforma_voucher(self):
        ret = super(AccountPaymentOrder, self).proforma_voucher()
        bank_st_line_obj = self.env['account.bank.statement.line']

        for payment_order in self:
            for concept in payment_order.concept_line_ids:
                journal = concept.journal_id or payment_order.journal_id
                if journal.type != 'bank':
                    continue

                st_line_data = concept._prepare_statement_line_data()
                bank_st_line_obj.create(st_line_data)

        return ret


class AccountPaymentOrderConceptLine(models.Model):

    _inherit = 'account.payment.order.concept.line'

    def _prepare_statement_line_data(self):
        payment_order = self.payment_order_id
        line_type = payment_order.type

        # Si el voucher no tiene partner, ponemos el de la compania
        partner = payment_order.partner_id or payment_order.company_id.partner_id
        journal = self.journal_id or payment_order.journal_id

        if payment_order.type == 'payment':
            sign = 1
            #account = journal.default_debit_account_id
        else:
            sign = -1
            #account = journal.default_credit_account_id

        amount = self.amount * sign

        st_line_data = {
            'ref': self.name,
            'name': self.name or payment_order.number,
            'account_id': self.account_id.id,
            'journal_id': journal.id,
            'date': payment_order.date,
            'company_id': payment_order.company_id.id,
            'payment_order_id': payment_order.id,
            'partner_id': partner.id,
            'line_type': line_type,
            'amount': amount,
            'state': 'open',
        }

        return st_line_data