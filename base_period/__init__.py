##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from . import models  # noqa
from odoo import api, SUPERUSER_ID
import time


def load(cr):
    date = time.strftime('%Y-%m-01')
    cr.execute("update account_move set date=%(date)s",
        {'date': date})
