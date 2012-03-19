# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import logging

import routes
import loadbalancers


from balancer.common import wsgi

logger = logging.getLogger(__name__)


class API(wsgi.Router):

    """WSGI router for balancer v1 API requests."""

    def __init__(self, conf, **local_conf):
        self.conf = conf
        mapper = routes.Mapper()

        lb_resource = loadbalancers.create_resource(self.conf)

        mapper.resource("loadbalancers", "loadbalancers", controller=lb_resource,
                        collection={'detail': 'GET'})
                        
        mapper.connect("/loadbalancers/", controller=lb_resource, action="index")
        
        mapper.connect("/loadbalancers/{id}", controller=lb_resource,
                       action="loadbalancer_data", conditions=dict(method=["GET"]))
        
        mapper.connect("/loadbalancers/",
                       controller=lb_resource,
                       action="create",
                       conditions=dict(method=["POST"]))


   

        super(API, self).__init__(mapper)