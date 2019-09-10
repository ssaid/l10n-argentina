# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _check_duplicated_records(cr):
    """
    l10n_ar_invoice_currency may have the denomination_E and fiscal_position_proveedor_exterior
    AIM of this migration is to delete without any data-loss by re-assigning id's to correct rows.
    As the module l10n_ar_IC depends of this module the migration will be called before upgrading
    that module (which deletes denomination_E and FPPE)
    """
    todo = [
        ('denomination_E', 'invoice_denomination', 'invoice.denomination'),
        ('fiscal_position_proveedor_exterior', 'account_fiscal_position', 'account.fiscal.position'),
    ]
    for ext_id, table, model in todo:
        q = """
        SELECT res_id FROM ir_model_data
        WHERE module='l10n_ar_invoice_currency'
            AND model=%(model)s
            AND name=%(ext_id)s
        """
        q_p = {'ext_id': ext_id, 'model': model}
        cr.execute(q, q_p)
        if cr.rowcount:
            old_id, = cr.fetchone()
            new_q = q.replace('l10n_ar_invoice_currency', 'l10n_ar_point_of_sale')
            cr.execute(new_q, q_p)
            if cr.rowcount:
                new_id, = cr.fetchone()
                _logger.info(
                    'Moving %s %s from #%s -> #%s', table, ext_id, old_id, new_id)
                try:
                    merge_records(cr, table, old_id, new_id)
                except Exception:
                    _logger.exception(
                        'Unable to move %s from %s to %s', ext_id, old_id, new_id)
                else:
                    cr.commit()
            else:
                _logger.error('Unable to find l10n_ar_point_of_sale.denomination_E')


def migrate(cr, installed_version):
    _check_duplicated_records(cr)


def merge_records(cr, rec_table, origin_record, target_record):
    """
    :rec_table: table_name (invoice_denomination)
    :origin_record: id
    :target_record: id
    """

    count_list = list_tables_referencing_record(
        cr, rec_table, origin_record)

    ref_tables = list(count_list.keys())
    cr.execute("SAVEPOINT bulk_savepoint")

    for ref_t in ref_tables:
        dot_index = ref_t.find(".")
        table = {
            'name': ref_t[0:dot_index],
            'column': ref_t[dot_index + 1:],
        }

        replace_query = """
            UPDATE """ + table['name'] + """
                SET """ + table['column'] + """ = %(target_record_id)s
                WHERE """ + table['column'] + """ = %(origin_record_id)s """

        try:
            q_p = {
                'target_record_id': target_record,
                'origin_record_id': origin_record,
            }
            _logger.info(cr.mogrify(replace_query, q_p))
            cr.execute(replace_query, q_p)
        except Exception as error:
            check_error(cr, table, error, origin_record)

        cr.execute("SAVEPOINT bulk_savepoint")

    count_list = list_tables_referencing_record(
        cr, rec_table, origin_record)

    if count_list:
        raise NameError('Record have referencing')

    _logger.warning('Maybe you want to run: DELETE FROM ' + rec_table + ' WHERE id=' + str(origin_record))

    return True


def list_tables_referencing_record(cr, rec_table, rec_id):
    """
    rec_table: invoice_denomination
    rec_id: id of record
    returns {'Table.Field': count}
    """

    query = """
    SELECT
        tc.table_name,
        kcu.column_name
    FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
    WHERE constraint_type = 'FOREIGN KEY'
        AND ccu.table_name='""" + rec_table + """'
    """
    cr.execute(query)
    fetch = cr.fetchall()
    tables = [{
        'name': t[0],
        'column': t[1],
    } for t in fetch]
    res = {}
    for table in tables:
        count_query = """
        SELECT COUNT(*) FROM """ + table['name'] + """
        WHERE """ + table['column'] + """ = %(rec_id)s
        """
        cr.execute(count_query, {
            'rec_id': rec_id,
        })
        qres = cr.fetchone()
        count = int(qres[0])
        thash = (".").join([table['name'], table['column']])
        if count:
            res[thash] = count
    _logger.info('Current IDs pointing to [%s #%s]: %s', rec_table, rec_id, res)
    return res


def check_error(cr, table, error, origin_record_id=None, target_record_id=None):
    UNIQUE_VIOLATION = '23505'

    if error.pgcode == UNIQUE_VIOLATION:
        cr.execute("ROLLBACK TO SAVEPOINT bulk_savepoint")
        q = """
            SELECT * FROM """ + table['name'] + """ LIMIT 1
            """
        cr.execute(q)
        columns = cr.description
        if not len(columns) == 2:
            raise error

        delete_query = """
            DELETE FROM """ + table['name'] + """
                WHERE """ + table['column'] + """ = %(origin_record_id)s
            """
        cr.execute(delete_query, {
            'origin_record_id': origin_record_id,
        })
    else:
        raise error

    return True
