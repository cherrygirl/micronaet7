# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

{
    'name': 'Construction Catalog',
    'version': '0.0.1',
    'category': 'Generic Modules / ETL',
    'description': """
        Construction catalog for import the newest catalog 
        on web and import product and categories
    """,
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        'product',
        'stock',
        'sale',
    ],
    'init_xml': [], 
    'data': [
        'security/ir.model.access.csv',
        
        'scheduler.xml',
        'construction_views.xml',        
        
        'data/construction_data.xml',
        'data/uom_data.xml',
    ],
    'demo_xml': [],
    'active': False, 
    'installable': True, 
}
