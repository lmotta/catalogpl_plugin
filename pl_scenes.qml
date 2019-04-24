<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" simplifyAlgorithm="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" simplifyMaxScale="1" labelsEnabled="0" simplifyDrawingTol="1" simplifyLocal="1" readOnly="0" simplifyDrawingHints="1" version="3.4.7-Madeira" minScale="1e+8">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" type="singleSymbol" forceraster="0" enableorderby="0">
    <symbols>
      <symbol type="fill" force_rhr="0" alpha="0.344" clip_to_extent="1" name="0">
        <layer pass="0" enabled="1" class="SimpleFill" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="60,175,213,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="date1" value="2019-03-07"/>
    <property key="date2" value="2019-03-10"/>
    <property key="dualview/previewExpressions">
      <value>item_id</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="item_type" value="PSScene4Band"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory penColor="#000000" diagramOrientation="Up" enabled="0" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" labelPlacementMethod="XHeight" sizeType="MM" rotationOffset="270" scaleBasedVisibility="0" scaleDependency="Area" penAlpha="255" minScaleDenominator="0" penWidth="0" backgroundAlpha="255" opacity="1" width="15" lineSizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" height="15" maxScaleDenominator="1e+8" barWidth="5" minimumSize="0">
      <fontProperties style="Regular" description="Noto Sans,10,-1,0,50,0,0,0,0,0,Regular"/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings zIndex="0" placement="1" dist="0" priority="0" linePlacementFlags="18" obstacle="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="item_type">
      <editWidget type="Hidden">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="item_id">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="date">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="meta_json">
      <editWidget type="Hidden">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="meta_jsize">
      <editWidget type="Hidden">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="item_type" name=""/>
    <alias index="1" field="item_id" name=""/>
    <alias index="2" field="date" name=""/>
    <alias index="3" field="meta_json" name=""/>
    <alias index="4" field="meta_jsize" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" expression="" field="item_type"/>
    <default applyOnUpdate="0" expression="" field="item_id"/>
    <default applyOnUpdate="0" expression="" field="date"/>
    <default applyOnUpdate="0" expression="" field="meta_json"/>
    <default applyOnUpdate="0" expression="" field="meta_jsize"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="item_type"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="item_id"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="date"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="meta_json"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="meta_jsize"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="item_type"/>
    <constraint desc="" exp="" field="item_id"/>
    <constraint desc="" exp="" field="date"/>
    <constraint desc="" exp="" field="meta_json"/>
    <constraint desc="" exp="" field="meta_jsize"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
    <actionsetting notificationMessage="" type="1" icon="" id="{40828a1e-6547-4a9f-824f-0b2ca6ae8248}" capture="0" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'highlight'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="" name="Highlight" isEnabledOnlyWhenEditable="0">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting notificationMessage="" type="1" icon="" id="{49cbfb81-84d0-40f6-bb24-41fc68ed4611}" capture="0" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'zoom'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="" name="Zoom" isEnabledOnlyWhenEditable="0">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting notificationMessage="" type="1" icon="" id="{33cfc66a-0787-44f7-955a-d36be49cb5dc}" capture="0" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'addxyztiles'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Add XYZ tiles" name="Add XYZ tiles" isEnabledOnlyWhenEditable="0">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting notificationMessage="" type="1" icon="" id="{b7822965-b5e1-4f61-be6b-7a9f1e599d8e}" capture="0" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'downloadImages'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Downloads images" name="Downloads images" isEnabledOnlyWhenEditable="0">
      <actionScope id="Layer"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="1" sortExpression="&quot;date&quot;">
    <columns>
      <column width="-1" type="field" hidden="0" name="item_type"/>
      <column width="-1" type="field" hidden="0" name="item_id"/>
      <column width="-1" type="field" hidden="0" name="date"/>
      <column width="-1" type="field" hidden="0" name="meta_json"/>
      <column width="-1" type="field" hidden="0" name="meta_jsize"/>
      <column width="-1" type="actions" hidden="1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit>loadForm</editforminit>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>/home/lmotta/.local/share/QGIS/QGIS3/profiles/default/python/plugins/catalogpl_plugin/form.py</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <widgets/>
  <previewExpression>item_id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
