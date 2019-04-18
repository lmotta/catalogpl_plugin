<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="0" simplifyAlgorithm="0" version="3.4.6-Madeira" hasScaleBasedVisibilityFlag="0" maxScale="0" simplifyDrawingHints="1" simplifyMaxScale="1" minScale="1e+8" styleCategories="AllStyleCategories" simplifyDrawingTol="1" simplifyLocal="1" readOnly="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" enableorderby="0" forceraster="0" symbollevels="0">
    <symbols>
      <symbol type="fill" force_rhr="0" name="0" clip_to_extent="1" alpha="0.344">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
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
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="date1" value="2019-04-15"/>
    <property key="date2" value="2019-04-17"/>
    <property key="dualview/previewExpressions" value="item_id"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="item_type" value="PSScene4Band"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory backgroundAlpha="255" sizeType="MM" minScaleDenominator="0" lineSizeScale="3x:0,0,0,0,0,0" height="15" width="15" maxScaleDenominator="1e+8" minimumSize="0" penWidth="0" penAlpha="255" scaleDependency="Area" backgroundColor="#ffffff" opacity="1" sizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" rotationOffset="270" penColor="#000000" barWidth="5" enabled="0" diagramOrientation="Up" labelPlacementMethod="XHeight" lineSizeType="MM">
      <fontProperties description="Noto Sans,10,-1,0,50,0,0,0,0,0,Regular" style="Regular"/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" priority="0" showAll="1" placement="1" dist="0" zIndex="0" linePlacementFlags="18">
    <properties>
      <Option type="Map">
        <Option type="QString" name="name" value=""/>
        <Option name="properties"/>
        <Option type="QString" name="type" value="collection"/>
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
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="date">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
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
    <alias field="item_type" name="" index="0"/>
    <alias field="item_id" name="" index="1"/>
    <alias field="date" name="" index="2"/>
    <alias field="meta_json" name="" index="3"/>
    <alias field="meta_jsize" name="" index="4"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="item_type" expression=""/>
    <default applyOnUpdate="0" field="item_id" expression=""/>
    <default applyOnUpdate="0" field="date" expression=""/>
    <default applyOnUpdate="0" field="meta_json" expression=""/>
    <default applyOnUpdate="0" field="meta_jsize" expression=""/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" field="item_type" constraints="0" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" field="item_id" constraints="0" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" field="date" constraints="0" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" field="meta_json" constraints="0" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" field="meta_jsize" constraints="0" unique_strength="0" exp_strength="0"/>
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
    <actionsetting id="{9955ade2-4aa6-4229-a26f-eeab7164652d}" type="1" shortTitle="" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'highlight'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Highlight" notificationMessage="" capture="0" icon="">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting id="{5ed235fb-0dae-4bec-b727-033d0f365c20}" type="1" shortTitle="" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'zoom'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Zoom" notificationMessage="" capture="0" icon="">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting id="{c2dc7c97-1212-41b9-a273-51143f72a025}" type="1" shortTitle="Add XYZ tiles" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'addxyztiles'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Add XYZ tiles" notificationMessage="" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting id="{f5f6023c-4533-4886-8e33-ff1d64e87a68}" type="1" shortTitle="Update assets status" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'updateAssetsStatus'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Update assets status" notificationMessage="" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting id="{f55b110f-3f41-4c0d-9657-5f66d54eca50}" type="1" shortTitle="Active assets" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'activeAssets'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Active assets" notificationMessage="" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
    <actionsetting id="{12c5a841-ae07-4fb1-aa47-088c9a380765}" type="1" shortTitle="Downloads images" action="from qgis import utils as QgsUtils&#xa;&#xa;def getFunctionActionsForm(pluginName):&#xa;    &quot;&quot;&quot;&#xa;    Function from Plugin for actions Form&#xa;&#xa;    :param pluginName: Name of plugin&#xa;    &quot;&quot;&quot;&#xa;    getInstanceInPlugin = lambda plugin: plugin.dock # _init_.py: initGui()&#xa;    getActionsForm = lambda plugin: plugin.dock.pl.actionsForm # class_instance.py: _init_()&#xa;    plugins = {}&#xa;    for name, obj in QgsUtils.plugins.items():&#xa;        plugins[ name ] = obj&#xa;    if not pluginName in plugins:&#xa;        return { 'isOk': False, 'message': &quot;Missing {name} Plugin.&quot;.format(name=pluginName) }&#xa;    if getInstanceInPlugin( plugins[ pluginName ] ) is None:&#xa;        return { 'isOk': False, 'message': &quot;Run the {name} Plugin.&quot;.format(name=pluginName) }&#xa;    return { 'isOk': True, 'function': getActionsForm( plugins[ pluginName ] ) }&#xa;&#xa;nameAction = 'downloadImages'&#xa;title = &quot;Action Planet&quot;&#xa;msgBar =  QgsUtils.iface.messageBar()&#xa;r = getFunctionActionsForm('catalogpl_plugin')&#xa;if r['isOk']:&#xa;    actionsForm = r['function']&#xa;    r = actionsForm( nameAction, [% $id %] )&#xa;    if not r['isOk']:&#xa;        msgBar.pushCritical( title, r['message'] )&#xa;else:&#xa;    msgBar.pushCritical( title, r['message'] )&#xa;" isEnabledOnlyWhenEditable="0" name="Downloads images" notificationMessage="" capture="0" icon="">
      <actionScope id="Layer"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column type="field" name="item_type" width="-1" hidden="0"/>
      <column type="field" name="item_id" width="-1" hidden="0"/>
      <column type="field" name="date" width="-1" hidden="0"/>
      <column type="field" name="meta_json" width="-1" hidden="0"/>
      <column type="field" name="meta_jsize" width="-1" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
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
