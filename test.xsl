<?xml version="1.0" encoding="ISO-8859-1" standalone="yes"?>
<?modxslt-stylesheet type="text/xsl" media="fuffa, screen and $GET[stylesheet]" href="./$GET[stylesheet]" alternate="no" title="Translation using provided stylesheet" charset="ISO-8859-1" ?>
<?modxslt-stylesheet type="text/xsl" media="screen" alternate="no" title="Show raw source of the XML file" charset="ISO-8859-1" ?>
<!-- This stylesheet implements some validation tests on IDSDef.xml -->
<xsl:stylesheet xmlns:yaslt="http://www.mod-xslt2.com/ns/2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" version="2.0" extension-element-prefixes="yaslt" xmlns:fn="http://www.w3.org/2005/02/xpath-functions" xmlns:local="http://www.example.com/functions/local" exclude-result-prefixes="local xs">
	<xsl:output method="xml" encoding="UTF-8"/>
	<!-- Function for multiplying the number of descendents with timebasepath attribute by the occurrence of the child AoS -->
	<xsl:function name="local:count-nodes" as="xs:anyAtomicType">
		<xsl:param name="nodes" as="node()*"/>
		<xsl:value-of select="$nodes[1]/@maxoccur*count($nodes[1]//field[@timebasepath])" />
		<!--		<xsl:sequence select="
    for $seq in (1 to count($nodes))
    return $nodes[$seq]@maxoccur
 "/>-->
	</xsl:function>
	<!--$cumul=0
    for $seq in (1 to count($nodes))
    $cumul = $cumul + 1
    return $cumul-->
	<xsl:template match="/*">
		<IDSs>
			<xsl:for-each select="IDS">
				<xsl:element name="IDS">
					<xsl:attribute name="name" select="@name"/>
					<xsl:apply-templates select=".//field[@data_type='struct_array' and not(@maxoccur='unbounded')]"/>
				</xsl:element>
			</xsl:for-each>
		</IDSs>
	</xsl:template>
	<!-- A generic template for printing the out_come of an error detection (adds a line to the output text report with the description of the error) -->
	<xsl:template name="count_dynamic_signals" match="field">
		<xsl:if test="not(ancestor::*[@data_type='struct_array'])">
			<!-- Do something only if this is the top level of AoS (not other AoS ancestor), otherwise skip the whole template -->
			<xsl:element name="{@name}">
				<xsl:choose>
					<!--<xsl:when test=".//field[@maxoccur and not(contains(@maxoccur,'unbounded'))]">-->
					<xsl:when test="not(.//field[@maxoccur and .//field[@timebasepath]])">
						<!-- When there is no static AoS descendent with dynamic signals below this node : just count 1) all fields having a timebasepath attribute 2) all AoS type 3 (unbounded) but avoiding couting nested AoS type 2 since they don't introduce an additional timebase -->
						<xsl:attribute name="max_dynamic_nodes" select="(count(.//field[@timebasepath]) + count(.//field[@maxoccur='unbounded' and not(ancestor::*[@maxoccur='unbounded'])])) * @maxoccur"/>
						<!-- Count all fields having a timebasepath argument + the AoS3 which are dynamic as well -->
					</xsl:when>
					<xsl:when test="count(.//field[@maxoccur and .//field[@timebasepath]])=1">
						<!-- This method overestimates a bit the number of nodes since (.//field[@timebasepath]) also counts those below further static AoS descendents ... which are also counted (correctly) in the local:count-nodes function ... but it is better to overstimate a little bit -->
						<xsl:attribute name="max_dynamic_nodes" select="(count(.//field[@timebasepath]) + count(.//field[@maxoccur='unbounded' and not(ancestor::*[@maxoccur='unbounded'])]) + local:count-nodes(.//field[@maxoccur and .//field[@timebasepath]]) ) * @maxoccur"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:attribute name="max_dynamic_nodes" select="'ERROR : unexpected case'"/>
					</xsl:otherwise>
				</xsl:choose>
				<!--<xsl:sequence select=".//field[@timebasepath]"/>-->
				<!--<xsl:attribute name='cumul'><xsl:value-of>local:count-nodes(<xsl:sequence select=".//field[@timebasepath]"/>)</xsl:value-of></xsl:attribute>-->
			</xsl:element>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>