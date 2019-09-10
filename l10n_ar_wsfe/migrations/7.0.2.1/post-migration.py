# -*- coding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID, pooler

_logger = logging.getLogger(__name__)


def _do_update(cr, pool):
    # env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Setting fiscal_type_id fiscal_type_normal to all invoices")
    q = """
    SELECT res_id FROM ir_model_data
    WHERE module ~ 'l10n_ar_wsfe'
        AND name ~ 'fiscal_type_normal'
    """
    cr.execute(q)
    if cr.rowcount:
        fiscal_type_id, = cr.fetchone()
        cr.execute("UPDATE account_invoice SET fiscal_type_id=%(id)s", {'id': fiscal_type_id})
    else:
        _logger.warning('Unable to find l10n_ar_wsfe.fiscal_type_normal')

    # Re-Compute voucher_type_id (now with data loaded)
    invoice_obj = pool.get('account.invoice')
    invoices = invoice_obj.search(cr, SUPERUSER_ID, [])
    _logger.info('Re-Computing voucher_type for %s invoice(s)', len(invoices))
    res = invoice_obj._compute_voucher_type_id(cr, SUPERUSER_ID, invoices, None, None)
    for k, v in res.items():
        q = "UPDATE account_invoice SET voucher_type_id=%(vti)s WHERE id=%(id)s"
        q_p = {'id': k, 'vti': v}
        cr.execute(q, q_p)


def migrate(cr, installed_version):
    pool = pooler.get_pool(cr.dbname)
    _do_update(cr, pool)
