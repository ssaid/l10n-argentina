# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _do_update(cr):
    try:
        _logger.info("Step 1: Deleting existing voucher types")
        q = """
            DELETE
            FROM wsfe_voucher_type
            """
        cr.execute(q)
        _logger.info("Step 2: Deleting records from ir_model_data")
        q = """
            DELETE FROM ir_model_data
            WHERE model = 'wsfe.voucher_type'
            AND module = 'l10n_ar_wsfe'
        """
        cr.execute(q)
        _logger.info("Step 3: Drop and Re-Create voucher_type_id of account_invoice (Prevents re-calculation voucher_type_id without data non-loaded)")
        cr.execute("ALTER TABLE account_invoice DROP COLUMN IF EXISTS voucher_type_id")
        cr.execute("ALTER TABLE account_invoice ADD COLUMN voucher_type_id int4")
    except Exception as e:
        _logger.warning(e)
        cr.rollback()
    else:
        cr.commit()


def migrate(cr, installed_version):
    _do_update(cr)
