#
#

# Copyright (C) 2013 Google Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import mock

from ganeti import objects
from ganeti import rpc


def CreateRpcRunnerMock():
  """Creates a new L{mock.MagicMock} tailored for L{rpc.RpcRunner}

  """
  ret = mock.MagicMock(spec=rpc.RpcRunner)
  return ret


class RpcResultsBuilder(object):
  """Helper class which assists in constructing L{rpc.RpcResult} objects.

  This class provides some convenience methods for constructing L{rpc.RpcResult}
  objects. It is possible to create single results with the C{Create*} methods
  or to create multi-node results by repeatedly calling the C{Add*} methods and
  then obtaining the final result with C{Build}.

  The C{node} parameter of all the methods can either be a L{objects.Node}
  object, a node UUID or a node name. You have to provide the cluster config
  in the constructor if you want to use node UUID's/names.

  A typical usage of this class is as follows::

    self.rpc.call_some_rpc.return_value = \
      RpcResultsBuilder(cfg=self.cfg) \
        .AddSuccessfulNode(node1,
                           {
                             "result_key": "result_data",
                             "another_key": "other_data",
                           }) \
        .AddErrorNode(node2) \
        .Build()

  """

  def __init__(self, cfg=None, use_node_names=False):
    """Constructor.

    @type cfg: L{ganeti.config.ConfigWriter}
    @param cfg: used to resolve nodes if not C{None}
    @type use_node_names: bool
    @param use_node_names: if set to C{True}, the node field in the RPC results
          will contain the node name instead of the node UUID.
    """
    self._cfg = cfg
    self._use_node_names = use_node_names
    self._results = []

  def _GetNode(self, node_id):
    if isinstance(node_id, objects.Node):
      return node_id

    node = None
    if self._cfg is not None:
      node = self._cfg.GetNodeInfo(node_id)
      if node is None:
        node = self._cfg.GetNodeInfoByName(node_id)

    assert node is not None, "Failed to find '%s' in configuration" % node_id
    return node

  def _GetNodeId(self, node_id):
    node = self._GetNode(node_id)
    if self._use_node_names:
      return node.name
    else:
      return node.uuid

  def CreateSuccessfulNodeResult(self, node, data={}):
    """@see L{RpcResultsBuilder}

    @param node: @see L{RpcResultsBuilder}.
    @type data: dict
    @param data: the data as returned by the RPC
    @rtype: L{rpc.RpcResult}
    """
    return rpc.RpcResult(data=(True, data), node=self._GetNodeId(node))

  def CreateFailedNodeResult(self, node):
    """@see L{RpcResultsBuilder}

    @param node: @see L{RpcResultsBuilder}.
    @rtype: L{rpc.RpcResult}
    """
    return rpc.RpcResult(failed=True, node=self._GetNodeId(node))

  def CreateOfflineNodeResult(self, node):
    """@see L{RpcResultsBuilder}

    @param node: @see L{RpcResultsBuilder}.
    @rtype: L{rpc.RpcResult}
    """
    return rpc.RpcResult(failed=True, node=self._GetNodeId(node))

  def CreateErrorNodeResult(self, node, error_msg=None):
    """@see L{RpcResultsBuilder}

    @param node: @see L{RpcResultsBuilder}.
    @type error_msg: string
    @param error_msg: the error message as returned by the RPC
    @rtype: L{rpc.RpcResult}
    """
    return rpc.RpcResult(data=(False, error_msg), node=self._GetNodeId(node))

  def AddSuccessfulNode(self, node, data={}):
    """@see L{CreateSuccessfulNode}"""
    self._results.append(self.CreateSuccessfulNodeResult(node, data))
    return self

  def AddFailedNode(self, node):
    """@see L{CreateFailedNode}"""
    self._results.append(self.CreateFailedNodeResult(node))
    return self

  def AddOfflineNode(self, node):
    """@see L{CreateOfflineNode}"""
    self._results.append(self.CreateOfflineNodeResult(node))

  def AddErrorNode(self, node, error_msg=None):
    """@see L{CreateErrorNode}"""
    self._results.append(self.CreateErrorNodeResult(node, error_msg=error_msg))

  def Build(self):
    """Creates a dictionary holding multi-node results

    @rtype: dict
    """
    return dict((result.node, result) for result in self._results)