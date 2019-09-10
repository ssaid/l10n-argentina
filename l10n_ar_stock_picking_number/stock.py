# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
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

from openerp.osv import osv, fields


class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"

    _columns = {
        'renum_pick_id': fields.many2one('stock.picking.out', 'Renumerated', help="Reference to the new picking created for renumerate this one. You cannot delete pickings if it is done, so it is cancelled and a new one is created, corrected and renumerated"),
    }

    def action_done(self, cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = super(stock_picking, self).action_done(cr, uid, ids,
                                                     context=context)
        pickings = self.browse(cr, uid, ids, context=context)
        for pick in pickings:
            if pick.type == 'out':
                seq = 'stock.picking.out.ar'
                new_pick_name = seq_obj.next_by_code(cr, uid, seq)
                vals = {'name': new_pick_name}
                self.write(cr, uid, pick.id, vals, context=context)

        return res


class stock_picking_out(osv.osv):
    _name = "stock.picking.out"
    _inherit = "stock.picking.out"

    _columns = {
        'renum_pick_id': fields.many2one('stock.picking.out', 'Renumerated', help="Reference to the new picking created for renumerate this one. You cannot delete pickings if it is done, so it is cancelled and a new one is created, corrected and renumerated"),
    }
