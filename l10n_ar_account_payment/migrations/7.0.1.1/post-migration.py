# -*- coding: utf-8 -*-

import psycopg2


def _do_update(cr):
    """
    Retrieve the journals of payment|receipt and set this journal to the account.vouchers
    """
    try:
        cr.execute("SELECT id FROM account_journal WHERE type ~ 'payment'")
        if cr.rowcount:
            payment_journal_id = cr.fetchone()[0]
        else:  # Generate the journal for payment
            # Generate sequence
            q = """
                select max(lala::numeric) + 1 as tv from (select regexp_replace(right(reference, 8), '\D', '', 'g') lala from account_voucher where type ~ 'payment' and reference is not null) a where lala != '';
            """
            cr.execute(q)
            next_number, = cr.fetchone()
            q = """
                INSERT INTO ir_sequence
                (implementation, name, number_increment, number_next, padding, prefix, active)
                VALUES
                (%(implementation)s, %(name)s, %(number_increment)s, %(number_next)s, %(padding)s, %(prefix)s, True)
                RETURNING id
            """
            q_params = {
                'implementation': 'no_gap',
                'name': 'OP0001',
                'number_increment': 1,
                'number_next': next_number,
                'padding': 8,
                'prefix': 'OP0001-'
            }
            cr.execute(q, q_params)
            seq_id = cr.fetchone()[0]
            q = """
                INSERT INTO account_journal
                (code, company_id, name, sequence_id, type)
                VALUES
                (%(code)s, %(company_id)s, %(name)s, %(sequence_id)s, %(type)s)
                RETURNING id
            """
            q_params = {
                'code': 'OP0001',
                'company_id': 1,
                'name': 'Talonario OP0001',
                'sequence_id': seq_id,
                'type': 'payment',
            }
            cr.execute(q, q_params)
            payment_journal_id = cr.fetchone()[0]
        q = "UPDATE account_voucher SET journal_id=%(j_id)s WHERE type ~ 'payment'"
        q_params = {'j_id': payment_journal_id}
        cr.execute(q, q_params)
        cr.execute("SELECT id FROM account_journal WHERE type ~ 'receipt'")
        if cr.rowcount:
            receipt_journal_id = cr.fetchone()[0]
        else:
            # Generate sequence
            q = """
                select max(lala::numeric) + 1 as tv from (select regexp_replace(right(reference, 8), '\D', '', 'g') lala from account_voucher where type ~ 'receipt' and reference is not null) a where lala != '';
            """
            cr.execute(q)
            next_number, = cr.fetchone()
            q = """
                INSERT INTO ir_sequence
                (implementation, name, number_increment, number_next, padding, prefix, active)
                VALUES
                (%(implementation)s, %(name)s, %(number_increment)s, %(number_next)s, %(padding)s, %(prefix)s, True)
                RETURNING id
            """
            q_params = {
                'implementation': 'no_gap',
                'name': 'R0001',
                'number_increment': 1,
                'number_next': next_number,
                'padding': 8,
                'prefix': 'R0001-'
            }
            cr.execute(q, q_params)
            seq_id = cr.fetchone()[0]
            q = """
                INSERT INTO account_journal
                (code, company_id, name, sequence_id, type)
                VALUES
                (%(code)s, %(company_id)s, %(name)s, %(sequence_id)s, %(type)s)
                RETURNING id
            """
            q_params = {
                'code': 'R 0001',
                'company_id': 1,
                'name': 'Talonario R0001',
                'sequence_id': seq_id,
                'type': 'receipt',
            }
            cr.execute(q, q_params)
            receipt_journal_id = cr.fetchone()[0]
        q = "UPDATE account_voucher SET journal_id=%(j_id)s WHERE type ~ 'receipt';"
        q_params = {'j_id': receipt_journal_id}
        cr.execute(q, q_params)
    except psycopg2.ProgrammingError:
        cr.rollback()
    else:
        cr.commit()


def fix_number_reference(cr):
    """
    1. Backup number to old_number
    2. Copy reference to number
    3. Move old_number to reference
    """
    try:
        cr.execute('ALTER TABLE account_voucher ADD column old_number varchar')
        cr.execute('UPDATE account_voucher SET old_number=number')
        cr.execute('UPDATE account_voucher SET number=reference')
        cr.execute('ALTER TABLE account_voucher DROP COLUMN reference')
        cr.execute('ALTER TABLE account_voucher RENAME COLUMN old_number TO reference')
    except psycopg2.ProgrammingError:
        cr.rollback()
    else:
        cr.commit()


def migrate(cr, installed_version):
    _do_update(cr)
    fix_number_reference(cr)
