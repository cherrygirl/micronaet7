# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
###############################################################################
import os
import sys
import netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta        
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class res_partner_followup_category(orm.Model):
    ''' Followup event
    '''
    _name = 'res.partner.followup.category'
    _description = 'Partner followup category'
    
    _columns = {
        'name': fields.char('Category', size=64, required=True),
        'note': fields.text('Note'),
        }

class res_partner_followup(orm.Model):
    ''' Followup event
    '''
    _name = 'res.partner.followup'
    _description = 'Partner followup'

    # ----------------
    # Workflow method:
    # ----------------
    def wkf_follow_draft(self, cr, uid, ids, context=None):
        ''' State function for draft
        '''
        self.write(cr, uid, ids, {
            'state': 'draft', }, context=context)
        return True

    def wkf_follow_confirmed(self, cr, uid, ids, context=None):
        ''' State function for confirmed
        '''
        self.write(cr, uid, ids, {
            'ref': self.pool.get('ir.sequence').get(cr, uid, 'loan.header'),
            'confirmed_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'confirmed',
            }, context=context)
        return True

    def wkf_follow_close(self, cr, uid, ids, context=None):
        ''' State function for close
        '''
        self.write(cr, uid, ids, {
            'close_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'close', 
            }, context=context)
        return True

    def wkf_follow_cancel(self, cr, uid, ids, context=None):
        ''' State function for cancel
        '''
        self.write(cr, uid, ids, {
            'cancel_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'cancel', 
            }, context=context)
        return True
    
    _columns = {
        # Loan description:
        'ref': fields.char('Ref.', size=40, help="Reference"),            
        'name': fields.char('Description', 
            size=128, required=True, help="Title of followp elements"),            
        'agent_name': fields.char('Agent for activity', 
            size=128, help="Title of followp elements"),    
               
         #TODO m2m ??        
        'partner_id': fields.many2one('res.partner', 'Partner', 
            help='Partner that open loan or that is referred to',
            required=True),
        'created_id': fields.many2one('res.users', 'Created', 
            help='user that create followup', readonly=True),
        'assigned_id': fields.many2one('res.users', 'Assigned', 
            help='Assigned to', ),
        'note': fields.text('Note'),
        
        # Loan descriptiove information:
        'urgency':fields.selection([
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'), ], 'Urgency'),       
        'category_id': fields.many2one('res.partner.followup.category', 
            'Category', required=False, ),#ondelete='set null'),    

        'todo_date': fields.datetime('Todo max date'),
        # Date elements (used in workflow):        
        'draft_date': fields.date('Create date', readonly=True),
        'confirmed_date': fields.date('Confirmed Date', readonly=True),
        'close_date': fields.date('Close Date', readonly=True),
        'cancel_date': fields.date('Cancel Date', readonly=True),
        'counter': fields.integer('Counter'),

        # Workflow:
        'state': fields.selection([
            ('draft','Draft'),         # Draft state, to complete
            ('confirmed','Confirmed'), # Confirm information
            ('close','Close'),         # End of life of loan
            ('cancel','Reject'),       # Not approved
            ],'State', readonly=True, select=True),
        }
        
    _defaults = {
        'draft_date': lambda *a: datetime.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT),
        'urgency': lambda *a: 'medium',
        'created_id': lambda s, cr, uid, ctx: uid,
        'assigned_id': lambda s, cr, uid, ctx: uid,
        'counter': lambda *x: 1, # used for graph view
        'state': lambda *a: 'draft',
        }

class res_partner_loan(orm.Model):
    ''' Add extra relation to partner obj
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'followup_ids': fields.one2many('res.partner.followup', 'partner_id', 
            'Followup'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
