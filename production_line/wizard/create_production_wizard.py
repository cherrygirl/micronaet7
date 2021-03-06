# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#    ########################################################################
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
from openerp.osv import fields,osv
from datetime import datetime
from openerp.tools.translate import _


# Generic function 
def return_view(self, cr, uid, res_id, view_name, object_name):
    '''Function that return dict action for next step of the wizard
    '''
    if not view_name: return {'type':'ir.actions.act_window_close'}

    view_element=view_name.split(".")
    views=[]
    
    if len(view_element)!=2: return  {'type':'ir.actions.act_window_close'}

    model_id=self.pool.get('ir.model.data').search(cr, uid, [('model','=','ir.ui.view'), ('module','=',view_element[0]), ('name', '=', view_element[1])])
    if model_id:
        view_id=self.pool.get('ir.model.data').read(cr, uid, model_id)[0]['res_id']
        views=[(view_id, 'form'),(False, 'tree')]

    return {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': object_name, # object linked to the view
            'views': views,
            'domain': [('id', 'in', res_id)], 
            #'views': [(view_id, 'form')],
            #'view_id': False,
            'type': 'ir.actions.act_window',
            #'target': 'new',
            'res_id': res_id,  # IDs selected
            # TODO domain for filter?
           }

class create_mrp_production_wizard(osv.osv_memory):
    ''' Wizard that create a production order based on selected order lines
    '''
    _name = "mrp.production.create.wizard"
    
    # Utility funtion
    def preserve_window(self, cr, uid, ids, context=None):
        ''' Create action for return the same open wizard window
        '''
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[
            ('model', '=', 'mrp.production.create.wizard'),
            ('name','=','Wizard create production order')])
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Wizard create production order",
            'res_model': 'mrp.production.create.wizard',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'nodestroy': True,
        }
                                
    # Wizard button:
    def action_create_mrp_production_order(self, cr, uid, ids, context=None):
        ''' Create production order based on product_id and depend on quantity
            Redirect mrp.production form after
        '''
        if context is None:
           context = {}

        wizard_browse=self.browse(cr, uid, ids, context=context)[0] # wizard fields proxy

        # Create a production order and open it:
        production_pool=self.pool.get("mrp.production")
        data={'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.production'),
              'product_id': wizard_browse.product_id.id,
              'product_qty': wizard_browse.total,
              'product_uom': wizard_browse.product_id.uom_id.id,
              'date_planned': wizard_browse.date_deadline,
              'bom_id': wizard_browse.bom_id.id,
              'user_id': uid,
              #'origin': "mexal order",
              'order_lines_ids': [(6,0,context.get("active_ids",[]))],
              }
        #if wizard_browse.all_in_one: # Create lavoration order
        #    pass#data['']
                  
        p_id = self.pool.get("mrp.production").create(cr, uid, data, context=context)  
        # Load element from BOM:
        self.pool.get("mrp.production")._action_load_materials_from_bom(cr, uid, p_id, context=context)    
        return return_view(self, cr, uid, p_id, "mrp.mrp_production_form_view", "mrp.production") 
        #return {'type':'ir.actions.act_window_close'}   # close

    # default function:        
    def default_oc_list(self, cr, uid, field, context=None):
        ''' Get list of order for confirm as default
        '''
        sol_pool = self.pool.get('sale.order.line')
        ids = sol_pool.search(cr, uid, [('id','in',context.get("active_ids",[]))], context=context)
        sol_browse = sol_pool.browse(cr, uid, ids, context=context) 
                
        default = {
            "list": _("- Q. in store (don't produce): %6.3f\n") % (
                sol_browse[0].product_id.accounting_qty if (len(sol_browse)>0 and sol_browse[0].product_id) else 0.0), 
            "error": False, 
            "total": 0.0 - (sol_browse[0].product_id.accounting_qty if (len(sol_browse)>0 and sol_browse[0].product_id) else 0.0), 
            "product": False, 
            "deadline": False, 
            "bom": False
        }
             
        res = default.get(field, False)
        
        old_product_id = False       
        try:
            if field == "product":
                return sol_browse[0].product_id.id
        except:
            return False    
        try:
            if field=="bom":
                return self.pool.get("mrp.bom").search(cr, uid, [('product_id','=',sol_browse[0].product_id.id)], context=context)
        except:
            return False    
        
        for item in sol_browse:
            if old_product_id==False:
                old_product_id=item.product_id.id
                
            # Test function mode ###############################################    
            if field =="list":
                if item.product_id.id != old_product_id:
                    res="Error! Choose order line that are of one product ID"
                    break            
                        
                res+="+ OC: %s [Row: %s] q.: %s (Scad.: %s).\n" % (
                    item.order_id.name,
                    item.sequence,
                    item.product_uom_qty,
                    "%s/%s/%s" % (
                        item.date_deadline[8:10],
                        item.date_deadline[5:7],
                        item.date_deadline[:4]) if item.date_deadline else "Not present!"
                    )
            elif field == "error":
                if item.product_id.id != old_product_id:
                    return True
            elif field == "total":
                res += item.product_uom_qty or 0.0
            elif field == "deadline":
                if not res:
                    res = item.date_deadline
                if item.date_deadline < res:
                    res = item.date_deadline      
        return res
   
    _columns = {
        'name':fields.text('List of OC elements',),
        'error':fields.boolean('Error', required=False),        
        'all_in_one':fields.boolean('All in one', required=False, help="All the production is made in one lavoration"),
        'total': fields.float('Total', digits=(16, 2), required=True),
        'product_id':fields.many2one('product.product', 'Product', required=True),
        'bom_id':fields.many2one('mrp.bom', 'BOM', required=True),
        'date_deadline': fields.date('Date deadline', required=True, help="Generated automatically based on min deadline of order header selected, changeable form user but not tipped!"),
        }
        
    _defaults = {
        'name':  lambda s, cr, uid, c: s.default_oc_list(cr, uid, "list", context=c),
        'all_in_one': lambda *a: False,
        'error': lambda s, cr, uid, c: s.default_oc_list(cr, uid, "error", context=c),
        'total': lambda s, cr, uid, c: s.default_oc_list(cr, uid, "total", context=c),        
        'product_id': lambda s, cr, uid, c: s.default_oc_list(cr, uid, "product", context=c),        
        'bom_id': lambda s, cr, uid, c: s.default_oc_list(cr, uid, "bom", context=c),        
        'date_deadline': lambda s, cr, uid, c: s.default_oc_list(cr, uid, "deadline", context=c),        
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


