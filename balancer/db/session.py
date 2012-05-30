# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Session management functions."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import DisconnectionError

from balancer.common import cfg


CACHE = {
    'maker': None,
    'engine': None
}

DB_GROUP = 'sql'
DB_OPTIONS = (
    cfg.IntOpt('idle_timeout', default=3600),
    cfg.StrOpt('connection', default='sqlite:///glance.sqlite'),
)


class MySQLPingListener(object):

    """
    Ensures that MySQL connections checked out of the
    pool are alive.

    Borrowed from:
    http://groups.google.com/group/sqlalchemy/msg/a4ce563d802c929f

    Error codes caught:
    * 2006 MySQL server has gone away
    * 2013 Lost connection to MySQL server during query
    * 2014 Commands out of sync; you can't run this command now
    * 2045 Can't open shared memory; no answer from server (%lu)
    * 2055 Lost connection to MySQL server at '%s', system error: %d

    from http://dev.mysql.com/doc/refman/5.6/en/error-messages-client.html
    """

    def checkout(self, dbapi_con, con_record, con_proxy):
        try:
            dbapi_con.cursor().execute('select 1')
        except dbapi_con.OperationalError, ex:
            if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
                logging.warn('Got mysql server has gone away: %s', ex)
                raise DisconnectionError("Database server went away")
            else:
                raise


def get_session(conf, autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy session."""

    if CACHE['maker'] is None or CACHE['engine'] is None:
        CACHE['engine'] = get_engine(conf)
        CACHE['maker'] = get_maker(CACHE['engine'], autocommit,
                                   expire_on_commit)

    session = CACHE['maker']
    return session


def get_engine(conf):
    """Return a SQLAlchemy engine."""

    register_conf_opts(conf)

    connection_dict = make_url(conf.sql.connection)

    engine_args = {'pool_recycle': conf.sql.idle_timeout,
                   'echo': False,
                   'convert_unicode': True
                   }

    if 'sqlite' in connection_dict.drivername:
        engine_args['poolclass'] = NullPool

    if 'mysql' in connection_dict.drivername:
        engine_args['listeners'] = [MySQLPingListener()]

    return create_engine(conf.sql.connection, **engine_args)


def get_maker(engine, autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy sessionmaker using the given engine."""

    return sessionmaker(bind=engine, autocommit=autocommit,
                        expire_on_commit=expire_on_commit)


def register_conf_opts(conf, options=DB_OPTIONS, group=DB_GROUP):
    """Register database options."""

    conf.register_group(cfg.OptGroup(name=group))
    for option in options:
        if option.name not in conf:
            conf.register_opt(option)
