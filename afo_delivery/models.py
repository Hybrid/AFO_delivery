# -*- coding: utf-8 -*-

from openerp import models, fields, api

class afo_delivery_environment(models.Model):
    _name = 'afo_delivery.environment'
    _inherit = 'mail.thread'
    _track = {
        'env_status' : {
            'afo_delivery.mt_env_changed': lambda self, cr, uid, obj, ctx=None: obj.env_status,
        },
        'component_ids':{
            'afo_delivery.mt_env_changed': lambda self, cr, uid, obj, ctx=None: obj.component_ids,
        },
        'delivery_ids':{
            'afo_delivery.mt_env_delivery_changed': lambda self, cr, uid, obj, ctx=None: obj.delivery_ids,
        }
    }

    name = fields.Char('Title')
    description = fields.Text('Description')
    env_status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive'), ('deleted', 'Deleted')], 'Status', 
        help="""* Status of the environment:
        \n Active: The environment is currently ready for use.
        \n Inactive: The environment is currently not available for use.
        \n Deleted: The environment does not exist anymore
        """, default='active', track_visibility='onchange' )
    is_production = fields.Boolean(string='Production Environment?',default=False)
    component_ids = fields.One2many('afo_delivery.environment_component', 'environment_id', 'Installed Component', track_visibility='onchange')
    delivery_ids = fields.One2many('afo_delivery.environment_delivery', 'environment_id', 'Installed Deliveries', track_visibility='onchange')

class afo_delivery_component_type(models.Model):
    _name = 'afo_delivery.component_type'

    name = fields.Char()
    description = fields.Text('Description')

class afo_delivery_environment_component(models.Model):
    _name = 'afo_delivery.environment_component'

    name = fields.Char('Name', compute='_compute_name')
    component_type = fields.Many2one('afo_delivery.component_type', 'Component', required=True)
    version = fields.Char('Version', required=True)
    environment_id = fields.Many2one('afo_delivery.environment', 'Environment', required=True)
    note = fields.Text('Notes') 
    install_date = fields.Date('Installation Date')
    install_user = fields.Many2one('res.users', string='Installed by')
    comp_status = fields.Selection([('active', 'Active'), ('inactive', 'Obsolete')], 'Status', 
        help="""* Status of the component:
        \n Active: The component is still used in some environment, maybe in production
        \n Obsolete: The component is outdated and is kept for consistency of older deliveries
        """, default='active')

    _defaults={
            'install_user':lambda self, cr, uid, ctx=None: uid,
            'install_date': fields.date.today(),
        }

    def _compute_name(self):
        for rec in self:
            rec.name = "%s - %s" % (rec.component_type.name, rec.version)

    def write(self, cr, uid, ids, vals, context=None):
        res = super(afo_delivery_environment_component, self).write(cr, uid, ids, vals, context=context)
        env_obj = self.pool.get('afo_delivery.environment')
        for rec in self.browse(cr, uid, ids, context=context):
            message = '<span>Component [%s] was changed</span> <br/>' % rec.component_type.name
            message += '%s - Status= %s' % (rec.name, rec.comp_status)
            env_obj.message_post(cr, uid, [rec.environment_id.id], body=message, context=context)
        return res

class afo_delivery_delivery(models.Model):
    _name = 'afo_delivery.delivery'
    _order = 'delivery_date desc'

    _inherit = 'mail.thread'
    _track = {
        'del_status' : {
            'afo_delivery.mt_del_status': lambda self, cr, uid, obj, ctx=None: obj.del_status,
        },
        'environment_ids':{
            'afo_delivery.mt_del_deployed': lambda self, cr, uid, obj, ctx=None: obj.environment_ids,
        },
    }

    name = fields.Char()
    crm_defect_idt = fields.Char('CRM Defect ID', help=""" The identifier of the defect in the vendor's CRM """)
    external_defect_idt = fields.Char('External Defect ID', help=""" The identifier of the defect in your bug tracking tool """)
    description = fields.Text('Description')
    delivery_date = fields.Date('Delivery Date')
    content = fields.Text('Content', help=""" Files contained in the delivery (max 30) """)
    del_status = fields.Selection([('new', 'New'), ('test', 'In Test'), ('discard', 'Discarded'), ('accept', 'Accepted'), ('production', 'Production')], 'Status',
         help="""* Status of the environment (please note all changes are manual):
        \n New: The delivery has been received and no action was taken yet
        \n In Test: The delivery was installed on at least one environment and is currently being tested
        \n Discarded: The delivery was refused due to some failed test or a newer version
        \n Accepted: The delivery has been successfully tested and is ready to go in production
        \n Production: The delivery has been installed on the production environment and is LIVE
        """, default='new')
    owner_name = fields.Char('Owner', help=""" The person who made the delivery""")
    environment_ids = fields.One2many('afo_delivery.environment_delivery', 'delivery_id', 'Installation', track_visibility='onchange')
    component_ids = fields.One2many('afo_delivery.delivery_component', 'delivery_id', 'Components Impacted')

    def deploy_to_environment(self, cr, uid, id, context=None):
        return True

    def discard(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'del_status': 'discard'}, context=context)
        return True
    
class afo_delivery_environment_delivery(models.Model):
    _name = 'afo_delivery.environment_delivery'

    _order = 'install_date desc, planned_date desc'

    name = fields.Char(compute='_compute_name')
    environment_id = fields.Many2one('afo_delivery.environment', 'Environment', required=True)
    delivery_id = fields.Many2one('afo_delivery.delivery', 'Delivery', required=True)
    install_date = fields.Date('Installation Date')
    install_user = fields.Many2one('res.users', string='Installed by')
    install_status = fields.Selection([('planned', 'Planned'), ('in_progress', 'In Progress'), ('failed', 'Failed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], 'Installation Status',
                    help=""" * Status of the delivery installation:
                    \n Planned: Delivery has been planned to be installed on this environment at the planned date
                    \n In Progress: Delivery is currently being installed on the environment
                    \n Failed: Installation of the delivery failed
                    \n Completed: Delivery was successfully installed
                    \n Cancelled: Installation on this envronment was cancelled""", default='planned')
    planned_date = fields.Date('Planned Date')
    #technical field used to know from which view we are coming from. Used only for propagation of information to followers!
    from_view = fields.Char()

    def _compute_name(self):
        for rec in self:
            rec.name = '%s - [%s]: %s' % (rec.delivery_id.name, rec.environment_id.name, rec.install_status)

    def create(self, cr, uid, vals, context=None):
        res = super(afo_delivery_environment_delivery, self).create(cr, uid, vals, context=context)
        env_obj = self.pool.get('afo_delivery.environment')
        del_obj = self.pool.get('afo_delivery.delivery')
        for rec in self.browse(cr, uid, res, context=context):
            message = '<span> %s </span> <br/>' % (rec.name)
            # Only propagate information to the other part of the many2many relationship since it is already tracked when working from the main model.
            if rec.from_view == 'env_view':
                del_obj.message_post(cr, uid, [rec.delivery_id.id], body=message, context=context, subtype='mt_del_deployed')
            elif rec.from_view == 'del_view':
                env_obj.message_post(cr, uid, [rec.environment_id.id], body=message, context=context, subtype='mt_env_delivery_changed')
            else:
                del_obj.message_post(cr, uid, [rec.delivery_id.id], body=message, context=context, subtype='mt_del_deployed')
                env_obj.message_post(cr, uid, [rec.environment_id.id], body=message, context=context, subtype='mt_env_delivery_changed')
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(afo_delivery_environment_delivery, self).write(cr, uid, ids, vals, context=context)
        env_obj = self.pool.get('afo_delivery.environment')
        del_obj = self.pool.get('afo_delivery.delivery')
        for rec in self.browse(cr, uid, ids, context=context):
            message = '<span>[%s] - Delivery [%s] was changed</span> <br/>' % (rec.environment_id.name, rec.delivery_id.name)
            if rec.install_status == 'planned':
                if rec.planned_date:
                    message += 'Installation is planned on %s' % str(rec.planned_date)
                else:
                    message += 'Installation is planned but no date were provided'
            elif rec.install_status == 'in_progress':
                message += 'Installation of this delivery is in progress!'
            elif rec.install_status == 'failed':
                message += 'A problem occured during the installation of the delivery!'
            elif rec.install_status == 'completed':
                message += 'Successfully deployed!'
            elif rec.install_status == 'cancelled':
                message += 'This installation was cancelled'
            env_obj.message_post(cr, uid, [rec.environment_id.id], body=message, context=context, subtype='mt_env_delivery_changed')
            del_obj.message_post(cr, uid, [rec.delivery_id.id], body=message, context=context, subtype='mt_del_deployed')
        return res

class afo_delivery_delivery_component(models.Model):
    _name = 'afo_delivery.delivery_component'

    delivery_id = fields.Many2one('afo_delivery.delivery', 'Delivery', required=True)
    component_id = fields.Many2one('afo_delivery.component_type', 'Component', required=True)

