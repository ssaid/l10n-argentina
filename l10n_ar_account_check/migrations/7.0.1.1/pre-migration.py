# -*- coding: utf-8 -*-

from openupgradelib import openupgrade

column_renames = {
    'account_third_check': [
        ('voucher_id', 'source_voucher_id'),
    ],
    'third_check_voucher_rel': [
        ('voucher_id', 'dest_voucher_id'),
    ]
}


@openupgrade.migrate()
def migrate(cr, version):
    if not version:
        return
    openupgrade.rename_columns(cr, column_renames)
