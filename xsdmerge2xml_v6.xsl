<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:fn="http://www.w3.org/2005/xpath-functions">
	<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
	<!-- Script to create an XML file from the .xsd schema, but adding the appinfo nodes to the outputs -->
	<!-- we avoid XMLSpy -->
	<!-- derived from FI EUITM -->
	<xsl:template match="/*">
		<xsl:apply-templates select="/*/xs:element" mode="declare_child"/>
	</xsl:template>
	<!-- First, we scan at the CPO level , unsure what the declare_child is needed for, select all xs:elements-->
	<xsl:template name="process_element" match="xs:element" mode="declare_child">
		<xsl:choose>
			<xsl:when test="@name">
				<!-- this element has a name, create an element with this name -->
				<xsl:element name="{@name}">
					<xsl:apply-templates select="xs:annotation"/>
					<!-- add the documentation and appinfo from the schema -->
					<!-- if the element has a type, expand it as a complex type-->
					<xsl:if test="@type">
					    <xsl:call-template name="doComplexTypeDeclare">
							<xsl:with-param name="thisType" select="@type"/>
						</xsl:call-template>
					</xsl:if>
					<!-- just drill down -->
					<xsl:apply-templates select="*/*/xs:element" mode="declare_child"/>
					<xsl:apply-templates select="*/*/xs:group"/>
					<xsl:apply-templates select="xs:complexType/xs:group"/>
					<!-- if there is a group, expand it -->
				</xsl:element>
				<xsl:if test="@maxOccurs">
				<xsl:element name="{@name}">
					<xsl:apply-templates select="xs:annotation"/>
					<!-- add the documentation and appinfo from the schema -->
					<!-- if the element has a type, expand it as a complex type-->
					<xsl:if test="@type">
					    <xsl:call-template name="doComplexTypeDeclare">
							<xsl:with-param name="thisType" select="@type"/>
						</xsl:call-template>
					</xsl:if>
					<!-- just drill down -->
					<xsl:apply-templates select="*/*/xs:element" mode="declare_child"/>
					<xsl:apply-templates select="*/*/xs:group"/>
					<xsl:apply-templates select="xs:complexType/xs:group"/>
					<!-- if there is a group, expand it -->
				</xsl:element>
				</xsl:if>
			</xsl:when>
			<xsl:when test="@ref">
				<!-- if this has a reference, just expand the reference -->
				<xsl:call-template name="doRefDeclare">
					<xsl:with-param name="thisRef" select="@ref"/>
				</xsl:call-template>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template match="xs:annotation[ancestor::xs:element[@name='ids_properties']]">
		<!-- do not annotate IDS -->
	</xsl:template>
	<xsl:template match="xs:annotation">
		<xsl:apply-templates select="xs:documentation"/>
		<xsl:apply-templates select="xs:appinfo"/>
	</xsl:template>
	<xsl:template match="xs:group">
		<!-- expand any group -->
		<xsl:call-template name="doGroupDeclare">
			<xsl:with-param name="thisRef" select="@ref"/>
		</xsl:call-template>
	</xsl:template>
	<xsl:template match="xs:appinfo">
		<!-- expand appinfo -->
		<xsl:for-each select="child::*">
			<xsl:element name="{name()}">
				<xsl:value-of select="."/>
			</xsl:element>
		</xsl:for-each>
	</xsl:template>
	<xsl:template match="xs:documentation">
		<!-- replicate documentation -->
		<xsl:element name="documentation">
			<xsl:value-of select="."/>
		</xsl:element>
	</xsl:template>
	
	<!-- This template assumes that the support xsd is in the same utilities directory as the xsl -->
	<xsl:template name="doGroupDeclare">
		<!-- expand this group with a defined reference name, searching both support files -->
		<xsl:param name="thisRef"/>
		<xsl:for-each select="document('utilities/dd_support.xsd')/*/xs:group[@name=$thisRef]/xs:sequence/xs:element">
			<xsl:element name="{@name}">
				<xsl:value-of select="@fixed"/>
				<xsl:value-of select="@default"/>
			</xsl:element>
		</xsl:for-each>
		<xsl:for-each select="document('utilities/dd_support.xsd')/*/xs:group[@name='Data_Properties']/xs:sequence/xs:element">
			<xsl:element name="{@name}">
				<xsl:value-of select="@fixed"/>
				<xsl:value-of select="@default"/>
			</xsl:element>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template name="doRefDeclare">
		<!-- expand this ref with a defined reference name, searching support file -->
		<xsl:param name="thisRef"/>
		<xsl:apply-templates select="document('utilities/dd_support.xsd')/*/xs:element[@name=$thisRef]" mode="declare_child"/>
	</xsl:template>
	
	<xsl:template name="doComplexTypeDeclare">
		<xsl:param name="thisType"/>
		<xsl:if test="not(xs:complexType)"><xsl:apply-templates select="/*/xs:complexType[@name=$thisType]/*/xs:element" mode="declare_child"/></xsl:if>
		<!-- up to now, this assumes the complexType is in dd_support, it has to be extended to the case where the complexType is in the original xsd file itself, or even in an include -->
	</xsl:template>

</xsl:stylesheet>