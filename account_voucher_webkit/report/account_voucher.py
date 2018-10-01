# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2013 Serpent Consulting Services (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
import time

from openerp.report import report_sxw
import amount_to_text_sp

UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VENTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

UNITS = (
        ('',''),
        ('MIL ','MIL '),
        ('MILLON ','MILLONES '),
        ('MIL MILLONES ','MIL MILLONES '),
        ('BILLON ','BILLONES '),
        ('MIL BILLONES ','MIL BILLONES '),
        ('TRILLON ','TRILLONES '),
        ('MIL TRILLONES','MIL TRILLONES'),
        ('CUATRILLON','CUATRILLONES'),
        ('MIL CUATRILLONES','MIL CUATRILLONES'),
        ('QUINTILLON','QUINTILLONES'),
        ('MIL QUINTILLONES','MIL QUINTILLONES'),
        ('SEXTILLON','SEXTILLONES'),
        ('MIL SEXTILLONES','MIL SEXTILLONES'),
        ('SEPTILLON','SEPTILLONES'),
        ('MIL SEPTILLONES','MIL SEPTILLONES'),
        ('OCTILLON','OCTILLONES'),
        ('MIL OCTILLONES','MIL OCTILLONES'),
        ('NONILLON','NONILLONES'),
        ('MIL NONILLONES','MIL NONILLONES'),
        ('DECILLON','DECILLONES'),
        ('MIL DECILLONES','MIL DECILLONES'),
        ('UNDECILLON','UNDECILLONES'),
        ('MIL UNDECILLONES','MIL UNDECILLONES'),
        ('DUODECILLON','DUODECILLONES'),
        ('MIL DUODECILLONES','MIL DUODECILLONES'),
)

MONEDAS = (
    {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
    {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
    {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
    {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
    {'country': u'Peru', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
    {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'},
    {'country': u'Argentina', 'currency': 'ARS', 'singular': u'peso', 'plural': u'pesos', 'symbol': u'$'}
)
def hundreds_word(number):
    """Converts a positive number less than a thousand (1000) to words in Spanish

    Args:
        number (int): A positive number less than 1000
    Returns:
        A string in Spanish with first letters capitalized representing the number in letters

    Examples:
        >>> to_word(123)
        'Ciento Ventitres'
    """
    converted = ''
    if not (0 < number < 1000):
        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    cientos = number_str[6:]


    if(cientos):
        if(cientos == '001'):
            converted += 'UN '
        elif(int(cientos) > 0):
            converted += '%s ' % __convert_group(cientos)


    return converted.title().strip()



def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if(n == '100'):
        output = "CIEN "
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output

def to_word(number, mi_moneda=None):

    """Converts a positive number less than:
    (999999999999999999999999999999999999999999999999999999999999999999999999)
    to words in Spanish

    Args:
        number (int): A positive number less than specified above
        mi_moneda(str,optional): A string in ISO 4217 short format
    Returns:
        A string in Spanish with first letters capitalized representing the number in letters

    Examples:
        >>> number_words(53625999567)
        'Cincuenta Y Tres Mil Seiscientos Venticinco Millones Novecientos Noventa Y Nueve Mil Quinientos Sesenta Y Siete'
    """
    #~ if mi_moneda != None:
        #~ try:
            #~ moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
            #~ if number < 2:
                #~ moneda = moneda['singular']
            #~ else:
                #~ moneda = moneda['plural']
        #~ except:
            #~ return "Tipo de moneda invalida"
    #~ else:
    moneda = ""

    human_readable = []
    num_units = format(number,',').split(',')
    for i,n in enumerate(num_units):
        if int(n) != 0:
            words = hundreds_word(int(n))
            units = UNITS[len(num_units)-i-1][0 if int(n) == 1 else 1]
            human_readable.append([words,units])

    #filtrar MIL MILLONES - MILLONES -> MIL - MILLONES
    for i,item in enumerate(human_readable):
        try:
            if human_readable[i][1].find(human_readable[i+1][1]):
                human_readable[i][1] = human_readable[i][1].replace(human_readable[i+1][1],'')
        except IndexError:
            pass
    human_readable = [item for sublist in human_readable for item in sublist]
    human_readable.append(moneda)
    return ' '.join(human_readable).replace('  ',' ').title().strip()
    

class order(report_sxw.rml_parse):
    
    
    def _get_amount_to_text(self, uid, original, context=None):
        res = {}
        parte_decimal = int(round(abs(original)-abs(int(original)),2)*100)
        aux = ''
        if parte_decimal:
            return to_word(int(original),'ARS').lower() + ' de pesos con ' + str(parte_decimal) + '/100'
            
        return to_word(int(original),'ARS').lower() + ' de pesos'
        
    def __init__(self, cr, uid, name, context=None):
        super(order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time, 
            'show_formas_de_pago':self._show_formas_de_pago,
            'show_comprobantes_cr':self._show_comprobantes_cr,
            'show_comprobantes_dr':self._show_comprobantes_dr,
            'show_cheques_propios':self._show_cheques_propios,
            'show_cheques_recibo_terceros':self._show_cheques_recibo_terceros,
            'show_cheques_terceros':self._show_cheques_terceros,
            'show_retenciones':self._show_retenciones,
            'amount_to_text_sp': self._get_amount_to_text,
            'saldo': self._saldo,
        })

    def _show_formas_de_pago(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from payment_mode_receipt_line where voucher_id=%s',(voucher_id,))
        aux = cr.fetchone()
        return aux[0]

    def _show_cheques_propios(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from account_issued_check where voucher_id=%s',(voucher_id,))
        aux = cr.fetchone()
        return aux[0]

    def _show_cheques_recibo_terceros(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from account_third_check where source_voucher_id=%s',(voucher_id,))
        aux = cr.fetchone()
        return aux[0]

    def _show_cheques_terceros(self, uid, voucher_id, context=None):
        cr = self.cr
        print voucher_id
        cr.execute('select sum(tc.amount) from third_check_voucher_rel tr, account_third_check tc \
                    where tr.third_check_id=tc.id and tr.dest_voucher_id=%s',(voucher_id,))
        aux = cr.fetchone()
        return aux[0]
        
    def _show_comprobantes_cr(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from account_voucher_line where voucher_id=%s and type=%s',(voucher_id,'cr',))
        aux = cr.fetchone()
        return aux[0]
        
    def _show_comprobantes_dr(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from account_voucher_line where voucher_id=%s and type=%s',(voucher_id,'dr',))
        aux = cr.fetchone()
        return aux[0]
        
    def _show_retenciones(self, uid, voucher_id, context=None):
        cr = self.cr
        cr.execute('select sum(amount) from retention_tax_line where voucher_id=%s',(voucher_id,))
        aux = cr.fetchone()
        return aux[0]
        
    def _saldo(self, original, amount, context=None):
        return original - amount


    #~ def amount_to_text_sp(self, number, currency):
        #~ #return ''
        #~ print number
        #~ units_number = int(number)
        #~ units_name = currency
        #~ if units_number > 1:
            #~ units_name += 's'
        #~ units = _10000_to_text_sp(units_number)
        #~ units = units_number and '%s %s' % (units, units_name) or ''
#~ 
    #~ #   cents_number = int(number * 100) % 100
        #~ cents_number = int(round(math.fmod(number * 100,100)))
        #~ cents_name = (cents_number > 1) and 'centavos' or 'centavo'
        #~ cents = _100_to_text_sp(cents_number)
        #~ cents = cents_number and '%s %s' % (cents, cents_name) or ''
#~ 
    #~ #   cents = '%s / 100' % (cents_number)
#~ 
        #~ if units and cents:
            #~ cents = ' '+cents
#~ 
        #~ return (cents_number > 1) and (units + ' con ' + cents) or units
        
report_sxw.report_sxw('report.account.voucher.webkit', 'account.voucher', 'addons/account_voucher_webkit/report/account_voucher.mako', parser=order, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

