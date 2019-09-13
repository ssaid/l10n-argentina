#' -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 E-MIPS (http://www.e-mips.com.ar) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
from wsfetools.wsfe_suds import WSFEv1 as wsfe
from datetime import datetime
import time


class wsfe_tax_codes(osv.osv):
    _name = "wsfe.tax.codes"
    _description = "Tax Codes"
    _columns = {
        'code' : fields.char('Code', required=False, size=4),
        'name' : fields.char('Desc', required=True, size=64),
        'to_date' : fields.date('Effect Until'),
        'from_date' : fields.date('Effective From'),
        'tax_id' : fields.many2one('account.tax','Account Tax'),
        'tax_code_id': fields.many2one('account.tax.code', 'Account Tax Code'),
        'wsfe_config_id' : fields.many2one('wsfe.config','WSFE Configuration'),
        'from_afip': fields.boolean('From AFIP'),
        'exempt_operations': fields.boolean('Exempt Operations', help='Check it if this VAT Tax corresponds to vat tax exempts operations, such as to sell books, milk, etc. The taxes with this checked, will be reported to AFIP as  exempt operations (base amount) without VAT applied on this'),
    }


class wsfe_optionals(osv.osv):
    _name = "wsfe.optionals"
    _description = "WSFE Optionals"

    _columns = {
        'code': fields.char('Code', required=False, size=4),
        'name': fields.char('Desc', required=True, size=64),
        'to_date': fields.date('Effect Until'),
        'from_date': fields.date('Effective From'),
        'from_afip': fields.boolean('From AFIP'),
        'wsfe_config_id': fields.many2one('wsfe.config', 'WSFE Configuration'),
    }


class wsfe_config(osv.osv):
    _name = "wsfe.config"
    _description = "Configuration for WSFE"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'cuit': fields.related('company_id', 'partner_id', 'vat', type='char', string='Cuit'),
        'url' : fields.char('URL for WSFE', size=60, required=True),
        'homologation' : fields.boolean('Homologation', help="If true, there will be some validations that are disabled, for example, invoice number correlativeness"),
        'point_of_sale_ids': fields.many2many('pos.ar', 'pos_ar_wsfe_rel', 'wsfe_config_id', 'pos_ar_id', 'Points of Sale'),
        'vat_tax_ids' : fields.one2many('wsfe.tax.codes', 'wsfe_config_id' ,'Taxes', domain=[('from_afip', '=', True)]),
        'exempt_operations_tax_ids' : fields.one2many('wsfe.tax.codes', 'wsfe_config_id' ,'Taxes', domain=[('from_afip', '=', False), ('exempt_operations', '=', True)]),
        'optional_ids': fields.one2many('wsfe.optionals', 'wsfe_config_id', 'Optionals', domain=[('from_afip', '=', True)]),
        'wsaa_ticket_id' : fields.many2one('wsaa.ta', 'Ticket Access'),
        'company_id' : fields.many2one('res.company', 'Company Name' , required=True),
    }

    _sql_constraints = [
        #('company_uniq', 'unique (company_id)', 'The configuration must be unique per company !')
    ]

    _defaults = {
        'company_id' : lambda self, cr, uid, context=None: self.pool.get('res.users')._get_company(cr, uid, context=context),
        'homologation': lambda *a: False,
        }

    def create(self, cr, uid, vals, context):

        # Creamos tambien un TA para este servcio y esta compania
        ta_obj = self.pool.get('wsaa.ta')
        wsaa_obj = self.pool.get('wsaa.config')
        service_obj = self.pool.get('afipws.service')

        # Buscamos primero el wsaa que corresponde a esta compania
        # porque hay que recordar que son unicos por compania
        wsaa_ids = wsaa_obj.search(cr, uid, [('company_id','=', vals['company_id'])], context=context)
        service_ids = service_obj.search(cr, uid, [('name','=', 'wsfe')], context=context)
        if wsaa_ids:
            ta_vals = {
                'name': service_ids[0],
                'company_id': vals['company_id'],
                'config_id' : wsaa_ids[0],
                }

            ta_id = ta_obj.create(cr, uid, ta_vals, context)
            vals['wsaa_ticket_id'] = ta_id

        return super(wsfe_config, self).create(cr, uid, vals, context)

    # TODO: Cuando se borra esta configuracion
    # debemos borrar el wsaa.ta correspondiente
    #def unlink(self, cr, uid, ids):

    def get_config(self, cr, uid):
        # Obtenemos la compania que esta utilizando en este momento este usuario
        company_id = self.pool.get('res.users')._get_company(cr, uid)
        if not company_id:
            raise osv.except_osv(_('Company Error!'), _('There is no company being used by this user'))

        ids = self.search(cr, uid, [('company_id','=',company_id)])
        if not ids:
            raise osv.except_osv(_('WSFE Config Error!'), _('There is no WSFE configuration set to this company'))

        return self.browse(cr, uid, ids[0])


    def check_errors(self, cr, uid, res, raise_exception=True, context=None):
        msg = ''
        if 'errors' in res:
            errors = [error.msg for error in res['errors']]
            err_codes = [str(error.code) for error in res['errors']]
            msg = ' '.join(errors)
            msg = msg + ' Codigo/s Error:' + ' '.join(err_codes)

            if msg != '' and raise_exception:
                raise osv.except_osv(_('WSFE Error!'), msg)

        return msg

    def check_observations(self, cr, uid, res, context):
        msg = ''
        if 'observations' in res:
            observations = [obs.msg for obs in res['observations']]
            obs_codes = [str(obs.code) for obs in res['observations']]
            msg = ' '.join(observations)
            msg = msg + ' Codigo/s Observacion:' + ' '.join(obs_codes)

            # Escribimos en el log del cliente web
            #self.log(cr, uid, None, msg, context)

        return msg

    def get_invoice_CAE(self, cr, uid, ids, invoice_ids, pos, voucher_type, details, context={}):
        ta_obj = self.pool.get('wsaa.ta')

        conf = self.browse(cr, uid, ids)[0]
        token, sign = ta_obj.get_token_sign(cr, uid, [conf.wsaa_ticket_id.id], context=context)

        _wsfe = wsfe(conf.cuit, token, sign, conf.url)
        res = _wsfe.fe_CAE_solicitar(pos, voucher_type, details)

        return res

    def _parse_result(self, cr, uid, ids, invoice_ids, result, context=None):

        invoice_obj = self.pool.get('account.invoice')

        if not context:
            context = {}

        invoices_approbed = {}

        # Verificamos el resultado de la Operacion
        # Si no fue aprobado
        if result['Resultado'] == 'R':
            msg = ''
            if result['Errores']:
                msg = 'Errores: ' + '\n'.join(result['Errores']) + '\n'

            if context.get('raise-exception', True):
                raise osv.except_osv(_('AFIP Web Service Error'),
                                     _('La factura no fue aprobada. \n%s') % msg)

        elif result['Resultado'] == 'A' or result['Resultado'] == 'P':
            index = 0
            for inv in invoice_obj.browse(cr, uid, invoice_ids):
                invoice_vals = {}
                comp = result['Comprobantes'][index]
                if comp['Observaciones']:
                    msg = 'Observaciones: ' + '\n'.join(comp['Observaciones'])

                # Chequeamos que se corresponda con la factura que enviamos a validar
                doc_type, doc_num = self._get_doctype_and_num(inv)
                doc_tipo = comp['DocTipo'] == int(doc_type)
                doc_num = comp['DocNro'] == int(doc_num)
                cbte = True
                if inv.internal_number:
                    cbte = comp['CbteHasta'] == int(inv.internal_number.split('-')[1])
                else:
                    # TODO: El nro de factura deberia unificarse para que se setee en una funcion
                    # o algo asi para que no haya posibilidad de que sea diferente nunca en su formato
                    invoice_vals['internal_number'] = '%04d-%08d' % (result['PtoVta'], comp['CbteHasta'])

                if not all([doc_tipo, doc_num, cbte]):
                    raise osv.except_osv(_("WSFE Error!"), _("Validated invoice that not corresponds!"))

                if comp['Resultado'] == 'A':
                    invoice_vals['cae'] = comp['CAE']
                    invoice_vals['cae_due_date'] = comp['CAEFchVto']
                    invoices_approbed[inv.id] = invoice_vals

                index += 1

        return invoices_approbed

    def _log_wsfe_request(self, cr, uid, ids, pos, voucher_type_code, details, res, context=None):
        wsfe_req_obj = self.pool.get('wsfe.request')
        voucher_type_obj = self.pool.get('wsfe.voucher_type')
        voucher_type_ids = voucher_type_obj.search(cr, uid, [('code','=',voucher_type_code)])
        voucher_type_name = voucher_type_obj.read(cr, uid, voucher_type_ids, ['name'])[0]['name']
        req_details = []
        for index, comp in enumerate(res['Comprobantes']):
            detail = details[index]

            # Esto es para fixear un bug que al hacer un refund, si fallaba algo con la AFIP
            # se hace el rollback por lo tanto el refund que se estaba creando ya no existe en
            # base de datos y estariamos violando una foreign key contraint. Por eso,
            # chequeamos que existe info de la invoice_id, sino lo seteamos en False
            read_inv = self.pool.get('account.invoice').read(cr, uid, detail['invoice_id'], ['id', 'internal_number'], context=context)

            if not read_inv:
                invoice_id = False
            else:
                invoice_id = detail['invoice_id']

            det = {
                'name': invoice_id,
                'concept': str(detail['Concepto']),
                'doctype': detail['DocTipo'], # TODO: Poner aca el nombre del tipo de documento
                'docnum': str(detail['DocNro']),
                'voucher_number': comp['CbteHasta'],
                'voucher_date': comp['CbteFch'],
                'amount_total': detail['ImpTotal'],
                'cae': comp['CAE'],
                'cae_duedate': comp['CAEFchVto'],
                'result': comp['Resultado'],
                'currency': detail['MonId'],
                'currency_rate': detail['MonCotiz'],
                'observations': '\n'.join(comp['Observaciones']),
            }

            req_details.append((0, 0, det))

        # Chequeamos el reproceso
        reprocess = False
        if res['Reproceso'] == 'S':
            reprocess = True

        vals = {
            'voucher_type': voucher_type_name,
            'nregs': len(details),
            'pos_ar': '%04d' % pos,
            'date_request': time.strftime('%Y-%m-%d %H:%M:%S'),
            'result': res['Resultado'],
            'reprocess': reprocess,
            'errors': '\n'.join(res['Errores']),
            'detail_ids': req_details,
            }

        return wsfe_req_obj.create(cr, uid, vals)

    def get_last_voucher(self, cr, uid, ids, pos, voucher_type, context={}):
        ta_obj = self.pool.get('wsaa.ta')

        conf = self.browse(cr, uid, ids)[0]
        token, sign = ta_obj.get_token_sign(cr, uid, [conf.wsaa_ticket_id.id], context=context)

        _wsfe = wsfe(conf.cuit, token, sign, conf.url)
        res = _wsfe.fe_comp_ultimo_autorizado(pos, voucher_type)

        self.check_errors(cr, uid, res, context=context)
        self.check_observations(cr, uid, res, context=context)
        last = res['response']
        return last

    def get_voucher_info(self, cr, uid, ids, pos, voucher_type, number, context={}):
        ta_obj = self.pool.get('wsaa.ta')

        conf = self.browse(cr, uid, ids)[0]
        token, sign = ta_obj.get_token_sign(cr, uid, [conf.wsaa_ticket_id.id], context=context)

        _wsfe = wsfe(conf.cuit, token, sign, conf.url)
        res = _wsfe.fe_comp_consultar(pos, voucher_type, number)

        self.check_errors(cr, uid, res, context=context)
        self.check_observations(cr, uid, res, context=context)
        #last = res['response'].CbteNro

        res = res['response']

        result = {
            'DocTipo' : res[0].DocTipo,
            'DocNro' : res[0].DocNro,
            'CbteDesde' : res[0].CbteDesde,
            'CbteHasta' : res[0].CbteHasta,
            'CbteFch' : res[0].CbteFch,
            'ImpTotal' : res[0].ImpTotal,
            'ImpTotConc' : res[0].ImpTotConc,
            'ImpNeto' : res[0].ImpNeto,
            'ImpOpEx' : res[0].ImpOpEx,
            'ImpTrib' : res[0].ImpTrib,
            'ImpIVA' : res[0].ImpIVA,
            'FchServDesde' : res[0].FchServDesde,
            'FchServHasta' : res[0].FchServHasta,
            'FchVtoPago' : res[0].FchVtoPago,
            'MonId' : res[0].MonId,
            'MonCotiz' : res[0].MonCotiz,
            'Resultado' : res[0].Resultado,
            'CodAutorizacion' : res[0].CodAutorizacion,
            'EmisionTipo' : res[0].EmisionTipo,
            'FchVto' : res[0].FchVto,
            'FchProceso' : res[0].FchProceso,
            'PtoVta' : res[0].PtoVta,
            'CbteTipo' : res[0].CbteTipo,
        }

        return result

    def read_tax(self, cr, uid , ids , context={}):
        ta_obj = self.pool.get('wsaa.ta')
        wsfe_tax_obj = self.pool.get('wsfe.tax.codes')
        wsfe_optionals_obj = self.pool.get('wsfe.optionals')

        conf = self.browse(cr, uid, ids)[0]
        token, sign = ta_obj.get_token_sign(cr, uid, [conf.wsaa_ticket_id.id], context=context)

        _wsfe = wsfe(conf.cuit, token, sign, conf.url)
        res = _wsfe.fe_param_get_tipos_iva()

        # Chequeamos los errores
        msg = self.check_errors(cr, uid, res, raise_exception=False, context=context)
        if msg:
            # TODO: Hacer un wrapping de los errores, porque algunos son
            # largos y se imprimen muy mal en pantalla
            raise osv.except_osv(_('Error reading taxes'), msg)

        #~ Armo un lista con los codigos de los Impuestos
        for r in res['response']:
            res_c = wsfe_tax_obj.search(cr, uid , [('code','=', r.Id )])

            #~ Si tengo no los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                fd = datetime.strptime(r.FchDesde, '%Y%m%d')
                try:
                    td = datetime.strptime(r.FchHasta, '%Y%m%d')
                except ValueError:
                    td = False

                wsfe_tax_obj.create(cr, uid , {'code': r.Id, 'name': r.Desc, 'to_date': td,
                        'from_date': fd, 'wsfe_config_id': ids[0], 'from_afip': True } , context={})
            #~ Si los codigos estan en la db los modifico
            else :
                fd = datetime.strptime(r.FchDesde, '%Y%m%d')
                #'NULL' ?? viene asi de fe_param_get_tipos_iva():
                try:
                    td = datetime.strptime(r.FchHasta, '%Y%m%d')
                except ValueError:
                    td = False

                wsfe_tax_obj.write(cr, uid , res_c[0] , {'code': r.Id, 'name': r.Desc, 'to_date': td ,
                    'from_date': fd, 'wsfe_config_id': ids[0], 'from_afip': True } )

        res = _wsfe.fe_param_get_tipos_opcionales()

        # Chequeamos los errores
        msg = self.check_errors(
            cr, uid, res, raise_exception=False, context=context)

        if msg:
            raise osv.except_osv(_('Error reading optionals'), msg)

        for r in res['response']:
            res_c = wsfe_optionals_obj.search(cr, uid , [('code','=', r.Id )])

            #~ Si tengo no los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                fd = datetime.strptime(r.FchDesde, '%Y%m%d')
                try:
                    td = datetime.strptime(r.FchHasta, '%Y%m%d')
                except ValueError:
                    td = False

                wsfe_optionals_obj.create(
                    cr, uid , {
                        'code': r.Id, 'name': r.Desc, 'to_date': td,
                        'from_date': fd, 'wsfe_config_id': ids[0],
                        'from_afip': True } , context={})
            #~ Si los codigos estan en la db los modifico
            else :
                fd = datetime.strptime(r.FchDesde, '%Y%m%d')
                #'NULL' ?? viene asi de fe_param_get_tipos_iva():
                try:
                    td = datetime.strptime(r.FchHasta, '%Y%m%d')
                except ValueError:
                    td = False

                wsfe_optionals_obj.write(
                    cr, uid , res_c[0] , {
                        'code': r.Id, 'name': r.Desc, 'to_date': td ,
                        'from_date': fd, 'wsfe_config_id': ids[0],
                        'from_afip': True } )


        return True

    def _get_doctype_and_num(self, inv):

        partner = inv.partner_id.parent_id or inv.partner_id
        doc_type = partner.document_type_id and partner.document_type_id.afip_code or '99'
        doc_num = partner.vat or '0'

        # Si no tiene vat o no tiene tipo doc, quedan doc_num=0 y doc_type=99
        if doc_num == '0' or doc_type == '99':
            doc_num = '0'
            doc_type = '99'

        return doc_type, doc_num

    def prepare_details(self, cr, uid, conf, invoice_ids, context=None):
        obj_precision = self.pool.get('decimal.precision')
        invoice_obj = self.pool.get('account.invoice')
        company_id = self.pool.get('res.users')._get_company(cr, uid)

        obj_data = self.pool.get('ir.model.data')
        wsfcred_type = obj_data.get_object_reference(
            cr, uid, 'l10n_ar_wsfe', 'fiscal_type_fcred')[1]

        details = []

        first_num = context.get('first_num', False)
        cbte_nro = 0

        for inv in invoice_obj.browse(cr, uid, invoice_ids):
            detalle = {}

            doc_type, doc_num = self._get_doctype_and_num(inv)

            fiscal_position = inv.fiscal_position
            # Chequeamos si el concepto es producto, servicios o productos y servicios
            product_service = [l.product_id and l.product_id.type or 'consu' for l in inv.invoice_line]

            service = all([ps == 'service' for ps in product_service])
            products = all([ps == 'consu' or ps == 'product' for ps in product_service])

            # Calculamos el concepto de la factura, dependiendo de las
            # lineas de productos que se estan vendiendo
            concept = None
            if products:
                concept = 1 # Productos
            elif service:
                concept =  2 # Servicios
            else:
                concept = 3 # Productos y Servicios

            if not fiscal_position:
                raise osv.except_osv(_('Customer Configuration Error'),
                                    _('There is no fiscal position configured for the customer %s') % inv.partner_id.name)

            # Obtenemos el numero de comprobante a enviar a la AFIP teniendo en
            # cuenta que inv.number == 000X-00000NN o algo similar.
            if not inv.internal_number:
                if not first_num:
                    raise osv.except_osv(_("WSFE Error!"), _("There is no first invoice number declared!"))
                inv_number = first_num
            else:
                inv_number = inv.internal_number

            if not cbte_nro:
                cbte_nro = inv_number.split('-')[1]
                cbte_nro = int(cbte_nro)
            else:
                cbte_nro = cbte_nro + 1

            if not inv.date_invoice:
                date_inv = datetime.strftime(datetime.now(), '%Y-%m-%d')
            else:
                date_inv = inv.date_invoice
            date_invoice = datetime.strptime(date_inv, '%Y-%m-%d')
            formatted_date_invoice = date_invoice.strftime('%Y%m%d')
            date_due = inv.date_due and datetime.strptime(inv.date_due, '%Y-%m-%d').strftime('%Y%m%d') or formatted_date_invoice

#            company_currency_id = self.pool.get('res.company').read(cr, uid, company_id, ['currency_id'], context=context)['currency_id'][0]
#            if inv.currency_id.id != company_currency_id:
#                raise osv.except_osv(_("WSFE Error!"), _("Currency cannot be different to company currency. Also check that company currency is ARS"))

            detalle['invoice_id'] = inv.id

            detalle['Concepto'] = concept
            detalle['DocTipo'] = doc_type
            detalle['DocNro'] = doc_num
            detalle['CbteDesde'] = cbte_nro
            detalle['CbteHasta'] = cbte_nro
            detalle['CbteFch'] = date_invoice.strftime('%Y%m%d')
            if concept in [2,3]:
                detalle['FchServDesde'] = formatted_date_invoice
                detalle['FchServHasta'] = formatted_date_invoice
                detalle['FchVtoPago'] = date_due
            elif inv.fiscal_type_id.id == wsfcred_type:
                detalle['FchVtoPago'] = date_due

            # Obtenemos la moneda de la factura
            # Lo hacemos por el wsfex_config, por cualquiera de ellos
            # si es que hay mas de uno
            currency_code_obj = self.pool.get('wsfex.currency.codes')
            currency_code_ids = currency_code_obj.search(cr, uid,
                    [('currency_id', '=', inv.currency_id.id)], context=context)

            if not currency_code_ids:
                raise osv.except_osv(_("WSFE Error!"), _("Currency has to be configured correctly in WSFEX Configuration."))

            currency_code = currency_code_obj.read(cr, uid, currency_code_ids[0],
                    ['code'], context=context)['code']

            # Cotizacion
            company_currency_id = self.pool.get('res.company').read(cr, uid, company_id, ['currency_id'], context=context)['currency_id'][0]
            invoice_rate = 1.0
            if inv.currency_id.id != company_currency_id:
                invoice_rate = inv.currency_rate

            detalle['MonId'] = currency_code
            detalle['MonCotiz'] = invoice_rate

            iva_array = []

            importe_neto = 0.0
            importe_operaciones_exentas = inv.amount_exempt
            importe_iva = 0.0
            importe_tributos = 0.0
            importe_total = 0.0
            importe_neto_no_gravado = inv.amount_no_taxed

            # Procesamos las taxes
            taxes = inv.tax_line
            for tax in taxes:
                found = False
                for eitax in conf.vat_tax_ids + conf.exempt_operations_tax_ids:
                    if eitax.tax_code_id.id == tax.tax_code_id.id:
                        found = True
                        if eitax.exempt_operations:
                            pass
                            #importe_operaciones_exentas += tax.base
                        else:
                            importe_iva += tax.amount
                            importe_neto += tax.base
                            iva2 = {'Id': int(eitax.code), 'BaseImp': tax.base, 'Importe': tax.amount}
                            iva_array.append(iva2)
                if not found:
                    importe_tributos += tax.amount

            importe_total = importe_neto + importe_neto_no_gravado + importe_operaciones_exentas + importe_iva + importe_tributos
#            print 'Importe total: ', importe_total
#            print 'Importe neto gravado: ', importe_neto
#            print 'Importe IVA: ', importe_iva
#            print 'Importe Operaciones Exentas: ', importe_operaciones_exentas
#            print 'Importe neto No gravado: ', importe_neto_no_gravado
#            print 'Array de IVA: ', iva_array

            # Chequeamos que el Total calculado por el Open, se corresponda
            # con el total calculado por nosotros, tal vez puede haber un error
            # de redondeo
            prec = obj_precision.precision_get(cr, uid, 'Account')
            if round(importe_total, prec) != round(inv.amount_total, prec):
                raise osv.except_osv(_('Error in amount_total!'), _("The total amount of the invoice does not corresponds to the total calculated." \
                    "Maybe there is an rounding error!. (Amount Calculated: %f)") % (importe_total))

            # Detalle del array de IVA
            detalle['Iva'] = iva_array
            detalle['Opcionales'] = map(lambda o: {
                'Id': int(o.optional_id.code),
                'Valor': o.value}, inv.optional_ids)

            # Detalle de los importes
            detalle['ImpOpEx'] = importe_operaciones_exentas
            detalle['ImpNeto'] = importe_neto
            detalle['ImpTotConc'] = importe_neto_no_gravado
            detalle['ImpIVA'] = importe_iva
            detalle['ImpTotal'] = inv.amount_total
            detalle['ImpTrib'] = importe_tributos
            detalle['Tributos'] = None
            #print 'Detalle de facturacion: ', detalle

            # Associated Comps
            CbtesAsoc = []
            total_associated = 0.0
            for associated_inv in inv.associated_inv_ids:
                tipo_cbte = associated_inv.voucher_type_id.code
                pos, number = associated_inv.internal_number.split('-')
                cbte_fch = datetime.strptime(
                    associated_inv.date_invoice, '%Y-%m-%d').strftime('%Y%m%d')
                CbteAsoc = {
                    'Tipo': tipo_cbte,
                    'PtoVta': int(pos),
                    'Nro': int(number),
                    'Cuit': inv.company_id.partner_id.vat,
                    'CbteFch': cbte_fch,
                }

                total_associated += associated_inv.amount_total
                CbtesAsoc.append(CbteAsoc)

            if CbtesAsoc and inv.fiscal_type_id.id == wsfcred_type:
                detalle['CbtesAsoc'] = CbtesAsoc

                anulled_inv = 'S' if total_associated == inv.amount_total else 'N'

                # Anulacion
                detalle['Opcionales'].append({
                    'Id': 22,
                    'Valor': anulled_inv,
                })

            # Agregamos un hook para agregar tributos o IVA que pueda ser
            # llamado de otros modulos. O mismo para modificar el detalle.
            detalle = invoice_obj.hook_add_taxes(cr, uid, inv, detalle)

            details.append(detalle)

        #print 'Detalles: ', details
        return details

wsfe_config()
wsfe_tax_codes()

class wsfe_voucher_type(osv.osv):
    _name = "wsfe.voucher_type"
    _description = "Voucher Type for Electronic Invoice"

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=False, help='Voucher Type, eg.: Factura A, Nota de Credito B, etc.'),
        'code': fields.char('Code', size=4, required=True, help='Internal Code assigned by AFIP for voucher type'),

        'voucher_model': fields.selection([
            ('account.invoice','Factura/NC/ND'),
            ('account.voucher','Recibo'),],'Voucher Model', select=True, required=True),

        'document_type' : fields.selection([
            ('invoice','Factura'),
            ('refund','Nota de Credito'),
            ('debit','Nota de Debito'),
            ],'Document Type', select=True, required=True, readonly=False),

        'denomination_id': fields.many2one('invoice.denomination', 'Denomination', required=False),
        'fiscal_type_id': fields.many2one('account.invoice.fiscal.type', 'Fiscal type'),
    }

    """Es un comprobante que una empresa envía a su cliente, en la que se le notifica haber cargado o debitado en su cuenta una determinada suma o valor, por el concepto que se indica en la misma nota. Este documento incrementa el valor de la deuda o saldo de la cuenta, ya sea por un error en la facturación, interés por mora en el pago, o cualquier otra circunstancia que signifique el incremento del saldo de una cuenta.
It is a proof that a company sends to your client, which is notified to be charged or debited the account a certain sum or value, the concept shown in the same note. This document increases the value of the debt or account balance, either by an error in billing, interest for late payment, or any other circumstance that means the increase in the balance of an account."""


    # def get_voucher_type(self, cr, uid, voucher, context=None):
    #
    #     # Chequeamos el modelo
    #     voucher_model = None
    #     model = voucher._table_name
    #
    #     if model == 'account.invoice':
    #         voucher_model = 'invoice'
    #
    #         denomination_id = voucher.denomination_id.id
    #         type = voucher.type
    #         fiscal_type_id = voucher.fiscal_type_id.id
	#
    #         if type == 'out_invoice':
    #             # TODO: Activar esto para ND
    #             if voucher.is_debit_note:
    #                 type = 'out_debit'
    #
    #         res = self.search(
    #             cr, uid, [
    #                 ('voucher_model','=',voucher_model),
    #                 ('document_type','=',type),
    #                 ('denomination_id','=',denomination_id)],
    #             context=context)
    #
    #         if fiscal_type_id:
    #             res = filter(
    #                 lambda vt: vt.fiscal_type_id.id == fiscal_type_id, res)
    #
    #         if not len(res):
    #             raise osv.except_osv(_("Voucher type error!"), _("There is no voucher type that corresponds to this object"))
    #
    #         # if len(res) > 1:
    #         #     raise osv.except_osv(_("Voucher type error!"), _("There is more than one voucher type that corresponds to this object"))
    #
    #         return self.read(cr, uid, res[0], ['code'], context=context)['code']
    #
    #     elif model == 'account.voucher':
    #         voucher_model = 'voucher'
    #
    #     return None

wsfe_voucher_type()
