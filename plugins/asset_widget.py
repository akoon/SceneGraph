#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class AssetWidget(NodeWidget):
    widget_type  = 'asset'
    def __init__(self, dagnode, parent=None):
        super(AssetWidget, self).__init__(dagnode, parent)