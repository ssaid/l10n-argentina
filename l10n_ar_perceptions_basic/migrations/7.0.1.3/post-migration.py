# -*- coding: utf-8 -*-
__name__ = u"Popula las columnas tax_code_amount y base_code_amount por multimoneda"
import logging

logger = logging.getLogger(__name__)

def migrate(cr, version):
    if not version:
        return
    try:
        cr.execute("""
            UPDATE perception_tax_line SET tax_currency=amount, base_currency=base
            WHERE tax_currency IS NULL AND base_currency IS NULL
        """)
    except Exception as e:
        logger.warning('Error in update: %s' % e)
