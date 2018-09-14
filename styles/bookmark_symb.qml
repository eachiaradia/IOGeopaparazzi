<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyAlgorithm="0" readOnly="0" simplifyDrawingHints="1" maxScale="0" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" simplifyMaxScale="1" version="3.2.0-Bonn" minScale="1e+8" simplifyDrawingTol="1" labelsEnabled="0">
  <renderer-v2 enableorderby="0" symbollevels="0" type="singleSymbol" forceraster="0">
    <symbols>
      <symbol clip_to_extent="1" type="fill" alpha="1" name="0">
        <layer enabled="1" locked="0" class="SimpleFill" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="120,164,41,92" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="120,164,41,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="1" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="no" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory barWidth="5" penWidth="0" lineSizeScale="3x:0,0,0,0,0,0" rotationOffset="270" backgroundColor="#ffffff" enabled="0" opacity="1" minScaleDenominator="0" penColor="#000000" sizeType="MM" sizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" height="15" penAlpha="255" diagramOrientation="Up" width="15" labelPlacementMethod="XHeight" scaleBasedVisibility="0" backgroundAlpha="255" minimumSize="0" maxScaleDenominator="1e+8" scaleDependency="Area">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" dist="0" placement="1" zIndex="0" showAll="1" linePlacementFlags="18" priority="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <fieldConfiguration>
    <field name="_id">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="lon">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="lat">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="zoom">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="bnorth">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="bsouth">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="bwest">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="beast">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="text">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="_id" name=""/>
    <alias index="1" field="lon" name=""/>
    <alias index="2" field="lat" name=""/>
    <alias index="3" field="zoom" name=""/>
    <alias index="4" field="bnorth" name=""/>
    <alias index="5" field="bsouth" name=""/>
    <alias index="6" field="bwest" name=""/>
    <alias index="7" field="beast" name=""/>
    <alias index="8" field="text" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="_id" expression="" applyOnUpdate="0"/>
    <default field="lon" expression="" applyOnUpdate="0"/>
    <default field="lat" expression="" applyOnUpdate="0"/>
    <default field="zoom" expression="" applyOnUpdate="0"/>
    <default field="bnorth" expression="" applyOnUpdate="0"/>
    <default field="bsouth" expression="" applyOnUpdate="0"/>
    <default field="bwest" expression="" applyOnUpdate="0"/>
    <default field="beast" expression="" applyOnUpdate="0"/>
    <default field="text" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="_id" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="lon" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="lat" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="zoom" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="bnorth" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="bsouth" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="bwest" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="beast" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="text" exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="_id" exp="" desc=""/>
    <constraint field="lon" exp="" desc=""/>
    <constraint field="lat" exp="" desc=""/>
    <constraint field="zoom" exp="" desc=""/>
    <constraint field="bnorth" exp="" desc=""/>
    <constraint field="bsouth" exp="" desc=""/>
    <constraint field="bwest" exp="" desc=""/>
    <constraint field="beast" exp="" desc=""/>
    <constraint field="text" exp="" desc=""/>
  </constraintExpressions>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column width="-1" hidden="0" type="field" name="_id"/>
      <column width="-1" hidden="0" type="field" name="lon"/>
      <column width="-1" hidden="0" type="field" name="lat"/>
      <column width="-1" hidden="0" type="field" name="zoom"/>
      <column width="-1" hidden="0" type="field" name="bnorth"/>
      <column width="-1" hidden="0" type="field" name="bsouth"/>
      <column width="-1" hidden="0" type="field" name="bwest"/>
      <column width="-1" hidden="0" type="field" name="beast"/>
      <column width="-1" hidden="0" type="field" name="text"/>
      <column width="-1" hidden="1" type="actions"/>
    </columns>
  </attributetableconfig>
  <editform></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
I form QGIS possono avere una funzione Python che può essere chiamata quando un form viene aperto.

Usa questa funzione per aggiungere logica extra ai tuoi forms..

Inserisci il nome della funzione nel campo "Funzione Python di avvio".

Segue un esempio:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="_id"/>
    <field editable="1" name="beast"/>
    <field editable="1" name="bnorth"/>
    <field editable="1" name="bsouth"/>
    <field editable="1" name="bwest"/>
    <field editable="1" name="lat"/>
    <field editable="1" name="lon"/>
    <field editable="1" name="text"/>
    <field editable="1" name="zoom"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="_id"/>
    <field labelOnTop="0" name="beast"/>
    <field labelOnTop="0" name="bnorth"/>
    <field labelOnTop="0" name="bsouth"/>
    <field labelOnTop="0" name="bwest"/>
    <field labelOnTop="0" name="lat"/>
    <field labelOnTop="0" name="lon"/>
    <field labelOnTop="0" name="text"/>
    <field labelOnTop="0" name="zoom"/>
  </labelOnTop>
  <widgets/>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <expressionfields/>
  <previewExpression>_id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
