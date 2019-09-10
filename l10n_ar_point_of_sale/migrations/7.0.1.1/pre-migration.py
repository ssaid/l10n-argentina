# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def get_denomination_in_use(cr, denomination):
    """
    Try to get denomination in use
    """
    q = """
    SELECT invd.id
    FROM invoice_denomination invd
        JOIN account_invoice ai ON ai.denomination_id = invd.id
    WHERE invd.name ~* %(denomination)s GROUP BY invd.id HAVING count(*) > 0
    ORDER BY count(*) DESC
    """
    cr.execute(q, {'denomination': denomination})
    ids = [i[0] for i in cr.fetchall()]
    ilen = len(ids)
    res = None
    if ilen:
        if ilen > 1:
            _logger.warning('More than one denomination E available: %s. Choosing the first one.' % ids)
        res = ids[0]
    else:
        _logger.warning('Not results for %s' % cr.mogrify(q))
    return res


def lookup_afp_for_den(cr, denid):
    q = """
        SELECT id
        FROM account_fiscal_position
        WHERE active=True and local=False and (
            denomination_id=%(den_id)s OR denom_supplier_id=%(den_id)s
        )
    """
    q_p = {'den_id': denid}
    cr.execute(q, q_p)
    ids = [i[0] for i in cr.fetchall()]
    res = None
    if ids:
        if len(ids) > 1:
            _logger.warning('More than one fiscal position matching query(choosing first one): %s' % cr.mogrify(q, q_p))
        res = ids[0]
    return res


def _do_update(cr):
    """
    Check if exist a denomination with E name and related to documents
    """
    den_eid = get_denomination_in_use(cr, '^e$')
    if den_eid:
        # Generate IMD for the denomination E
        q = """
        INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
        VALUES (%(name)s, %(module)s, %(model)s, %(res_id)s, True)
        """
        q_p = {
            'name': 'denomination_E',
            'module': 'l10n_ar_point_of_sale',
            'model': 'invoice.denomination',
            'res_id': den_eid,
        }
        _logger.info('Generating imd for denomination_E')
        try:
            cr.execute(q, q_p)
        except Exception:
            _logger.exception('Unable to add imd for denomination_E to %s' % den_eid)
            cr.rollback()
        else:
            _logger.info('[IMD] denomination_E refers to invoice.denomination %s' % den_eid)
            cr.commit()

        # Lookup AFP for denomination E
        afpid = lookup_afp_for_den(cr, den_eid)
        if afpid:
            # Generate IMD for the AFP Exterior
            q = """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            VALUES (%(name)s, %(module)s, %(model)s, %(res_id)s, True)
            """
            q_p = {
                'name': 'fiscal_position_proveedor_exterior',
                'module': 'l10n_ar_point_of_sale',
                'model': 'account.fiscal.position',
                'res_id': afpid,
            }
            _logger.info('Generating imd for fiscal_position_proveedor_exterior')
            try:
                cr.execute(q, q_p)
            except Exception:
                _logger.exception('Unable to add imd for fiscal_position_proveedor_exterior to %s' % afpid)
                cr.rollback()
            else:
                _logger.info('[IMD] fiscal_position_proveedor_exterior refers to account.fiscal.position %s' % afpid)
                cr.commit()

    # Denomination M
    den_eid = get_denomination_in_use(cr, '^m$')
    if den_eid:
        # Generate IMD for the denomination M
        q = """
        INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
        VALUES (%(name)s, %(module)s, %(model)s, %(res_id)s, True)
        """
        q_p = {
            'name': 'denomination_M',
            'module': 'l10n_ar_point_of_sale',
            'model': 'invoice.denomination',
            'res_id': den_eid,
        }
        _logger.info('Generating imd for denomination_M')
        try:
            cr.execute(q, q_p)
        except Exception:
            _logger.exception('Unable to add imd for denomination_M to %s' % den_eid)
            cr.rollback()
        else:
            _logger.info('[IMD] denomination_M refers to invoice.denomination %s' % den_eid)
            cr.commit()

    # Handle final_consumer AFP
    q = """
    SELECT id FROM account_fiscal_position
    WHERE is_final_consumer is True
    """
    cr.execute(q)
    if cr.rowcount:
        afpid, = cr.fetchone()
        q = """
        SELECT id FROM ir_model_data
        WHERE name ~* 'fiscal_position_final_consumer'
        """
        cr.execute(q)
        if not cr.rowcount:
            # Generate IMD for the AFP Consumidor Final
            q = """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            VALUES (%(name)s, %(module)s, %(model)s, %(res_id)s, True)
            """
            q_p = {
                'name': 'fiscal_position_final_consumer',
                'module': 'l10n_ar_point_of_sale',
                'model': 'account.fiscal.position',
                'res_id': afpid,
            }
            _logger.info('Generating IMD for fiscal_position_final_consumer')
            try:
                cr.execute(q, q_p)
            except Exception:
                _logger.exception('Unable to add imd for fiscal_position_final_consumer to %s' % afpid)
                cr.rollback()
            else:
                _logger.info('[IMD] fiscal_position_final_consumer refers to account.fiscal.position %s' % afpid)
                cr.commit()


def migrate(cr, installed_version):
    return _do_update(cr)
