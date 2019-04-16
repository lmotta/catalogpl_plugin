<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" simplifyDrawingTol="1" version="3.4.6-Madeira" labelsEnabled="0" simplifyMaxScale="1" simplifyAlgorithm="0" simplifyDrawingHints="1" simplifyLocal="1" readOnly="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" minScale="1e+8">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" enableorderby="0" forceraster="0" type="singleSymbol">
    <symbols>
      <symbol name="0" clip_to_extent="1" force_rhr="0" alpha="0.344" type="fill">
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="date1" value="2018-03-01"/>
    <property key="date2" value="2019-04-01"/>
    <property key="dualview/previewExpressions" value="item_id"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="item_type" value="SkySatScene"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0" enabled="0" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" labelPlacementMethod="XHeight" barWidth="5" opacity="1" diagramOrientation="Up" height="15" width="15" rotationOffset="270" backgroundAlpha="255" sizeType="MM" lineSizeType="MM" scaleBasedVisibility="0" minScaleDenominator="0" maxScaleDenominator="1e+8" penColor="#000000" penWidth="0" scaleDependency="Area" penAlpha="255">
      <fontProperties description="Noto Sans,10,-1,0,50,0,0,0,0,0,Regular" style="Regular"/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" obstacle="0" dist="0" zIndex="0" placement="1" linePlacementFlags="18" showAll="1">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
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
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="date">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
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
    <alias name="" field="item_type" index="0"/>
    <alias name="" field="item_id" index="1"/>
    <alias name="" field="date" index="2"/>
    <alias name="" field="meta_json" index="3"/>
    <alias name="" field="meta_jsize" index="4"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="item_type" applyOnUpdate="0" expression=""/>
    <default field="item_id" applyOnUpdate="0" expression=""/>
    <default field="date" applyOnUpdate="0" expression=""/>
    <default field="meta_json" applyOnUpdate="0" expression=""/>
    <default field="meta_jsize" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" constraints="0" field="item_type" exp_strength="0" unique_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="item_id" exp_strength="0" unique_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="date" exp_strength="0" unique_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="meta_json" exp_strength="0" unique_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="meta_jsize" exp_strength="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="item_type" exp="" desc=""/>
    <constraint field="item_id" exp="" desc=""/>
    <constraint field="date" exp="" desc=""/>
    <constraint field="meta_json" exp="" desc=""/>
    <constraint field="meta_jsize" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
    <actionsetting name="Highlight" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'highlight'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{b803e4af-161c-489d-891b-5ec896afa933}" type="1" capture="0" icon="">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting name="Zoom" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'zoom'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{f9551787-fea0-4f4b-8313-53eb4fb16ff6}" type="1" capture="0" icon="">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting name="Add XYZ tiles" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'addxyztiles'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Add XYZ tiles" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{ce059ffb-ec58-4714-b170-30efc33ce1dd}" type="1" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting name="Update assets status" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'updateAssetsStatus'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Update assets status" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{c6c754f7-10e1-4499-97c6-b98e66e91e1b}" type="1" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting name="Active assets" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'activeAssets'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Active assets" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{bca09050-fc75-4a9b-a9c9-670300b6bf9d}" type="1" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting name="Downloads images" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if plugins [pluginName ].dock is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': plugins[ pluginName ].dock.pl.actionsForm }&#xa;&#xa;nameAction = 'downloadImages'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" shortTitle="Downloads images" notificationMessage="" isEnabledOnlyWhenEditable="0" id="{0730750d-c148-4f83-9a51-9df5428aa3e0}" type="1" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column name="item_type" width="-1" type="field" hidden="0"/>
      <column name="item_id" width="-1" type="field" hidden="0"/>
      <column name="date" width="-1" type="field" hidden="0"/>
      <column name="meta_json" width="-1" type="field" hidden="0"/>
      <column name="meta_jsize" width="-1" type="field" hidden="0"/>
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
  <editorlayout>uifilelayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <widgets/>
  <previewExpression>item_id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
